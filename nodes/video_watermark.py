import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoWatermark(FFmpegBase):
    """
    视频水印处理节点
    功能：为视频添加图片或文字水印
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "watermark_type": (["image", "text"], {"default": "image"}),
                "position": (["top_left", "top_right", "bottom_left", "bottom_right", "center"], 
                           {"default": "bottom_right"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "image_path": ("STRING", {"default": ""}),
                "text_content": ("STRING", {"default": ""}),
                "font_file": ("STRING", {"default": ""}),
                "font_size": ("INT", {"default": 24, "min": 8, "max": 72}),
                "font_color": ("STRING", {"default": "white"}),
                "opacity": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0}),
                "margin": ("INT", {"default": 10, "min": 0}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "add_watermark"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"watermark_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def get_position_expression(self, position: str, margin: int) -> Tuple[str, str]:
        """获取水印位置表达式"""
        positions = {
            "top_left": (f"{margin}", f"{margin}"),
            "top_right": (f"main_w-overlay_w-{margin}", f"{margin}"),
            "bottom_left": (f"{margin}", f"main_h-overlay_h-{margin}"),
            "bottom_right": (f"main_w-overlay_w-{margin}", f"main_h-overlay_h-{margin}"),
            "center": ("(main_w-overlay_w)/2", "(main_h-overlay_h)/2"),
        }
        return positions.get(position, positions["bottom_right"])

    def add_watermark(self, input_video: str, watermark_type: str,
                     position: str, use_gpu: bool,
                     image_path: str = "", text_content: str = "",
                     font_file: str = "", font_size: int = 24,
                     font_color: str = "white", opacity: float = 0.8,
                     margin: int = 10, preset: str = "medium") -> Tuple[str]:
        """添加水印"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",
            ]

            # 添加GPU相关参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend(["-i", input_video])

            # 构建滤镜字符串
            filter_complex = []
            
            if use_gpu:
                filter_complex.append("[0:v]hwupload_cuda[main]")
            else:
                filter_complex.append("[0:v]null[main]")

            # 获取位置表达式
            x_pos, y_pos = self.get_position_expression(position, margin)

            if watermark_type == "image":
                if not image_path or not os.path.exists(image_path):
                    raise FileNotFoundError("水印图片文件不存在")
                
                # 添加水印图片输入
                command.extend(["-i", image_path])
                
                if use_gpu:
                    filter_complex.extend([
                        f"[1:v]format=rgba,hwupload_cuda[watermark]",
                        f"[main][watermark]overlay=x={x_pos}:y={y_pos}:alpha={opacity}[out]"
                    ])
                else:
                    filter_complex.extend([
                        f"[1:v]format=rgba[watermark]",
                        f"[main][watermark]overlay=x={x_pos}:y={y_pos}:alpha={opacity}[out]"
                    ])

            else:  # text watermark
                if not text_content:
                    raise ValueError("水印文字内容不能为空")

                font_settings = f"fontsize={font_size}:fontcolor={font_color}"
                if font_file and os.path.exists(font_file):
                    font_settings += f":fontfile='{font_file}'"

                if use_gpu:
                    filter_complex.extend([
                        f"[main]drawtext=text='{text_content}':{font_settings}:x={x_pos}:y={y_pos}:alpha={opacity}[out]"
                    ])
                else:
                    filter_complex.extend([
                        f"[main]drawtext=text='{text_content}':{font_settings}:x={x_pos}:y={y_pos}:alpha={opacity}[out]"
                    ])

            if use_gpu:
                filter_complex.append("[out]hwdownload,format=nv12[final]")
            else:
                filter_complex.append("[out]format=yuv420p[final]")

            # 添加滤镜链
            command.extend([
                "-filter_complex", ";".join(filter_complex),
                "-map", "[final]",
                "-map", "0:a"
            ])

            # 添加编码器参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",
                    "-rc:v", "vbr",
                    "-cq:v", "23",
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", preset,
                    "-crf", "23",
                ])

            # 复制音频流
            command.extend(["-c:a", "copy"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"添加水印失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"添加水印时出错: {str(e)}")
            return (str(e),)