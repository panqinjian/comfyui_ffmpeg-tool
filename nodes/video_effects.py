import os
from typing import Tuple, List
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoEffects(FFmpegBase):
    """
    视频特效节点
    功能：添加各种视频特效，如模糊、锐化、颜色调整等
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "effect_type": (["blur", "sharpen", "color_adjust", "vignette", 
                                "mirror", "fade", "glow", "vintage"], 
                               {"default": "blur"}),
                "intensity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "cinematic", "dreamy", "dramatic", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "brightness": ("FLOAT", {"default": 0.0, "min": -1.0, "max": 1.0}),
                "contrast": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "saturation": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0}),
                "hue": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "apply_effect"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "effect_type": "blur",
                "intensity": 0.5,
                "brightness": 0.0,
                "contrast": 1.0,
                "saturation": 1.0
            },
            "cinematic": {
                "effect_type": "color_adjust",
                "intensity": 0.7,
                "brightness": -0.1,
                "contrast": 1.2,
                "saturation": 1.3
            },
            "dreamy": {
                "effect_type": "glow",
                "intensity": 0.6,
                "brightness": 0.1,
                "contrast": 0.9,
                "saturation": 1.2
            },
            "dramatic": {
                "effect_type": "vignette",
                "intensity": 0.8,
                "brightness": -0.2,
                "contrast": 1.4,
                "saturation": 0.8
            }
        }
        return presets.get(preset, presets["default"])

    def get_effect_filter(self, effect_type: str, intensity: float,
                         brightness: float = 0.0, contrast: float = 1.0,
                         saturation: float = 1.0, hue: float = 0.0) -> str:
        """获取特效滤镜参数"""
        filters = {
            "blur": f"boxblur={int(intensity*20)}:1",
            "sharpen": f"unsharp={intensity*5}:5:0",
            "color_adjust": (f"eq=brightness={brightness+1}:contrast={contrast}:" +
                           f"saturation={saturation}:gamma=1"),
            "vignette": (f"vignette=PI/{4-intensity*3}:" +
                        f"eval=frame:x0=(W/2):y0=(H/2)"),
            "mirror": "hflip,split[m1][m2];[m1]crop=iw/2:ih:0:0[left];[m2]crop=iw/2:ih:iw/2:0[right];[left][right]hstack",
            "fade": f"fade=in:0:30,fade=out:{intensity*100}:30",
            "glow": f"gblur=sigma={intensity*3},curves=all='0/0 0.5/0.4 1/1'",
            "vintage": ("curves=r='0/0.11 .42/.51 1/0.95':g='0/0 0.50/0.48 1/1':" +
                       "b='0/0.22 .49/.44 1/0.8',colorbalance=rs=0:gs=0:bs=0:" +
                       "rm=.1:gm=0:bm=-.1:rh=.1:gh=0:bh=-.1,vignette")
        }
        return filters.get(effect_type, filters["blur"])

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"effect_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def apply_effect(self, input_video: str, effect_type: str,
                    intensity: float, use_gpu: bool,
                    preset: str = "default",
                    brightness: float = 0.0,
                    contrast: float = 1.0,
                    saturation: float = 1.0,
                    hue: float = 0.0) -> Tuple[str]:
        """执行视频特效应用"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            if preset != "custom":
                preset_params = self.get_preset_params(preset)
                effect_type = preset_params["effect_type"]
                intensity = preset_params["intensity"]
                brightness = preset_params.get("brightness", brightness)
                contrast = preset_params.get("contrast", contrast)
                saturation = preset_params.get("saturation", saturation)

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 获取特效滤镜
            effect_filter = self.get_effect_filter(
                effect_type, intensity, brightness, contrast, saturation, hue
            )

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
            command.extend(["-vf", effect_filter])

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
            print(f"应用视频特效时出错: {str(e)}")
            return (str(e),)