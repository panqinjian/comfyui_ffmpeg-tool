import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoResize(FFmpegBase):
    """
    视频尺寸调整节点
    功能：调整视频分辨率和尺寸，支持多种缩放算法
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "输入视频": ("STRING", {"default": ""}),
                "分辨率方案": (["自定义", "4K(3840x2160)", "2K(2560x1440)", "1080P(1920x1080)", 
                           "720P(1280x720)", "480P(854x480)", "360P(640x360)", 
                           "竖屏1080P(1080x1920)", "竖屏720P(720x1280)", 
                           "方形1:1(1080x1080)", "B站竖屏(720x1280)"], {"default": "自定义"}),
                "宽度": ("INT", {"default": 1920, "min": 0}),
                "高度": ("INT", {"default": 1080, "min": 0}),
                "保持宽高比": ("BOOLEAN", {"default": True}),
                "缩放算法": (["双线性", "双三次", "兰索斯", "最近邻"], 
                         {"default": "双三次"}),
                "使用GPU": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "编码速度": (["中等", "快速", "慢速"], {"default": "中等"}),
                "填充颜色": ("STRING", {"default": "black"}),
                "尺寸对齐": ("INT", {"default": 2, "min": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "resize_video"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"resized_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def get_resolution(self, resolution_preset: str, width: int, height: int) -> Tuple[int, int]:
        """根据预设获取分辨率"""
        resolution_map = {
            "自定义": (width, height),
            "4K(3840x2160)": (3840, 2160),
            "2K(2560x1440)": (2560, 1440),
            "1080P(1920x1080)": (1920, 1080),
            "720P(1280x720)": (1280, 720),
            "480P(854x480)": (854, 480),
            "360P(640x360)": (640, 360),
            "竖屏1080P(1080x1920)": (1080, 1920),
            "竖屏720P(720x1280)": (720, 1280),
            "方形1:1(1080x1080)": (1080, 1080),
            "B站竖屏(720x1280)": (720, 1280)
        }
        return resolution_map.get(resolution_preset, (width, height))

    def resize_video(self, 输入视频: str, 分辨率方案: str, 宽度: int, 高度: int,
                    保持宽高比: bool, 缩放算法: str,
                    使用GPU: bool, 编码速度: str = "中等",
                    填充颜色: str = "black",
                    尺寸对齐: int = 2) -> Tuple[str]:
        """执行视频尺寸调整"""
        try:
            # 获取实际分辨率
            actual_width, actual_height = self.get_resolution(分辨率方案, 宽度, 高度)

            # 参数映射
            scaling_method_map = {
                "双线性": "bilinear",
                "双三次": "bicubic",
                "兰索斯": "lanczos",
                "最近邻": "neighbor"
            }
            preset_map = {
                "快速": "fast",
                "中等": "medium",
                "慢速": "slow"
            }

            # 检查输入视频是否存在
            if not os.path.exists(输入视频):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(输入视频)

            # 构建基本命令
            command = ["ffmpeg", "-y"]

            # 添加GPU相关参数
            if 使用GPU:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend(["-i", 输入视频])

            # 构建滤镜字符串
            filter_complex = []

            # 添加缩放滤镜
            scale_filter = f"scale={actual_width}:{actual_height}"
            if 保持宽高比:
                scale_filter += ":force_original_aspect_ratio=decrease"
            scale_filter += f":flags={scaling_method_map[缩放算法]}"
            filter_complex.append(scale_filter)

            # 如果保持宽高比，添加填充
            if 保持宽高比:
                pad_filter = f"pad={actual_width}:{actual_height}:(ow-iw)/2:(oh-ih)/2:{填充颜色}"
                filter_complex.append(pad_filter)

            # 确保尺寸是指定数的倍数
            if 尺寸对齐 > 1:
                filter_complex.append(
                    f"scale=trunc(iw/{尺寸对齐})*{尺寸对齐}:trunc(ih/{尺寸对齐})*{尺寸对齐}"
                )

            # 添加滤镜链
            command.extend(["-vf", ",".join(filter_complex)])

            # 添加编码器参数
            if 使用GPU:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",
                    "-tune", "hq",
                    "-rc:v", "vbr",
                    "-cq:v", "23",
                    "-profile:v", "high",
                    "-pix_fmt", "yuv420p"
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", preset_map[编码速度],
                    "-crf", "23",
                    "-profile:v", "high",
                    "-pix_fmt", "yuv420p"
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
            print(f"调整视频尺寸时出错: {str(e)}")
            return (str(e),)