import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoFormat(FFmpegBase):
    """
    视频格式转换节点
    功能：转换视频格式，支持各种常见视频格式之间的转换
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "output_format": (["mp4", "mov", "avi", "mkv", "webm", "gif", 
                                 "flv", "wmv", "m4v", "ts"], 
                                {"default": "mp4"}),
                "codec": (["h264", "h265", "vp8", "vp9", "av1", "mpeg4", 
                          "prores", "dnxhd"], 
                         {"default": "h264"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "web", "archive", "mobile", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "quality": ("INT", {"default": 23, "min": 0, "max": 51}),  # CRF值
                "bitrate": ("STRING", {"default": ""}),  # 如 "5M"
                "audio_codec": (["aac", "mp3", "ac3", "opus", "copy"], 
                              {"default": "aac"}),
                "audio_bitrate": ("STRING", {"default": "128k"}),
                "pixel_format": (["yuv420p", "yuv422p", "yuv444p", "rgb24"], 
                               {"default": "yuv420p"}),
                "faststart": ("BOOLEAN", {"default": True}),
                "metadata_copy": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "convert_format"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "codec": "h264",
                "quality": 23,
                "audio_codec": "aac",
                "audio_bitrate": "128k",
                "pixel_format": "yuv420p",
                "faststart": True
            },
            "web": {
                "codec": "h264",
                "quality": 28,
                "audio_codec": "aac",
                "audio_bitrate": "96k",
                "pixel_format": "yuv420p",
                "faststart": True
            },
            "archive": {
                "codec": "h265",
                "quality": 18,
                "audio_codec": "aac",
                "audio_bitrate": "192k",
                "pixel_format": "yuv420p",
                "faststart": False
            },
            "mobile": {
                "codec": "h264",
                "quality": 26,
                "audio_codec": "aac",
                "audio_bitrate": "96k",
                "pixel_format": "yuv420p",
                "faststart": True
            }
        }
        return presets.get(preset, presets["default"])

    def get_codec_params(self, codec: str, use_gpu: bool) -> dict:
        """获取编解码器参数"""
        gpu_params = self.get_gpu_params(use_gpu)
        
        codec_params = {
            "h264": {
                "video_codec": gpu_params["h264_encoder"],
                "options": ["-profile:v", "high"]
            },
            "h265": {
                "video_codec": "libx265" if not use_gpu else "hevc_nvenc",
                "options": ["-tag:v", "hvc1", "-x265-params", "log-level=error"]
            },
            "vp8": {
                "video_codec": "libvpx",
                "options": ["-deadline", "good", "-cpu-used", "2"]
            },
            "vp9": {
                "video_codec": "libvpx-vp9",
                "options": ["-deadline", "good", "-cpu-used", "2"]
            },
            "av1": {
                "video_codec": "libaom-av1",
                "options": ["-strict", "experimental", "-cpu-used", "4"]
            },
            "mpeg4": {
                "video_codec": "mpeg4",
                "options": ["-vtag", "xvid"]
            },
            "prores": {
                "video_codec": "prores_ks",
                "options": ["-profile:v", "3", "-vendor", "apl0"]
            },
            "dnxhd": {
                "video_codec": "dnxhd",
                "options": ["-profile:v", "dnxhr_hq"]
            }
        }
        return codec_params.get(codec, codec_params["h264"])

    def convert_format(self, input_video: str, output_format: str,
                      codec: str, use_gpu: bool, preset: str = "default",
                      quality: int = 23, bitrate: str = "",
                      audio_codec: str = "aac",
                      audio_bitrate: str = "128k",
                      pixel_format: str = "yuv420p",
                      faststart: bool = True,
                      metadata_copy: bool = True) -> Tuple[str]:
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video, output_format)

            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 构建基础命令
            command = [
                "ffmpeg",
                "-y"  # 覆盖输出文件
            ]

            # 添加硬件加速参数
            if use_gpu:
                command.extend(gpu_params["hw_accel"])

            # 添加输入文件
            command.extend(["-i", input_video])

            # 添加视频编码参数
            if use_gpu and codec in ["h264", "hevc"]:
                command.extend([
                    "-c:v", gpu_params[f"{codec}_encoder"],
                    "-preset", "p4",  # 使用较快的预设
                    "-tune", "hq",    # 高质量调优
                    "-rc:v", "vbr",   # 可变比特率
                    "-cq", str(quality)
                ])
                
                if bitrate:
                    command.extend(["-b:v", bitrate])
            else:
                command.extend([
                    "-c:v", self.get_software_encoder(codec),
                    "-crf", str(quality)
                ])

            # 添加音频参数
            if audio_codec != "copy":
                command.extend([
                    "-c:a", audio_codec,
                    "-b:a", audio_bitrate
                ])
            else:
                command.extend(["-c:a", "copy"])

            # 添加快速启动参数
            if faststart and output_format in ["mp4", "m4v"]:
                command.extend(["-movflags", "+faststart"])

            # 添加元数据复制参数
            if metadata_copy:
                command.extend(["-map_metadata", "0"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"转换视频格式时出错: {str(e)}")
            return (str(e),)

    def get_software_encoder(self, codec: str) -> str:
        """获取软件编码器名称"""
        encoders = {
            "h264": "libx264",
            "hevc": "libx265",
            "vp8": "libvpx",
            "vp9": "libvpx-vp9",
            "av1": "libaom-av1",
            "mpeg4": "mpeg4",
            "prores": "prores_ks",
            "dnxhd": "dnxhd"
        }
        return encoders.get(codec, "libx264")