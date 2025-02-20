import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoDenoise(FFmpegBase):
    """
    视频降噪节点
    功能：使用多种降噪算法减少视频噪点
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "denoise_type": (["nlmeans", "hqdn3d", "dctdnoiz", "owdenoise"], 
                                {"default": "nlmeans"}),
                "strength": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "light", "medium", "strong", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "temporal_size": ("INT", {"default": 3, "min": 1, "max": 7}),
                "spatial_size": ("INT", {"default": 5, "min": 1, "max": 9}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "denoise_video"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "denoise_type": "nlmeans",
                "strength": 5.0,
                "temporal_size": 3,
                "spatial_size": 5
            },
            "light": {
                "denoise_type": "nlmeans",
                "strength": 3.0,
                "temporal_size": 2,
                "spatial_size": 3
            },
            "medium": {
                "denoise_type": "hqdn3d",
                "strength": 6.0,
                "temporal_size": 4,
                "spatial_size": 6
            },
            "strong": {
                "denoise_type": "dctdnoiz",
                "strength": 8.0,
                "temporal_size": 5,
                "spatial_size": 7
            }
        }
        return presets.get(preset, presets["default"])

    def get_denoise_filter(self, denoise_type: str, strength: float,
                          temporal_size: int, spatial_size: int) -> str:
        """获取降噪滤镜参数"""
        filters = {
            "nlmeans": f"nlmeans=s={strength}:p={spatial_size}:r={temporal_size}",
            "hqdn3d": f"hqdn3d=luma_spatial={strength}:chroma_spatial={strength/2}:" +
                     f"luma_tmp={strength*temporal_size/3}:chroma_tmp={strength*temporal_size/6}",
            "dctdnoiz": f"dctdnoiz=sigma={strength*10}:overlap={spatial_size}",
            "owdenoise": f"owdenoise=depth={int(strength)}:s={spatial_size}"
        }
        return filters.get(denoise_type, filters["nlmeans"])

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"denoised_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def denoise_video(self, input_video: str, denoise_type: str,
                     strength: float, use_gpu: bool,
                     preset: str = "default",
                     temporal_size: int = 3,
                     spatial_size: int = 5) -> Tuple[str]:
        """执行视频降噪"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            if preset != "custom":
                preset_params = self.get_preset_params(preset)
                denoise_type = preset_params["denoise_type"]
                strength = preset_params["strength"]
                temporal_size = preset_params["temporal_size"]
                spatial_size = preset_params["spatial_size"]

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
            ]

            # 添加 GPU 加速参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend(["-i", input_video])

            # 获取降噪滤镜
            denoise_filter = self.get_denoise_filter(
                denoise_type, strength, temporal_size, spatial_size
            )

            # 添加滤镜参数
            command.extend(["-vf", denoise_filter])

            # 添加编码参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",
                    "-rc:v", "vbr",
                    "-cq:v", "23"
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23"
                ])

            # 复制音频流
            command.extend(["-c:a", "copy"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"降噪视频时出错: {str(e)}")
            return (str(e),)