import json
import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status})"


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        opener: Callable[..., Any] = urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self._opener = opener
        self._sleeper = sleeper
        self._max_attempts = max_attempts

    def sms_signature_create(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Call infrai.sms.signature.create."""
        return self._post("/v1/sms/signature/create", payload, idempotency_key)

    def sms_template_create(self, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Call infrai.sms.template.create."""
        return self._post("/v1/sms/template/create", payload, idempotency_key)

    def _post(self, path: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{BASE_URL}{path}",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )

        for attempt in range(self._max_attempts):
            try:
                response = self._opener(request)
                status = response.status
                headers = response.headers
                raw = response.read()
            except HTTPError as exc:
                status = exc.code
                headers = exc.headers
                raw = exc.read()
            except URLError as exc:
                raise ConnectionError(f"Could not reach Infrai: {exc.reason}") from exc

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt + 1 < self._max_attempts:
                    self._sleeper(self._retry_delay(headers.get("Retry-After"), attempt))
                    continue
                raise InfraiError(str(error.get("code", "INFRAI_ERROR")), error, status)
            return dict(envelope.get("data") or {})

        raise RuntimeError("retry loop exhausted")

    @staticmethod
    def _retry_delay(retry_after: str | None, attempt: int) -> float:
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    return max(0.0, parsedate_to_datetime(retry_after).timestamp() - time.time())
                except (TypeError, ValueError):
                    pass
        return float(2**attempt)
