import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoReverse(FFmpegBase):
    """
    视频倒放节点
    功能：将视频倒序播放
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "maintain_quality": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "audio_reverse": ("BOOLEAN", {"default": False}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "reverse_video"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"reversed_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def reverse_video(self, input_video: str, use_gpu: bool,
                     maintain_quality: bool, audio_reverse: bool = False,
                     preset: str = "medium") -> Tuple[str]:
        """执行视频倒放"""
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
                filter_complex.append("hwupload_cuda")

            # 添加倒放滤镜
            filter_complex.append("reverse")

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
                    "-cq:v", "23" if maintain_quality else "28",
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", preset,
                    "-crf", "23" if maintain_quality else "28",
                ])

            # 处理音频
            if audio_reverse:
                command.extend([
                    "-af", "areverse",
                    "-c:a", "aac",
                    "-b:a", "128k"
                ])
            else:
                command.extend(["-c:a", "copy"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"倒放视频时出错: {str(e)}")
            return (str(e),)