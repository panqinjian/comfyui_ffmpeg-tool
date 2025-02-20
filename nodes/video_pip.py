import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoPiP(FFmpegBase):
    """
    画中画节点
    功能：将一个视频嵌入到另一个视频中，支持位置和大小调整
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "main_video": ("STRING", {"default": ""}),    # 主视频路径
                "pip_video": ("STRING", {"default": ""}),     # 画中画视频路径
                "position": (["top_left", "top_right", "bottom_left", "bottom_right", "center", "custom"], 
                           {"default": "bottom_right"}),
                "pip_scale": ("FLOAT", {"default": 0.3, "min": 0.1, "max": 1.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "corner", "side_by_side", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "x_offset": ("INT", {"default": 10, "min": 0}),
                "y_offset": ("INT", {"default": 10, "min": 0}),
                "border_width": ("INT", {"default": 2, "min": 0}),
                "border_color": ("STRING", {"default": "white"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "create_pip"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "position": "bottom_right",
                "pip_scale": 0.3,
                "border_width": 2
            },
            "corner": {
                "position": "top_right",
                "pip_scale": 0.25,
                "border_width": 3
            },
            "side_by_side": {
                "position": "custom",
                "pip_scale": 0.5,
                "x_offset": "W/2",
                "y_offset": 0,
                "border_width": 0
            }
        }
        return presets.get(preset, presets["default"])

    def get_position_params(self, position: str, scale: float,
                          x_offset: int, y_offset: int) -> str:
        """获取位置参数"""
        w_expr = f"w*{scale}"
        h_expr = f"h*{scale}"
        positions = {
            "top_left": f"x={x_offset}:y={y_offset}",
            "top_right": f"x=main_w-overlay_w-{x_offset}:y={y_offset}",
            "bottom_left": f"x={x_offset}:y=main_h-overlay_h-{y_offset}",
            "bottom_right": f"x=main_w-overlay_w-{x_offset}:y=main_h-overlay_h-{y_offset}",
            "center": "x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2",
            "custom": f"x={x_offset}:y={y_offset}"
        }
        return positions.get(position, positions["bottom_right"])

    def create_output_path(self, main_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(main_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"pip_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def create_unique_output_path(self, input_video: str) -> str:
        """创建唯一的输出文件路径"""
        # 获取输出目录
        directory = folder_paths.get_output_directory()
        
        # 获取输入文件的扩展名
        ext = os.path.splitext(input_video)[1]
        if not ext:
            ext = ".mp4"
        
        # 生成唯一的文件名
        base_name = "pip_video"
        counter = 1
        while True:
            if counter == 1:
                file_name = f"{base_name}{ext}"
            else:
                file_name = f"{base_name}_{counter}{ext}"
            
            output_path = os.path.join(directory, file_name)
            if not os.path.exists(output_path):
                return output_path
            counter += 1

    def create_pip(self, main_video: str, pip_video: str,
                  position: str, pip_scale: float,
                  use_gpu: bool, preset: str = "default",
                  x_offset: int = 10, y_offset: int = 10,
                  border_width: int = 2,
                  border_color: str = "white") -> Tuple[str]:
        """创建画中画效果"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(main_video):
                raise FileNotFoundError(f"主视频文件不存在: {main_video}")
            if not os.path.exists(pip_video):
                raise FileNotFoundError(f"画中画视频文件不存在: {pip_video}")

            # 创建输出路径
            output_path = self.create_unique_output_path(main_video)
            
            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 构建命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖输出文件
            ]

            # 添加硬件加速输入参数
            if use_gpu:
                command.extend([
                    "-hwaccel", "cuda",
                    "-hwaccel_output_format", "nv12"
                ])

            # 添加输入
            command.extend([
                "-i", main_video,  # 主视频
                "-i", pip_video    # 画中画视频
            ])

            # 构建滤镜复杂度
            filter_parts = []

            # 处理主视频和画中画视频
            filter_parts.append("[0:v]format=nv12[main];")
            filter_parts.append(f"[1:v]format=nv12,scale=iw*{pip_scale}:ih*{pip_scale}")

            # 如果有边框，添加边框效果
            if border_width > 0:
                filter_parts.append(f",pad=w=iw+{border_width*2}:h=ih+{border_width*2}:x={border_width}:y={border_width}:color={border_color}")

            # 添加 PiP 标记
            filter_parts.append("[pip];")

            # 根据位置添加叠加滤镜
            if position == "custom":
                # 使用自定义偏移量
                overlay_params = f"x={x_offset}:y={y_offset}"
            else:
                # 预设位置
                position_params = {
                    "top_left": "x=10:y=10",
                    "top_right": "x=main_w-overlay_w-10:y=10",
                    "bottom_left": "x=10:y=main_h-overlay_h-10",
                    "bottom_right": "x=main_w-overlay_w-10:y=main_h-overlay_h-10",
                    "center": "x=(main_w-overlay_w)/2:y=(main_h-overlay_h)/2"
                }
                overlay_params = position_params.get(position, position_params['bottom_right'])

            # 添加叠加滤镜
            filter_parts.append(f"[main][pip]overlay={overlay_params}")

            # 构建完整的滤镜字符串
            filter_complex = "".join(filter_parts)

            # 添加滤镜复杂度参数
            command.extend(["-filter_complex", filter_complex])

            # 添加编码器参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p4",
                    "-tune", "hq",
                    "-rc:v", "vbr",
                    "-cq", "23"
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23"
                ])

            # 添加音频参数
            command.extend(["-c:a", "copy"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            error_msg = str(e)
            print(f"创建画中画时出错: {error_msg}")
            return (error_msg,)