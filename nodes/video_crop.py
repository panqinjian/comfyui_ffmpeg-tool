import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoCrop(FFmpegBase):
    """
    视频裁剪节点
    功能：裁剪视频画面的特定区域
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "x": ("INT", {"default": 0, "min": 0}),
                "y": ("INT", {"default": 0, "min": 0}),
                "width": ("INT", {"default": 0, "min": 0}),
                "height": ("INT", {"default": 0, "min": 0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "center_square", "left_half", "right_half",
                           "top_half", "bottom_half", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "keep_aspect": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "crop_video"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0
            },
            "center_square": {
                "x": "in_w/4",
                "y": "in_h/4",
                "width": "min(in_w,in_h)/2",
                "height": "min(in_w,in_h)/2"
            },
            "left_half": {
                "x": 0,
                "y": 0,
                "width": "in_w/2",
                "height": "in_h"
            },
            "right_half": {
                "x": "in_w/2",
                "y": 0,
                "width": "in_w/2",
                "height": "in_h"
            },
            "top_half": {
                "x": 0,
                "y": 0,
                "width": "in_w",
                "height": "in_h/2"
            },
            "bottom_half": {
                "x": 0,
                "y": "in_h/2",
                "width": "in_w",
                "height": "in_h/2"
            }
        }
        return presets.get(preset, presets["default"])

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"cropped_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def crop_video(self, input_video: str, x: int, y: int,
                  width: int, height: int, use_gpu: bool,
                  preset: str = "default",
                  keep_aspect: bool = True) -> Tuple[str]:
        """执行视频裁剪"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 获取视频原始尺寸
            video_info = self.get_video_resolution(input_video)
            if not video_info:
                raise RuntimeError("无法获取视频尺寸信息")
            
            orig_width, orig_height = video_info

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

            # 处理裁剪参数
            if preset == "default":
                # 默认预设：使用整个视频尺寸
                actual_width = orig_width
                actual_height = orig_height
                actual_x = 0
                actual_y = 0
            elif preset != "custom":
                # 其他预设
                preset_params = self.get_preset_params(preset)
                actual_x = preset_params["x"]
                actual_y = preset_params["y"]
                actual_width = preset_params["width"]
                actual_height = preset_params["height"]
            else:
                # 自定义参数
                # 如果宽度或高度为0，使用原始尺寸减去偏移量
                actual_width = width if width > 0 else (orig_width - x)
                actual_height = height if height > 0 else (orig_height - y)
                actual_x = x
                actual_y = y

            # 确保裁剪区域不超出原始视频范围
            actual_width = min(actual_width, orig_width - actual_x)
            actual_height = min(actual_height, orig_height - actual_y)

            # 构建裁剪参数
            crop_params = f"crop={actual_width}:{actual_height}:{actual_x}:{actual_y}"

            # 构建滤镜字符串
            filter_complex = [crop_params]
            
            # 如果需要保持宽高比
            if keep_aspect:
                filter_complex.append("setsar=1:1")

            # 添加滤镜参数
            command.extend(["-vf", ",".join(filter_complex)])

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
            print(f"裁剪视频时出错: {str(e)}")
            return (str(e),)