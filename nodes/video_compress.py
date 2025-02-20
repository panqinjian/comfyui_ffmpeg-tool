import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoCompress(FFmpegBase):
    """
    视频压缩节点
    功能：压缩视频文件大小，支持多种压缩策略
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "compression_level": (["light", "medium", "heavy", "extreme"], 
                                   {"default": "medium"}),
                "target_size_mb": ("FLOAT", {"default": 0.0, "min": 0.0}),
                "maintain_quality": ("BOOLEAN", {"default": True}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "web", "mobile", "archive", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "audio_bitrate": ("INT", {"default": 128, "min": 32, "max": 320}),
                "max_width": ("INT", {"default": 1920, "min": 0}),
                "max_height": ("INT", {"default": 1080, "min": 0}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "compress_video"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "compression_level": "medium",
                "audio_bitrate": 128,
                "max_width": 1920,
                "max_height": 1080
            },
            "web": {
                "compression_level": "heavy",
                "audio_bitrate": 96,
                "max_width": 1280,
                "max_height": 720
            },
            "mobile": {
                "compression_level": "extreme",
                "audio_bitrate": 64,
                "max_width": 854,
                "max_height": 480
            },
            "archive": {
                "compression_level": "light",
                "audio_bitrate": 192,
                "max_width": 1920,
                "max_height": 1080
            }
        }
        return presets.get(preset, presets["default"])

    def get_compression_params(self, level: str) -> dict:
        """获取压缩参数"""
        params = {
            "light": {
                "crf": 23,
                "preset": "medium",
                "codec": "h264"
            },
            "medium": {
                "crf": 28,
                "preset": "faster",
                "codec": "h265"
            },
            "heavy": {
                "crf": 32,
                "preset": "veryfast",
                "codec": "h265"
            },
            "extreme": {
                "crf": 35,
                "preset": "ultrafast",
                "codec": "h265"
            }
        }
        return params.get(level, params["medium"])

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"compressed_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def compress_video(self, input_video: str, compression_level: str,
                      target_size_mb: float, maintain_quality: bool,
                      use_gpu: bool, preset: str = "default",
                      audio_bitrate: int = 128,
                      max_width: int = 1920,
                      max_height: int = 1080) -> Tuple[str]:
        """执行视频压缩"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            preset_params = self.get_preset_params(preset)
            if preset != "custom":
                compression_level = preset_params["compression_level"]
                audio_bitrate = preset_params["audio_bitrate"]
                max_width = preset_params["max_width"]
                max_height = preset_params["max_height"]

            # 获取压缩参数
            comp_params = self.get_compression_params(compression_level)

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
            ]

            # 添加GPU相关参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend(["-i", input_video])

            # 添加视频编码参数
            if use_gpu:
                codec = "h264_nvenc" if comp_params["codec"] == "h264" else "hevc_nvenc"
                command.extend([
                    "-c:v", codec,
                    "-preset", "p7",  # 使用 NVENC 特定的预设
                    "-rc:v", "vbr",   # 使用可变比特率
                    "-cq:v", str(comp_params["crf"]),
                ])
            else:
                codec = "libx264" if comp_params["codec"] == "h264" else "libx265"
                command.extend([
                    "-c:v", codec,
                    "-preset", comp_params["preset"],
                    "-crf", str(comp_params["crf"]),
                ])

            # 添加尺寸限制
            if max_width > 0 and max_height > 0:
                command.extend([
                    "-vf", f"scale=w='min({max_width},iw)':h='min({max_height},ih)':force_original_aspect_ratio=1"
                ])

            # 如果指定了目标大小
            if target_size_mb > 0:
                duration = float(os.popen(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_video}"').read().strip())
                total_bitrate = int((target_size_mb * 8192) / duration)
                video_bitrate = total_bitrate - (audio_bitrate * 1024)
                if video_bitrate > 0:
                    command.extend([
                        "-b:v", f"{video_bitrate}k",
                        "-maxrate", f"{int(video_bitrate * 1.5)}k",
                        "-bufsize", f"{video_bitrate * 2}k"
                    ])

            # 添加音频参数
            command.extend([
                "-c:a", "aac",
                "-b:a", f"{audio_bitrate}k"
            ])

            # 如果需要保持质量
            if maintain_quality:
                command.extend(["-qmin", "0", "-qmax", "69"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"压缩视频时出错: {str(e)}")
            return (str(e),)