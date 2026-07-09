def ms_text_converter(ms: int) -> str:
    """Converts ms into ISO formatted timpestamp string"""
    s = ms // 1000
    ms_remainder = ms % 1000
    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}.{ms_remainder:03d}"


def seconds_to_timestamp(s: float) -> str:
    """Converts seconds to ISO formatted timestamp string"""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    secs = s % 60

    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
