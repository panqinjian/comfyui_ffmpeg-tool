import os
from typing import Tuple
import folder_paths
from .base.ffmpeg_base import FFmpegBase

class VideoAudio(FFmpegBase):
    """视频音频处理节点"""
    
    # 中英文参数映射
    VALUE_MAPPING = {
        # 预设
        "默认": "default",
        "语音": "voice",
        "音乐": "music",
        "自定义": "custom",
        
        # 降噪
        "关闭": "off",
        "弱": "light",
        "中": "medium",
        "强": "heavy",
        
        # 操作
        "混合": "mix",
        "替换": "replace",
        "提取": "extract"
    }
    
    # 反向映射
    REVERSE_VALUE_MAPPING = {v: k for k, v in VALUE_MAPPING.items()}
    
    # 预设配置
    PRESET_CONFIG = {
        "default": {
            "volume_multi": 1.0,
            "noise_reduction": "off",
            "fade_in": 0,
            "fade_out": 0,
            "audio_bitrate": 128
        },
        "voice": {
            "volume_multi": 1.2,
            "noise_reduction": "medium",
            "fade_in": 0.3,
            "fade_out": 0.3,
            "audio_bitrate": 96
        },
        "music": {
            "volume_multi": 0.8,
            "noise_reduction": "off",
            "fade_in": 1.0,
            "fade_out": 1.0,
            "audio_bitrate": 256
        },
        "custom": {
            "volume_multi": 1.0,
            "noise_reduction": "off",
            "fade_in": 0,
            "fade_out": 0,
            "audio_bitrate": 128
        }
    }
    
    def __init__(self):
        super().__init__()
        
        # 参数名称映射
        self.PARAM_MAPPING = {
            "视频": "video",
            "操作": "operation",
            "预设": "preset",
            "音量": "volume",
            "使用GPU": "use_gpu",
            "降噪级别": "noise_reduction",
            "循环音频": "loop_audio",
            "移除原音频": "remove_original_audio",
            "音频开始时间": "audio_start_time",
            "音频文件": "audio_file",
            "淡入时长": "fade_in",
            "淡出时长": "fade_out",
            "音频时长": "audio_duration",
            "第二音频": "secondary_audio",
            "工作目录": "work_dir",
            "音频比特率": "audio_bitrate"
        }
        
        # 反向映射
        self.REVERSE_PARAM_MAPPING = {v: k for k, v in self.PARAM_MAPPING.items()}
        
        # 设置预设选择的监听器
        self.preset_widget = self.get_widget("预设")  # 获取预设选择的 UI 组件
        self.preset_widget.on_change(self.update_related_parameters)
        
        # 获取其他相关设置的 UI 组件
        self.audio_bitrate_widget = self.get_widget("音频比特率")
        self.volume_widget = self.get_widget("音量")
        self.noise_reduction_widget = self.get_widget("降噪级别")
        self.fade_in_widget = self.get_widget("淡入时长")
        self.fade_out_widget = self.get_widget("淡出时长")

    def update_related_parameters(self, selected_preset):
        preset_params = self.get_preset_params(selected_preset)
        # 更新其他相关设置，例如音频比特率
        self.audio_bitrate_widget.set_value(preset_params['audio_bitrate'])
        self.volume_widget.set_value(preset_params['volume_multi'])
        self.noise_reduction_widget.set_value(preset_params['noise_reduction'])
        self.fade_in_widget.set_value(preset_params['fade_in'])
        self.fade_out_widget.set_value(preset_params['fade_out'])

    def get_preset_params(self, preset_name):
        preset = self.PRESET_CONFIG.get(preset_name, self.PRESET_CONFIG['default'])
        return {
            "audio_bitrate": preset['audio_bitrate'],
            "volume_multi": preset['volume_multi'],
            "noise_reduction": preset['noise_reduction'],
            "fade_in": preset['fade_in'],
            "fade_out": preset['fade_out'],
        }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "视频": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "视频文件路径（支持拖放）"
                }),
                "操作": (["混合", "替换", "提取"], {"default": "混合"}),
                "预设": (["默认", "语音", "音乐", "自定义"], {"default": "默认"}),
                "音量": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "使用GPU": ("BOOLEAN", {"default": True}),
                "降噪级别": (["关闭", "弱", "中", "强"], {"default": "关闭"}),
            },
            "optional": {
                "循环音频": ("BOOLEAN", {"default": False}),
                "移除原音频": ("BOOLEAN", {"default": False}),
                "音频开始时间": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
                "音频文件": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "外部音频文件路径（可选）"
                }),
                "淡入时长": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
                "淡出时长": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
                "音频时长": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "step": 0.1
                }),
                "第二音频": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "第二音频文件路径（可选）"
                }),
                "工作目录": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "工作目录路径（可选）"
                }),
                "音频比特率": ("INTEGER", {
                    "default": 128,
                    "min": 32,
                    "max": 512,
                    "step": 32
                }),
            }
        }
        
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_video_audio"
    CATEGORY = "FFmpeg/音频处理"

    def convert_params_to_english(self, **kwargs):
        """将中文参数转换为英文"""
        english_kwargs = {}
        for k, v in kwargs.items():
            # 转换参数名
            eng_key = self.PARAM_MAPPING.get(k, k)
            # 转换参数值（如果是字符串且在映射中存在）
            eng_value = self.VALUE_MAPPING.get(v, v) if isinstance(v, str) else v
            english_kwargs[eng_key] = eng_value
        return english_kwargs

    def process_video_audio(self, **kwargs) -> Tuple[str]:
        """处理视频音频"""
        try:
            # 转换所有参数为英文
            eng_kwargs = self.convert_params_to_english(**kwargs)
            
            # 检查必要的输入
            if not eng_kwargs.get('video'):
                return ("请提供视频文件路径",)
            
            video_path = os.path.abspath(eng_kwargs['video'])
            if not os.path.exists(video_path):
                return (f"视频文件不存在: {video_path}",)
            
            # 检查音频文件
            if eng_kwargs.get('audio_file'):
                audio_path = os.path.abspath(eng_kwargs['audio_file'])
                if not os.path.exists(audio_path):
                    return (f"音频文件不存在: {audio_path}",)
            
            # 检查第二音频文件
            if eng_kwargs.get('secondary_audio'):
                secondary_audio_path = os.path.abspath(eng_kwargs['secondary_audio'])
                if not os.path.exists(secondary_audio_path):
                    return (f"第二音频文件不存在: {secondary_audio_path}",)
            
            # 生成输出路径
            output_path = self.get_unique_output_path(".mp4")
            
            # 构建命令
            command = [self.ffmpeg_path, "-y"]
            
            # 获取GPU相关参数
            gpu_params = self.get_gpu_params(eng_kwargs.get('use_gpu', False))
            command.extend(gpu_params['hw_accel'])
            
            # 添加输入文件
            command.extend(["-i", video_path])
            if eng_kwargs.get('audio_file'):
                command.extend(["-i", audio_path])
            if eng_kwargs.get('secondary_audio'):
                command.extend(["-i", secondary_audio_path])
            
            # 复制视频流
            command.extend(["-c:v", gpu_params['h264_encoder']])
            
            # 构建音频滤镜
            audio_filters = self.build_audio_filters(**eng_kwargs)
            if audio_filters:
                command.extend(["-filter_complex", audio_filters])
            
            # 设置输出编码器
            command.extend(["-c:a", "aac"])
            
            # 添加输出文件
            command.append(output_path)
            
            # 执行命令
            returncode, stdout, stderr = self.execute_ffmpeg(command, timeout=int(eng_kwargs.get('timeout', 3600)))
            
            if returncode != 0:
                # 清理临时文件
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except:
                        pass
                return (f"处理失败: {stderr}",)
            
            return (output_path,)
            
        except Exception as e:
            error_msg = f"处理视频音频时出错: {e.__class__.__name__}: {str(e)}"
            print(error_msg)
            # 清理临时文件
            if 'output_path' in locals() and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            return (error_msg,)

    def build_audio_filters(self, **kwargs) -> str:
        """构建音频滤镜"""
        try:
            # 获取预设配置
            preset_name = self.VALUE_MAPPING.get(kwargs.get('preset', '默认'), 'default')
            preset = self.PRESET_CONFIG.get(preset_name, self.PRESET_CONFIG['default'])
            
            # 特殊操作的处理
            if kwargs.get('remove_original_audio', False) or kwargs.get('operation') == "extract":
                return "anullsrc=r=44100:cl=stereo"
            
            # 构建基本滤镜链
            filters = []
            
            # 音量调整
            volume = kwargs.get('volume', 1.0)
            if preset_name != 'custom':
                volume *= preset['volume_multi']
            
            if volume != 1.0:
                filters.append(f"volume={volume}")
            
            # 降噪处理
            noise_reduction = kwargs.get('noise_reduction', 'off')
            if noise_reduction != 'off':
                filters.append(f"arnndn=model=rnnoise/{noise_reduction}.model")
            elif preset['noise_reduction'] != 'off':
                filters.append(f"arnndn=model=rnnoise/{preset['noise_reduction']}.model")
            
            # 淡入淡出处理
            fade_in = kwargs.get('fade_in', preset['fade_in'])
            fade_out = kwargs.get('fade_out', preset['fade_out'])
            
            if fade_in > 0:
                filters.append(f"afade=t=in:st=0:d={fade_in}")
            
            if fade_out > 0:
                duration = kwargs.get('audio_duration', 0)
                if not duration and kwargs.get('video'):
                    duration = self.get_video_duration(kwargs['video']) or 0
                
                if duration > 0:
                    filters.append(f"afade=t=out:st={duration-fade_out}:d={fade_out}")
            
            # 循环音频
            if kwargs.get('loop_audio', False):
                filters.append("aloop=loop=-1")
            
            # 音频延迟
            if kwargs.get('audio_start_time', 0) > 0:
                filters.append(f"adelay={int(kwargs['audio_start_time']*1000)}")
            
            # 音频混合
            if kwargs.get('operation') == "mix" and kwargs.get('audio_file'):
                filters.append("amix=inputs=2:duration=longest")
            
            # 返回滤镜字符串
            return ",".join(filters) if filters else ""
            
        except Exception as e:
            print(f"构建音频滤镜失败: {e.__class__.__name__}: {str(e)}")
            raise
