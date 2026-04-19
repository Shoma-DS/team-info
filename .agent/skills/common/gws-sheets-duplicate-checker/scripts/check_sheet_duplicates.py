#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "user-presets"
OUTPUT_DIR = Path.cwd() / "outputs" / "gws-duplicate-checker"


def extract_spreadsheet_id(raw: str) -> str:
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", raw)
    if match:
        return match.group(1)
    return raw.strip()


def extract_gid(raw: str) -> int | None:
    match = re.search(r"(?:[#?&]gid=)(\d+)", raw)
    if match:
        return int(match.group(1))
    return None


def run_gws(command: list[str]) -> dict:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "gws command failed")
    return json.loads(completed.stdout)


def quote_sheet_title(sheet_title: str) -> str:
    escaped = sheet_title.replace("'", "''")
    return f"'{escaped}'"


def column_index_to_letter(index: int) -> str:
    result = ""
    current = index + 1
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return sanitized.strip("_") or "template"


def markdown_report_path(spreadsheet_title: str, sheet_title: str, key_columns: list[str]) -> Path:
    suffix = sanitize_filename("_".join(key_columns[:3]))
    return OUTPUT_DIR / f"{sanitize_filename(spreadsheet_title)}_{sanitize_filename(sheet_title)}_{suffix}_report.md"


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input(prompt + suffix).strip().lower()
    if raw == "":
        return default
    return raw in {"y", "yes"}


def choose_from_list(prompt: str, options: list[str], default_index: int | None = None) -> str:
    while True:
        default_note = f" [{default_index + 1}]" if default_index is not None else ""
        raw = input(f"{prompt}{default_note}: ").strip()
        if raw == "" and default_index is not None:
            return options[default_index]
        if raw.isdigit():
            choice = int(raw) - 1
            if 0 <= choice < len(options):
                return options[choice]
        if raw in options:
            return raw
        print("候補の番号か名前を入力してください。")


def choose_multiple_from_list(prompt: str, options: list[str], default_indices: list[int] | None = None) -> list[str]:
    default_label = ""
    if default_indices:
        default_label = " [" + ",".join(str(index + 1) for index in default_indices) + "]"
    print(prompt)
    print("複数選択する場合は `1,3,5` のように入力してください。")
    while True:
        raw = input(f"番号を選んでください{default_label}: ").strip()
        if raw == "" and default_indices:
            return [options[index] for index in default_indices]
        tokens = [token.strip() for token in raw.split(",") if token.strip()]
        if not tokens:
            print("1つ以上選んでください。")
            continue
        selected = []
        valid = True
        for token in tokens:
            if token.isdigit():
                choice = int(token) - 1
                if 0 <= choice < len(options):
                    value = options[choice]
                    if value not in selected:
                        selected.append(value)
                    continue
            if token in options:
                if token not in selected:
                    selected.append(token)
                continue
            valid = False
            break
        if valid and selected:
            return selected
        print("候補の番号をカンマ区切りで入力してください。")


def choose_start_mode(template_name: str, has_explicit_config: bool) -> str:
    if template_name:
        return "template"
    if has_explicit_config:
        return "new"
    print("\n最初にモードを選んでください。")
    print("  1. 保存済みテンプレートを使う")
    print("  2. 新規で重複チェック条件を決める")
    while True:
        raw = input("番号を選んでください [2]: ").strip() or "2"
        if raw == "1":
            return "template"
        if raw == "2":
            return "new"
        print("1-2 を入力してください。")


def fetch_metadata(spreadsheet_id: str) -> dict:
    return run_gws(
        [
            "gws",
            "sheets",
            "spreadsheets",
            "get",
            "--params",
            json.dumps({"spreadsheetId": spreadsheet_id, "includeGridData": False}, ensure_ascii=False),
        ]
    )


def fetch_values(spreadsheet_id: str, range_name: str) -> dict:
    return run_gws(
        [
            "gws",
            "sheets",
            "spreadsheets",
            "values",
            "get",
            "--params",
            json.dumps({"spreadsheetId": spreadsheet_id, "range": range_name}, ensure_ascii=False),
        ]
    )


def append_column(spreadsheet_id: str, sheet_id: int):
    run_gws(
        [
            "gws",
            "sheets",
            "spreadsheets",
            "batchUpdate",
            "--params",
            json.dumps({"spreadsheetId": spreadsheet_id}, ensure_ascii=False),
            "--json",
            json.dumps(
                {
                    "requests": [
                        {
                            "appendDimension": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "length": 1,
                            }
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        ]
    )


def write_values(spreadsheet_id: str, updates: list[dict]):
    run_gws(
        [
            "gws",
            "sheets",
            "spreadsheets",
            "values",
            "batchUpdate",
            "--params",
            json.dumps({"spreadsheetId": spreadsheet_id}, ensure_ascii=False),
            "--json",
            json.dumps(
                {
                    "valueInputOption": "USER_ENTERED",
                    "data": updates,
                },
                ensure_ascii=False,
            ),
        ]
    )


def load_rows(payload: dict) -> tuple[list[str], list[dict]]:
    values = payload.get("values", [])
    if len(values) < 2:
        raise ValueError("ヘッダ行とデータ行が必要です")
    headers = values[0]
    rows = []
    for offset, raw_row in enumerate(values[1:], start=2):
        row = {"__row_number": offset}
        for index, key in enumerate(headers):
            row[key] = raw_row[index] if index < len(raw_row) else ""
        rows.append(row)
    return headers, rows


def normalize_value(value: str) -> str:
    return str(value or "").strip()


def build_duplicate_groups(rows: list[dict], key_columns: list[str], exclude_all_blank: bool = True) -> tuple[dict[tuple[str, ...], list[dict]], int]:
    groups: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    skipped = 0
    for row in rows:
        key = tuple(normalize_value(row.get(column, "")) for column in key_columns)
        if exclude_all_blank and all(part == "" for part in key):
            skipped += 1
            continue
        groups[key].append(row)
    duplicate_groups = {key: group for key, group in groups.items() if len(group) >= 2}
    return duplicate_groups, skipped


def build_duplicate_occurrence_map(duplicate_groups: dict[tuple[str, ...], list[dict]]) -> dict[int, bool]:
    occurrence_map: dict[int, bool] = {}
    for group in duplicate_groups.values():
        sorted_group = sorted(group, key=lambda row: row["__row_number"])
        for index, row in enumerate(sorted_group):
            occurrence_map[row["__row_number"]] = index >= 1
    return occurrence_map


def preview_rows(headers: list[str], rows: list[dict], limit: int = 5):
    print("\n列候補:")
    for index, header in enumerate(headers, start=1):
        print(f"  {index}. {header}")

    print("\n先頭データ:")
    for row in rows[:limit]:
        preview = " | ".join(f"{header}={row.get(header, '')}" for header in headers[:6])
        print(f"  - row {row['__row_number']}: {preview}")


def print_duplicate_summary(duplicate_groups: dict[tuple[str, ...], list[dict]], key_columns: list[str], rows: list[dict], skipped: int):
    duplicate_row_count = sum(max(0, len(group) - 1) for group in duplicate_groups.values())
    print("\n重複チェック結果:")
    print(f"  - データ行数: {len(rows)}")
    print(f"  - 空欄除外行数: {skipped}")
    print(f"  - 重複グループ数: {len(duplicate_groups)}")
    print(f"  - 重複行数: {duplicate_row_count}")

    if not duplicate_groups:
        print("  - 重複は見つかりませんでした。")
        return

    print("\n重複グループの例:")
    for index, (key, group) in enumerate(duplicate_groups.items(), start=1):
        if index > 10:
            remaining = len(duplicate_groups) - 10
            if remaining > 0:
                print(f"  - ほか {remaining} グループ")
            break
        sorted_group = sorted(group, key=lambda row: row["__row_number"])
        row_numbers = ", ".join(str(row["__row_number"]) for row in sorted_group)
        key_text = " / ".join(f"{column}={value or '(空欄)'}" for column, value in zip(key_columns, key))
        first_row = sorted_group[0]["__row_number"]
        duplicate_rows = ", ".join(str(row["__row_number"]) for row in sorted_group[1:]) or "-"
        print(f"  - {key_text} -> 初回 row {first_row} / 重複 row {duplicate_rows}")


def build_write_plan(
    rows: list[dict],
    key_columns: list[str],
    duplicate_groups: dict[tuple[str, ...], list[dict]],
    exclude_all_blank: bool,
    target_column: str,
    preserve_non_duplicates: bool,
) -> tuple[list[list[str]], list[dict]]:
    occurrence_map = build_duplicate_occurrence_map(duplicate_groups)
    values: list[list[str]] = []
    anomaly_rows: list[dict] = []

    for row in rows:
        row_number = row["__row_number"]
        key = tuple(normalize_value(row.get(column, "")) for column in key_columns)
        current_value = normalize_value(row.get(target_column, ""))
        is_blank_key = exclude_all_blank and all(part == "" for part in key)
        is_duplicate_occurrence = occurrence_map.get(row_number, False)

        if current_value == "重複" and not is_duplicate_occurrence:
            reason = "初回行" if key in duplicate_groups else "非重複行"
            anomaly_rows.append(
                {
                    "row_number": row_number,
                    "reason": reason,
                    "current_value": current_value,
                    "key_text": " / ".join(f"{column}={value or '(空欄)'}" for column, value in zip(key_columns, key)),
                }
            )

        if is_duplicate_occurrence:
            values.append(["重複"])
            continue

        non_duplicate_value = default_non_duplicate_value(target_column, current_value)
        if preserve_non_duplicates or is_blank_key or non_duplicate_value != "":
            values.append([non_duplicate_value])
            continue

        values.append([""])

    return values, anomaly_rows


def default_non_duplicate_value(target_column: str, current_value: str) -> str:
    if target_column == "1S" and current_value == "":
        return "1S予定"
    return current_value


def save_anomaly_report(
    spreadsheet_title: str,
    sheet_title: str,
    key_columns: list[str],
    anomaly_rows: list[dict],
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = markdown_report_path(spreadsheet_title, sheet_title, key_columns)
    lines = [
        f"# 重複マーク見直しレポート",
        "",
        f"- スプレッドシート: {spreadsheet_title}",
        f"- シート: {sheet_title}",
        f"- 判定列: {', '.join(key_columns)}",
        "",
    ]
    if not anomaly_rows:
        lines.append("問題のある `重複` マークは見つかりませんでした。")
    else:
        lines.append("| 行番号 | 理由 | 現在値 | 判定キー |")
        lines.append("|---|---|---|---|")
        for item in anomaly_rows:
            lines.append(
                f"| {item['row_number']} | {item['reason']} | {item['current_value']} | {item['key_text']} |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def list_templates() -> list[dict]:
    if not TEMPLATE_DIR.exists():
        return []
    records = []
    for path in sorted(TEMPLATE_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = str(path)
        records.append(payload)
    return records


def choose_template(template_name: str) -> dict | None:
    templates = list_templates()
    if not templates:
        print("\n保存済みテンプレートはまだありません。")
        return None

    if template_name:
        for template in templates:
            if template.get("name") == template_name:
                return template
        raise ValueError(f"テンプレート '{template_name}' が見つかりません。")

    print("\n保存済みテンプレート:")
    for index, template in enumerate(templates, start=1):
        print(f"  {index}. {template.get('name', f'template-{index}')}")
    names = [template.get("name", f"template-{index}") for index, template in enumerate(templates, start=1)]
    selected = choose_from_list("使うテンプレートを選んでください", names, default_index=0)
    for template in templates:
        if template.get("name") == selected:
            return template
    return None


def save_template(config: dict):
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    template_name = input("テンプレート名を入力してください: ").strip()
    if not template_name:
        print("テンプレート名が空なので保存をスキップしました。")
        return
    payload = dict(config)
    payload["name"] = template_name
    path = TEMPLATE_DIR / f"{sanitize_filename(template_name)}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"テンプレート保存: {path}")


def choose_sheet(sheet_records: list[dict], default_title: str | None = None, auto_select: bool = False) -> dict:
    titles = [record["title"] for record in sheet_records]
    default_index = 0
    if default_title and default_title in titles:
        default_index = titles.index(default_title)
        if auto_select:
            for record in sheet_records:
                if record["title"] == default_title:
                    print(f"\n対象シート: {default_title}")
                    return record

    print("\nシート一覧:")
    for index, record in enumerate(sheet_records, start=1):
        print(f"  {index}. {record['title']}")
    selected_title = choose_from_list("どのシートを使いますか", titles, default_index=default_index)
    for record in sheet_records:
        if record["title"] == selected_title:
            return record
    raise ValueError("シートを選択できませんでした。")


def ask_target_column(headers: list[str], template: dict | None, non_interactive: bool) -> tuple[str, str]:
    mode = template.get("target_mode") if template else ""
    target_value = template.get("target_value") if template else ""

    if non_interactive and mode not in {"new_column", "existing_column"}:
        raise ValueError("テンプレートの target_mode が不正です。")

    if not non_interactive:
        print("\n重複結果の書き込み先:")
        print("  1. 新規列を末尾に追加する")
        print("  2. 既存列へ書き込む")
        while True:
            default_raw = "1" if mode == "new_column" else "2" if mode == "existing_column" else "1"
            raw = input(f"番号を選んでください [{default_raw}]: ").strip() or default_raw
            if raw == "1":
                mode = "new_column"
                break
            if raw == "2":
                mode = "existing_column"
                break
            print("1-2 を入力してください。")

    if mode == "existing_column":
        if target_value in headers:
            return mode, target_value
        if non_interactive:
            raise ValueError(f"テンプレートの既存列 '{target_value}' が見つかりません。")
        target_value = choose_from_list("どの既存列に書き込みますか", headers, default_index=max(0, len(headers) - 1))
        return mode, target_value

    if non_interactive:
        if not target_value:
            raise ValueError("テンプレートの新規列ヘッダが空です。")
        return mode, target_value

    default_header = target_value or "重複チェック"
    target_value = input(f"新規列のヘッダ名を入力してください [{default_header}]: ").strip() or default_header
    return mode, target_value


def find_first_matching_template(template: dict | None, headers: list[str], fallback: str | None = None, non_interactive: bool = False) -> str:
    if template and template.get("key_columns"):
        missing = [column for column in template["key_columns"] if column not in headers]
        if not missing:
            return ",".join(template["key_columns"])
        if non_interactive:
            raise ValueError(f"テンプレートの重複判定列が見つかりません: {', '.join(missing)}")
    if fallback and fallback in headers:
        return fallback
    return ""


def build_interactive_config(
    headers: list[str],
    template: dict | None,
    non_interactive: bool,
    cli_key_columns: list[str],
    cli_target_mode: str,
    cli_target_column: str,
) -> dict:
    default_indices = None
    uid_header = "uid"
    if template and template.get("key_columns"):
        mapped = []
        for column in template["key_columns"]:
            if column in headers:
                mapped.append(headers.index(column))
        if mapped:
            default_indices = mapped
    elif uid_header in headers:
        default_indices = [headers.index(uid_header)]
    elif headers:
        default_indices = [0]

    if cli_key_columns:
        key_columns = cli_key_columns
    elif non_interactive:
        key_columns = template.get("key_columns", []) if template else []
        if not key_columns:
            raise ValueError("テンプレートの重複判定列が空です。")
    else:
        key_columns = choose_multiple_from_list("重複判定に使う列を選んでください。", headers, default_indices=default_indices)

    exclude_all_blank = True
    if template and "exclude_all_blank" in template:
        exclude_all_blank = bool(template["exclude_all_blank"])
    if not non_interactive:
        exclude_all_blank = ask_yes_no("選択列がすべて空欄の行は除外しますか？", default=exclude_all_blank)

    if cli_target_mode and cli_target_column:
        target_mode, target_value = cli_target_mode, cli_target_column
    else:
        target_mode, target_value = ask_target_column(headers, template, non_interactive)
    return {
        "key_columns": key_columns,
        "exclude_all_blank": exclude_all_blank,
        "target_mode": target_mode,
        "target_value": target_value,
    }


def ensure_existing_column_overwrite_ok(rows: list[dict], target_column: str, non_interactive: bool):
    existing_values = [normalize_value(row.get(target_column, "")) for row in rows]
    filled = sum(1 for value in existing_values if value != "")
    if filled == 0:
        return
    if non_interactive:
        return
    print(f"\n既存列 '{target_column}' にはすでに {filled} 件の値があります。")
    if not ask_yes_no("上書きして続けますか？", default=False):
        raise RuntimeError("既存列の上書きをキャンセルしました。")


def resolve_target_column(sheet_record: dict, headers: list[str], target_mode: str, target_value: str) -> tuple[int, str, bool]:
    if target_mode == "existing_column":
        if target_value not in headers:
            raise ValueError(f"既存列 '{target_value}' が見つかりません。")
        return headers.index(target_value), target_value, False

    properties = sheet_record["properties"]
    column_count = int(properties.get("gridProperties", {}).get("columnCount", len(headers)))
    return column_count, target_value, True


def apply_duplicate_status(
    spreadsheet_id: str,
    sheet_record: dict,
    rows: list[dict],
    target_column_index: int,
    target_header: str,
    values: list[list[str]],
    create_new_column: bool,
):
    if create_new_column:
        append_column(spreadsheet_id, int(sheet_record["properties"]["sheetId"]))

    column_letter = column_index_to_letter(target_column_index)
    sheet_range = quote_sheet_title(sheet_record["title"])
    updates = [
        {
            "range": f"{sheet_range}!{column_letter}1",
            "values": [[target_header]],
        },
        {
            "range": f"{sheet_range}!{column_letter}2:{column_letter}{len(values) + 1}",
            "values": values,
        },
    ]
    write_values(spreadsheet_id, updates)
    print(f"\n書き込み完了: {sheet_record['title']}!{column_letter}1:{column_letter}{len(values) + 1}")


def build_sheet_records(metadata: dict) -> list[dict]:
    records = []
    for sheet in metadata.get("sheets", []):
        properties = sheet.get("properties", {})
        records.append(
            {
                "title": properties.get("title", ""),
                "properties": properties,
            }
        )
    if not records:
        raise ValueError("シート一覧を取得できませんでした。")
    return records


def main():
    parser = argparse.ArgumentParser(description="gws CLI で Google Sheets の重複チェックを行う")
    parser.add_argument("--spreadsheet-url", default="")
    parser.add_argument("--template-name", default="")
    parser.add_argument("--apply-write", action="store_true")
    parser.add_argument("--sheet-name", default="")
    parser.add_argument("--key-columns", default="")
    parser.add_argument("--target-mode", choices=["new_column", "existing_column"], default="")
    parser.add_argument("--target-column", default="")
    args = parser.parse_args()

    has_explicit_config = bool(args.sheet_name and args.key_columns and args.target_mode and args.target_column)
    mode = choose_start_mode(args.template_name, has_explicit_config)
    spreadsheet_url = args.spreadsheet_url or input("スプレッドシートURLを入力してください: ").strip()
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)
    gid = extract_gid(spreadsheet_url)

    metadata = fetch_metadata(spreadsheet_id)
    title = metadata.get("properties", {}).get("title", "Google Spreadsheet")
    sheet_records = build_sheet_records(metadata)
    default_sheet_title = None
    if gid is not None:
        for record in sheet_records:
            if int(record["properties"].get("sheetId", -1)) == gid:
                default_sheet_title = record["title"]
                break

    print(f"\nスプレッドシート: {title}")

    template = None
    non_interactive = has_explicit_config
    if mode == "template":
        template = choose_template(args.template_name)
        if template is None:
            mode = "new"
        else:
            non_interactive = bool(args.template_name and args.apply_write)

    selected_sheet = choose_sheet(
        sheet_records,
        default_title=(
            args.sheet_name
            or (template.get("selected_sheet") if template and template.get("selected_sheet") else default_sheet_title)
        ),
        auto_select=bool(args.sheet_name or (args.template_name and args.apply_write)),
    )
    payload = fetch_values(spreadsheet_id, quote_sheet_title(selected_sheet["title"]))
    headers, rows = load_rows(payload)
    preview_rows(headers, rows)

    cli_key_columns = [column.strip() for column in args.key_columns.split(",") if column.strip()]
    if cli_key_columns:
        missing = [column for column in cli_key_columns if column not in headers]
        if missing:
            raise ValueError(f"指定された重複判定列が見つかりません: {', '.join(missing)}")
    config = build_interactive_config(
        headers,
        template if mode == "template" else None,
        non_interactive,
        cli_key_columns,
        args.target_mode,
        args.target_column,
    )

    duplicate_groups, skipped = build_duplicate_groups(rows, config["key_columns"], config["exclude_all_blank"])
    print_duplicate_summary(duplicate_groups, config["key_columns"], rows, skipped)

    target_index, target_header, create_new_column = resolve_target_column(
        selected_sheet,
        headers,
        config["target_mode"],
        config["target_value"],
    )
    if not create_new_column:
        ensure_existing_column_overwrite_ok(rows, target_header, non_interactive)

    preserve_non_duplicates = config["target_mode"] == "existing_column"
    status_values, anomaly_rows = build_write_plan(
        rows,
        config["key_columns"],
        duplicate_groups,
        config["exclude_all_blank"],
        target_header,
        preserve_non_duplicates=preserve_non_duplicates,
    )
    report_path = save_anomaly_report(title, selected_sheet["title"], config["key_columns"], anomaly_rows)
    print(f"\nレポート保存: {report_path}")

    should_write = args.apply_write if non_interactive else ask_yes_no("この内容をシートへ書き込みますか？", default=True)
    if should_write:
        apply_duplicate_status(
            spreadsheet_id,
            selected_sheet,
            rows,
            target_index,
            target_header,
            status_values,
            create_new_column,
        )
    else:
        print("\nシートへの書き込みはスキップしました。")

    template_config = {
        "selected_sheet": selected_sheet["title"],
        "key_columns": config["key_columns"],
        "exclude_all_blank": config["exclude_all_blank"],
        "target_mode": config["target_mode"],
        "target_value": config["target_value"],
    }
    if not non_interactive and ask_yes_no("今回の条件をテンプレート保存しますか？", default=False):
        save_template(template_config)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nキャンセルしました。", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
