import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoSplitting(FFmpegBase):
    """
    视频分割节点
    功能：将视频分割成多个片段
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "split_mode": (["time", "duration", "segments"], {"default": "time"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "start_time": ("STRING", {"default": "00:00:00"}),
                "duration": ("STRING", {"default": "00:01:00"}),
                "segments": ("INT", {"default": 2, "min": 2, "max": 100}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_paths",)
    FUNCTION = "split_video"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str, index: int) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"split_{video_hash}_part{index}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def get_video_duration(self, input_video: str) -> float:
        """获取视频总时长"""
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_video}"'
        duration = float(os.popen(cmd).read().strip())
        return duration

    def split_video(self, input_video: str, split_mode: str,
                   use_gpu: bool, start_time: str = "00:00:00",
                   duration: str = "00:01:00", segments: int = 2,
                   preset: str = "medium") -> Tuple[str]:
        """执行视频分割"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            output_files = []
            total_duration = self.get_video_duration(input_video)

            if split_mode == "segments":
                segment_duration = total_duration / segments
                for i in range(segments):
                    output_path = self.create_output_path(input_video, i)
                    start = i * segment_duration
                    
                    command = [
                        "ffmpeg",
                        "-y",
                    ]

                    if use_gpu:
                        command.extend(["-hwaccel", "cuda"])

                    command.extend([
                        "-i", input_video,
                        "-ss", str(start),
                        "-t", str(segment_duration),
                    ])

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

                    command.extend([
                        "-c:a", "copy",
                        output_path
                    ])

                    success, message = self.execute_ffmpeg(command)
                    if success:
                        output_files.append(output_path)
                    else:
                        raise RuntimeError(f"分割第{i+1}段时失败: {message}")

            else:  # time or duration mode
                output_path = self.create_output_path(input_video, 0)
                command = [
                    "ffmpeg",
                    "-y",
                ]

                if use_gpu:
                    command.extend(["-hwaccel", "cuda"])

                command.extend([
                    "-i", input_video,
                    "-ss", start_time,
                ])

                if split_mode == "duration":
                    command.extend(["-t", duration])

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

                command.extend([
                    "-c:a", "copy",
                    output_path
                ])

                success, message = self.execute_ffmpeg(command)
                if success:
                    output_files.append(output_path)
                else:
                    raise RuntimeError(f"分割视频时失败: {message}")

            return (",".join(output_files),)

        except Exception as e:
            print(f"分割视频时出错: {str(e)}")
            return (str(e),)