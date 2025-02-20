import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoEnhance(FFmpegBase):
    """
    视频增强节点
    功能：提升视频质量，包括超分辨率、降噪、锐化、色彩增强等
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "enhance_type": (["quality", "detail", "color", "hdr", "stabilize", 
                                "denoise", "deinterlace", "framerate", "all"], 
                               {"default": "quality"}),
                "intensity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "film", "animation", "sports", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "quality_level": ("INT", {"default": 2, "min": 1, "max": 4}),
                "sharpness": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "denoising": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "color_boost": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0}),
                "target_fps": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 120.0}),
                "hdr_tone": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "enhance_video"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "enhance_type": "quality",
                "intensity": 0.5,
                "quality_level": 2,
                "sharpness": 1.0,
                "denoising": 0.5,
                "color_boost": 1.0
            },
            "film": {
                "enhance_type": "all",
                "intensity": 0.7,
                "quality_level": 3,
                "sharpness": 1.2,
                "denoising": 0.3,
                "color_boost": 1.1,
                "hdr_tone": 1.2
            },
            "animation": {
                "enhance_type": "detail",
                "intensity": 0.6,
                "quality_level": 2,
                "sharpness": 1.4,
                "denoising": 0.2,
                "color_boost": 1.3
            },
            "sports": {
                "enhance_type": "framerate",
                "intensity": 0.8,
                "quality_level": 2,
                "sharpness": 1.1,
                "denoising": 0.4,
                "target_fps": 60.0
            }
        }
        return presets.get(preset, presets["default"])

    def get_enhance_filters(self, enhance_type: str, intensity: float,
                          quality_level: int = 2, sharpness: float = 1.0,
                          denoising: float = 0.5, color_boost: float = 1.0,
                          target_fps: float = 0.0, hdr_tone: float = 1.0) -> str:
        """生成增强滤镜字符串"""
        filters = []
        
        if enhance_type in ["quality", "all"]:
            # 质量增强
            filters.extend([
                f"scale=iw*{quality_level}:ih*{quality_level}:flags=lanczos",
                f"unsharp=5:5:{sharpness}:3:3:{sharpness*0.75}"
            ])

        if enhance_type in ["detail", "all"]:
            # 细节增强
            filters.extend([
                f"unsharp=7:7:{intensity*2}",
                "pp=de"  # 默认边缘增强
            ])

        if enhance_type in ["color", "all"]:
            # 色彩增强
            filters.extend([
                f"eq=saturation={1+color_boost*0.5}:contrast={1+intensity*0.3}",
                f"vibrance={intensity*30}",
                "colorlevels=rimin=0.058:gimin=0.058:bimin=0.058"
            ])

        if enhance_type in ["hdr", "all"]:
            # HDR效果增强
            filters.extend([
                f"zscale=t=linear:npl=100,tonemap=tonemap=hable:desat=0:peak={hdr_tone}",
                "normalize=blackpt=black:whitept=white:smoothing=0.1"
            ])

        if enhance_type in ["stabilize", "all"]:
            # 视频稳定
            filters.extend([
                "vidstabdetect=shakiness=5:accuracy=15",
                f"vidstabtransform=smoothing={30*intensity}:optzoom=1:interpol=linear"
            ])

        if enhance_type in ["denoise", "all"]:
            # 降噪处理
            filters.extend([
                f"nlmeans=s={denoising}:p=7:r=15",
                f"hqdn3d={denoising*10}"
            ])

        if enhance_type in ["deinterlace", "all"]:
            # 去隔行
            filters.append("yadif=mode=1")

        if enhance_type in ["framerate", "all"] and target_fps > 0:
            # 帧率提升
            filters.append(f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc")

        return ",".join(filters)

    def enhance_video(self, input_video: str, enhance_type: str,
                     intensity: float, use_gpu: bool,
                     preset: str = "default",
                     quality_level: int = 2,
                     sharpness: float = 1.0,
                     denoising: float = 0.5,
                     color_boost: float = 1.0,
                     target_fps: float = 0.0,
                     hdr_tone: float = 1.0) -> Tuple[str]:
        """增强视频"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 应用预设参数
            if preset != "custom":
                preset_params = self.get_preset_params(preset)
                enhance_type = preset_params["enhance_type"]
                intensity = preset_params["intensity"]
                quality_level = preset_params.get("quality_level", quality_level)
                sharpness = preset_params.get("sharpness", sharpness)
                denoising = preset_params.get("denoising", denoising)
                color_boost = preset_params.get("color_boost", color_boost)
                target_fps = preset_params.get("target_fps", target_fps)
                hdr_tone = preset_params.get("hdr_tone", hdr_tone)

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 获取增强滤镜
            enhance_filters = self.get_enhance_filters(
                enhance_type, intensity, quality_level,
                sharpness, denoising, color_boost,
                target_fps, hdr_tone
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
            command.extend(["-vf", enhance_filters])

            # 添加编码参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",
                    "-rc:v", "vbr",
                    "-cq:v", "18"  # 使用较高质量
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", "slow",  # 使用较慢的编码以提高质量
                    "-crf", "18"
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
            print(f"增强视频时出错: {str(e)}")
            return (str(e),)