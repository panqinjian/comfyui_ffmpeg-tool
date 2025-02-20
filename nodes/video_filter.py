import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoFilter(FFmpegBase):
    """
    视频滤镜节点
    功能：应用各种视频滤镜效果，如模糊、锐化、色彩调整等
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "filter_type": (["blur", "sharpen", "edge", "emboss", "noise", 
                               "colorbalance", "eq", "hue", "curves", "lut"], 
                              {"default": "blur"}),
                "intensity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "artistic", "retro", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "red": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "green": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "blue": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "brightness": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "saturation": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0}),
                "gamma": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
                "lut_file": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "apply_filter"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "filter_type": "blur",
                "intensity": 0.5,
                "red": 1.0,
                "green": 1.0,
                "blue": 1.0
            },
            "artistic": {
                "filter_type": "curves",
                "intensity": 0.7,
                "red": 1.2,
                "green": 0.9,
                "blue": 1.1
            },
            "retro": {
                "filter_type": "colorbalance",
                "intensity": 0.6,
                "red": 1.3,
                "green": 0.8,
                "blue": 0.7
            }
        }
        return presets.get(preset, presets["default"])

    def get_filter_string(self, filter_type: str, intensity: float,
                         red: float = 1.0, green: float = 1.0, blue: float = 1.0,
                         brightness: float = 0.0, contrast: float = 1.0,
                         saturation: float = 1.0, gamma: float = 1.0,
                         lut_file: str = "") -> str:
        """生成滤镜字符串"""
        if filter_type == "blur":
            sigma = intensity * 5
            return f"boxblur=luma_radius={sigma}:luma_power=1"
        elif filter_type == "sharpen":
            return f"unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount={intensity*5}"
        elif filter_type == "edge":
            return "edgedetect=low=0.1:high=0.4"
        elif filter_type == "emboss":
            return f"convolution='0 1 0 -1 1 1 0 -1 0':normalize=0:saturation={intensity}"
        elif filter_type == "noise":
            return f"noise=alls={intensity*100}:allf=t"
        elif filter_type == "colorbalance":
            return (f"colorbalance=rs={red-1}:gs={green-1}:bs={blue-1}:" +
                   f"rm={red-1}:gm={green-1}:bm={blue-1}:" +
                   f"rh={red-1}:gh={green-1}:bh={blue-1}")
        elif filter_type == "eq":
            return (f"eq=brightness={brightness}:contrast={contrast}:" +
                   f"saturation={saturation}:gamma={gamma}")
        elif filter_type == "hue":
            return f"hue=h={intensity*360}:s={saturation}"
        elif filter_type == "curves":
            return (f"curves=r='0/0 0.5/{red*0.5} 1/{red}':"+
                   f"g='0/0 0.5/{green*0.5} 1/{green}':"+
                   f"b='0/0 0.5/{blue*0.5} 1/{blue}'")
        elif filter_type == "lut" and lut_file:
            if not os.path.exists(lut_file):
                raise ValueError("LUT文件不存在")
            return f"lut3d=file='{lut_file}'"
        else:
            return ""

    def apply_filter(self, input_video: str, filter_type: str,
                    intensity: float, use_gpu: bool,
                    preset: str = "default",
                    red: float = 1.0,
                    green: float = 1.0,
                    blue: float = 1.0,
                    brightness: float = 0.0,
                    contrast: float = 1.0,
                    saturation: float = 1.0,
                    gamma: float = 1.0,
                    lut_file: str = "") -> Tuple[str]:
        """应用视频滤镜"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            if preset != "custom":
                preset_params = self.get_preset_params(preset)
                filter_type = preset_params["filter_type"]
                intensity = preset_params["intensity"]
                red = preset_params["red"]
                green = preset_params["green"]
                blue = preset_params["blue"]

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 获取滤镜字符串
            filter_string = self.get_filter_string(
                filter_type, intensity, red, green, blue,
                brightness, contrast, saturation, gamma, lut_file
            )

            if not filter_string:
                raise ValueError("无效的滤镜类型或参数")

            # 构建命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
            ]

            # 添加 GPU 加速参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend(["-i", input_video])

            # 添加滤镜参数
            command.extend(["-vf", filter_string])

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
            print(f"应用滤镜时出错: {str(e)}")
            return (str(e),)