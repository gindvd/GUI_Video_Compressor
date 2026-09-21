def containers_for(codec: str) -> list[str]:
    if codec in ("libsvtav1", "libvpx-vp9"):
        return ["mkv", "webm", "mp4"]
    return ["mp4", "mkv", "mov"]


def audio_codecs_for(container: str) -> list[str]:
    return {
        "mkv": ["aac", "mp3", "libopus", "libvorbis"],
        "mp4": ["aac", "mp3", "libopus"],
        "webm": ["libopus", "libvorbis"],
        "mov": ["aac", "mp3"],
    }[container]


def codecs_for(hardware: str) -> list[str]:
    return {
        "NVIDIA": ["h264_nvenc", "hevc_nvenc"],
        "AMD": ["h264_amf", "hevc_amf"],
        "Intel": ["h264_qsv", "hevc_qsv"],
        "Intel-Linux": ["h264_vaapi", "hevc_vaapi"],
    }[hardware]


def preset_supported(codec: str) -> bool:
    return codec not in (
        "h264_amf",
        "hevc_amf",
        "h264_vaapi",
        "hevc_vaapi",
        "libsvtav1",
    )
