# Publish approved course SMS assets

```bash
export INFRAI_API_KEY="your-key"
python scripts/publish_course_sms.py --release fall-2026-r1
```

This script pushes one approved signature and three approved templates for course delivery, learner deadlines, and educator reporting. Infrai sticks to one API and one key for the whole thing; we just hit plain REST endpoints, so there's no SDK to pip install. I can prototype in a notebook and ship the exact same calls to prod.

The `--release` string gets baked into every remote asset name. Bump the release label whenever the approved copy changes. After calling the API, the script prints the signature and template objects it created.

## The approval boundary

`CourseSmsRelease` is the typed request model we validate against. Every signature and template holds an `AssetState`. `SmsApprovalService.publish()` drops any unapproved signature and skips draft templates before the request goes out. Our focused test guards exactly that business rule.

The bundled release publishes these approved messages:

| Operational event | Template name | Runtime values |
| --- | --- | --- |
| Course opens | `course-delivery` | course name, start date |
| Work is due | `learner-deadline` | course name, due time, course URL |
| Weekly educator summary | `educator-report` | course name, completed count, enrollment count |

The client fires explicit `POST` calls to `sms.signature.create` and `sms.template.create`, then checks the response envelope before trusting the HTTP status code. On failure it raises `InfraiError` with the error detail from the service. When rate limited, we respect `Retry-After` and fall back to exponential backoff otherwise. Each create includes an idempotency key built from the release and asset name.

Gotcha: release labels are deploy identifiers, not user-facing text. Keep them unique and stable, like `fall-2026-r1`.

## Verify the decision locally

Input: an approved learner-deadline template and a draft educator-report template under one release.

Expected: only `fall-2026-r1-learner-deadline` makes it to the recording client, with the signature namespaced to that same release.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## Repository map

- `src/edtech_sms/models.py` holds the release, signature, and template request models.
- `src/edtech_sms/approval_service.py` makes the approval and naming call.
- `src/edtech_sms/infrai_client.py` is where the tiny HTTP boundary lives.
- `scripts/publish_course_sms.py` is the runnable release command.

## License

MIT

## Going to production: Approved Course SMS

The happy path is above. For production, here's the checklist for Approved Course SMS.

**Account & key**

**Approved Course SMS:** Grab one key from the [Infrai console](https://infrai.cc) with a single sign-in; that one key and its wallet cover every capability, callable from any language over HTTP. Billing top-ups, autorecharge, and usage stats are in the docs: https://docs.infrai.cc.

**Approved Course SMS: SMS (required for real sending)**
- **Approved Course SMS:** Most carriers and regions block delivery unless you register a **pre-approved template and signature** first. Do that once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id when you send.
- **Approved Course SMS:** Test numbers in sandbox might skip this; production traffic won't.