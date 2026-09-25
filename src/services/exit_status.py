from enum import Enum, auto


class ExitStatus(Enum):
    SUCCESS = auto()
    ERROR = auto()
    TERMINATED = auto()
    BUSY = auto()
