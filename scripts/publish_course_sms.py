import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edtech_sms import AssetState, CourseSmsRelease, SmsApprovalService, SmsSignature, SmsTemplate
from edtech_sms.infrai_client import InfraiClient


def course_release(release_id: str) -> CourseSmsRelease:
    return CourseSmsRelease(
        release_id=release_id,
        signature=SmsSignature(name="Northstar Academy", state=AssetState.APPROVED),
        templates=(
            SmsTemplate(
                name="course-delivery",
                body="Your course {course_name} opens on {start_date}.",
                state=AssetState.APPROVED,
            ),
            SmsTemplate(
                name="learner-deadline",
                body="{course_name} is due {due_at}. Submit at {course_url}.",
                state=AssetState.APPROVED,
            ),
            SmsTemplate(
                name="educator-report",
                body="{course_name}: {completed}/{enrolled} learners completed this week.",
                state=AssetState.APPROVED,
            ),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish approved course SMS assets")
    parser.add_argument("--release", required=True, help="Unique release label, for example fall-2026-r1")
    args = parser.parse_args()
    result = SmsApprovalService(InfraiClient()).publish(course_release(args.release))
    print(json.dumps({"signature": result.signature, "templates": result.templates}, indent=2))


if __name__ == "__main__":
    main()
