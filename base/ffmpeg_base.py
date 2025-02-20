import os
import sys
import hashlib
import subprocess
from typing import List, Dict, Tuple, Optional, Union
import folder_paths

class FFmpegBase:
    """
    FFmpeg基础类
    提供FFmpeg操作的基础功能和工具方法
    """
    
    def __init__(self):
        self.ffmpeg_path = self._get_ffmpeg_path()
        self.ffprobe_path = self._get_ffprobe_path()
        self.temp_dir = folder_paths.get_temp_directory()
        os.makedirs(self.temp_dir, exist_ok=True)

    @staticmethod
    def _get_ffmpeg_path() -> str:
        """获取ffmpeg可执行文件路径"""
        if sys.platform == 'win32':
            return 'ffmpeg.exe'
        return 'ffmpeg'

    @staticmethod
    def _get_ffprobe_path() -> str:
        """获取ffprobe可执行文件路径"""
        if sys.platform == 'win32':
            return 'ffprobe.exe'
        return 'ffprobe'

    def get_video_hash(self, video_path: str) -> str:
        """
        生成视频文件的哈希值
        用于创建唯一的输出文件名
        """
        if not os.path.exists(video_path):
            return hashlib.md5(video_path.encode()).hexdigest()[:8]
        
        file_stat = os.stat(video_path)
        hash_input = f"{video_path}{file_stat.st_size}{file_stat.st_mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def get_gpu_params(self, use_gpu: bool) -> Dict[str, Union[List[str], str]]:
        """
        获取GPU相关的FFmpeg参数
        """
        if not use_gpu:
            return {
                "hw_accel": [],
                "h264_encoder": "libx264"
            }

        # 检测系统和GPU类型
        if sys.platform == 'win32':
            # NVIDIA GPU
            return {
                "hw_accel": ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"],
                "h264_encoder": "h264_nvenc"
            }
        elif sys.platform == 'darwin':
            # macOS (VideoToolbox)
            return {
                "hw_accel": ["-hwaccel", "videotoolbox"],
                "h264_encoder": "h264_videotoolbox"
            }
        else:
            # Linux (VAAPI)
            return {
                "hw_accel": ["-hwaccel", "vaapi", "-hwaccel_output_format", "vaapi"],
                "h264_encoder": "h264_vaapi"
            }

    def execute_ffmpeg(self, command: List[str]) -> Tuple[bool, str]:
        """
        执行FFmpeg命令
        返回: (成功标志, 输出信息)
        """
        try:
            # 确保第一个参数是ffmpeg
            if command[0] != "ffmpeg":
                command[0] = self.ffmpeg_path

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            # 检查执行结果
            if process.returncode != 0:
                return False, stderr
            
            return True, stdout
        except Exception as e:
            return False, str(e)

    def execute_ffprobe(self, command: List[str]) -> Optional[str]:
        """
        执行FFprobe命令
        返回: 命令输出或None(如果失败)
        """
        try:
            # 确保第一个参数是ffprobe
            if command[0] != "ffprobe":
                command[0] = self.ffprobe_path

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            # 检查执行结果
            if process.returncode != 0:
                print(f"FFprobe执行错误: {stderr}")
                return None
            
            return stdout
        except Exception as e:
            print(f"FFprobe执行异常: {str(e)}")
            return None

    def get_video_duration(self, video_path: str) -> Optional[float]:
        """获取视频时长(秒)"""
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "format=duration",
            video_path
        ]
        
        result = self.execute_ffprobe(command)
        if result:
            import json
            try:
                data = json.loads(result)
                return float(data['format']['duration'])
            except:
                return None
        return None

    def get_video_resolution(self, video_path: str) -> Optional[Tuple[int, int]]:
        """获取视频分辨率"""
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            video_path
        ]
        
        result = self.execute_ffprobe(command)
        if result:
            import json
            try:
                data = json.loads(result)
                stream = data['streams'][0]
                return (int(stream['width']), int(stream['height']))
            except:
                return None
        return None

    def get_video_framerate(self, video_path: str) -> Optional[float]:
        """获取视频帧率"""
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            video_path
        ]
        
        result = self.execute_ffprobe(command)
        if result:
            import json
            try:
                data = json.loads(result)
                fps_str = data['streams'][0]['r_frame_rate']
                num, den = map(int, fps_str.split('/'))
                return num / den
            except:
                return None
        return None

    def create_output_path(self, input_path: str, suffix: str = "") -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_path)
        base_output_dir = folder_paths.get_output_directory()
        if suffix:
            output_filename = f"{video_hash}_{suffix}.mp4"
        else:
            output_filename = f"{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def ensure_directory(self, path: str) -> None:
        """确保目录存在"""
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def cleanup_temp_files(self, *files: str) -> None:
        """清理临时文件"""
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                print(f"清理临时文件失败 {file}: {str(e)}")

    def format_time(self, seconds: float) -> str:
        """格式化时间为 HH:MM:SS.mmm 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    def parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        if not time_str:
            return 0.0
        
        # 处理纯数字（秒数）
        if time_str.replace(".", "").isdigit():
            return float(time_str)
            
        # 处理时:分:秒格式
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:
                raise ValueError("无效的时间格式")
        except:
            raise ValueError("无效的时间格式")

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"