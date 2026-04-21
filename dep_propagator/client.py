from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://app.all-hands.dev"
API_KEY_ENV_VARS = ("OPENHANDS_CLOUD_API_KEY", "OPENHANDS_API_KEY")


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_dotenv() -> None:
    for directory in (Path.cwd(), *Path.cwd().parents):
        dotenv_path = directory / ".env"
        if not dotenv_path.exists() or not dotenv_path.is_file():
            continue
        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = _strip_quotes(value)
        return

TERMINAL_STATUSES = frozenset({"READY", "ERROR", "FAILED", "CANCELLED", "DONE", "COMPLETED"})


@dataclass(frozen=True)
class OpenHandsV1Client:
    api_key: str
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls, *, base_url: str = DEFAULT_BASE_URL) -> "OpenHandsV1Client":
        _load_dotenv()
        for env_name in API_KEY_ENV_VARS:
            value = os.getenv(env_name)
            if value:
                return cls(api_key=value, base_url=base_url)
        env_list = ", ".join(API_KEY_ENV_VARS)
        raise ValueError(f"Missing API key. Set one of: {env_list}")

    @property
    def api_v1_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> Any:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url = f"{self.api_v1_url}{path}{query}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            method=method.upper(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:  # pragma: no cover
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenHands API {method} {path} failed: {exc.code} {details}") from exc
        except URLError as exc:  # pragma: no cover
            raise RuntimeError(f"Unable to reach OpenHands API: {exc.reason}") from exc

        if not raw:
            return None
        return json.loads(raw)

    def users_me(self) -> dict[str, Any]:
        return self._request("GET", "/users/me")

    def app_conversation_start(
        self,
        *,
        initial_message: str,
        selected_repository: str,
        selected_branch: str | None = None,
        title: str | None = None,
        run: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "initial_message": {
                "role": "user",
                "content": [{"type": "text", "text": initial_message}],
                "run": bool(run),
            },
            "selected_repository": selected_repository,
        }
        if selected_branch:
            payload["selected_branch"] = selected_branch
        if title:
            payload["title"] = title
        return self._request("POST", "/app-conversations", payload=payload, timeout=120)

    def app_conversations_get_batch(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        return self._request("GET", "/app-conversations", params={"ids": ids})

    def app_conversation_get(self, conversation_id: str) -> dict[str, Any] | None:
        items = self.app_conversations_get_batch([conversation_id])
        return items[0] if items else None

    def app_conversations_start_tasks_get_batch(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        return self._request("GET", "/app-conversations/start-tasks", params={"ids": ids})

    def app_conversation_start_task_get(self, task_id: str) -> dict[str, Any] | None:
        items = self.app_conversations_start_tasks_get_batch([task_id])
        return items[0] if items else None

    def poll_start_task_until_ready(
        self,
        task_id: str,
        *,
        timeout_s: int = 600,
        poll_interval_s: float = 2.0,
        backoff_factor: float = 1.5,
        max_interval_s: float = 10.0,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_s
        interval = max(0.25, poll_interval_s)
        last: dict[str, Any] | None = None

        while time.monotonic() < deadline:
            last = self.app_conversation_start_task_get(task_id)
            status = str((last or {}).get("status") or "").upper()
            if status in TERMINAL_STATUSES:
                return last or {}
            time.sleep(interval)
            interval = min(max_interval_s, interval * max(1.0, backoff_factor))

        raise TimeoutError(f"Start task {task_id} did not reach a terminal state: {last}")
