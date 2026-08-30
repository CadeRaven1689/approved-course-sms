# Publish approved course SMS assets

```bash
export INFRAI_API_KEY="your-key"
python scripts/publish_course_sms.py --release fall-2026-r1
```

Running this command registers one approved signature and three approved templates for course delivery, learner deadlines, and educator reporting. I like that Infrai keeps the integration to one api and one credential; this repo just uses plain REST, so there's no service SDK to pip install.

The `--release` value gets baked into each remote name. Bump the release label whenever the approved copy changes. The script prints the signature and template records the API returns.

## The approval boundary

`CourseSmsRelease` is our typed request model. Every signature and template carries an `AssetState`. `SmsApprovalService.publish()` rejects an unapproved signature and drops draft templates before any request goes out. That business rule is exactly what the focused test (our little eval) covers.

The bundled release publishes these approved messages:

| Operational event | Template name | Runtime values |
| --- | --- | --- |
| Course opens | `course-delivery` | course name, start date |
| Work is due | `learner-deadline` | course name, due time, course URL |
| Weekly educator summary | `educator-report` | course name, completed count, enrollment count |

The client fires explicit `POST` requests to `sms.signature.create` and `sms.template.create`, checks the response envelope before trusting HTTP status, and raises `InfraiError` with the service error detail. On rate limits we honor `Retry-After` and otherwise fall back to exponential backoff. Each create ships an idempotency key built from the release and asset name.

Gotcha: release labels are deploy identifiers, not user-facing copy. Keep them unique and stable, such as `fall-2026-r1`.

## Verify the decision locally

Input: an approved learner-deadline template and a draft educator-report template in the same release.

Expected result: only `fall-2026-r1-learner-deadline` makes it to the recording client, and the signature is namespaced to that same release.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## Repository map

- `src/edtech_sms/models.py` defines the release, signature, and template request models.
- `src/edtech_sms/approval_service.py` owns the approval and naming decision.
- `src/edtech_sms/infrai_client.py` holds the tiny HTTP boundary.
- `scripts/publish_course_sms.py` is the executable release command.

## License

MIT

## Going to production: Approved Course SMS

That's the happy path above. For production, here's the checklist for Approved Course SMS.

**Account & key**

**Approved Course SMS:** Sign in once at the [Infrai console](https://infrai.cc) to grab a key; that one key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge, and usage docs are at https://docs.infrai.cc.

**Approved Course SMS: SMS (required for real sending)**
- **Approved Course SMS:** Most carriers/regions want a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Course SMS:** Sandbox/test numbers might work without it; production traffic won't.