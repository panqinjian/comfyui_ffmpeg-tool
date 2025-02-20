from .base.ffmpeg_base import FFmpegBase

class VideoAudioMix(FFmpegBase):
    """
    视频音频混合节点
    功能：替换视频中的音频或混合音频
    """

    def __init__(self):
        super().__init__()
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                'conditioning_1': ('CONDITIONING',), 'conditioning_2': ('CONDITIONING',),
                "视频文件": ("STRING",input ),
                "音频文件": ("STRING", input),
                "视频音量": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 5.0, "step": 0.1}),
                "音频音量": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 5.0, "step": 0.1}),
                "使用GPU": ("BOOLEAN", {"default": True}),
                "降噪级别": (["关闭", "弱", "中", "强"], {"default": "关闭"}),
                "比特率": (["语音(64k)", "播客(96k)", "音乐(128k)", "电影(192k)", "游戏(256k)", "高质音乐(320k)", "无损(flac)"], {"default": "音乐(128k)"}),  
                "声道": (["单声道(1)", "立体声(2)", "5.1声道(6)", "7.1声道(8)"], {"default": "立体声(2)"}),  
                "覆盖原文件": ("BOOLEAN", {"default": False}),
            },
            "optional": {
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
            },
        }

    RETURN_TYPES = (
        "output_path",  # 输出处理后的文件路径
    )
    FUNCTION = "process_video_audio"
    CATEGORY = "FFmpeg/音频处理"

    def adjust_audio_length(self, video_file: str, audio_file: str) -> list:
        """比较输入视频长度和音频长度，如果音频长度小于视频长度，则循环音频"""
        video_duration = self.get_video_duration(video_file)
        audio_duration = self.get_audio_duration(audio_file)

        command = []
        if audio_duration < video_duration:
            command.append("-stream_loop -1")  # 循环音频

        return command

    def process_video_audio(self, 视频文件: str, 音频文件: str, 视频音量: float, 音频音量: float, 使用GPU: bool, 降噪级别: str, 比特率: str, 声道: str, 覆盖原文件: bool, **kwargs) -> tuple:
        """
        处理视频和音频混合，并应用降噪。
        """
        if 覆盖原文件:
            output_path = 视频文件
        else:
            output_path = self.create_output_path(视频文件, "VideoAudioMix")

        command = [
            self.ffmpeg_path,
            "-y",  # 覆盖已存在的文件
        ]

        if 使用GPU:
            gpu_params = self.get_gpu_params(True)
            command.extend(gpu_params['hw_accel'])

        command.extend(["-i", 视频文件])

        audio_loop_command = self.adjust_audio_length(视频文件, 音频文件)
        if audio_loop_command:
            command.extend(audio_loop_command)
        command.extend(["-i", 音频文件])

        command.extend([
            "-c:v", "copy",  # 复制视频流
        ])

        command.append("-filter_complex")

        command_str = f"[0:a]volume={视频音量}[a1];[1:a]volume={音频音量}[a2]"

        fade_in = kwargs.get('fade_in', 0)
        fade_out = kwargs.get('fade_out', 0)

        if fade_in > 0:
            command_str += f";[a1]afade=t=in:st=0:d={fade_in}"

        if fade_out > 0:
            duration = self.get_video_duration(视频文件) or 0
            if duration > 0:
                command_str += f";[a1]afade=t=out:st={duration-fade_out}:d={fade_out}"

        command_str += f";[a1][a2]amix=inputs=2:duration=first:dropout_transition=3"

        if 降噪级别 != "关闭":
            # 获取平均分贝
            average_db = self.get_average_db(音频文件)  # 获取音频文件的平均分贝
            if average_db is None:
                average_db = -20.0  # 设置默认值
            afftdn_command = self.get_afftdn_command(average_db, 降噪级别)
            command_str += f"[aout];[aout]{afftdn_command['command']};"
        else:
            command_str += ";"

        command.append(command_str)

        # 比特率和声道映射字典
        bitrate_mapping = {
            "语音(64k)": "64k",
            "播客(96k)": "96k",
            "音乐(128k)": "128k",
            "电影(192k)": "192k",
            "游戏(256k)": "256k",
            "高质音乐(320k)": "320k",
            "无损(flac)": "flac"
        }
        channel_mapping = {
            "单声道(1)": "1",
            "立体声(2)": "2",
            "5.1声道(6)": "6",
            "7.1声道(8)": "8"
        }

        # 添加比特率和声道设置
        if 比特率 == "无损(flac)":
            command.extend(["-c:a", "flac"])  # 使用无损编码器 FLAC
        else:
            command.extend(["-b:a", bitrate_mapping[比特率]])  # 添加比特率设置
        command.extend(["-ac", channel_mapping[声道]])  # 添加声道设置

        command.append(output_path)
        returncode, stdout, stderr = self.execute_ffmpeg(command)

        if returncode != 0:
            return (f"处理失败: {stderr}",)

        return (output_path,)

    def mmse_denoise_scipy(self, input_audio: str, output_audio: str) -> None:
        """
        使用最小均方误差（MMSE）算法进行降噪。
        """
        import numpy as np
        import scipy.io.wavfile as wav
        from scipy.fft import fft, ifft

        # 读取音频文件
        sample_rate, audio_data = wav.read(input_audio)

        # 进行傅里叶变换
        audio_fft = fft(audio_data)

        # 估计噪声（这里使用简单的均值作为噪声估计）
        noise_estimate = np.mean(np.abs(audio_fft))

        # 应用 MMSE 降噪处理
        mmse_output = audio_fft * (1 - noise_estimate / (np.abs(audio_fft) + 1e-10))

        # 进行逆傅里叶变换
        denoised_audio = ifft(mmse_output).real

        # 保存降噪后的音频
        wav.write(output_audio, sample_rate, denoised_audio.astype(np.int16))

    def spectral_subtraction_scipy(self, input_audio: str, output_audio: str) -> None:
        """
        使用谱减法进行降噪。
        """
        import numpy as np
        import scipy.io.wavfile as wav
        from scipy.fft import fft, ifft

        # 读取音频文件
        sample_rate, audio_data = wav.read(input_audio)

        # 进行傅里叶变换
        audio_fft = fft(audio_data)

        # 估计噪声（这里使用简单的均值作为噪声估计）
        noise_estimate = np.mean(np.abs(audio_fft))

        # 应用谱减法处理
        spectral_output = np.maximum(np.abs(audio_fft) - noise_estimate, 0) * np.exp(1j * np.angle(audio_fft))

        # 进行逆傅里叶变换
        denoised_audio = ifft(spectral_output).real

        # 保存降噪后的音频
        wav.write(output_audio, sample_rate, denoised_audio.astype(np.int16))

    def mmse_denoise_ffmpeg(self, input_audio: str, output_audio: str) -> None:
        """
        使用最小均方误差（MMSE）算法进行降噪，支持任意媒体格式。
        """
        import ffmpeg
        import numpy as np
        from scipy.fft import fft, ifft

        # 使用 FFmpeg 读取音频文件
        out, _ = (
            ffmpeg.input(input_audio)
            .output('pipe:', format='wav')
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # 将音频数据转换为 NumPy 数组
        audio_data = np.frombuffer(out, np.int16)
        
        # 进行傅里叶变换
        audio_fft = fft(audio_data)

        # 估计噪声
        noise_estimate = np.mean(np.abs(audio_fft))
        
        # 应用 MMSE 降噪处理
        mmse_output = audio_fft * (1 - noise_estimate / (np.abs(audio_fft) + 1e-10))
        
        # 进行逆傅里叶变换
        denoised_audio = ifft(mmse_output).real.astype(np.int16)
        
        # 使用 FFmpeg 保存降噪后的音频
        ffmpeg.input('pipe:', format='wav').output(output_audio).run(input=denoised_audio.tobytes())

    def spectral_subtraction_ffmpeg(self, input_audio: str, output_audio: str) -> None:
        """
        使用谱减法进行降噪，支持任意媒体格式。
        """
        import ffmpeg
        import numpy as np
        from scipy.fft import fft, ifft

        # 使用 FFmpeg 读取音频文件
        out, _ = (
            ffmpeg.input(input_audio)
            .output('pipe:', format='wav')
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # 将音频数据转换为 NumPy 数组
        audio_data = np.frombuffer(out, np.int16)
        
        # 进行傅里叶变换
        audio_fft = fft(audio_data)

        # 估计噪声
        noise_estimate = np.mean(np.abs(audio_fft))
        
        # 应用谱减法处理
        spectral_output = np.maximum(np.abs(audio_fft) - noise_estimate, 0) * np.exp(1j * np.angle(audio_fft))
        
        # 进行逆傅里叶变换
        denoised_audio = ifft(spectral_output).real.astype(np.int16)
        
        # 使用 FFmpeg 保存降噪后的音频
        ffmpeg.input('pipe:', format='wav').output(output_audio).run(input=denoised_audio.tobytes())

    def get_afftdn_command(self, average_db: float, level: str) -> dict:
        """
        根据输入的平均分贝和等级参数返回 afftdn 的 command 参数。
        等级分为强、中、弱。
        """
        # 设置降噪强度
        if level == '强':
            noise_reduction_strength = 0.9
            gain = 1.5  # 较高的增益
        elif level == '中':
            noise_reduction_strength = 0.5
            gain = 1.0  # 中等增益
        elif level == '弱':
            noise_reduction_strength = 0.2
            gain = 0.5  # 较低的增益
        else:
            raise ValueError("等级参数无效，必须为 '强', '中', 或 '弱'。")

        # 根据平均分贝调整降噪参数
        if average_db < -30:
            noise_estimation = 100
        elif average_db < -20:
            noise_estimation = 200
        else:
            noise_estimation = 300

        # 返回 afftdn 的 command 参数和相关参数的字典
        command = f'afftdn=n={noise_estimation}:p={noise_reduction_strength}:g={gain}'
        return {
            'command': command,
            'noise_reduction_strength': noise_reduction_strength,
            'gain': gain,
            'noise_estimation': noise_estimation
        }

    def get_average_db(self, audio_file: str) -> float:
        """
        获取音频文件的平均分贝（dB）水平。
        """
        import subprocess

        # 使用 FFmpeg 提取音频流并计算分贝
        command = [
            "ffmpeg", 
            "-i", audio_file,
            "-af", "volumedetect",
            "-f", "null", 
            "/dev/null"
        ]
        
        # 运行命令并捕获输出
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        
        # 从输出中提取平均分贝
        output = result.stderr
        for line in output.splitlines():
            if "mean_volume" in line:
                # 提取平均分贝值
                mean_db = float(line.split(":")[1].strip().replace("dB", ""))
                return mean_db
        
        return None  # 如果未找到，返回 None
