import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoSpeed(FFmpegBase):
    """
    视频速度调整节点
    功能：调整视频播放速度，支持加速和减速
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "speed_factor": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
                "maintain_pitch": ("BOOLEAN", {"default": True}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
                "audio_quality": ("INT", {"default": 3, "min": 0, "max": 5}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "adjust_speed"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"speed_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def adjust_speed(self, input_video: str, speed_factor: float,
                    maintain_pitch: bool, use_gpu: bool,
                    preset: str = "medium",
                    audio_quality: int = 3) -> Tuple[str]:
        """执行视频速度调整"""
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

            # 添加速度调整滤镜
            filter_complex.append(f"setpts={1/speed_factor}*PTS")

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

            # 处理音频
            if maintain_pitch:
                command.extend([
                    "-af", f"asetrate=44100*{speed_factor},aresample=44100,atempo=1.0",
                    "-c:a", "aac",
                    "-q:a", str(audio_quality),
                ])
            else:
                command.extend([
                    "-af", f"atempo={speed_factor}",
                    "-c:a", "aac",
                    "-q:a", str(audio_quality),
                ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"调整视频速度时出错: {str(e)}")
            return (str(e),)