import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoConvert(FFmpegBase):
    """
    视频格式转换节点
    功能：将视频转换为不同的格式，支持多种编码器和容器格式
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "output_format": (["mp4", "mov", "mkv", "avi", "webm", "gif"], 
                                {"default": "mp4"}),
                "video_codec": (["h264", "h265", "vp9", "av1"], 
                              {"default": "h264"}),
                "quality": ("INT", {"default": 23, "min": 0, "max": 51}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "high_quality", "fast_convert", 
                           "compress", "animation"], 
                          {"default": "default"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "convert_video"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "quality": 23,
                "output_format": "mp4",
                "video_codec": "h264"
            },
            "high_quality": {
                "quality": 18,
                "output_format": "mov",
                "video_codec": "h265"
            },
            "fast_convert": {
                "quality": 28,
                "output_format": "mp4",
                "video_codec": "h264"
            },
            "compress": {
                "quality": 30,
                "output_format": "mp4",
                "video_codec": "h265"
            },
            "animation": {
                "quality": 20,
                "output_format": "gif",
                "video_codec": None
            }
        }
        return presets.get(preset, presets["default"])

    def get_codec_params(self, video_codec: str, use_gpu: bool) -> dict:
        """获取编码器参数"""
        if not use_gpu:
            return {
                "h264": {"codec": "libx264", "options": []},
                "h265": {"codec": "libx265", "options": []},
                "vp9": {"codec": "libvpx-vp9", "options": []},
                "av1": {"codec": "libaom-av1", "options": []}
            }.get(video_codec, {"codec": "libx264", "options": []})
        else:
            return {
                "h264": {"codec": "h264_nvenc", "options": []},
                "h265": {"codec": "hevc_nvenc", "options": []},
                "vp9": {"codec": "libvpx-vp9", "options": []},  # VP9 暂不支持 GPU
                "av1": {"codec": "libaom-av1", "options": []}   # AV1 暂不支持 GPU
            }.get(video_codec, {"codec": "h264_nvenc", "options": []})

    def create_output_path(self, input_video: str, output_format: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"converted_{video_hash}.{output_format}"
        return os.path.join(base_output_dir, output_filename)

    def convert_video(self, input_video: str, output_format: str,
                     video_codec: str, quality: int, use_gpu: bool,
                     preset: str = "default") -> Tuple[str]:
        """执行视频格式转换"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            preset_params = self.get_preset_params(preset)
            if preset != "default":
                quality = preset_params["quality"]
                output_format = preset_params["output_format"]
                video_codec = preset_params["video_codec"]

            # 创建输出文件路径
            output_path = self.create_output_path(input_video, output_format)

            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 获取编码器参数
            codec_params = self.get_codec_params(video_codec, use_gpu)

            # 构建命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
                *gpu_params["hw_accel"],
                "-i", input_video,
            ]

            # 特殊处理 GIF 格式
            if output_format == "gif":
                command.extend([
                    "-vf", "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                    "-loop", "0"
                ])
            else:
                # 添加编码器参数
                command.extend([
                    "-c:v", codec_params["codec"],
                    *codec_params["options"],
                    "-crf", str(quality),
                    "-preset", "medium",
                    "-c:a", "aac",
                    "-b:a", "128k"
                ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"转换视频时出错: {str(e)}")
            return (str(e),)