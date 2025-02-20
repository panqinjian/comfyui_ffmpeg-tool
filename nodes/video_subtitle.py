import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoSubtitle(FFmpegBase):
    """
    视频字幕处理节点
    功能：添加、移除或提取视频字幕
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "mode": (["add", "remove", "extract"], {"default": "add"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "subtitle_file": ("STRING", {"default": ""}),
                "font_file": ("STRING", {"default": ""}),
                "font_size": ("INT", {"default": 24, "min": 8, "max": 72}),
                "font_color": ("STRING", {"default": "white"}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
                "subtitle_encoding": ("STRING", {"default": "utf-8"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "process_subtitle"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str, mode: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        if mode == "extract":
            output_filename = f"subtitle_{video_hash}.srt"
        else:
            output_filename = f"subtitle_{mode}_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def process_subtitle(self, input_video: str, mode: str,
                        use_gpu: bool, subtitle_file: str = "",
                        font_file: str = "", font_size: int = 24,
                        font_color: str = "white",
                        preset: str = "medium",
                        subtitle_encoding: str = "utf-8") -> Tuple[str]:
        """处理视频字幕"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video, mode)

            if mode == "add":
                # 检查字幕文件
                if not subtitle_file or not os.path.exists(subtitle_file):
                    raise FileNotFoundError("字幕文件不存在")

                command = [
                    "ffmpeg",
                    "-y",
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

                # 添加字幕滤镜
                subtitle_filter = f"subtitles='{subtitle_file}':force_style='"
                if font_file and os.path.exists(font_file):
                    subtitle_filter += f"FontName={os.path.splitext(os.path.basename(font_file))[0]},"
                subtitle_filter += f"FontSize={font_size},PrimaryColour=&H{font_color}'"
                
                filter_complex.append(subtitle_filter)

                if use_gpu:
                    filter_complex.append("hwdownload")
                    filter_complex.append("format=nv12")

                # 添加滤镜链
                command.extend(["-vf", ",".join(filter_complex)])

                # 添加编码器参数
                if use_gpu:
                    command.extend([
                        "-c:v", "h264_nvenc",
                        "-preset", "p7",
                        "-rc:v", "vbr",
                        "-cq:v", "23",
                    ])
                else:
                    command.extend([
                        "-c:v", "libx264",
                        "-preset", preset,
                        "-crf", "23",
                    ])

                # 复制音频流
                command.extend(["-c:a", "copy"])

            elif mode == "remove":
                command = [
                    "ffmpeg",
                    "-y",
                ]

                if use_gpu:
                    command.extend(["-hwaccel", "cuda"])

                command.extend([
                    "-i", input_video,
                    "-map", "0:v",  # 只选择视频流
                    "-map", "0:a",  # 只选择音频流
                ])

                if use_gpu:
                    command.extend([
                        "-c:v", "h264_nvenc",
                        "-preset", "p7",
                        "-rc:v", "vbr",
                        "-cq:v", "23",
                    ])
                else:
                    command.extend([
                        "-c:v", "libx264",
                        "-preset", preset,
                        "-crf", "23",
                    ])

                command.extend(["-c:a", "copy"])

            else:  # extract
                command = [
                    "ffmpeg",
                    "-y",
                    "-i", input_video,
                    "-map", "0:s:0",  # 选择第一个字幕流
                    "-c:s", "srt",
                ]

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"字幕处理失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"处理视频字幕时出错: {str(e)}")
            return (str(e),)