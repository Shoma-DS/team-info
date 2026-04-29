"""
営業文字起こし取得・保存スクリプト
AI分析はClaude Code / Codex が担当するため、このスクリプトはデータ取得と保存のみを行う。
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from classify import (
    classify_session_context,
    classify_speaker,
    classify_type,
    metadata_summary_json,
)
from save_transcript import (
    build_supabase_record,
    load_loom_export,
    save_transcript,
    upsert_supabase_record,
)


def process_url(loom_url: str) -> dict:
    results = {"url": loom_url, "steps": {}, "files": {}}
    today = date.today().isoformat()

    print(f"\n{'='*50}")
    print(f"処理開始: {loom_url}")
    print(f"{'='*50}")

    # Step 1: 文字起こし取得
    print("\n[1/3] Loom APIから文字起こしを取得中...")
    try:
        transcript, video_id = fetch_transcript_for_url(loom_url)
        print(f"      取得完了（文字数: {len(transcript)}）")
        results["steps"]["fetch"] = "OK"
    except Exception as e:
        print(f"      失敗: {e}")
        results["steps"]["fetch"] = f"失敗: {e}"
        return results

    # Step 2: キーワードベースで種別・話者を簡易判別
    print("\n[2/3] 種別・話者を判別中...")
    type_result = classify_type(transcript)
    speaker_result = classify_speaker(transcript)
    session_result = classify_session_context(transcript)
    type_ = type_result.get("type", "unknown")
    speaker = speaker_result.get("speaker", "unknown")
    print(f"      種別: {type_} （信頼度: {type_result.get('confidence')}%）")
    print(f"      担当者: {speaker_result.get('display_name', speaker)} （信頼度: {speaker_result.get('confidence')}%）")
    print(f"      セッション: {session_result.get('session_kind')} / タグ: {', '.join(session_result.get('tags', [])) or '-'}")
    if type_result.get("confidence", 0) < 60 or speaker_result.get("confidence", 0) < 60:
        print("      ⚠ 信頼度が低いため、Claude Codeが内容を確認して修正します")
    results["steps"]["classify"] = "OK"

    # unknownのままでも保存はする
    if type_ == "unknown":
        type_ = "1s"
    if speaker == "unknown":
        speaker = "unknown"

    # Step 3: 文字起こし保存
    print("\n[3/3] 文字起こしを保存中...")
    try:
        transcript_path = save_transcript(
            transcript=transcript,
            loom_id=video_id,
            speaker=speaker,
            type_=type_,
            date_str=today,
            meta={
                "confidence_type": type_result.get("confidence", 0),
                "confidence_speaker": speaker_result.get("confidence", 0),
            },
            extra_meta={
                "facilitator_name": speaker_result.get("display_name", ""),
                "facilitator_role": speaker_result.get("role", ""),
                "organization_name": speaker_result.get("organization_name", ""),
                "session_summary": metadata_summary_json(speaker_result, session_result),
            },
        )
        print(f"      保存先: {transcript_path}")
        results["files"]["transcript"] = str(transcript_path)
        results["steps"]["save"] = "OK"
    except Exception as e:
        print(f"      失敗: {e}")
        results["steps"]["save"] = f"失敗: {e}"
        return results

    return results


def process_export_dir(export_dir: str, sync_supabase: bool, supabase_table: str | None) -> dict:
    results = {"export_dir": export_dir, "steps": {}, "files": {}}
    today = date.today().isoformat()

    print(f"\n{'='*50}")
    print(f"処理開始: {export_dir}")
    print(f"{'='*50}")

    print("\n[1/4] Loom MCP export を読み込み中...")
    try:
        export_data = load_loom_export(Path(export_dir))
        transcript = export_data["transcript"]
        video_id = export_data["loom_id"]
        print(f"      読み込み完了（文字数: {len(transcript)}）")
        results["steps"]["load_export"] = "OK"
    except Exception as e:
        print(f"      失敗: {e}")
        results["steps"]["load_export"] = f"失敗: {e}"
        return results

    print("\n[2/4] 種別・話者を判別中...")
    type_result = classify_type(transcript)
    speaker_result = classify_speaker(transcript)
    session_result = classify_session_context(
        transcript,
        video_name=export_data.get("video_name", ""),
    )
    type_ = type_result.get("type", "unknown")
    speaker = speaker_result.get("speaker", "unknown")
    print(f"      種別: {type_} （信頼度: {type_result.get('confidence')}%）")
    print(f"      担当者: {speaker_result.get('display_name', speaker)} （信頼度: {speaker_result.get('confidence')}%）")
    print(f"      セッション: {session_result.get('session_kind')} / タグ: {', '.join(session_result.get('tags', [])) or '-'}")
    if type_result.get("confidence", 0) < 60 or speaker_result.get("confidence", 0) < 60:
        print("      ⚠ 信頼度が低いため、Codex が内容を確認して修正してください")
    results["steps"]["classify"] = "OK"

    if type_ == "unknown":
        type_ = "1s"

    print("\n[3/4] 文字起こしを保存中...")
    try:
        transcript_path = save_transcript(
            transcript=transcript,
            loom_id=video_id,
            speaker=speaker,
            type_=type_,
            date_str=today,
            meta={
                "confidence_type": type_result.get("confidence", 0),
                "confidence_speaker": speaker_result.get("confidence", 0),
            },
            extra_meta={
                "source": "loom_mcp",
                "video_name": export_data.get("video_name", ""),
                "recorded_at": export_data.get("recorded_at", ""),
                "loom_owner_name": export_data.get("owner_name", ""),
                "facilitator_name": speaker_result.get("display_name", ""),
                "facilitator_role": speaker_result.get("role", ""),
                "organization_name": speaker_result.get("organization_name", ""),
                "session_summary": metadata_summary_json(speaker_result, session_result),
            },
        )
        print(f"      保存先: {transcript_path}")
        results["files"]["transcript"] = str(transcript_path)
        results["steps"]["save"] = "OK"
    except Exception as e:
        print(f"      失敗: {e}")
        results["steps"]["save"] = f"失敗: {e}"
        return results

    if not sync_supabase:
        return results

    print("\n[4/4] Supabase に登録中...")
    try:
        record = build_supabase_record(
            export_data=export_data,
            transcript_path=transcript_path,
            speaker=speaker,
            type_=type_,
            type_result=type_result,
            speaker_result=speaker_result,
            session_result=session_result,
            processed_date=today,
        )
        saved = upsert_supabase_record(record, table_name=supabase_table)
        target_table = supabase_table or os.environ.get("SUPABASE_TABLE", "sales_coaching_transcripts")
        print(f"      登録完了: {target_table}")
        if isinstance(saved, dict) and saved.get("loom_video_id"):
            print(f"      loom_video_id: {saved['loom_video_id']}")
        results["steps"]["supabase"] = "OK"
        results["files"]["supabase_table"] = target_table
    except Exception as e:
        print(f"      失敗: {e}")
        results["steps"]["supabase"] = f"失敗: {e}"

    return results


def fetch_transcript_for_url(loom_url: str) -> tuple[str, str]:
    from fetch_loom import fetch_transcript, get_video_id

    return fetch_transcript(loom_url), get_video_id(loom_url)


def main():
    parser = argparse.ArgumentParser(
        description="Loom文字起こし取得・保存（AI分析はClaude Codeが担当）"
    )
    parser.add_argument("--url", help="Loom動画URL（1件）")
    parser.add_argument("--url-file", help="LoomURL一覧ファイル（1行1URL）")
    parser.add_argument(
        "--loom-export-dir",
        action="append",
        help="Loom MCP が保存した export ディレクトリ。metadata.json と transcript.txt を含む",
    )
    parser.add_argument(
        "--sync-supabase",
        action="store_true",
        help="ローカル保存後に Supabase へ upsert する",
    )
    parser.add_argument(
        "--supabase-table",
        help="Supabase の登録先テーブル名。未指定時は SUPABASE_TABLE または sales_coaching_transcripts",
    )
    args = parser.parse_args()

    jobs: list[tuple[str, str]] = []
    if args.url:
        jobs.append(("url", args.url))
    if args.url_file:
        url_file = Path(args.url_file)
        if not url_file.exists():
            print(f"エラー: ファイルが見つかりません: {args.url_file}")
            sys.exit(1)
        jobs.extend(
            ("url", line.strip())
            for line in url_file.read_text().splitlines()
            if line.strip()
        )
    if args.loom_export_dir:
        jobs.extend(("export", path) for path in args.loom_export_dir if path.strip())

    if not jobs:
        parser.print_help()
        sys.exit(1)

    all_results = []
    for kind, value in jobs:
        if kind == "url":
            result = process_url(value)
        else:
            result = process_export_dir(
                value,
                sync_supabase=args.sync_supabase,
                supabase_table=args.supabase_table,
            )
        all_results.append(result)

    print(f"\n{'='*50}")
    print("取得完了サマリー")
    print(f"{'='*50}")
    for r in all_results:
        success = all(v == "OK" for v in r["steps"].values())
        status = "成功" if success else "一部失敗"
        label = r.get("url") or r.get("export_dir") or "unknown"
        print(f"\n{label} → {status}")
        for step, res in r["steps"].items():
            mark = "✓" if res == "OK" else "✗"
            print(f"  {mark} {step}: {res}")
        if r.get("files"):
            print("\n  次のステップ: Claude Codeに以下を渡してください")
            for label, path in r["files"].items():
                print(f"    {path}")

    print("\n" + "="*50)
    print("Claude Codeへの指示例:")
    print("  「personal/deguchishouma/sales/coaching/transcripts/ の新しいファイルを分析して」")
    print("="*50)


if __name__ == "__main__":
    main()
