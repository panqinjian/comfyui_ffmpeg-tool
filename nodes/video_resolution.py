import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoResolution(FFmpegBase):
    """
    视频分辨率调整节点
    功能：调整视频分辨率，支持多种预设和自定义分辨率
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "resolution": (["4K", "2K", "1080p", "720p", "480p", "360p", "custom"], 
                             {"default": "1080p"}),
                "width": ("INT", {"default": 1920, "min": 0}),
                "height": ("INT", {"default": 1080, "min": 0}),
                "keep_aspect": ("BOOLEAN", {"default": True}),
                "scaling_method": (["bicubic", "bilinear", "lanczos", "neighbor"], 
                                 {"default": "bicubic"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "force_divisible": ("INT", {"default": 2, "min": 1}),
                "pad_color": ("STRING", {"default": "black"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "adjust_resolution"
    CATEGORY = "FFmpeg"

    def get_resolution_params(self, resolution: str) -> dict:
        """获取分辨率参数"""
        resolutions = {
            "4K": {"width": 3840, "height": 2160},
            "2K": {"width": 2560, "height": 1440},
            "1080p": {"width": 1920, "height": 1080},
            "720p": {"width": 1280, "height": 720},
            "480p": {"width": 854, "height": 480},
            "360p": {"width": 640, "height": 360}
        }
        return resolutions.get(resolution, {"width": 1920, "height": 1080})

    def get_scaling_filter(self, method: str) -> str:
        """获取缩放滤镜参数"""
        filters = {
            "bicubic": "bicubic",
            "bilinear": "bilinear",
            "lanczos": "lanczos",
            "neighbor": "neighbor"
        }
        return filters.get(method, "bicubic")

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"resolution_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def adjust_resolution(self, input_video: str, resolution: str,
                        width: int, height: int, keep_aspect: bool,
                        scaling_method: str, use_gpu: bool,
                        force_divisible: int = 2,
                        pad_color: str = "black") -> Tuple[str]:
        """执行分辨率调整"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 获取目标分辨率
            if resolution != "custom":
                res_params = self.get_resolution_params(resolution)
                width = res_params["width"]
                height = res_params["height"]

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 获取缩放滤镜方法
            scale_method = self.get_scaling_filter(scaling_method)
            
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

            # 构建滤镜字符串
            filter_complex = []
            
            if use_gpu:
                filter_complex.append("hwupload_cuda")
            
            # 添加缩放滤镜
            if keep_aspect:
                if force_divisible > 1:
                    filter_complex.append(
                        f"scale=w='min({width},iw)':h='min({height},ih)'" +
                        f":flags={scale_method}:force_original_aspect_ratio=decrease," +
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:{pad_color}," +
                        f"scale='2*trunc(iw/{force_divisible})*{force_divisible}':" +
                        f"'2*trunc(ih/{force_divisible})*{force_divisible}'"
                    )
                else:
                    filter_complex.append(
                        f"scale=w='min({width},iw)':h='min({height},ih)'" +
                        f":flags={scale_method}:force_original_aspect_ratio=decrease," +
                        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:{pad_color}"
                    )
            else:
                if force_divisible > 1:
                    filter_complex.append(
                        f"scale={width}:{height}:flags={scale_method}," +
                        f"scale='2*trunc(iw/{force_divisible})*{force_divisible}':" +
                        f"'2*trunc(ih/{force_divisible})*{force_divisible}'"
                    )
                else:
                    filter_complex.append(f"scale={width}:{height}:flags={scale_method}")

            if use_gpu:
                filter_complex.append("hwdownload")
                filter_complex.append("format=nv12")

            # 添加编码器参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",  # 使用 NVENC 特定的预设
                    "-rc:v", "vbr",   # 使用可变比特率
                    "-cq:v", "23",
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                ])

            # 添加滤镜链
            command.extend(["-vf", ",".join(filter_complex)])

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
            print(f"调整分辨率时出错: {str(e)}")
            return (str(e),)