#!/usr/bin/env python3
"""
GitHub Actions またはローカルからカレンダー予定を取得し、会議リンクを整備して通知する。
Google Calendar / Zoom / ProLine / Discord の資格情報は環境変数で受け取り、
ローカル実行では repo root の .env / .env.local も自動で読み込む。
"""

from __future__ import annotations

import argparse
import ast
import base64
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


HTTP_TIMEOUT_SEC = 30
DEFAULT_TIMEZONE = "Asia/Tokyo"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
HOME_TEAM_INFO_ROOT = pathlib.Path.home() / "team-info"
DEFAULT_ENV_FILES = (
    REPO_ROOT / ".env",
    REPO_ROOT / ".env.local",
    HOME_TEAM_INFO_ROOT / ".env",
    HOME_TEAM_INFO_ROOT / ".env.local",
)
DEFAULT_GWS_CREDENTIALS_FILE = pathlib.Path.home() / ".config" / "team-info" / "gws_credentials_auto.json"
DEFAULT_GWSMCP_OAUTH_CLIENT_FILE = pathlib.Path.home() / ".config" / "google-workspace-mcp" / "oauth-client.json"
DEFAULT_GWSMCP_TOKENS_FILE = pathlib.Path.home() / ".config" / "google-workspace-mcp" / "tokens.json"
CALENDAR_BACKEND = "direct"
PRIMARY_SOURCE_LABEL = "株式会社Keystone出口"
LINE_STATUS_KEY = "team-info.line-status"
LINE_UID_KEY = "team-info.line-uid"
LINE_SENT_URL_KEY = "team-info.line-sent-url"
MEETING_URL_KEY = "team-info.zoom-url"
MEETING_ID_KEY = "team-info.zoom-meeting-id"
MEETING_MESSAGE_HEADER = "[team-info] 会議情報"
URL_PATTERNS = (
    r"https://[\w.-]*zoom\.us/j/[\w?=&%#.-]+",
    r"https://meet\.google\.com/[\w-]+",
)
LOADED_ENV_FILES: list[pathlib.Path] = []
LOADED_SETTINGS_FILE: pathlib.Path | None = None
GOOGLE_CREDENTIALS_CACHE: dict[str, str] | None = None


class SummaryError(RuntimeError):
    pass


def parse_env_file_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    if value[0] in ("'", '"') and value[-1:] == value[0]:
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, str):
                return parsed
        except (SyntaxError, ValueError):
            return value[1:-1]
    return value


def load_env_file(path: pathlib.Path, *, override: bool = False) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export "):].lstrip()
        if "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        if not override and key in os.environ:
            continue
        os.environ[key] = parse_env_file_value(raw_value)
    LOADED_ENV_FILES.append(path)


def load_env_files(explicit_path: str = "") -> None:
    paths: list[pathlib.Path]
    if explicit_path:
        paths = [pathlib.Path(explicit_path).expanduser()]
    elif os.environ.get("DAILY_SUMMARY_ENV_FILE"):
        paths = [pathlib.Path(os.environ["DAILY_SUMMARY_ENV_FILE"]).expanduser()]
    else:
        paths = list(DEFAULT_ENV_FILES)

    override = os.environ.get("DAILY_SUMMARY_ENV_OVERRIDE", "").lower() in {"1", "true", "yes"}
    seen: set[pathlib.Path] = set()
    for path in paths:
        resolved = path.resolve() if path.exists() else path
        if resolved in seen:
            continue
        seen.add(resolved)
        load_env_file(path, override=override)


def getenv_any(*names: str, default: str = "") -> str:
    for name in names:
        value = getenv(name)
        if value:
            return value
    return default


def load_google_credentials_payload() -> dict[str, str]:
    global GOOGLE_CREDENTIALS_CACHE
    if GOOGLE_CREDENTIALS_CACHE is not None:
        return GOOGLE_CREDENTIALS_CACHE

    def normalize_single_file_payload(path: pathlib.Path) -> dict[str, str]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {
            key: str(payload.get(key) or "").strip()
            for key in ("client_id", "client_secret", "refresh_token")
            if str(payload.get(key) or "").strip()
        }

    def normalize_gwsmcp_pair() -> dict[str, str]:
        if not DEFAULT_GWSMCP_OAUTH_CLIENT_FILE.exists() or not DEFAULT_GWSMCP_TOKENS_FILE.exists():
            return {}
        try:
            client_payload = json.loads(DEFAULT_GWSMCP_OAUTH_CLIENT_FILE.read_text(encoding="utf-8"))
            token_payload = json.loads(DEFAULT_GWSMCP_TOKENS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(client_payload, dict) or not isinstance(token_payload, dict):
            return {}
        payload = {
            "client_id": client_payload.get("client_id"),
            "client_secret": client_payload.get("client_secret"),
            "refresh_token": token_payload.get("refresh_token"),
        }
        return {
            key: str(payload.get(key) or "").strip()
            for key in ("client_id", "client_secret", "refresh_token")
            if str(payload.get(key) or "").strip()
        }

    path_value = getenv_any("GOOGLE_CREDENTIALS_FILE", "GWS_CREDENTIALS_FILE")
    if path_value:
        GOOGLE_CREDENTIALS_CACHE = normalize_single_file_payload(pathlib.Path(path_value).expanduser())
        return GOOGLE_CREDENTIALS_CACHE

    for payload in (normalize_gwsmcp_pair(), normalize_single_file_payload(DEFAULT_GWS_CREDENTIALS_FILE)):
        if all(payload.get(key) for key in ("client_id", "client_secret", "refresh_token")):
            GOOGLE_CREDENTIALS_CACHE = payload
            return GOOGLE_CREDENTIALS_CACHE

    GOOGLE_CREDENTIALS_CACHE = {
        key: str(payload.get(key) or "").strip()
        for key in ("client_id", "client_secret", "refresh_token")
        if str(payload.get(key) or "").strip()
    }
    return GOOGLE_CREDENTIALS_CACHE


def google_config_value(field: str) -> str:
    dedicated_env_names = {
        "client_id": ("GOOGLE_CLIENT_ID",),
        "client_secret": ("GOOGLE_CLIENT_SECRET",),
        "refresh_token": ("GOOGLE_REFRESH_TOKEN",),
    }[field]
    value = getenv_any(*dedicated_env_names)
    if value:
        return value
    file_value = load_google_credentials_payload().get(field, "")
    if file_value:
        return file_value
    alias_env_names = {
        "client_id": ("GOOGLE_OAUTH_CLIENT_ID",),
        "client_secret": ("GOOGLE_OAUTH_CLIENT_SECRET",),
        "refresh_token": ("GOOGLE_OAUTH_REFRESH_TOKEN",),
    }[field]
    return getenv_any(*alias_env_names)


def require_google_config(field: str, display_name: str) -> str:
    value = google_config_value(field)
    if not value:
        raise SummaryError(f"Required env/config is missing: {display_name}")
    return value


def load_webhook_from_file(path: pathlib.Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("url") or payload.get("webhook_url") or "").strip()


def resolve_config_path(path_value: str, base_dir: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def find_default_daily_summary_settings_file() -> pathlib.Path | None:
    candidates = list(REPO_ROOT.glob("personal/*/scripts/daily-calendar-summary/daily_summary_settings.json"))
    if HOME_TEAM_INFO_ROOT != REPO_ROOT:
        candidates.extend(HOME_TEAM_INFO_ROOT.glob("personal/*/scripts/daily-calendar-summary/daily_summary_settings.json"))
    existing = [path for path in candidates if path.exists()]
    if len(existing) == 1:
        return existing[0]
    return None


def load_daily_summary_settings_payload() -> tuple[dict[str, Any] | None, pathlib.Path | None]:
    global LOADED_SETTINGS_FILE
    path_value = getenv("DAILY_SUMMARY_SETTINGS_FILE")
    path = pathlib.Path(path_value).expanduser() if path_value else find_default_daily_summary_settings_file()
    if not path or not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    LOADED_SETTINGS_FILE = path
    return payload, path.parent


def find_default_daily_webhook_file() -> pathlib.Path | None:
    candidates = list(REPO_ROOT.glob("personal/*/discord/discord-daily-webhook.json"))
    if HOME_TEAM_INFO_ROOT != REPO_ROOT:
        candidates.extend(HOME_TEAM_INFO_ROOT.glob("personal/*/discord/discord-daily-webhook.json"))
    existing = [path for path in candidates if path.exists()]
    if len(existing) == 1:
        return existing[0]
    return None


def discord_daily_webhook_url() -> str:
    value = getenv_any("DISCORD_DAILY_WEBHOOK", "DISCORD_WEBHOOK_DAILY")
    if value:
        return value

    path_value = getenv_any("DISCORD_DAILY_WEBHOOK_FILE", "DISCORD_WEBHOOK_DAILY_FILE")
    path = pathlib.Path(path_value).expanduser() if path_value else find_default_daily_webhook_file()
    if path:
        return load_webhook_from_file(path)
    return ""


def require_discord_daily_webhook() -> str:
    value = discord_daily_webhook_url()
    if not value:
        raise SummaryError("Required env/config is missing: DISCORD_DAILY_WEBHOOK")
    return value


@dataclass(frozen=True)
class ZoomAccount:
    key: str
    label: str
    account_id: str
    client_id: str
    client_secret: str
    host_user_id: str = "me"
    title_prefixes: tuple[str, ...] = ()
    default: bool = False


@dataclass(frozen=True)
class LineAccount:
    key: str
    label: str
    sender_url: str
    sender_token: str = ""
    title_prefixes: tuple[str, ...] = ()
    title_keywords: tuple[str, ...] = ()
    default: bool = False


@dataclass(frozen=True)
class ExtraCalendar:
    calendar_id: str
    label: str
    title_keywords: tuple[str, ...] = ()
    google_meet_on_primary_overlap: bool = False


def getenv(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def require_env(name: str) -> str:
    value = getenv(name)
    if not value:
        raise SummaryError(f"Required secret/env is missing: {name}")
    return value


def parse_json_env(name: str) -> Any:
    value = getenv(name)
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SummaryError(f"{name} is not valid JSON") from exc


def request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | list[Any] | None, str]:
    body: bytes | None = None
    request_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as response:
            text = response.read().decode("utf-8", errors="replace")
            parsed: dict[str, Any] | list[Any] | None = None
            if text.strip():
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
            return response.status, parsed, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        raise SummaryError(f"HTTP {exc.code} {exc.reason} for {url}: {compact_error_text(parsed, text)}") from exc
    except urllib.error.URLError as exc:
        raise SummaryError(f"Request failed for {url}: {exc}") from exc


def compact_error_text(parsed: Any, text: str) -> str:
    if isinstance(parsed, dict):
        for key in ("error_description", "error", "message"):
            if parsed.get(key):
                return str(parsed[key])[:500]
        return json.dumps(parsed, ensure_ascii=False)[:500]
    return text[:500]


def google_access_token() -> str:
    status, parsed, _ = request_json(
        "https://oauth2.googleapis.com/token",
        method="POST",
        form={
            "client_id": require_google_config("client_id", "GOOGLE_CLIENT_ID"),
            "client_secret": require_google_config("client_secret", "GOOGLE_CLIENT_SECRET"),
            "refresh_token": require_google_config("refresh_token", "GOOGLE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
    )
    if status != 200 or not isinstance(parsed, dict) or not parsed.get("access_token"):
        raise SummaryError("Google OAuth token refresh did not return an access token")
    return str(parsed["access_token"])


def google_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def resolve_calendar_backend() -> str:
    configured = getenv("DAILY_SUMMARY_CALENDAR_BACKEND").lower()
    if configured in {"gws", "direct"}:
        return configured
    return "gws" if shutil.which("gws") else "direct"


def run_gws_calendar(method: str, params: dict[str, Any], body: dict[str, Any] | None = None) -> dict[str, Any]:
    command = ["gws", "calendar", "events", method, "--params", json.dumps(params, ensure_ascii=False)]
    if body is not None:
        command.extend(["--json", json.dumps(body, ensure_ascii=False)])
    result = subprocess.run(command, text=True, capture_output=True, timeout=120)
    if result.returncode != 0:
        detail = (result.stderr.strip() or result.stdout.strip() or "unknown error")[:800]
        raise SummaryError(f"gws calendar events {method} failed: {detail}")
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SummaryError(f"gws calendar events {method} returned non-JSON output") from exc
    if not isinstance(parsed, dict):
        raise SummaryError(f"gws calendar events {method} returned unexpected output")
    if isinstance(parsed.get("error"), dict):
        raise SummaryError(f"gws calendar events {method} returned error: {compact_error_text(parsed.get('error'), result.stdout)}")
    return parsed


def calendar_api_url(calendar_id: str, suffix: str = "") -> str:
    encoded = urllib.parse.quote(calendar_id, safe="")
    return f"https://www.googleapis.com/calendar/v3/calendars/{encoded}/events{suffix}"


def fetch_events(
    token: str,
    calendar_id: str,
    date_str: str,
    tz: ZoneInfo,
    source_label: str = "",
) -> list[dict[str, Any]]:
    day_start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    params = urllib.parse.urlencode(
        {
            "timeMin": day_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "timeMax": day_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": "80",
            "timeZone": str(tz),
        }
    )
    if CALENDAR_BACKEND == "gws":
        parsed = run_gws_calendar("list", {
            "calendarId": calendar_id,
            "timeMin": day_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "timeMax": day_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 80,
            "timeZone": str(tz),
        })
        return [normalize_event(item, calendar_id, tz, source_label) for item in parsed.get("items", [])]

    status, parsed, _ = request_json(
        calendar_api_url(calendar_id, f"?{params}"),
        headers=google_headers(token),
    )
    if status != 200 or not isinstance(parsed, dict):
        raise SummaryError("Google Calendar events.list returned an unexpected response")
    return [normalize_event(item, calendar_id, tz, source_label) for item in parsed.get("items", [])]


def normalize_event(item: dict[str, Any], calendar_id: str, tz: ZoneInfo, source_label: str = "") -> dict[str, Any]:
    start = item.get("start") or {}
    end = item.get("end") or {}
    title = item.get("summary") or "（タイトルなし）"
    description = item.get("description") or ""

    if "date" in start:
        return {
            "event_id": item.get("id"),
            "calendar_id": calendar_id,
            "title": title,
            "start": None,
            "end": None,
            "start_iso": None,
            "duration": None,
            "description": description,
            "location": item.get("location") or "",
            "allDay": True,
            "source_label": source_label,
            "raw": item,
        }

    start_dt = parse_calendar_datetime(start.get("dateTime"), tz)
    end_dt = parse_calendar_datetime(end.get("dateTime"), tz)
    duration = int((end_dt - start_dt).total_seconds() / 60) if start_dt and end_dt else 60
    return {
        "event_id": item.get("id"),
        "calendar_id": calendar_id,
        "title": title,
        "start": start_dt.strftime("%H:%M") if start_dt else "",
        "end": end_dt.strftime("%H:%M") if end_dt else "",
        "start_iso": start_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if start_dt else None,
        "duration": duration,
        "description": description,
        "location": item.get("location") or "",
        "allDay": False,
        "source_label": source_label,
        "raw": item,
    }


def parse_calendar_datetime(value: str | None, tz: ZoneInfo) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(tz)


def event_end_datetime(event: dict[str, Any], tz: ZoneInfo) -> datetime | None:
    if not event.get("start_iso"):
        return None
    start = datetime.fromisoformat(str(event["start_iso"]).replace("Z", "+00:00")).astimezone(tz)
    return start + timedelta(minutes=int(event.get("duration") or 60))


def extract_line_user_id(description: str, raw_event: dict[str, Any] | None = None) -> str | None:
    private = (((raw_event or {}).get("extendedProperties") or {}).get("private") or {})
    private_uid = private.get(LINE_UID_KEY)
    if private_uid:
        return str(private_uid).strip()
    patterns = (
        r"[?&]uid=([A-Za-z0-9_-]+)",
        r"\buid\s*[:=]\s*([A-Za-z0-9_-]+)",
        r"ユーザーID\s*[:=：＝]\s*([A-Za-z0-9_-]+)",
        r"\"uid\"\s*:\s*\"([A-Za-z0-9_-]+)\"",
    )
    for pattern in patterns:
        match = re.search(pattern, description or "", flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_meeting_url(text: str | None) -> str | None:
    if not text:
        return None
    for pattern in URL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0).rstrip(".,;)")
    return None


def extract_event_meeting_url(event: dict[str, Any]) -> str | None:
    google_meet = extract_event_google_meet_url(event)
    if google_meet:
        return google_meet
    private = ((event.get("raw") or {}).get("extendedProperties") or {}).get("private") or {}
    for source in (event.get("location"), event.get("description"), private.get(MEETING_URL_KEY)):
        url = extract_meeting_url(str(source or ""))
        if url:
            return url
    return None


def extract_event_google_meet_url(event: dict[str, Any]) -> str | None:
    raw = event.get("raw") or {}
    hangout = raw.get("hangoutLink")
    if hangout:
        return str(hangout)
    for entry in (((raw.get("conferenceData") or {}).get("entryPoints")) or []):
        uri = extract_meeting_url((entry or {}).get("uri"))
        if uri and (entry or {}).get("entryPointType") == "video":
            return uri
    return None


def extract_zoom_meeting_id(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"/j/(\d+)", url)
    return match.group(1) if match else None


def meeting_provider_label(url: str | None) -> str:
    if "meet.google.com/" in (url or ""):
        return "Google Meet"
    return "Zoom"


def display_event_title(event: dict[str, Any]) -> str:
    title = str(event.get("title") or "（タイトルなし）")
    source_label = str(event.get("source_label") or "").strip()
    if source_label and source_label != PRIMARY_SOURCE_LABEL:
        return f"{title}（{source_label}）"
    return title


def load_account_credentials(item: dict[str, Any], base_dir: pathlib.Path | None) -> dict[str, str]:
    credentials_file = str(item.get("credentials_file") or "").strip()
    if not credentials_file or base_dir is None:
        return {}
    path = resolve_config_path(credentials_file, base_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        key: str(payload.get(key) or "").strip()
        for key in ("account_id", "client_id", "client_secret")
        if str(payload.get(key) or "").strip()
    }


def config_value(item: dict[str, Any], field: str, default: str = "", base_dir: pathlib.Path | None = None) -> str:
    value = str(item.get(field) or "").strip()
    if value:
        return value
    env_name = str(item.get(f"{field}_env") or "").strip()
    if env_name:
        value = getenv(env_name)
        if value:
            return value
    credentials = load_account_credentials(item, base_dir)
    if credentials.get(field):
        return credentials[field]
    return default


def load_zoom_accounts() -> list[ZoomAccount]:
    raw_accounts = parse_json_env("DAILY_SUMMARY_ZOOM_ACCOUNTS_JSON")
    settings_base_dir: pathlib.Path | None = None
    if raw_accounts is None:
        settings_payload, settings_base_dir = load_daily_summary_settings_payload()
        if settings_payload and isinstance(settings_payload.get("zoom_accounts"), list):
            raw_accounts = settings_payload["zoom_accounts"]
    accounts: list[ZoomAccount] = []
    if raw_accounts is not None:
        if not isinstance(raw_accounts, list):
            raise SummaryError("DAILY_SUMMARY_ZOOM_ACCOUNTS_JSON must be an array")
        for index, item in enumerate(raw_accounts, start=1):
            if not isinstance(item, dict):
                raise SummaryError("Each zoom account must be an object")
            account = ZoomAccount(
                key=config_value(item, "key", base_dir=settings_base_dir),
                label=config_value(item, "label", config_value(item, "key", base_dir=settings_base_dir), base_dir=settings_base_dir),
                account_id=config_value(item, "account_id", base_dir=settings_base_dir),
                client_id=config_value(item, "client_id", base_dir=settings_base_dir),
                client_secret=config_value(item, "client_secret", base_dir=settings_base_dir),
                host_user_id=config_value(item, "host_user_id", "me", base_dir=settings_base_dir) or "me",
                title_prefixes=tuple(str(v) for v in item.get("title_prefixes") or []),
                default=bool(item.get("default")),
            )
            missing = [
                field
                for field, value in (
                    ("key", account.key),
                    ("account_id", account.account_id),
                    ("client_id", account.client_id),
                    ("client_secret", account.client_secret),
                )
                if not value
            ]
            if missing:
                raise SummaryError(
                    f"Zoom account #{index} is missing {', '.join(missing)}. "
                    "Set the value directly or use *_env keys in DAILY_SUMMARY_ZOOM_ACCOUNTS_JSON."
                )
            accounts.append(account)
    else:
        default_secret_names = ("ZOOM_ACCOUNT_ID", "ZOOM_CLIENT_ID", "ZOOM_CLIENT_SECRET")
        default_values = {name: getenv(name) for name in default_secret_names}
        if any(default_values.values()) and not all(default_values.values()):
            missing = [name for name, value in default_values.items() if not value]
            raise SummaryError(f"Incomplete Zoom default secrets: missing {', '.join(missing)}")

    if not accounts and getenv("ZOOM_ACCOUNT_ID") and getenv("ZOOM_CLIENT_ID") and getenv("ZOOM_CLIENT_SECRET"):
        accounts.append(
            ZoomAccount(
                key="default",
                label=getenv("ZOOM_ACCOUNT_LABEL", "default"),
                account_id=getenv("ZOOM_ACCOUNT_ID"),
                client_id=getenv("ZOOM_CLIENT_ID"),
                client_secret=getenv("ZOOM_CLIENT_SECRET"),
                host_user_id=getenv("ZOOM_HOST_USER_ID", "me"),
                default=True,
            )
        )
    return accounts


def load_line_accounts() -> list[LineAccount]:
    raw_accounts = parse_json_env("DAILY_SUMMARY_LINE_ACCOUNTS_JSON")
    accounts: list[LineAccount] = []
    if raw_accounts is not None:
        if not isinstance(raw_accounts, list):
            raise SummaryError("DAILY_SUMMARY_LINE_ACCOUNTS_JSON must be an array")
        for item in raw_accounts:
            if not isinstance(item, dict):
                raise SummaryError("Each line account must be an object")
            accounts.append(
                LineAccount(
                    key=str(item.get("key") or "").strip(),
                    label=str(item.get("label") or item.get("key") or "").strip(),
                    sender_url=str(item.get("sender_url") or "").strip(),
                    sender_token=str(item.get("sender_token") or "").strip(),
                    title_prefixes=tuple(str(v) for v in item.get("title_prefixes") or []),
                    title_keywords=tuple(str(v) for v in item.get("title_keywords") or []),
                    default=bool(item.get("default")),
                )
            )
    elif getenv("PROLINE_MESSAGE_SENDER_URL") or getenv("LINE_MESSAGE_SENDER_URL"):
        accounts.append(
            LineAccount(
                key="default",
                label=getenv("LINE_ACCOUNT_LABEL", "既存公式LINE"),
                sender_url=getenv("PROLINE_MESSAGE_SENDER_URL") or getenv("LINE_MESSAGE_SENDER_URL"),
                sender_token=getenv("PROLINE_MESSAGE_SENDER_TOKEN") or getenv("LINE_MESSAGE_SENDER_TOKEN"),
                default=True,
            )
        )
    return [account for account in accounts if account.key and account.sender_url]


def load_extra_calendars() -> list[ExtraCalendar]:
    raw_calendars = parse_json_env("DAILY_SUMMARY_EXTRA_CALENDARS_JSON")
    if raw_calendars is None:
        return []
    if not isinstance(raw_calendars, list):
        raise SummaryError("DAILY_SUMMARY_EXTRA_CALENDARS_JSON must be an array")
    calendars: list[ExtraCalendar] = []
    for item in raw_calendars:
        if not isinstance(item, dict):
            raise SummaryError("Each extra calendar must be an object")
        calendar_id = str(item.get("calendar_id") or item.get("id") or "").strip()
        if not calendar_id:
            raise SummaryError("Extra calendar requires calendar_id")
        calendars.append(
            ExtraCalendar(
                calendar_id=calendar_id,
                label=str(item.get("label") or calendar_id).strip(),
                title_keywords=tuple(str(v) for v in item.get("title_keywords") or []),
                google_meet_on_primary_overlap=bool(item.get("google_meet_on_primary_overlap")),
            )
        )
    return calendars


def choose_zoom_account(title: str, accounts: list[ZoomAccount]) -> ZoomAccount | None:
    if not accounts:
        return None
    for account in accounts:
        if account.default:
            continue
        if any(title.startswith(prefix) for prefix in account.title_prefixes):
            return account
    return next((account for account in accounts if account.default), accounts[0])


def choose_line_account(title: str, accounts: list[LineAccount]) -> LineAccount | None:
    if not accounts:
        return None
    for account in accounts:
        if account.default:
            continue
        if any(title.startswith(prefix) for prefix in account.title_prefixes):
            return account
        if any(keyword in title for keyword in account.title_keywords):
            return account
    return next((account for account in accounts if account.default), accounts[0])


def zoom_access_token(account: ZoomAccount) -> str:
    auth = base64.b64encode(f"{account.client_id}:{account.client_secret}".encode()).decode()
    query = urllib.parse.urlencode({"grant_type": "account_credentials", "account_id": account.account_id})
    status, parsed, _ = request_json(
        f"https://zoom.us/oauth/token?{query}",
        method="POST",
        headers={"Authorization": f"Basic {auth}"},
    )
    if status != 200 or not isinstance(parsed, dict) or not parsed.get("access_token"):
        raise SummaryError(f"Zoom token request failed for account {account.label}")
    return str(parsed["access_token"])


def create_zoom_meeting(event: dict[str, Any], account: ZoomAccount, tz_name: str) -> tuple[str, str | None]:
    token = zoom_access_token(account)
    payload = {
        "topic": event["title"],
        "type": 2,
        "start_time": event["start_iso"],
        "duration": int(event.get("duration") or 60),
        "timezone": tz_name,
        "settings": {
            "join_before_host": True,
            "waiting_room": False,
        },
    }
    user_id = urllib.parse.quote(account.host_user_id, safe="")
    status, parsed, _ = request_json(
        f"https://api.zoom.us/v2/users/{user_id}/meetings",
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
        payload=payload,
    )
    if status not in (200, 201) or not isinstance(parsed, dict) or not parsed.get("join_url"):
        raise SummaryError(f"Zoom meeting creation failed for {event['title']}")
    return str(parsed["join_url"]), str(parsed.get("id") or extract_zoom_meeting_id(str(parsed["join_url"])) or "")


def build_share_message(event: dict[str, Any], meeting_url: str, meeting_id: str | None = None) -> str:
    lines = [
        "お世話になっております。",
        f"本日 {event.get('start') or ''}〜{event.get('end') or ''} の「{event['title']}」の会議リンクをお送りします。",
        "",
    ]
    if meeting_id:
        lines.extend([f"ミーティングID: {meeting_id}", ""])
    lines.extend([meeting_url, "", "よろしくお願いいたします。"])
    return "\n".join(lines)


def build_description(description: str, meeting_url: str, share_message: str, meeting_id: str | None = None) -> str:
    provider = meeting_provider_label(meeting_url)
    block_lines = [MEETING_MESSAGE_HEADER]
    if meeting_id and provider == "Zoom":
        block_lines.extend(["Zoom Meeting ID:", meeting_id, ""])
    block_lines.extend([f"{provider} URL:", meeting_url, "", f"{provider} URL送信メッセージ:", share_message])
    clean_description = strip_old_team_info_block(description)
    return (clean_description.rstrip() + "\n\n" + "\n".join(block_lines)).strip()


def strip_old_team_info_block(description: str) -> str:
    lines = (description or "").replace("\r\n", "\n").split("\n")
    kept: list[str] = []
    skipping = False
    for line in lines:
        if line.strip() == MEETING_MESSAGE_HEADER:
            skipping = True
            continue
        if skipping and line.strip().startswith("[team-info] "):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept).strip()


def patch_calendar_event(token: str, calendar_id: str, event: dict[str, Any], body: dict[str, Any]) -> None:
    raw_event_id = str(event["event_id"])
    if CALENDAR_BACKEND == "gws":
        parsed = run_gws_calendar("patch", {
            "calendarId": calendar_id,
            "eventId": raw_event_id,
            "conferenceDataVersion": 1,
        }, body)
    else:
        event_id = urllib.parse.quote(raw_event_id, safe="")
        status, parsed, _ = request_json(
            calendar_api_url(calendar_id, f"/{event_id}?conferenceDataVersion=1"),
            method="PATCH",
            headers=google_headers(token),
            payload=body,
        )
        if status != 200 or not isinstance(parsed, dict):
            raise SummaryError(f"Calendar patch failed for {event['title']}")
    event["raw"] = parsed
    event["description"] = parsed.get("description") or event.get("description") or ""
    event["location"] = parsed.get("location") or event.get("location") or ""


def merge_private_properties(raw_event: dict[str, Any], updates: dict[str, str]) -> dict[str, Any]:
    existing = ((raw_event.get("extendedProperties") or {}).get("private") or {})
    merged = dict(existing)
    merged.update({key: value for key, value in updates.items() if value is not None})
    return {"extendedProperties": {"private": merged}}


def ensure_meeting_url(
    token: str,
    calendar_id: str,
    event: dict[str, Any],
    zoom_accounts: list[ZoomAccount],
    tz_name: str,
    provider: str = "zoom",
) -> tuple[str | None, str | None]:
    if provider == "google_meet":
        return ensure_google_meet_url(token, calendar_id, event)

    existing = extract_event_meeting_url(event)
    if existing:
        return existing, extract_zoom_meeting_id(existing)
    if not event.get("start_iso"):
        raise SummaryError(f"Cannot create Zoom meeting without a start time: {event['title']}")
    account = choose_zoom_account(event["title"], zoom_accounts)
    if not account:
        raise SummaryError(
            "Zoom account secrets are not configured. "
            "Set ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET, "
            "or DAILY_SUMMARY_ZOOM_ACCOUNTS_JSON."
        )
    meeting_url, meeting_id = create_zoom_meeting(event, account, tz_name)
    share_message = build_share_message(event, meeting_url, meeting_id)
    new_description = build_description(event.get("description") or "", meeting_url, share_message, meeting_id)
    existing_location = (event.get("location") or "").strip()
    new_location = meeting_url if not existing_location else f"{meeting_url}\n{existing_location}"
    body = {
        "description": new_description,
        "location": new_location,
    }
    body.update(merge_private_properties(event.get("raw") or {}, {MEETING_URL_KEY: meeting_url, MEETING_ID_KEY: meeting_id or ""}))
    patch_calendar_event(token, calendar_id, event, body)
    return meeting_url, meeting_id


def ensure_google_meet_url(token: str, calendar_id: str, event: dict[str, Any]) -> tuple[str | None, str | None]:
    existing_meet = extract_event_google_meet_url(event)
    if existing_meet:
        return existing_meet, None

    request_id = f"team-info-{uuid.uuid4().hex}"
    patch_calendar_event(
        token,
        calendar_id,
        event,
        {
            "conferenceData": {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        },
    )
    meeting_url = extract_event_google_meet_url(event) or extract_event_meeting_url(event)
    if not meeting_url:
        raise SummaryError(f"Google Meet creation failed for {event['title']}")
    share_message = build_share_message(event, meeting_url, None)
    new_description = build_description(event.get("description") or "", meeting_url, share_message, None)
    existing_location = (event.get("location") or "").strip()
    new_location = meeting_url if not existing_location else f"{meeting_url}\n{existing_location}"
    body = {
        "description": new_description,
        "location": new_location,
    }
    body.update(merge_private_properties(event.get("raw") or {}, {MEETING_URL_KEY: meeting_url, MEETING_ID_KEY: ""}))
    patch_calendar_event(token, calendar_id, event, body)
    return meeting_url, None


def was_line_sent(event: dict[str, Any], uid: str, meeting_url: str) -> bool:
    private = (((event.get("raw") or {}).get("extendedProperties") or {}).get("private") or {})
    return (
        private.get(LINE_STATUS_KEY) == "sent"
        and private.get(LINE_UID_KEY) == uid
        and private.get(LINE_SENT_URL_KEY) == meeting_url
    )


def send_line(account: LineAccount, uid: str, message: str) -> tuple[bool, str]:
    payload = {
        "userId": uid,
        "messageContent": message,
    }
    if account.sender_token:
        payload["token"] = account.sender_token
    status, parsed, text = request_json(
        account.sender_url,
        method="POST",
        headers={"User-Agent": "team-info github-actions daily summary"},
        payload=payload,
    )
    if status < 200 or status >= 300:
        return False, f"HTTP {status}"
    if isinstance(parsed, dict) and parsed.get("ok") is False:
        return False, str(parsed.get("error") or parsed)
    if isinstance(parsed, dict) and "ok" in parsed:
        return True, f"ok={parsed.get('ok')}"
    return True, f"HTTP {status}"


def send_discord(webhook_url: str, content: str) -> None:
    for chunk in chunk_message(content, 1900):
        status, _, _ = request_json(
            webhook_url,
            method="POST",
            headers={"User-Agent": "DiscordBot (https://github.com/Shoma-DS/team-info, 1.0)"},
            payload={"content": chunk},
        )
        if status not in (200, 204):
            raise SummaryError(f"Discord webhook returned HTTP {status}")
        time.sleep(0.3)


def chunk_message(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in text.splitlines():
        if len(current) + len(line) + 1 > limit and current:
            chunks.append(current.rstrip())
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current.rstrip())
    return chunks or [text[:limit]]


def format_date_label(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.month}月{dt.day}日"


def event_time_window(event: dict[str, Any], tz: ZoneInfo) -> tuple[datetime, datetime] | None:
    if event.get("allDay") or not event.get("start_iso"):
        return None
    start = datetime.fromisoformat(str(event["start_iso"]).replace("Z", "+00:00")).astimezone(tz)
    end = start + timedelta(minutes=int(event.get("duration") or 60))
    return start, end


def events_overlap(left: dict[str, Any], right: dict[str, Any], tz: ZoneInfo) -> bool:
    left_window = event_time_window(left, tz)
    right_window = event_time_window(right, tz)
    if not left_window or not right_window:
        return False
    left_start, left_end = left_window
    right_start, right_end = right_window
    return left_start < right_end and right_start < left_end


def is_sugashita_event(event: dict[str, Any]) -> bool:
    return "★" in str(event.get("title") or "")


def assign_google_meet_for_overlaps(events: list[dict[str, Any]], tz: ZoneInfo) -> None:
    """★付き以外の予定が重なる場合、先頭以外を Google Meet に寄せる。"""
    seen_zoom_candidates: list[dict[str, Any]] = []
    for event in sorted(
        (event for event in events if not event.get("allDay") and not is_sugashita_event(event)),
        key=lambda item: item.get("start_iso") or "",
    ):
        if event.get("force_google_meet") or extract_event_google_meet_url(event):
            continue
        overlaps_zoom_candidate = any(events_overlap(event, prior, tz) for prior in seen_zoom_candidates)
        if overlaps_zoom_candidate:
            event["force_google_meet"] = True
        else:
            seen_zoom_candidates.append(event)


def matches_extra_calendar_filter(event: dict[str, Any], calendar: ExtraCalendar) -> bool:
    if not calendar.title_keywords:
        return True
    target = f"{event.get('title') or ''}\n{event.get('description') or ''}"
    return any(keyword in target for keyword in calendar.title_keywords)


def process(args: argparse.Namespace) -> int:
    global CALENDAR_BACKEND
    CALENDAR_BACKEND = resolve_calendar_backend()
    tz_name = getenv("DAILY_SUMMARY_TIMEZONE", DEFAULT_TIMEZONE)
    tz = ZoneInfo(tz_name)
    date_str = args.date or datetime.now(tz).strftime("%Y-%m-%d")
    calendar_id = getenv("GOOGLE_CALENDAR_ID", "primary")
    webhook_url = require_discord_daily_webhook()
    google_token = "" if CALENDAR_BACKEND == "gws" else google_access_token()
    zoom_accounts = load_zoom_accounts()
    line_accounts = load_line_accounts()
    extra_calendars = load_extra_calendars()
    primary_events = fetch_events(google_token, calendar_id, date_str, tz, PRIMARY_SOURCE_LABEL)
    events = list(primary_events)
    primary_timed = [event for event in primary_events if not event.get("allDay")]

    for extra_calendar in extra_calendars:
        extra_events = fetch_events(google_token, extra_calendar.calendar_id, date_str, tz, extra_calendar.label)
        for event in extra_events:
            if event.get("allDay") or not matches_extra_calendar_filter(event, extra_calendar):
                continue
            event["force_google_meet"] = (
                extra_calendar.google_meet_on_primary_overlap
                and any(events_overlap(event, primary_event, tz) for primary_event in primary_timed)
            )
            events.append(event)

    events.sort(key=lambda event: event.get("start_iso") or "")
    assign_google_meet_for_overlaps(events, tz)

    if args.future_only:
        now = datetime.now(tz)
        events = [
            event for event in events
            if not event.get("allDay") and (event_end_datetime(event, tz) or now) >= now
        ]

    processed: list[dict[str, Any]] = []
    failures: list[str] = []
    for event in events:
        event_calendar_id = event.get("calendar_id") or calendar_id
        if event.get("allDay"):
            processed.append({**event, "meeting_url": None, "line_status": "all-day"})
            continue
        try:
            provider = "google_meet" if event.get("force_google_meet") else "zoom"
            meeting_url, meeting_id = ensure_meeting_url(
                google_token,
                event_calendar_id,
                event,
                zoom_accounts,
                tz_name,
                provider,
            )
            uid = extract_line_user_id(event.get("description") or "", event.get("raw") or {})
            line_status = "対象なし"
            if uid and meeting_url:
                line_account = choose_line_account(event["title"], line_accounts)
                if not line_account:
                    line_status = "送信URL未設定"
                    failures.append(f"{event['start']} {display_event_title(event)}: LINE送信URL未設定")
                elif was_line_sent(event, uid, meeting_url) and not args.force_resend:
                    line_status = f"送信済みスキップ（{line_account.label}）"
                else:
                    share_message = build_share_message(event, meeting_url, meeting_id)
                    ok, response_summary = send_line(line_account, uid, share_message)
                    if ok:
                        line_status = f"送信済み（{line_account.label}）"
                        body = merge_private_properties(
                            event.get("raw") or {},
                            {LINE_STATUS_KEY: "sent", LINE_UID_KEY: uid, LINE_SENT_URL_KEY: meeting_url},
                        )
                        patch_calendar_event(google_token, event_calendar_id, event, body)
                        print(f"[LINE] sent start={event.get('start')} response={response_summary}")
                    else:
                        line_status = f"送信失敗（{line_account.label}）"
                        failures.append(f"{event['start']} {display_event_title(event)}: LINE送信失敗: {response_summary}")
            elif uid and not meeting_url:
                line_status = "会議URLなし"
                failures.append(f"{event['start']} {display_event_title(event)}: 会議URLなし")
            processed.append({**event, "meeting_url": meeting_url, "line_status": line_status})
        except Exception as exc:
            failures.append(f"{event.get('start') or '--:--'} {display_event_title(event)}: {exc}")
            processed.append({**event, "meeting_url": None, "line_status": "処理失敗"})

    if failures:
        send_discord(webhook_url, build_failure_message(date_str, failures, processed))
        return 1

    if not args.skip_discord_summary:
        send_discord(webhook_url, build_summary_message(date_str, processed))
        for index, event in enumerate([event for event in processed if not event.get("allDay")], start=1):
            send_discord(webhook_url, build_detail_message(index, event))
    else:
        send_discord(webhook_url, build_manual_result_message(date_str, processed, args.force_resend))
    return 0


def check_config() -> int:
    global CALENDAR_BACKEND
    CALENDAR_BACKEND = resolve_calendar_backend()
    missing = [
        name
        for name, value in (
            ("GOOGLE_CLIENT_ID", google_config_value("client_id")),
            ("GOOGLE_CLIENT_SECRET", google_config_value("client_secret")),
            ("GOOGLE_REFRESH_TOKEN", google_config_value("refresh_token")),
            ("DISCORD_DAILY_WEBHOOK", discord_daily_webhook_url()),
        )
        if not value
    ]
    if missing:
        raise SummaryError("Missing required env: " + ", ".join(missing))

    zoom_accounts = load_zoom_accounts()
    if not zoom_accounts:
        raise SummaryError(
            "Zoom account config is missing. Set ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / "
            "ZOOM_CLIENT_SECRET, or DAILY_SUMMARY_ZOOM_ACCOUNTS_JSON."
        )

    line_accounts = load_line_accounts()
    extra_calendars = load_extra_calendars()
    report = {
        "ok": True,
        "loaded_env_files": [str(path) for path in LOADED_ENV_FILES],
        "loaded_settings_file": str(LOADED_SETTINGS_FILE) if LOADED_SETTINGS_FILE else "",
        "google_credentials_file": str(DEFAULT_GWS_CREDENTIALS_FILE) if DEFAULT_GWS_CREDENTIALS_FILE.exists() else "",
        "calendar_backend": CALENDAR_BACKEND,
        "discord_webhook_source": "env-or-file" if discord_daily_webhook_url() else "",
        "calendar_id": getenv("GOOGLE_CALENDAR_ID", "primary"),
        "zoom_accounts": [
            {
                "key": account.key,
                "label": account.label,
                "default": account.default,
                "title_prefixes": list(account.title_prefixes),
            }
            for account in zoom_accounts
        ],
        "line_accounts": [
            {
                "key": account.key,
                "label": account.label,
                "default": account.default,
                "title_prefixes": list(account.title_prefixes),
                "title_keywords": list(account.title_keywords),
            }
            for account in line_accounts
        ],
        "extra_calendars": [
            {
                "calendar_id": calendar.calendar_id,
                "label": calendar.label,
                "title_keywords": list(calendar.title_keywords),
                "google_meet_on_primary_overlap": calendar.google_meet_on_primary_overlap,
            }
            for calendar in extra_calendars
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def build_summary_message(date_str: str, events: list[dict[str, Any]]) -> str:
    all_day = [event for event in events if event.get("allDay")]
    timed = [event for event in events if not event.get("allDay")]
    lines = [f"**Shoの予定（{format_date_label(date_str)}）**"]
    if all_day:
        lines.append("【終日】 " + "、".join(event["title"] for event in all_day))
    if timed:
        lines.append("")
        for index, event in enumerate(timed, start=1):
            icon = "🔗" if event.get("meeting_url") else "📅"
            line = f"{icon} {index}. {display_event_title(event)}　{event.get('start')}〜{event.get('end')}"
            if event.get("line_status") and event["line_status"] != "対象なし":
                line += f" / LINE: {event['line_status']}"
            lines.append(line)
    if not all_day and not timed:
        lines.append("今日は予定なしです。")
    return "\n".join(lines)


def build_detail_message(index: int, event: dict[str, Any]) -> str:
    lines = [
        f"**{index}. {display_event_title(event)}**",
        f"{event.get('start')}〜{event.get('end')}",
    ]
    if event.get("meeting_url"):
        provider = meeting_provider_label(event["meeting_url"])
        lines.extend(["", f"{provider} URL:", event["meeting_url"]])
    if event.get("line_status") and event["line_status"] != "対象なし":
        lines.append(f"LINE: {event['line_status']}")
    return "\n".join(lines)


def build_manual_result_message(date_str: str, events: list[dict[str, Any]], force_resend: bool) -> str:
    lines = [
        f"**daily-calendar-summary 手動実行完了（{format_date_label(date_str)}）**",
        f"対象: {len([event for event in events if not event.get('allDay')])}件",
        f"強制再送: {'あり' if force_resend else 'なし'}",
    ]
    for event in events:
        if event.get("allDay"):
            continue
        lines.append(f"- {event.get('start')} {display_event_title(event)}: {event.get('line_status')}")
    return "\n".join(lines)


def build_failure_message(date_str: str, failures: list[str], events: list[dict[str, Any]]) -> str:
    lines = [
        f"**daily-calendar-summary エラー（{format_date_label(date_str)}）**",
        "一部の会議リンク作成またはLINE送信に失敗しました。",
        "",
        "失敗:",
    ]
    lines.extend(f"- {failure}" for failure in failures[:20])
    lines.extend(["", "処理状況:"])
    for event in events:
        if event.get("allDay"):
            continue
        lines.append(f"- {event.get('start')} {display_event_title(event)}: {event.get('line_status')}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="対象日 YYYY-MM-DD。未指定なら実行時のJST当日")
    parser.add_argument("--future-only", action="store_true", help="現在時刻以降の時刻付き予定だけ処理する")
    parser.add_argument("--force-resend", action="store_true", help="Calendar の送信済み記録を無視してLINEを再送する")
    parser.add_argument("--skip-discord-summary", action="store_true", help="朝サマリーではなく手動実行結果だけDiscordへ送る")
    parser.add_argument("--env-file", default="", help=".env として読み込むファイル。未指定なら repo root の .env / .env.local")
    parser.add_argument("--check-config", action="store_true", help="外部送信せず、.env と環境変数の設定だけ検査する")
    args = parser.parse_args()
    load_env_files(args.env_file)
    try:
        if args.check_config:
            raise SystemExit(check_config())
        raise SystemExit(process(args))
    except SummaryError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        webhook_url = discord_daily_webhook_url()
        if webhook_url:
            try:
                send_discord(webhook_url, f"**daily-calendar-summary 起動エラー**\n```text\n{exc}\n```")
            except Exception:
                pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
