import os
import json
from typing import Tuple, Dict
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoInfo(FFmpegBase):
    """
    视频信息节点
    功能：获取视频的详细信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "info_type": (["basic", "detailed", "streams", "frames", "packets"], 
                             {"default": "basic"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")  # 返回信息字符串和JSON格式
    RETURN_NAMES = ("info_text", "info_json")
    FUNCTION = "get_video_info"
    CATEGORY = "FFmpeg"

    def format_duration(self, duration_seconds: float) -> str:
        """格式化持续时间"""
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = duration_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def get_video_info(self, input_video: str, info_type: str) -> Tuple[str, str]:
        """获取视频信息"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 构建命令
            if info_type == "basic":
                command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    input_video
                ]
            elif info_type == "detailed":
                command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    "-show_chapters",
                    "-show_programs",
                    input_video
                ]
            elif info_type == "streams":
                command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    input_video
                ]
            elif info_type == "frames":
                command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_frames",
                    input_video
                ]
            else:  # packets
                command = [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_packets",
                    input_video
                ]

            # 执行命令
            result = self.execute_ffprobe(command)
            if not result:
                raise RuntimeError("无法获取视频信息")

            # 解析JSON结果
            info = json.loads(result)

            # 格式化信息文本
            info_text = ""
            if info_type == "basic":
                format_info = info.get("format", {})
                streams = info.get("streams", [])
                
                # 基本文件信息
                info_text += "文件信息:\n"
                info_text += f"文件名: {os.path.basename(input_video)}\n"
                info_text += f"格式: {format_info.get('format_name', 'N/A')}\n"
                info_text += f"时长: {self.format_duration(float(format_info.get('duration', 0)))}\n"
                info_text += f"大小: {self.format_size(int(format_info.get('size', 0)))}\n"
                info_text += f"比特率: {int(format_info.get('bit_rate', 0)) // 1000} kbps\n\n"

                # 流信息
                for stream in streams:
                    codec_type = stream.get("codec_type", "unknown")
                    if codec_type == "video":
                        info_text += "视频流:\n"
                        info_text += f"编码器: {stream.get('codec_name', 'N/A')}\n"
                        info_text += f"分辨率: {stream.get('width', 'N/A')}x{stream.get('height', 'N/A')}\n"
                        info_text += f"帧率: {stream.get('r_frame_rate', 'N/A')}\n"
                        info_text += f"像素格式: {stream.get('pix_fmt', 'N/A')}\n\n"
                    elif codec_type == "audio":
                        info_text += "音频流:\n"
                        info_text += f"编码器: {stream.get('codec_name', 'N/A')}\n"
                        info_text += f"采样率: {stream.get('sample_rate', 'N/A')} Hz\n"
                        info_text += f"声道数: {stream.get('channels', 'N/A')}\n"
                        info_text += f"比特率: {int(stream.get('bit_rate', 0)) // 1000} kbps\n\n"

            else:
                # 对于其他类型，直接使用格式化的JSON
                info_text = json.dumps(info, indent=2, ensure_ascii=False)

            # 返回文本信息和JSON字符串
            return (info_text, json.dumps(info, ensure_ascii=False))

        except Exception as e:
            error_msg = f"获取视频信息时出错: {str(e)}"
            return (error_msg, "{}")