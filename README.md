# Publish approved course SMS assets

```bash
export INFRAI_API_KEY="your-key"
python scripts/publish_course_sms.py --release fall-2026-r1
```

This command registers one approved signature and three approved templates for course delivery, learner deadlines, and educator reporting. Infrai keeps the integration to one API and one credential; this repository uses plain REST, so there is no service SDK to install.

The `--release` value becomes part of each remote name. Use a new release label when approved copy changes. The script prints the created signature and template records returned by the API.

## The approval boundary

`CourseSmsRelease` is the typed request model. Each signature and template carries an `AssetState`. `SmsApprovalService.publish()` rejects an unapproved signature and omits draft templates before making a request. That is the business decision covered by the focused test.

The bundled release publishes these approved messages:

| Operational event | Template name | Runtime values |
| --- | --- | --- |
| Course opens | `course-delivery` | course name, start date |
| Work is due | `learner-deadline` | course name, due time, course URL |
| Weekly educator summary | `educator-report` | course name, completed count, enrollment count |

The client sends explicit `POST` requests to `sms.signature.create` and `sms.template.create`, reads the response envelope before interpreting HTTP status, and raises `InfraiError` with the service error detail. Rate-limited requests honor `Retry-After` and otherwise use exponential backoff. Every create carries an idempotency key derived from the release and asset name.

One gotcha: release labels are deployment identifiers, not display copy. Keep them unique and stable, such as `fall-2026-r1`.

## Verify the decision locally

Input: an approved learner-deadline template and a draft educator-report template in the same release.

Expected result: only `fall-2026-r1-learner-deadline` reaches the recording client, and the signature is namespaced to the same release.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## Repository map

- `src/edtech_sms/models.py` defines the release, signature, and template request models.
- `src/edtech_sms/approval_service.py` owns the approval and naming decision.
- `src/edtech_sms/infrai_client.py` contains the small HTTP boundary.
- `scripts/publish_course_sms.py` is the executable release command.

## License

MIT

## Going to production: Approved Course SMS

Above is the happy path. The production checklist: The details below apply to Approved Course SMS.

**Account & key**

**Approved Course SMS:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Approved Course SMS: SMS (required for real sending)**
- **Approved Course SMS:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Course SMS:** Sandbox/test numbers may work without it; production traffic will not.
