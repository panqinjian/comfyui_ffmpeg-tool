import os
from typing import Tuple, List
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoConcat(FFmpegBase):
    """
    视频拼接节点
    功能：将多个视频按顺序拼接成一个视频
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_videos": ("STRING", {"default": "", "multiline": True}),  # 多个视频路径，每行一个
                "output_format": (["mp4", "mov", "mkv"], {"default": "mp4"}),
                "quality": ("INT", {"default": 23, "min": 0, "max": 51}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "high_quality", "fast_concat", "stream_copy"], 
                          {"default": "default"}),
                "transition": (["none", "fade", "dissolve"], {"default": "none"}),
                "transition_duration": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "concat_videos"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "quality": 23,
                "output_format": "mp4",
                "transition": "none"
            },
            "high_quality": {
                "quality": 18,
                "output_format": "mov",
                "transition": "dissolve"
            },
            "fast_concat": {
                "quality": 28,
                "output_format": "mp4",
                "transition": "none"
            },
            "stream_copy": {
                "quality": -1,  # 使用流复制
                "output_format": "mp4",
                "transition": "none"
            }
        }
        return presets.get(preset, presets["default"])

    def create_concat_file(self, video_list: List[str]) -> str:
        """创建用于拼接的文件列表"""
        concat_file = os.path.join(folder_paths.get_output_directory(), "concat_list.txt")
        with open(concat_file, 'w', encoding='utf-8') as f:
            for video in video_list:
                if os.path.exists(video):
                    f.write(f"file '{video}'\n")
        return concat_file

    def create_output_path(self, output_format: str) -> str:
        """创建输出文件路径"""
        import time
        timestamp = int(time.time())
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"concat_{timestamp}.{output_format}"
        return os.path.join(base_output_dir, output_filename)

    def concat_videos(self, input_videos: str, output_format: str,
                     quality: int, use_gpu: bool, preset: str = "default",
                     transition: str = "none",
                     transition_duration: float = 1.0) -> Tuple[str]:
        """执行视频拼接"""
        try:
            # 解析输入视频列表
            video_list = [v.strip() for v in input_videos.split('\n') if v.strip()]
            if not video_list:
                raise ValueError("没有输入视频")

            # 检查所有输入视频是否存在
            for video in video_list:
                if not os.path.exists(video):
                    raise FileNotFoundError(f"视频文件不存在: {video}")

            # 应用预设参数
            preset_params = self.get_preset_params(preset)
            if preset != "default":
                quality = preset_params["quality"]
                output_format = preset_params["output_format"]
                transition = preset_params["transition"]

            # 创建输出文件路径
            output_path = self.create_output_path(output_format)

            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 创建拼接列表文件
            concat_file = self.create_concat_file(video_list)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
                *gpu_params["hw_accel"],
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
            ]

            # 根据不同的转场效果添加滤镜
            if transition != "none":
                filter_complex = []
                for i in range(len(video_list) - 1):
                    if transition == "fade":
                        filter_complex.extend([
                            f"[{i}:v]fade=t=out:st={transition_duration}:d={transition_duration}[v{i}];",
                            f"[{i+1}:v]fade=t=in:st=0:d={transition_duration}[v{i+1}];"
                        ])
                    elif transition == "dissolve":
                        filter_complex.extend([
                            f"[{i}:v][{i+1}:v]xfade=transition=fade:duration={transition_duration}[v{i+1}];"
                        ])
                
                command.extend(["-filter_complex", "".join(filter_complex)])

            # 添加编码参数
            if quality >= 0:
                command.extend([
                    "-c:v", gpu_params["h264_encoder"],
                    "-crf", str(quality),
                    "-preset", "medium",
                    "-c:a", "aac",
                    "-b:a", "128k"
                ])
            else:
                # 使用流复制模式
                command.extend([
                    "-c", "copy"
                ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            # 清理临时文件
            if os.path.exists(concat_file):
                os.remove(concat_file)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"拼接视频时出错: {str(e)}")
            return (str(e),)