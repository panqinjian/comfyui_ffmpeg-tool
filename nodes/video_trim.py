import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoTrim(FFmpegBase):
    """
    视频裁剪节点
    功能：裁剪视频的时间段或帧范围
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "trim_mode": (["time", "frame"], {"default": "time"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "start_time": ("STRING", {"default": "00:00:00"}),
                "end_time": ("STRING", {"default": ""}),
                "duration": ("STRING", {"default": ""}),
                "start_frame": ("INT", {"default": 0, "min": 0}),
                "end_frame": ("INT", {"default": -1, "min": -1}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
                "maintain_quality": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "trim_video"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"trimmed_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def get_video_info(self, input_video: str) -> dict:
        """获取视频信息"""
        cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames,duration -of default=noprint_wrappers=1 "{input_video}"'
        info = {}
        for line in os.popen(cmd).readlines():
            key, value = line.strip().split('=')
            info[key] = float(value) if key == 'duration' else int(value)
        return info

    def trim_video(self, input_video: str, trim_mode: str,
                  use_gpu: bool, start_time: str = "00:00:00",
                  end_time: str = "", duration: str = "",
                  start_frame: int = 0, end_frame: int = -1,
                  preset: str = "medium",
                  maintain_quality: bool = True) -> Tuple[str]:
        """执行视频裁剪"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",
            ]

            # 添加GPU相关参数
            if use_gpu:
                command.extend(["-hwaccel", "cuda"])

            # 根据裁剪模式添加参数
            if trim_mode == "time":
                if start_time:
                    command.extend(["-ss", start_time])
                if end_time:
                    command.extend(["-to", end_time])
                elif duration:
                    command.extend(["-t", duration])
            else:  # frame mode
                video_info = self.get_video_info(input_video)
                total_frames = video_info.get('nb_frames', 0)
                
                if end_frame == -1:
                    end_frame = total_frames
                
                command.extend([
                    "-vf", f"select=between(n\\,{start_frame}\\,{end_frame})",
                    "-vsync", "0"
                ])

            # 添加输入文件
            command.extend(["-i", input_video])

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
                raise RuntimeError(f"裁剪视频失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"裁剪视频时出错: {str(e)}")
            return (str(e),)