import os
from typing import Tuple, List
import folder_paths
from ..base.ffmpeg_base import FFmpegBase

class VideoMerge(FFmpegBase):
    """
    视频合并节点
    功能：将多个视频合并为一个，支持多种合并方式
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_videos": ("STRING", {"default": "", "multiline": True}),  # 每行一个视频路径
                "merge_mode": (["concat", "stack_horizontal", "stack_vertical", "grid"], 
                             {"default": "concat"}),
                "use_gpu": ("BOOLEAN", {"default": True}),
                "preset": (["default", "seamless", "custom"], 
                          {"default": "default"}),
            },
            "optional": {
                "transition_time": ("FLOAT", {"default": 0.0, "min": 0.0}),
                "grid_columns": ("INT", {"default": 2, "min": 1}),
                "pad_color": ("STRING", {"default": "black"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "merge_videos"
    CATEGORY = "FFmpeg"

    def get_preset_params(self, preset: str) -> dict:
        """获取预设参数"""
        presets = {
            "default": {
                "transition_time": 0.0,
                "pad_color": "black"
            },
            "seamless": {
                "transition_time": 0.5,
                "pad_color": "black"
            }
        }
        return presets.get(preset, presets["default"])

    def create_output_path(self, input_videos: List[str]) -> str:
        """创建输出文件路径"""
        video_hash = self.get_video_hash(input_videos[0])
        base_output_dir = folder_paths.get_output_directory()
        output_filename = f"merged_{video_hash}.mp4"
        return os.path.join(base_output_dir, output_filename)

    def create_concat_file(self, input_videos: List[str]) -> str:
        """创建用于concat的临时文件"""
        concat_content = ""
        for video in input_videos:
            concat_content += f"file '{os.path.abspath(video)}'\n"
        
        concat_file = os.path.join(folder_paths.get_temp_directory(), "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            f.write(concat_content)
        
        return concat_file

    def merge_videos(self, input_videos: str, merge_mode: str,
                    use_gpu: bool, preset: str = "default",
                    transition_time: float = 0.0,
                    grid_columns: int = 2,
                    pad_color: str = "black") -> Tuple[str]:
        """合并视频"""
        try:
            # 解析输入视频列表
            video_list = [v.strip() for v in input_videos.split('\n') if v.strip()]
            if not video_list:
                raise ValueError("没有提供输入视频")

            # 创建输出路径
            output_path = self.create_unique_output_path(video_list[0])
            
            # 获取 GPU 参数
            gpu_params = self.get_gpu_params(use_gpu)

            # 根据合并模式构建滤镜
            filter_complex = []
            
            if merge_mode == "concat":
                # 创建 concat 文件列表
                concat_file = os.path.join(os.path.dirname(output_path), "concat.txt")
                with open(concat_file, 'w', encoding='utf-8') as f:
                    for video in video_list:
                        f.write(f"file '{video}'\n")
                
                command = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,
                    "-c:v", gpu_params["h264_encoder"] if use_gpu else "libx264",
                    "-crf", "23",
                    "-preset", "medium",
                    "-c:a", "aac",
                    output_path
                ]
                
            else:
                # 为每个输入添加缩放滤镜
                inputs = []
                for i, video in enumerate(video_list):
                    inputs.extend(["-i", video])
                    if merge_mode in ["stack_horizontal", "stack_vertical", "grid"]:
                        # 添加缩放滤镜，确保所有视频具有相同的尺寸
                        filter_complex.append(f"[{i}:v]scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color={pad_color}[v{i}];")

                # 构建合并滤镜
                if merge_mode == "stack_horizontal":
                    filter_complex.append("".join([f"[v{i}]" for i in range(len(video_list))]) + f"hstack=inputs={len(video_list)}[v]")
                elif merge_mode == "stack_vertical":
                    filter_complex.append("".join([f"[v{i}]" for i in range(len(video_list))]) + f"vstack=inputs={len(video_list)}[v]")
                elif merge_mode == "grid":
                    rows = (len(video_list) + grid_columns - 1) // grid_columns
                    current = 0
                    # 首先创建水平堆叠
                    for r in range(rows):
                        inputs_in_row = min(grid_columns, len(video_list) - r * grid_columns)
                        if inputs_in_row > 1:
                            filter_complex.append("".join([f"[v{current + i}]" for i in range(inputs_in_row)]) + 
                                               f"hstack=inputs={inputs_in_row}[row{r}];")
                        else:
                            filter_complex.append(f"[v{current}][row{r}]")
                        current += inputs_in_row
                    # 然后垂直堆叠所有行
                    if rows > 1:
                        filter_complex.append("".join([f"[row{i}]" for i in range(rows)]) + f"vstack=inputs={rows}[v]")

                command = [
                    "ffmpeg", "-y",
                    *inputs,
                    "-filter_complex", "".join(filter_complex),
                    "-map", "[v]",
                    "-map", "0:a",
                    "-c:v", gpu_params["h264_encoder"] if use_gpu else "libx264",
                    "-crf", "23",
                    "-preset", "medium",
                    "-c:a", "aac",
                    output_path
                ]

            # 执行命令
            success, message = self.execute_ffmpeg(command)

            if not success:
                raise RuntimeError(f"FFmpeg 执行失败: {message}")

            # 清理临时文件
            if merge_mode == "concat" and os.path.exists(concat_file):
                os.remove(concat_file)

            return (output_path,)

        except Exception as e:
            print(f"合并视频时出错: {str(e)}")
            return (str(e),)

    def create_unique_output_path(self, input_video: str) -> str:
        """创建唯一的输出文件路径"""
        directory = os.path.join(folder_paths.get_output_directory(), "video_merge")
        os.makedirs(directory, exist_ok=True)
        
        # 获取输入文件的扩展名
        ext = os.path.splitext(input_video)[1]
        if not ext:
            ext = ".mp4"
        
        # 生成唯一的文件名
        base_name = "merged"
        counter = 1
        while True:
            if counter == 1:
                file_name = f"{base_name}{ext}"
            else:
                file_name = f"{base_name}_{counter}{ext}"
            
            output_path = os.path.join(directory, file_name)
            if not os.path.exists(output_path):
                return output_path
            counter += 1