#!/usr/bin/env python3
"""
align_subtitles_to_audio.py — 字幕音声タイミング同期（Forced Alignment）

faster-whisper の word_timestamps を使い、SUBTITLE_TIMELINE の各エントリの
from/to フレームを実際の発話開始タイミングに合わせて修正する。

sync_subtitles_to_audio.py がセクション内で「文字数比例」で分配した
タイミングのズレを解消するのが主な用途。

Usage:
  python align_subtitles_to_audio.py \\
    --audio  path/to/narration.wav \\
    --ts     path/to/generated/Title.ts \\
    [--fps 30] [--model small] [--min-frames 30] [--search-window 3.0] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


# ──────────────────────────────────────────────────────────────
# テキスト正規化
# ──────────────────────────────────────────────────────────────

def normalize_ja(text: str) -> str:
    """比較用に記号・空白・改行を除去して正規化"""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'[\s\n\r「」『』【】（）()、。！？!?・〜~ー…]', '', text)
    return text


# ──────────────────────────────────────────────────────────────
# .ts ファイルの解析
# ──────────────────────────────────────────────────────────────

def parse_ts_entries(content: str) -> list[dict]:
    """SUBTITLE_TIMELINE の各エントリを解析して返す"""
    pattern = r'(\{\s*from:\s*(\d+),\s*to:\s*(\d+),\s*text:\s*"((?:[^"\\]|\\.)*)"\s*\})'
    entries = []
    for m in re.finditer(pattern, content):
        text = m.group(4).replace('\\n', '\n')
        entries.append({
            'orig_str': m.group(1),
            'from': int(m.group(2)),
            'to': int(m.group(3)),
            'text': text,
            'norm': normalize_ja(text),
            'span': (m.start(), m.end()),
        })
    return entries


# ──────────────────────────────────────────────────────────────
# Whisper 実行
# ──────────────────────────────────────────────────────────────

def run_whisper(audio_path: str, model_size: str = 'small') -> list[dict]:
    """faster-whisper で単語レベルタイムスタンプを取得"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit(
            "[error] faster_whisper が見つかりません。\n"
            "  pip install faster-whisper でインストールしてください。"
        )

    print(f"[align] モデル {model_size} を読み込み中...", flush=True)
    model = WhisperModel(model_size, device='cpu', compute_type='int8')

    print(f"[align] 音声を解析中: {audio_path}", flush=True)
    segments_gen, _ = model.transcribe(
        audio_path,
        language='ja',
        word_timestamps=True,
        beam_size=5,
        vad_filter=True,
        vad_parameters={'min_silence_duration_ms': 80},
    )

    words = []
    for seg in segments_gen:
        if seg.words:
            for w in seg.words:
                norm = normalize_ja(w.word)
                if norm:
                    words.append({
                        'raw': w.word.strip(),
                        'norm': norm,
                        'start': w.start,
                        'end': w.end,
                    })

    print(f"[align] {len(words)} 単語を検出", flush=True)
    return words


# ──────────────────────────────────────────────────────────────
# 文字レベルタイムライン構築
# ──────────────────────────────────────────────────────────────

def build_char_timeline(words: list[dict]) -> list[dict]:
    """単語タイムラインから文字単位のタイムラインを構築"""
    chars = []
    for w in words:
        n = len(w['norm'])
        dur = w['end'] - w['start']
        for i, ch in enumerate(w['norm']):
            chars.append({
                'char': ch,
                'start': w['start'] + dur * i / n,
                'end':   w['start'] + dur * (i + 1) / n,
            })
    return chars


# ──────────────────────────────────────────────────────────────
# 字幕テキストの開始時刻を推定
# ──────────────────────────────────────────────────────────────

def find_start_time(
    norm_text: str,
    chars: list[dict],
    expected_sec: float,
    search_window: float = 3.0,
    match_len: int = 3,
) -> float | None:
    """
    norm_text の先頭 match_len 文字を char_timeline で連続マッチし、
    expected_sec の前後 search_window 秒以内で最も近い候補を返す。
    連続マッチに失敗した場合は先頭1文字フォールバック。
    """
    if not norm_text or not chars:
        return None

    target = norm_text[:match_len]
    n = len(target)
    best_time = None
    best_dist = float('inf')

    # 連続マッチ（先頭 n 文字が連続して出現する位置を探す）
    for i in range(len(chars) - n + 1):
        window = [chars[i + k]['char'] for k in range(n)]
        if window == list(target):
            t = chars[i]['start']
            dist = abs(t - expected_sec)
            if dist < best_dist and dist <= search_window:
                best_dist = dist
                best_time = t

    if best_time is not None:
        return best_time

    # 連続マッチ失敗時 → 先頭1文字フォールバック（精度低）
    first_char = norm_text[0]
    for c in chars:
        if c['char'] != first_char:
            continue
        dist = abs(c['start'] - expected_sec)
        if dist < best_dist and dist <= search_window:
            best_dist = dist
            best_time = c['start']

    return best_time


# ──────────────────────────────────────────────────────────────
# メイン処理
# ──────────────────────────────────────────────────────────────

NAME_CARD_PATTERN = re.compile(r'^[1-9]\.')

def align(
    audio_path: str,
    ts_path: str,
    fps: int = 30,
    min_frames: int = 30,
    max_shift_frames: int = 45,
    search_window: float = 3.0,
    dry_run: bool = False,
    model_size: str = 'small',
) -> None:
    """
    max_shift_frames: この値を超えるシフトは誤検出とみなし元の値を保持する
    """

    content = Path(ts_path).read_text(encoding='utf-8')
    entries = parse_ts_entries(content)

    if not entries:
        print('[align] SUBTITLE_TIMELINE エントリが見つかりません。')
        return

    print(f'[align] {len(entries)} エントリ読み込み済み')

    # totalFrames を最後のエントリの to から取得（上限キャップ用）
    total_frames = entries[-1]['to']

    words = run_whisper(audio_path, model_size)
    if not words:
        print('[align] 単語が検出されませんでした。処理を中断します。')
        return

    chars = build_char_timeline(words)

    # ─── 各エントリの新 from を計算 ───────────────────────────
    raw_froms: list[int | None] = []
    for entry in entries:
        # 名前カード（"1.名前"）はセクション境界に依存するためスキップ
        if NAME_CARD_PATTERN.match(entry['norm']):
            raw_froms.append(None)
            continue
        expected_sec = entry['from'] / fps
        t = find_start_time(entry['norm'], chars, expected_sec, search_window)
        if t is not None:
            candidate = round(t * fps)
            shift = abs(candidate - entry['from'])
            if shift > max_shift_frames:
                raw_froms.append(None)
                print(f"  [skip] シフト大きすぎ({shift}f > {max_shift_frames}f): {entry['text'][:12]!r}")
            else:
                raw_froms.append(candidate)
        else:
            raw_froms.append(None)
            print(f"  [warn] アライメント失敗: {entry['text'][:12]!r}")

    # ─── 単調増加制約（逆行を防ぐ） ──────────────────────────
    # ※ アライメント失敗エントリも prev_from との比較を必ず行う
    new_froms: list[int] = []
    prev_from = 0
    for i, (entry, rf) in enumerate(zip(entries, raw_froms)):
        if rf is None:
            # アライメント失敗 → 元の from を使うが、逆行だけは防ぐ
            nf = max(entry['from'], prev_from)
        else:
            nf = max(rf, prev_from)
            if nf < entry['from'] - max_shift_frames:
                nf = max(entry['from'], prev_from)
        new_froms.append(nf)
        prev_from = nf

    # ─── 新 to を計算（重複しないよう next_from を最優先） ────────
    new_tos: list[int] = []
    for i, entry in enumerate(entries):
        orig_dur = entry['to'] - entry['from']
        proposed_to = new_froms[i] + orig_dur
        if i + 1 < len(entries):
            next_from = new_froms[i + 1]
            # 次エントリ開始を絶対に超えない（オーバーラップ禁止）
            proposed_to = min(proposed_to, next_from)
            # min_frames 保証は「次エントリまで十分余裕がある場合のみ」
            if next_from >= new_froms[i] + min_frames:
                proposed_to = max(proposed_to, new_froms[i] + min_frames)
        else:
            # 最終エントリ: totalFrames でキャップしつつ min_frames 保証
            proposed_to = min(proposed_to, total_frames)
            proposed_to = max(proposed_to, min(new_froms[i] + min_frames, total_frames))
        new_tos.append(proposed_to)

    # ─── 後処理: 表示時間が短すぎるエントリは元に戻す（収束まで繰り返す）
    # (単調増加制約のカスケードで min_frames 未満になった場合)
    half_min = min_frames // 2
    max_passes = 5
    for _pass in range(max_passes):
        reverted_any = False
        for i, entry in enumerate(entries):
            dur = new_tos[i] - new_froms[i]
            if dur < half_min:
                new_froms[i] = entry['from']
                new_tos[i] = entry['to']
                if i > 0 and new_tos[i - 1] > new_froms[i]:
                    new_tos[i - 1] = new_froms[i]
                print(f"  [revert] 表示時間 {dur}f < {half_min}f: {entry['text'][:12]!r} → 元タイミングに戻す")
                reverted_any = True
        if not reverted_any:
            break

    # ─── 差分表示 ───────────────────────────────────────────
    changes = [
        (e, nf, nt)
        for e, nf, nt in zip(entries, new_froms, new_tos)
        if nf != e['from'] or nt != e['to']
    ]

    print(f'\n[align] {len(changes)}/{len(entries)} エントリを更新:')
    for entry, nf, nt in changes:
        df = nf - entry['from']
        dt = nt - entry['to']
        label = entry['text'].replace('\n', '↵')[:14]
        print(
            f"  {label:16s}  "
            f"from {entry['from']:4d}→{nf:4d} ({df:+d})  "
            f"to   {entry['to']:4d}→{nt:4d} ({dt:+d})"
        )

    if not changes:
        print('[align] 修正不要。')

    if dry_run:
        print('\n[dry-run] ファイルへの書き込みはしません。')
        return

    if not changes:
        return

    # ─── ファイルを更新（後ろから置換して位置ズレを防ぐ） ────
    new_content = content
    for entry, nf, nt in sorted(changes, key=lambda x: x[0]['span'][0], reverse=True):
        start, end = entry['span']
        old_str = new_content[start:end]
        new_str = (
            old_str
            .replace(f"from: {entry['from']}", f"from: {nf}", 1)
            .replace(f"to: {entry['to']}", f"to: {nt}", 1)
        )
        new_content = new_content[:start] + new_str + new_content[end:]

    backup_path = Path(ts_path).with_suffix('.ts.before_align')
    backup_path.write_text(content, encoding='utf-8')
    Path(ts_path).write_text(new_content, encoding='utf-8')

    print(f'\n[align] 更新完了: {ts_path}')
    print(f'[align] バックアップ: {backup_path}')


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='字幕タイムラインを音声に forced alignment で同期する'
    )
    parser.add_argument('--audio', required=True, help='narration.wav のパス')
    parser.add_argument('--ts',    required=True, help='generated/Title.ts のパス')
    parser.add_argument('--fps',   type=int,   default=30,  help='フレームレート (default: 30)')
    parser.add_argument('--min-frames', type=int, default=30, help='字幕最小表示フレーム (default: 30)')
    parser.add_argument('--max-shift-frames', type=int, default=45,
                        help='これを超えるシフトは誤検出として棄却 (default: 45)')
    parser.add_argument('--search-window', type=float, default=3.0,
                        help='expected位置からの探索範囲(秒) (default: 3.0)')
    parser.add_argument('--model', default='small',
                        help='Whisperモデルサイズ: tiny/base/small/medium (default: small)')
    parser.add_argument('--dry-run', action='store_true', help='結果表示のみ・書き込みなし')
    args = parser.parse_args()

    align(
        audio_path=args.audio,
        ts_path=args.ts,
        fps=args.fps,
        min_frames=args.min_frames,
        max_shift_frames=args.max_shift_frames,
        search_window=args.search_window,
        dry_run=args.dry_run,
        model_size=args.model,
    )
