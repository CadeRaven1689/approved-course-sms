from dataclasses import dataclass
from enum import Enum


class AssetState(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


@dataclass(frozen=True)
class SmsSignature:
    name: str
    state: AssetState
    kind: str = "organization"
    remark: str = "Course operations messages"


@dataclass(frozen=True)
class SmsTemplate:
    name: str
    body: str
    state: AssetState
    locale: str = "en-US"
    message_type: str = "notification"
    international: bool = True


@dataclass(frozen=True)
class CourseSmsRelease:
    release_id: str
    signature: SmsSignature
    templates: tuple[SmsTemplate, ...]

    def approved_templates(self) -> tuple[SmsTemplate, ...]:
        return tuple(item for item in self.templates if item.state is AssetState.APPROVED)
