# ComfyUI FFmpeg Tool

## Nodes

### VideoAudioMix

#### Description
视频音频混合节点
功能：替换视频中的音频或混合音频

#### Input Types
- **视频文件**: STRING
- **音频文件**: STRING
- **视频音量**: FLOAT (default: 0.5)
- **音频音量**: FLOAT (default: 0.5)
- **使用GPU**: BOOLEAN (default: True)
- **降噪级别**: ENUM (options: "关闭", "弱", "中", "强", default: "关闭")
- **比特率**: ENUM (options: "语音(64k)", "播客(96k)", "音乐(128k)", "电影(192k)", "游戏(256k)", "高质音乐(320k)", "无损(flac)", default: "音乐(128k)")

#### 备注
----视频混合音频的降噪功能不可用，其他功能正常
----视频混合音频的降噪功能不可用
