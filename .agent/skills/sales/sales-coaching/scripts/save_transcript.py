"""
Loom export の文字起こし保存と Neon(Postgres) への upsert を担う。
repo 直下の `.env` も参照し、営業文字起こしのローカル保存と DB 同期をまとめて扱う。
"""

import json
import os
import re
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, RealDictCursor

REPO_ROOT = Path(__file__).resolve().parents[5]
COACHING_ROOT = REPO_ROOT / "personal" / "deguchishouma" / "sales" / "coaching"
ENV_PATH = REPO_ROOT / ".env"


def save_transcript(
    transcript: str,
    loom_id: str,
    speaker: str,
    type_: str,
    date_str: str,
    meta: dict,
    extra_meta: dict | None = None,
) -> Path:
    subdir = "1s" if type_ == "1s" else "interview"
    save_dir = COACHING_ROOT / "transcripts" / subdir
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{date_str}_{speaker}_{loom_id}.txt"
    filepath = save_dir / filename

    confidence_type = meta.get("confidence_type", 0)
    confidence_speaker = meta.get("confidence_speaker", 0)

    metadata_lines = [
        ("loom_id", loom_id),
        ("speaker", speaker),
        ("type", type_),
        ("date", date_str),
        ("confidence_type", f"{confidence_type}%"),
        ("confidence_speaker", f"{confidence_speaker}%"),
    ]
    if extra_meta:
        for key in (
            "source",
            "video_name",
            "loom_owner_name",
            "recorded_at",
            "organization_name",
            "facilitator_name",
            "facilitator_role",
            "session_summary",
        ):
            value = extra_meta.get(key)
            if value:
                metadata_lines.append((key, _one_line(value)))

    content = "# メタデータ\n"
    content += "".join(f"{key}: {value}\n" for key, value in metadata_lines)
    content += f"\n---\n\n{transcript}"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def parse_metadata(transcript_path: Path) -> dict:
    text = transcript_path.read_text(encoding="utf-8")
    meta = {}
    for line in text.splitlines():
        if line.startswith("---"):
            break
        if ": " in line and not line.startswith("#"):
            key, _, value = line.partition(": ")
            meta[key.strip()] = value.strip()
    body_start = text.find("\n---\n")
    meta["body"] = text[body_start + 5:].strip() if body_start != -1 else text
    return meta


def load_loom_export(export_dir: Path) -> dict:
    metadata_path = export_dir / "metadata.json"
    transcript_path = export_dir / "transcript.txt"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata.json が見つかりません: {metadata_path}")
    if not transcript_path.exists():
        raise FileNotFoundError(f"transcript.txt が見つかりません: {transcript_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    transcript = transcript_path.read_text(encoding="utf-8").strip()
    if not transcript:
        raise ValueError(f"transcript.txt が空です: {transcript_path}")

    return {
        "loom_id": metadata.get("id") or export_dir.name,
        "video_name": metadata.get("name", ""),
        "recorded_at": metadata.get("createdAt", ""),
        "duration_seconds": normalize_duration_seconds(metadata.get("playable_duration")),
        "owner_name": metadata.get("owner", {}).get("display_name", ""),
        "organization_name": metadata.get("organization", {}).get("name", ""),
        "views_total": normalize_integer(metadata.get("views", {}).get("total", 0)) or 0,
        "calendar_meeting_guid": metadata.get("calendarMeetingGuid", ""),
        "summary_text": _read_optional_text(export_dir / "summary.txt"),
        "chapters_text": _read_optional_text(export_dir / "chapters.txt"),
        "tasks_text": _read_optional_text(export_dir / "tasks.txt"),
        "comments_text": _read_optional_text(export_dir / "comments.txt"),
        "transcript": transcript,
        "export_dir": str(export_dir),
        "raw_metadata": metadata,
    }


def build_neon_record(
    export_data: dict,
    transcript_path: Path,
    speaker: str,
    type_: str,
    type_result: dict,
    speaker_result: dict,
    session_result: dict,
    processed_date: str,
) -> dict:
    return {
        "loom_video_id": export_data["loom_id"],
        "source": "loom_mcp",
        "video_name": export_data.get("video_name", ""),
        "recorded_at": export_data.get("recorded_at") or None,
        "processed_date": processed_date,
        "loom_owner_name": export_data.get("owner_name", ""),
        "organization_name": speaker_result.get("organization_name", ""),
        "duration_seconds": export_data.get("duration_seconds"),
        "views_total": export_data.get("views_total", 0),
        "speaker": speaker,
        "speaker_confidence": speaker_result.get("confidence", 0),
        "speaker_reason": speaker_result.get("reason", ""),
        "facilitator_name": speaker_result.get("display_name", ""),
        "facilitator_slug": speaker,
        "facilitator_role": speaker_result.get("role", ""),
        "facilitator_confidence": speaker_result.get("confidence", 0),
        "conversation_type": type_,
        "type_confidence": type_result.get("confidence", 0),
        "type_reason": type_result.get("reason", ""),
        "session_kind": session_result.get("session_kind", "other"),
        "session_confidence": session_result.get("confidence", 0),
        "session_reason": session_result.get("reason", ""),
        "session_tags": session_result.get("tags", []),
        "work_domain": session_result.get("work_domain", "other"),
        "calendar_meeting_guid": export_data.get("calendar_meeting_guid") or None,
        "transcript": export_data.get("transcript", ""),
        "summary_text": export_data.get("summary_text") or None,
        "chapters_text": export_data.get("chapters_text") or None,
        "tasks_text": export_data.get("tasks_text") or None,
        "comments_text": export_data.get("comments_text") or None,
        "transcript_local_path": str(transcript_path),
        "loom_export_dir": export_data.get("export_dir", ""),
        "raw_metadata": export_data.get("raw_metadata", {}),
    }


def upsert_neon_record(record: dict, table_name: str | None = None) -> dict:
    database_url = _get_env_value("NEON_DATABASE_URL") or _get_env_value("DATABASE_URL")
    target_table = resolve_neon_table_name(table_name)

    if not database_url:
        raise RuntimeError("NEON_DATABASE_URL または DATABASE_URL が必要です。")

    payload = dict(record)
    payload["session_tags"] = Json(payload.get("session_tags", []))
    payload["raw_metadata"] = Json(payload.get("raw_metadata", {}))
    columns = list(payload.keys())
    values = [payload[column] for column in columns]

    assignments = [
        sql.SQL("{field} = EXCLUDED.{field}").format(field=sql.Identifier(column))
        for column in columns
        if column != "loom_video_id"
    ]
    query = sql.SQL(
        """
        INSERT INTO {table} ({columns})
        VALUES ({values})
        ON CONFLICT (loom_video_id) DO UPDATE
        SET {assignments}
        RETURNING *
        """
    ).format(
        table=sql.Identifier(target_table),
        columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        values=sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        assignments=sql.SQL(", ").join(assignments),
    )

    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, values)
                payload = cur.fetchone()
            conn.commit()
    except psycopg2.Error as exc:
        raise RuntimeError(f"Neon 登録に失敗しました: {exc}") from exc

    return dict(payload) if payload else {}


def _read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _one_line(value: object) -> str:
    return str(value).replace("\n", " ").strip()


def _load_env_values() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _get_env_value(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value.strip()
    return _load_env_values().get(name, default).strip()


def resolve_neon_table_name(table_name: str | None = None) -> str:
    return table_name or _get_env_value("NEON_TABLE", "sales_coaching_transcripts")


def normalize_duration_seconds(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if value > 100000:
            return int(round(value / 1000))
        return int(round(value))
    if isinstance(value, dict):
        nested = value.get("seconds") or value.get("duration_seconds") or value.get("ms")
        return normalize_duration_seconds(nested)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if re.fullmatch(r"\d+(?:\.\d+)?", stripped):
            numeric = float(stripped)
            if numeric > 100000:
                return int(round(numeric / 1000))
            return int(round(numeric))
    return None


def normalize_integer(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None
    return None


def build_supabase_record(*args, **kwargs) -> dict:
    return build_neon_record(*args, **kwargs)


def upsert_supabase_record(record: dict, table_name: str | None = None) -> dict:
    return upsert_neon_record(record, table_name=table_name)
