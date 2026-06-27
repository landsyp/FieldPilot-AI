from enum import Enum


class ServiceType(str, Enum):
    FERTILIZER = "fertilizer"
    WEED_CONTROL = "weed_control"


class JobStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
