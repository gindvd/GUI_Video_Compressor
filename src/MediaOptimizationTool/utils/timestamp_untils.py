def ms_to_timestamp(ms: int) -> str:
    """
    Converts ms into ISO formatted timpestamp string

    Return time formatted as HH:MM:SS.xxx
    """
    s = ms // 1000
    ms_remainder = ms % 1000

    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)

    return f"{h:02d}:{m:02d}:{sec:02d}.{ms_remainder:03d}"


def ms_to_player_timestamp(ms: int) -> str:
    """
    Converts ms into ISO formatted timpestamp string for media player displays

    Return time formatted as HH:MM:SS
    """
    s = ms // 1000

    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)

    return f"{h:02d}:{m:02d}:{sec:02d}"
