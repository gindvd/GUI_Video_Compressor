def hwaccel_args_for(codec: str) -> list[str] | None:
    if codec.endswith("qsv"):
        return ["-init_hw_device", "qsv=hw", "-filter_hw_device", "hw",]
    elif codec.endswith("vaapi"):
        return ["-vaapi_device", "/dev/dri/renderD128",]
    
    return None

def quality_args_for(codec: str, crf: str) -> list[str]:

    if codec.endswith("nvenc"):
        return  ["-rc", "vbr", "-cq", crf, "-b:v", "0",]
    elif codec.endswith("amf"):
        return  ["-rc", "qvbr", "-qvbr_quality_level", crf,]
    elif codec.endswith("qsv"):
        return  ["-global_quality", crf, "-look_ahead", "1",]
    elif codec.endswith("vaapi"):
        return  ["-qp", crf,]
    elif codec.endswith("vp9"):
        return  ["-crf", crf,"-b:v", "0",]
    
    return ["-crf", crf,]

def scale_args_for(codec: str, fps: str, width: str, height: str) -> list[str]:
    if codec.endswith("vaapi"):
        return  [
                "-vf", 
                f"format=nv12,fps={fps},hwupload,scale_vaapi=w={width}:h={height}"
            ]
    
    hdcodecs = (
        "h264_nvenc", "hevc_nvenc",
        "h264_amf", "hevc_amf",
        "h264_qsv", "hevc_qsv"
    )
    
    return ["-vf", f"scale={width}:{height},fps={fps}",]

def get_audio_args(
    include_audio: bool, 
    audio_codec: str | None, 
    audio_bitrate: str | None
) -> list[str]:

    if not include_audio:
        return ["-an"]
    
    if audio_codec is None or audio_bitrate is None:
        return ["-an"]
    
    return ["-c:a", audio_codec, "-b:a", audio_bitrate,]

def quality_converter(quality: int) -> str:
    """Converts quality percentage into inverted CRF number"""
    quality_inverted = abs(quality / 100 - 1)
    crf = int(quality_inverted * 33 + 18) # Range 18 to 51

    return str(crf)
