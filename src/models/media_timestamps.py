from dataclasses import dataclass


@dataclass
class MediaTimestamps:
    start_time: str = "00:00:00.000"
    end_time: str = "00:00:00.000"
    full_duration: str = "00:00:00.000"
    trimmed_duration: str = "00:00:00.000"
