from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    @classmethod
    def choices(cls):
        return [(enum.name, enum.value) for enum in cls]
