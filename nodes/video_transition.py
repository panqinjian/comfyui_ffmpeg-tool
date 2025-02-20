import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoTransition(FFmpegBase):
    """
    视频转场效果节点
    功能：在两个视频之间添加转场效果
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video1": ("STRING", {"default": ""}),
                "input_video2": ("STRING", {"default": ""}),
                "transition_type": (["fade", "dissolve", "wipe", "slide", "zoom"], 
                                  {"default": "fade"}),
                "transition_duration": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
                "direction": (["left", "right", "up", "down"], {"default": "left"}),
                "maintain_quality": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "create_transition"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video1: str, input_video2: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video1 + input_video2)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"transition_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def create_transition(self, input_video1: str, input_video2: str,
                         transition_type: str, transition_duration: float,
                         use_gpu: bool, preset: str = "medium",
                         direction: str = "left",
                         maintain_quality: bool = True) -> Tuple[str]:
        """创建视频转场效果"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video1) or not os.path.exists(input_video2):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video1, input_video2)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",
            ]

            # 添加GPU相关参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 添加输入文件
            command.extend([
                "-i", input_video1,
                "-i", input_video2
            ])

            # 构建滤镜字符串
            filter_complex = []
            
            if use_gpu:
                filter_complex.extend([
                    "[0:v]hwupload_cuda[v0c]",
                    "[1:v]hwupload_cuda[v1c]"
                ])
                video_inputs = "[v0c][v1c]"
            else:
                video_inputs = "[0:v][1:v]"

            # 根据转场类型添加相应的滤镜
            if transition_type == "fade":
                filter_complex.append(
                    f"{video_inputs}xfade=transition=fade:duration={transition_duration}:offset=0[v]"
                )
            elif transition_type == "dissolve":
                filter_complex.append(
                    f"{video_inputs}xfade=transition=dissolve:duration={transition_duration}:offset=0[v]"
                )
            elif transition_type == "wipe":
                filter_complex.append(
                    f"{video_inputs}xfade=transition=wipe{direction}:duration={transition_duration}:offset=0[v]"
                )
            elif transition_type == "slide":
                filter_complex.append(
                    f"{video_inputs}xfade=transition=slide{direction}:duration={transition_duration}:offset=0[v]"
                )
            elif transition_type == "zoom":
                filter_complex.append(
                    f"{video_inputs}xfade=transition=zoom{direction}:duration={transition_duration}:offset=0[v]"
                )

            if use_gpu:
                filter_complex.append("[v]hwdownload,format=nv12[vout]")
                filter_complex.append("[vout]format=yuv420p[vfinal]")
            else:
                filter_complex.append("[v]format=yuv420p[vfinal]")

            # 添加滤镜链
            command.extend([
                "-filter_complex", ";".join(filter_complex),
                "-map", "[vfinal]",
                "-map", "0:a"  # 使用第一个视频的音频
            ])

            # 添加编码器参数
            if use_gpu:
                command.extend([
                    "-c:v", "h264_nvenc",
                    "-preset", "p7",
                    "-rc:v", "vbr",
                    "-cq:v", "23" if maintain_quality else "28",
                ])
            else:
                command.extend([
                    "-c:v", "libx264",
                    "-preset", preset,
                    "-crf", "23" if maintain_quality else "28",
                ])

            # 复制音频流
            command.extend(["-c:a", "copy"])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"创建转场效果失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"创建视频转场效果时出错: {str(e)}")
            return (str(e),)