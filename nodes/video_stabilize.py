import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoStabilize(FFmpegBase):
    """
    视频稳定节点
    功能：使用 vidstab 滤镜对视频进行稳定处理
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "smoothing": ("INT", {"default": 10, "min": 1, "max": 60}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "shakiness": ("INT", {"default": 5, "min": 1, "max": 10}),
                "accuracy": ("INT", {"default": 15, "min": 1, "max": 15}),
                "step_size": ("INT", {"default": 6, "min": 1, "max": 32}),
                "min_contrast": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "stabilize_video"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"stabilized_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def stabilize_video(self, input_video: str, smoothing: int,
                       use_gpu: bool, shakiness: int = 5,
                       accuracy: int = 15, step_size: int = 6,
                       min_contrast: float = 0.3,
                       preset: str = "medium") -> Tuple[str]:
        """执行视频稳定"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)
            
            # 创建临时文件用于存储变换数据
            transforms_file = os.path.join(os.path.dirname(output_path), "transforms.trf")

            # 第一遍：分析视频并生成变换数据
            analyze_command = [
                "ffmpeg",
                "-y",
                "-i", input_video,
                "-vf", f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:stepsize={step_size}:mincontrast={min_contrast}:result={transforms_file}",
                "-f", "null",
                "-"
            ]

            success, message = self.execute_ffmpeg(analyze_command)
            if not success:
                raise RuntimeError(f"视频分析失败: {message}")

            # 第二遍：应用稳定效果
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
                filter_complex.append("hwupload_cuda")

            # 添加视频稳定滤镜
            filter_complex.append(
                f"vidstabtransform=smoothing={smoothing}:input={transforms_file}:zoom=0:optzoom=2:interpol=linear"
            )

            # 添加裁剪以去除黑边
            filter_complex.append("crop=in_w*0.95:in_h*0.95")

            if use_gpu:
                filter_complex.append("hwdownload")
                filter_complex.append("format=nv12")

            # 添加滤镜链
            command.extend(["-vf", ",".join(filter_complex)])

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

            # 执行稳定处理
            success, message = self.execute_ffmpeg(command)

            # 清理临时文件
            if os.path.exists(transforms_file):
                os.remove(transforms_file)

            if not success:
                raise RuntimeError(f"视频稳定处理失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"稳定视频时出错: {str(e)}")
            return (str(e),)