import os
from typing import Tuple
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoStreaming(FFmpegBase):
    """
    视频流转换节点
    功能：将视频转换为流媒体格式，支持HLS和DASH
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "format": (["hls", "dash"], {"default": "hls"}),
                "segment_duration": ("INT", {"default": 6, "min": 1, "max": 30}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "playlist_name": ("STRING", {"default": "playlist"}),
                "preset": (["medium", "fast", "slow"], {"default": "medium"}),
                "quality_levels": ("INT", {"default": 3, "min": 1, "max": 5}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "create_stream"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str, format: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_dir = os.path.join(base_output_dir, f"stream_{video_hash}")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def create_stream(self, input_video: str, format: str,
                     segment_duration: int, use_gpu: bool,
                     playlist_name: str = "playlist",
                     preset: str = "medium",
                     quality_levels: int = 3) -> Tuple[str]:
        """执行流媒体转换"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 创建输出目录
            output_dir = self.create_output_path(input_video, format)
            
            # 基础命令
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
                filter_complex.append("hwdownload")
                filter_complex.append("format=nv12")

            # 添加滤镜链（如果有）
            if filter_complex:
                command.extend(["-vf", ",".join(filter_complex)])

            # 根据格式设置特定参数
            if format == "hls":
                output_path = os.path.join(output_dir, f"{playlist_name}.m3u8")
                command.extend([
                    "-c:v", "h264_nvenc" if use_gpu else "libx264",
                    "-preset", "p7" if use_gpu else preset,
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-f", "hls",
                    "-hls_time", str(segment_duration),
                    "-hls_list_size", "0",
                    "-hls_segment_filename", os.path.join(output_dir, "segment%03d.ts"),
                ])
            else:  # dash
                output_path = os.path.join(output_dir, f"{playlist_name}.mpd")
                command.extend([
                    "-c:v", "h264_nvenc" if use_gpu else "libx264",
                    "-preset", "p7" if use_gpu else preset,
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-f", "dash",
                    "-seg_duration", str(segment_duration),
                    "-init_seg_name", "init-$RepresentationID$.m4s",
                    "-media_seg_name", "chunk-$RepresentationID$-$Number%05d$.m4s",
                ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"流媒体转换失败: {message}")

            return (output_path,)

        except Exception as e:
            print(f"创建流媒体时出错: {str(e)}")
            return (str(e),)