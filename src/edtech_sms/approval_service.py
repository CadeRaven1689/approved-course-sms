import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from .models import AssetState, CourseSmsRelease, SmsTemplate


class ApprovalError(ValueError):
    pass


class SmsAssetClient(Protocol):
    def sms_signature_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]: ...

    def sms_template_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]: ...


@dataclass(frozen=True)
class PublishedRelease:
    signature: dict[str, object]
    templates: tuple[dict[str, object], ...]


class SmsApprovalService:
    def __init__(self, client: SmsAssetClient) -> None:
        self.client = client

    def publish(self, release: CourseSmsRelease) -> PublishedRelease:
        if release.signature.state is not AssetState.APPROVED:
            raise ApprovalError("signature must be approved")

        templates = release.approved_templates()
        if not templates:
            raise ApprovalError("release has no approved templates")

        namespace = self._slug(release.release_id)
        signature = self.client.sms_signature_create(
            {
                "name": f"{namespace}-{self._slug(release.signature.name)}",
                "type": release.signature.kind,
                "remark": release.signature.remark,
            },
            self._key(release.release_id, "signature", release.signature.name),
        )
        published = tuple(self._publish_template(release.release_id, namespace, item) for item in templates)
        return PublishedRelease(signature=signature, templates=published)

    def _publish_template(self, release_id: str, namespace: str, template: SmsTemplate) -> dict[str, object]:
        return self.client.sms_template_create(
            {
                "name": f"{namespace}-{self._slug(template.name)}",
                "body": template.body,
                "locale": template.locale,
                "message_type": template.message_type,
                "international": template.international,
            },
            self._key(release_id, "template", template.name),
        )

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        if not slug:
            raise ApprovalError("release and asset names must contain letters or numbers")
        return slug

    @staticmethod
    def _key(release_id: str, kind: str, name: str) -> str:
        raw = f"edtech-sms:{release_id}:{kind}:{name}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
