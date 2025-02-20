import os
from typing import Tuple, Dict
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoMetadata(FFmpegBase):
    """
    视频元数据处理节点
    功能：读取、修改视频的元数据信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video": ("STRING", {"default": ""}),
                "operation": (["read", "write", "remove"], {"default": "read"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "title": ("STRING", {"default": ""}),
                "artist": ("STRING", {"default": ""}),
                "album": ("STRING", {"default": ""}),
                "year": ("STRING", {"default": ""}),
                "description": ("STRING", {"default": ""}),
                "comment": ("STRING", {"default": ""}),
                "copyright": ("STRING", {"default": ""}),
                "language": ("STRING", {"default": ""}),
                "custom_metadata": ("STRING", {"default": ""}),  # 格式: key1=value1;key2=value2
            }
        }

    RETURN_TYPES = ("STRING", "STRING")  # 返回处理后的视频路径和元数据信息
    RETURN_NAMES = ("output_path", "metadata_info")
    FUNCTION = "process_metadata"
    CATEGORY = "FFmpeg"

    def create_output_path(self, input_video: str) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_video)
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"metadata_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def parse_custom_metadata(self, custom_metadata: str) -> Dict[str, str]:
        """解析自定义元数据字符串"""
        metadata = {}
        if custom_metadata:
            pairs = custom_metadata.split(";")
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    metadata[key.strip()] = value.strip()
        return metadata

    def process_metadata(self, input_video: str, operation: str,
                        use_gpu: bool, title: str = "",
                        artist: str = "", album: str = "",
                        year: str = "", description: str = "",
                        comment: str = "", copyright: str = "",
                        language: str = "",
                        custom_metadata: str = "") -> Tuple[str, str]:
        """处理视频元数据"""
        try:
            # 检查输入视频是否存在
            if not os.path.exists(input_video):
                raise FileNotFoundError("输入视频文件不存在")

            # 读取当前元数据
            current_metadata = {}
            metadata_command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                input_video
            ]
            result = self.execute_ffprobe(metadata_command)
            if result:
                import json
                probe_data = json.loads(result)
                current_metadata = probe_data.get("format", {}).get("tags", {})

            if operation == "read":
                # 直接返回当前元数据
                metadata_info = json.dumps(current_metadata, indent=2, ensure_ascii=False)
                return (input_video, metadata_info)

            # 创建输出文件路径
            output_path = self.create_output_path(input_video)

            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 构建基本命令
            command = [
                "ffmpeg",
                "-y",  # 覆盖已存在的文件
                *gpu_params["hw_accel"],
                "-i", input_video,
            ]

            # 处理元数据
            if operation == "write":
                # 添加基本元数据
                metadata_map = {
                    "title": title,
                    "artist": artist,
                    "album": album,
                    "year": year,
                    "description": description,
                    "comment": comment,
                    "copyright": copyright,
                    "language": language
                }

                # 添加所有非空的元数据
                for key, value in metadata_map.items():
                    if value:
                        command.extend(["-metadata", f"{key}={value}"])

                # 处理自定义元数据
                custom_meta = self.parse_custom_metadata(custom_metadata)
                for key, value in custom_meta.items():
                    command.extend(["-metadata", f"{key}={value}"])

            elif operation == "remove":
                # 移除所有元数据
                command.extend(["-map_metadata", "-1"])

            # 添加编码参数
            command.extend([
                "-c:v", gpu_params["h264_encoder"],
                "-crf", "23",  # 使用默认质量
                "-preset", "medium",
                "-c:a", "copy"  # 复制音频流
            ])

            # 添加输出路径
            command.extend([output_path])

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            # 读取更新后的元数据
            updated_metadata = {}
            if os.path.exists(output_path):
                result = self.execute_ffprobe(metadata_command)
                if result:
                    probe_data = json.loads(result)
                    updated_metadata = probe_data.get("format", {}).get("tags", {})

            metadata_info = json.dumps(updated_metadata, indent=2, ensure_ascii=False)
            return (output_path, metadata_info)

        except Exception as e:
            error_msg = f"处理元数据时出错: {str(e)}"
            return (input_video, error_msg)