"""
预设配置文件
包含各种视频处理节点的预设参数
"""

# 视频压缩预设
COMPRESS_PRESETS = {
    "high_quality": {
        "crf": 18,
        "preset": "slow",
        "tune": "film",
        "audio_bitrate": "192k"
    },
    "balanced": {
        "crf": 23,
        "preset": "medium",
        "tune": "film",
        "audio_bitrate": "128k"
    },
    "small_size": {
        "crf": 28,
        "preset": "faster",
        "tune": "film",
        "audio_bitrate": "96k"
    },
    "web": {
        "crf": 25,
        "preset": "fast",
        "tune": "fastdecode",
        "audio_bitrate": "128k"
    }
}

# 视频尺寸调整预设
RESIZE_PRESETS = {
    "4K": {
        "width": 3840,
        "height": 2160,
        "keep_aspect": True,
        "method": "lanczos"
    },
    "1080p": {
        "width": 1920,
        "height": 1080,
        "keep_aspect": True,
        "method": "bicubic"
    },
    "720p": {
        "width": 1280,
        "height": 720,
        "keep_aspect": True,
        "method": "bicubic"
    },
    "480p": {
        "width": 854,
        "height": 480,
        "keep_aspect": True,
        "method": "bilinear"
    }
}

# 视频速度调整预设
SPEED_PRESETS = {
    "slow_motion": {
        "speed": 0.5,
        "maintain_audio_pitch": True
    },
    "fast_forward": {
        "speed": 2.0,
        "maintain_audio_pitch": False
    },
    "time_lapse": {
        "speed": 10.0,
        "maintain_audio_pitch": False
    },
    "slight_slow": {
        "speed": 0.8,
        "maintain_audio_pitch": True
    }
}

# 视频旋转预设
ROTATE_PRESETS = {
    "clockwise_90": {
        "angle": 90,
        "keep_aspect": True
    },
    "counterclockwise_90": {
        "angle": -90,
        "keep_aspect": True
    },
    "flip_horizontal": {
        "flip": "horizontal"
    },
    "flip_vertical": {
        "flip": "vertical"
    }
}

# 视频裁剪预设
CROP_PRESETS = {
    "center_square": {
        "mode": "center",
        "aspect_ratio": "1:1"
    },
    "cinema_scope": {
        "mode": "center",
        "aspect_ratio": "2.35:1"
    },
    "portrait": {
        "mode": "center",
        "aspect_ratio": "9:16"
    },
    "landscape": {
        "mode": "center",
        "aspect_ratio": "16:9"
    }
}

# 水印预设
WATERMARK_PRESETS = {
    "corner_logo": {
        "position": "bottom_right",
        "opacity": 0.8,
        "margin": 20
    },
    "center_text": {
        "position": "center",
        "opacity": 0.5,
        "font_size": 48
    },
    "signature": {
        "position": "bottom_left",
        "opacity": 0.7,
        "margin": 10
    }
}

# 字幕预设
SUBTITLE_PRESETS = {
    "default": {
        "font_size": 24,
        "font_color": "white",
        "background_color": "black@0.4",
        "position": "bottom"
    },
    "movie": {
        "font_size": 28,
        "font_color": "white",
        "background_color": "none",
        "position": "bottom",
        "style": "movie"
    },
    "karaoke": {
        "font_size": 32,
        "font_color": "yellow",
        "background_color": "black@0.6",
        "position": "bottom",
        "style": "karaoke"
    }
}

# 视频稳定预设
STABILIZE_PRESETS = {
    "light": {
        "smoothing": 5,
        "accuracy": 10,
        "max_shift": 50,
        "max_angle": 1
    },
    "strong": {
        "smoothing": 15,
        "accuracy": 15,
        "max_shift": 100,
        "max_angle": 2
    },
    "cinematic": {
        "smoothing": 25,
        "accuracy": 20,
        "max_shift": 150,
        "max_angle": 3
    }
}

# 降噪预设
DENOISE_PRESETS = {
    "light": {
        "strength": 3,
        "type": "nlmeans",
        "temporal_size": 3
    },
    "medium": {
        "strength": 6,
        "type": "nlmeans",
        "temporal_size": 4
    },
    "strong": {
        "strength": 9,
        "type": "nlmeans",
        "temporal_size": 5
    }
}

# 分辨率预设
RESOLUTION_PRESETS = {
    "4K": {
        "width": 3840,
        "height": 2160,
        "scaling": "lanczos"
    },
    "2K": {
        "width": 2560,
        "height": 1440,
        "scaling": "lanczos"
    },
    "1080p": {
        "width": 1920,
        "height": 1080,
        "scaling": "bicubic"
    }
}

# 画中画预设
PIP_PRESETS = {
    "corner": {
        "position": "bottom_right",
        "size": 0.25,
        "margin": 20,
        "border": 2
    },
    "side": {
        "position": "right",
        "size": 0.5,
        "margin": 0,
        "border": 0
    },
    "floating": {
        "position": "custom",
        "size": 0.3,
        "margin": 30,
        "border": 3
    }
}

# 视频特效预设
EFFECTS_PRESETS = {
    "cinematic": {
        "contrast": 1.2,
        "saturation": 1.1,
        "brightness": -0.1,
        "vignette": 0.3
    },
    "vintage": {
        "sepia": 0.5,
        "contrast": 1.1,
        "grain": 0.2,
        "vignette": 0.4
    },
    "dramatic": {
        "contrast": 1.4,
        "saturation": 0.8,
        "brightness": -0.2,
        "vignette": 0.6
    }
}

# 音频处理预设
AUDIO_PRESETS = {
    "voice": {
        "volume": 1.2,
        "bass": -2,
        "treble": 4,
        "normalize": True
    },
    "music": {
        "volume": 0.8,
        "bass": 3,
        "treble": 2,
        "normalize": True
    },
    "podcast": {
        "volume": 1.0,
        "bass": 1,
        "treble": 3,
        "normalize": True
    }
}

# 元数据预设
METADATA_PRESETS = {
    "movie": {
        "title": True,
        "director": True,
        "year": True,
        "genre": True
    },
    "youtube": {
        "title": True,
        "description": True,
        "tags": True,
        "category": True
    },
    "minimal": {
        "title": True,
        "year": True
    }
}

# 缩略图预设
THUMBNAIL_PRESETS = {
    "preview": {
        "mode": "grid",
        "count": 9,
        "columns": 3,
        "interval": 10
    },
    "poster": {
        "mode": "single",
        "time": "10%",
        "width": 1280,
        "height": 720
    },
    "gif": {
        "mode": "gif",
        "duration": 3,
        "fps": 10,
        "width": 320
    }
}

# 合并预设
MERGE_PRESETS = {
    "simple": {
        "mode": "concat",
        "transition": None
    },
    "fade": {
        "mode": "concat",
        "transition": "fade",
        "duration": 1.0
    },
    "grid": {
        "mode": "grid",
        "columns": 2,
        "padding": 10
    }
}

# 剪辑预设
TRIM_PRESETS = {
    "accurate": {
        "mode": "precise",
        "reencoding": True
    },
    "fast": {
        "mode": "keyframe",
        "reencoding": False
    },
    "segment": {
        "mode": "segment",
        "duration": 60,
        "overlap": 0
    }
}