"""
Layer 2.5: BGM・効果音解析
- librosa で音声特徴量を抽出
- BGM区間（持続的な音楽）を調波打楽器分離で検出
- 効果音（SFX）をオンセット検出で分類
- ビートタイミングとテンポを検出
- 音量エネルギーの時系列を生成

出力フォーマット:
{
  "bgm_segments":   [{ "start", "end", "energy" }],         # BGM区間
  "sfx_events":     [{ "time", "type", "energy" }],         # 効果音イベント
  "beat_times":     [float, ...],                            # ビートの時刻（秒）
  "dominant_tempo": float,                                   # 支配的テンポ（BPM）
  "music_coverage": float,                                   # BGMが占める割合 0-1
  "energy_timeline":[{ "time", "energy" }],                  # 0.5秒ごとの音量
}
"""
from __future__ import annotations

from pathlib import Path


# ─── ユーティリティ ───────────────────────────────────────────────────────────

def _get_audio_path(output_dir: Path) -> Path:
    """speech_analysis が生成した audio.wav を再利用する"""
    audio_path = output_dir / "audio.wav"
    if not audio_path.exists():
        raise FileNotFoundError(
            f"audio.wav が見つかりません: {audio_path}\n"
            "speech_analysis (Layer 2) を先に実行してください。"
        )
    return audio_path


def _classify_sfx(spectral_centroid: float, onset_energy: float) -> str:
    """スペクトル重心と音量から効果音タイプを推定する"""
    if spectral_centroid > 4000:
        return "chime"       # チン・ベル系（高域）
    elif spectral_centroid < 800:
        return "impact"      # ドン・ドーン系（低域）
    elif onset_energy > 0.7:
        return "transition"  # 強めの遷移音
    else:
        return "whoosh"      # シュッ・スライド系（中域）


def _deduplicate_events(events: list[dict], min_gap: float = 0.3) -> list[dict]:
    """連続して検出された近接イベントをひとつにまとめる"""
    result: list[dict] = []
    for ev in events:
        if not result or ev["time"] - result[-1]["time"] > min_gap:
            result.append(ev)
    return result


# ─── メイン解析 ───────────────────────────────────────────────────────────────

def analyze_audio_scene(output_dir: Path) -> dict:
    """Layer 2.5 エントリポイント"""
    try:
        import librosa
        import numpy as np
    except ImportError:
        print("    ⚠️  librosa が未インストールのため BGM/SFX 解析をスキップします")
        print("       (pip install librosa でインストール後に再解析できます)")
        return _empty_result()

    audio_path = _get_audio_path(output_dir)

    # ─── 1. 音声ロード ──────────────────────────────────────────────────────
    sr = 22050
    y, _ = librosa.load(str(audio_path), sr=sr)

    # ─── 2. 共通フレームパラメータ ────────────────────────────────────────
    hop_length = 512
    frame_length = 2048

    # ─── 3. 全体 RMS エネルギー ───────────────────────────────────────────
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    frame_times = librosa.frames_to_time(
        np.arange(len(rms)), sr=sr, hop_length=hop_length
    )
    rms_norm = rms / (rms.max() + 1e-8)

    # ─── 4. エネルギータイムライン（0.5秒ごと） ──────────────────────────
    sample_interval = 0.5
    total_duration = float(frame_times[-1]) if len(frame_times) > 0 else 0.0
    energy_timeline: list[dict] = []
    for t in np.arange(0, total_duration, sample_interval):
        idx = int(np.searchsorted(frame_times, t))
        if idx < len(rms_norm):
            energy_timeline.append({
                "time": round(float(t), 2),
                "energy": round(float(rms_norm[idx]), 3),
            })

    # ─── 5. ビート検出 ────────────────────────────────────────────────────
    try:
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
        beat_times = [
            round(float(t), 3)
            for t in librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
        ]
        dominant_tempo = round(float(tempo), 1)
    except Exception:
        beat_times = []
        dominant_tempo = 0.0

    # ─── 6. 調波打楽器分離（BGM / 打楽器を分離） ─────────────────────────
    try:
        y_harmonic, _ = librosa.effects.hpss(y)
        bgm_rms = librosa.feature.rms(
            y=y_harmonic, frame_length=frame_length, hop_length=hop_length
        )[0]
        # 全体 RMS で正規化
        bgm_rms_norm = bgm_rms / (rms.max() + 1e-8)
    except Exception:
        bgm_rms_norm = rms_norm * 0.5  # fallback: 全体エネルギーの半分を推定

    # BGMありと判断するエネルギー閾値
    bgm_threshold = 0.15
    bgm_mask = bgm_rms_norm > bgm_threshold

    # マスクから区間リストを生成
    bgm_segments: list[dict] = []
    in_seg = False
    seg_start = 0.0
    for i, (is_bgm, t) in enumerate(zip(bgm_mask, frame_times)):
        if is_bgm and not in_seg:
            seg_start = float(t)
            in_seg = True
        elif not is_bgm and in_seg:
            seg_end = float(t)
            if seg_end - seg_start >= 0.5:  # 0.5秒以上の区間のみ
                seg_e = float(np.mean(bgm_rms_norm[max(0, i - 10): i + 1]))
                bgm_segments.append({
                    "start": round(seg_start, 2),
                    "end": round(seg_end, 2),
                    "energy": "high" if seg_e > 0.5 else ("medium" if seg_e > 0.2 else "low"),
                })
            in_seg = False
    if in_seg and len(frame_times) > 0:
        seg_e = float(np.mean(bgm_rms_norm[-10:]))
        bgm_segments.append({
            "start": round(seg_start, 2),
            "end": round(total_duration, 2),
            "energy": "high" if seg_e > 0.5 else ("medium" if seg_e > 0.2 else "low"),
        })

    # BGM カバー率
    bgm_duration = sum(s["end"] - s["start"] for s in bgm_segments)
    music_coverage = round(bgm_duration / total_duration, 3) if total_duration > 0 else 0.0

    # ─── 7. 効果音（SFX）検出 ────────────────────────────────────────────
    # スペクトル重心（音質）
    sc = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    sc_times = librosa.frames_to_time(
        np.arange(len(sc)), sr=sr, hop_length=hop_length
    )

    # オンセット検出（突発的な音の開始）
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, units="frames", hop_length=hop_length
    )
    onset_times_arr = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

    sfx_events: list[dict] = []
    for onset_time in onset_times_arr:
        idx = int(np.searchsorted(frame_times, onset_time))
        if idx >= len(rms_norm):
            continue
        e = float(rms_norm[idx])

        # 静かすぎるオンセットを除外
        if e < 0.25:
            continue

        # 周囲との比較でスパイクか確認
        surr_start = max(0, idx - 8)
        surr_end = min(len(rms_norm), idx + 8)
        surr_mean = float(np.mean(rms_norm[surr_start:surr_end]))
        if e < surr_mean * 1.4:
            continue

        # スペクトル重心を取得
        sc_idx = int(np.searchsorted(sc_times, onset_time))
        centroid = float(sc[sc_idx]) if sc_idx < len(sc) else 1500.0

        sfx_events.append({
            "time": round(float(onset_time), 3),
            "type": _classify_sfx(centroid, e),
            "energy": round(e, 3),
        })

    sfx_events = _deduplicate_events(sfx_events, min_gap=0.3)

    return {
        "bgm_segments": bgm_segments,
        "sfx_events": sfx_events,
        "beat_times": beat_times[:120],  # 最大120ビットに制限
        "dominant_tempo": dominant_tempo,
        "music_coverage": music_coverage,
        "energy_timeline": energy_timeline,
    }


def _empty_result() -> dict:
    """librosa 未インストール時のフォールバック"""
    return {
        "bgm_segments": [],
        "sfx_events": [],
        "beat_times": [],
        "dominant_tempo": 0.0,
        "music_coverage": 0.0,
        "energy_timeline": [],
    }
