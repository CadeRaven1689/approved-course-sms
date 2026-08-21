from edtech_sms import AssetState, CourseSmsRelease, SmsApprovalService, SmsSignature, SmsTemplate


class RecordingClient:
    def __init__(self) -> None:
        self.signatures: list[tuple[dict[str, object], str]] = []
        self.templates: list[tuple[dict[str, object], str]] = []

    def sms_signature_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        self.signatures.append((payload, idempotency_key))
        return {"signature_id": "sig_123"}

    def sms_template_create(self, payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
        self.templates.append((payload, idempotency_key))
        return {"template_id": f"tpl_{len(self.templates)}"}


def test_publish_excludes_draft_copy_and_namespaces_approved_assets() -> None:
    client = RecordingClient()
    release = CourseSmsRelease(
        release_id="Fall 2026 R1",
        signature=SmsSignature("Northstar Academy", AssetState.APPROVED),
        templates=(
            SmsTemplate("learner-deadline", "Due {due_at}", AssetState.APPROVED),
            SmsTemplate("educator-report", "Draft report", AssetState.DRAFT),
        ),
    )

    result = SmsApprovalService(client).publish(release)

    assert result.signature == {"signature_id": "sig_123"}
    assert [call[0]["name"] for call in client.templates] == ["fall-2026-r1-learner-deadline"]
    assert client.signatures[0][0]["name"] == "fall-2026-r1-northstar-academy"
    assert len(client.templates[0][1]) == 64
