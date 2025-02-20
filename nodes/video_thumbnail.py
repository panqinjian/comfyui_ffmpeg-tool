import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoThumbnail(FFmpegBase):
    """
    视频缩略图生成节点
    功能：从视频中提取缩略图，支持单帧和多帧
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "mode": (["single", "multiple"], {"default": "single"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "time_position": ("STRING", {"default": "00:00:00"}),
                "frame_interval": ("INT", {"default": 10, "min": 1}),
                "max_frames": ("INT", {"default": 10, "min": 1, "max": 100}),
                "width": ("INT", {"default": 320, "min": 32}),
                "height": ("INT", {"default": 240, "min": 32}),
                "quality": ("INT", {"default": 90, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "generate_thumbnail"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str, mode: str, index: int = 0) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        if mode == "single":
            output_filename = f"thumbnail_{video_hash}.jpg"
        else:
            output_filename = f"thumbnail_{video_hash}_%03d.jpg" if index == 0 else f"thumbnail_{video_hash}_{index:03d}.jpg"
        return os.path.join(base_output_dir, output_filename)

    def generate_thumbnail(self, input_video: str, mode: str,
                         use_gpu: bool, time_position: str = "00:00:00",
                         frame_interval: int = 10, max_frames: int = 10,
                         width: int = 320, height: int = 240,
                         quality: int = 90) -> Tuple[str]:
        """生成视频缩略图"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video, mode)

            if mode == "single":
                command = [
                    "ffmpeg",
                    "-y",
                ]

                if use_gpu:
                    command.extend(["-hwaccel", "cuda"])

                command.extend([
                    "-ss", time_position,
                    "-i", input_video,
                    "-vframes", "1",
                    "-vf", f"scale={width}:{height}",
                    "-q:v", str(int((100 - quality) / 5)),  # 转换质量参数
                ])

            else:  # multiple
                command = [
                    "ffmpeg",
                    "-y",
                ]

                if use_gpu:
                    command.extend(["-hwaccel", "cuda"])

                command.extend([
                    "-i", input_video,
                    "-vf", f"select=not(mod(n\\,{frame_interval})),scale={width}:{height}",
                    "-vsync", "0",
                    "-frame_pts", "1",
                    "-vframes", str(max_frames),
                    "-q:v", str(int((100 - quality) / 5)),
                ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"生成缩略图失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"生成视频缩略图时出错: {str(e)}")
            return (str(e),)