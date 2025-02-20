from .nodes.video_audio import VideoAudioMix
from .nodes.video_compress import VideoCompress
from .nodes.video_concat import VideoConcat
from .nodes.video_convert import VideoConvert
from .nodes.video_crop import VideoCrop
from .nodes.video_denoise import VideoDenoise
from .nodes.video_effects import VideoEffects
from .nodes.video_enhance import VideoEnhance
from .nodes.video_filter import VideoFilter
from .nodes.video_format import VideoFormat
from .nodes.video_info import VideoInfo
from .nodes.video_merge import VideoMerge
from .nodes.video_metadata import VideoMetadata
from .nodes.video_pip import VideoPiP
from .nodes.video_resolution import VideoResolution
from .nodes.video_resize import VideoResize
from .nodes.video_reverse import VideoReverse
from .nodes.video_rotate import VideoRotate
from .nodes.video_speed import VideoSpeed
from .nodes.video_splitting import VideoSplitting
from .nodes.video_stabilize import VideoStabilize
from .nodes.video_streaming import VideoStreaming
from .nodes.video_subtitle import VideoSubtitle
from .nodes.video_thumbnail import VideoThumbnail
from .nodes.video_transition import VideoTransition
from .nodes.video_trim import VideoTrim
from .nodes.video_watermark import VideoWatermark

NODE_CLASS_MAPPINGS = {
    "VideoAudioMix": VideoAudioMix,
    "VideoCompress": VideoCompress,
    "VideoConcat": VideoConcat,
    "VideoConvert": VideoConvert,
    "VideoCrop": VideoCrop,
    "VideoDenoise": VideoDenoise,
    "VideoEffects": VideoEffects,
    "VideoEnhance": VideoEnhance,
    "VideoFilter": VideoFilter,
    "VideoFormat": VideoFormat,
    "VideoInfo": VideoInfo,
    "VideoMerge": VideoMerge,
    "VideoMetadata": VideoMetadata,
    "VideoPiP": VideoPiP,
    "VideoResolution": VideoResolution,
    "VideoResize": VideoResize,
    "VideoReverse": VideoReverse,
    "VideoRotate": VideoRotate,
    "VideoSpeed": VideoSpeed,
    "VideoSplitting": VideoSplitting,
    "VideoStabilize": VideoStabilize,
    "VideoStreaming": VideoStreaming,
    "VideoSubtitle": VideoSubtitle,
    "VideoThumbnail": VideoThumbnail,
    "VideoTransition": VideoTransition,
    "VideoTrim": VideoTrim,
    "VideoWatermark": VideoWatermark
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoAudioMix": "视频音频混音",
    "VideoCompress": "视频压缩",
    "VideoConcat": "视频拼接",
    "VideoConvert": "视频转换",
    "VideoCrop": "视频裁剪",
    "VideoDenoise": "视频降噪",
    "VideoEffects": "视频特效",
    "VideoEnhance": "视频增强",
    "VideoFilter": "视频过滤",
    "VideoFormat": "视频格式",
    "VideoInfo": "视频信息",
    "VideoMerge": "视频合并",
    "VideoMetadata": "视频元数据",
    "VideoPiP": "视频画中画",
    "VideoResolution": "视频分辨率",
    "VideoResize": "视频调整大小",
    "VideoReverse": "视频反转",
    "VideoRotate": "视频旋转",
    "VideoSpeed": "视频速度",
    "VideoSplitting": "视频分割",
    "VideoStabilize": "视频稳定",
    "VideoStreaming": "视频流处理",
    "VideoSubtitle": "视频字幕",
    "VideoThumbnail": "视频缩略图生成",
    "VideoTransition": "视频转场",
    "VideoTrim": "视频剪辑",
    "VideoWatermark": "视频水印"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'VideoAudioMix', 'VideoCompress', 'VideoConcat', 'VideoConvert', 'VideoCrop', 'VideoDenoise', 'VideoEffects', 'VideoEnhance', 'VideoFilter', 'VideoFormat', 'VideoInfo', 'VideoMerge', 'VideoMetadata', 'VideoMixing', 'VideoPiP', 'VideoResolution', 'VideoResize', 'VideoReverse', 'VideoRotate', 'VideoSpeed', 'VideoSplitting', 'VideoStabilize', 'VideoStreaming', 'VideoSubtitle', 'VideoThumbnail', 'VideoTransition', 'VideoTrim', 'VideoWatermark']