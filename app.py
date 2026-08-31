import base64
import hashlib
import hmac
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

try:
    from supabase import create_client
except Exception:
    create_client = None


# ============================================================
# App / secrets
# ============================================================
st.set_page_config(page_title="東京ぶらり旅", page_icon="🎥", layout="centered")

JST = timezone(timedelta(hours=9))
APP_BUILD = "video-rebuild-v1"


def secret(name: str, default: Any = None) -> Any:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


OPENAI_API_KEY = str(secret("OPENAI_API_KEY", "") or "").strip()
VISION_MODEL = str(secret("VISION_MODEL", "gpt-5.6-luna") or "gpt-5.6-luna").strip()
SUPABASE_URL = str(secret("SUPABASE_URL", "") or "").strip()
SUPABASE_SECRET_KEY = str(secret("SUPABASE_SECRET_KEY", "") or "").strip()
PHOTO_BUCKET = str(secret("PHOTO_BUCKET", "burari-photos") or "burari-photos").strip()
FAMILY_PIN = str(secret("FAMILY_PIN", "") or "").strip()
VIDEO_ROOT = str(secret("BURARI_VIDEO_ROOT", "video-v2") or "video-v2").strip().strip("/")
USE_FAST_MODE = str(secret("USE_FAST_MODE", "false") or "false").lower() in {"1", "true", "yes", "on"}

# Recording stops at 15.2 s. Browser/MediaRecorder timing can overshoot slightly,
# so the server accepts up to 16.5 s (= 165 frames at 10 fps).
VIDEO_RECORD_SECONDS = 15.2
VIDEO_ACCEPT_SECONDS = 16.5
VIDEO_SAMPLE_FPS = 10
VIDEO_MAX_FRAMES = int(VIDEO_ACCEPT_SECONDS * VIDEO_SAMPLE_FPS)
VIDEO_MAX_BYTES = 25 * 1024 * 1024
VIDEO_MAX_MOMENTS = 9
VIDEO_AI_BATCH_SIZE = 25
VIDEO_FINALIST_COUNT = 36
VIDEO_PROCESSING_VERSION = "storage-inline-ai-v1"

VIDEO_DIR = f"{VIDEO_ROOT}/videos"
META_DIR = f"{VIDEO_ROOT}/meta"
MOMENT_DIR = f"{VIDEO_ROOT}/moments"


st.markdown(
    """
    <style>
      .block-container {max-width: 820px; padding-top: 2.0rem; padding-bottom: 3rem;}
      .burari-hero {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        margin-bottom: 1rem;
      }
      .burari-title {font-size: 1.8rem; font-weight: 800; line-height: 1.15;}
      .burari-sub {opacity: .72; margin-top: .35rem; font-size: .92rem;}
      .status-card {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 16px;
        padding: .8rem .9rem;
        margin: .6rem 0;
      }
      @media (max-width: 640px) {
        .block-container {padding-left: .8rem; padding-right: .8rem; padding-top: 1.1rem;}
        .burari-title {font-size: 1.55rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Clients / setup
# ============================================================
@st.cache_resource(show_spinner=False)
def supabase_client():
    if create_client is None:
        raise RuntimeError("supabase ライブラリがありません。requirements.txt を確認してください。")
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SECRET_KEY が設定されていません。")
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


@st.cache_resource(show_spinner=False)
def openai_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY が設定されていません。")
    from openai import OpenAI

    return OpenAI(api_key=OPENAI_API_KEY)


def require_setup() -> None:
    if create_client is None:
        st.error("Supabaseライブラリがありません。requirements.txt を更新してください。")
        st.stop()
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        st.error("Streamlit Secrets の SUPABASE_URL / SUPABASE_SECRET_KEY を確認してください。")
        st.stop()
    if not OPENAI_API_KEY:
        st.error("Streamlit Secrets の OPENAI_API_KEY を確認してください。")
        st.stop()
    try:
        # A harmless list call verifies the bucket and credentials without changing data.
        supabase_client().storage.from_(PHOTO_BUCKET).list(path=VIDEO_ROOT)
    except Exception as exc:
        st.error(f"Supabase Storage『{PHOTO_BUCKET}』を利用できません。")
        with st.expander("保護者向け詳細", expanded=True):
            st.code(str(exc))
        st.stop()


def require_pin() -> None:
    if not FAMILY_PIN:
        return
    if st.session_state.get("_pin_ok"):
        return

    st.markdown('<div class="burari-hero"><div class="burari-title">東京ぶらり旅</div><div class="burari-sub">家族用のあいことばを入力してください。</div></div>', unsafe_allow_html=True)
    entered = st.text_input("あいことば", type="password", key="_family_pin_input")
    if st.button("はいる", type="primary", use_container_width=True):
        if entered and hmac.compare_digest(entered.strip(), FAMILY_PIN):
            st.session_state["_pin_ok"] = True
            st.rerun()
        st.error("あいことばが違います。")
    st.stop()


# ============================================================
# Storage helpers
# ============================================================
def _storage_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if hasattr(value, "read"):
        return value.read()
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(value or b"")


def _extract_first(obj: Any, keys: tuple[str, ...]) -> str:
    if isinstance(obj, dict):
        for key in keys:
            value = obj.get(key)
            if value:
                return str(value)
        data = obj.get("data")
        if isinstance(data, dict):
            return _extract_first(data, keys)
    for key in keys:
        try:
            value = getattr(obj, key, None)
            if value:
                return str(value)
        except Exception:
            pass
    return ""


def _normalize_storage_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("/"):
        return SUPABASE_URL.rstrip("/") + value
    return SUPABASE_URL.rstrip("/") + "/" + value.lstrip("/")


def create_signed_upload(path: str) -> str:
    response = supabase_client().storage.from_(PHOTO_BUCKET).create_signed_upload_url(path)
    url = _extract_first(response, ("signed_url", "signedUrl", "signedURL", "url"))
    url = _normalize_storage_url(url)
    if not url:
        raise RuntimeError("Supabaseが動画アップロード用URLを返しませんでした。")
    return url


def create_signed_download(path: str, expires_in: int = 3600) -> str:
    response = supabase_client().storage.from_(PHOTO_BUCKET).create_signed_url(path, expires_in)
    url = _extract_first(response, ("signed_url", "signedUrl", "signedURL", "url"))
    return _normalize_storage_url(url)


def storage_upload(path: str, raw: bytes, content_type: str, upsert: bool = False) -> None:
    bucket = supabase_client().storage.from_(PHOTO_BUCKET)
    options = {
        "content-type": content_type,
        "cache-control": "3600",
    }
    if upsert:
        options["upsert"] = "true"
    try:
        bucket.upload(path=path, file=raw, file_options=options)
    except Exception:
        if not upsert:
            raise
        # Some storage-py versions prefer update() for an existing object.
        try:
            bucket.update(path=path, file=raw, file_options=options)
        except Exception:
            raise


def storage_download(path: str) -> bytes:
    return _storage_bytes(supabase_client().storage.from_(PHOTO_BUCKET).download(path))


def storage_remove(paths: list[str]) -> None:
    clean = [str(p).strip() for p in paths if str(p).strip()]
    if clean:
        supabase_client().storage.from_(PHOTO_BUCKET).remove(clean)


def storage_list(path: str) -> list[dict]:
    try:
        rows = supabase_client().storage.from_(PHOTO_BUCKET).list(path=path)
        return [x for x in (rows or []) if isinstance(x, dict)]
    except Exception:
        return []


def now_iso() -> str:
    return datetime.now(JST).isoformat()


def new_video_id() -> str:
    return datetime.now(JST).strftime("%Y%m%dT%H%M%S_%f") + "_" + uuid.uuid4().hex[:8]


def meta_path(video_id: str) -> str:
    return f"{META_DIR}/{video_id}.json"


def video_path(video_id: str) -> str:
    return f"{VIDEO_DIR}/{video_id}.video"


def moment_folder(video_id: str) -> str:
    return f"{MOMENT_DIR}/{video_id}"


def write_meta(meta: dict) -> None:
    payload = dict(meta or {})
    payload["updated_at"] = now_iso()
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    storage_upload(meta_path(str(payload["video_id"])), raw, "application/json", upsert=True)


def read_meta(video_id: str) -> dict | None:
    try:
        raw = storage_download(meta_path(video_id))
        value = json.loads(raw.decode("utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def list_meta_ids() -> list[str]:
    ids = []
    for row in storage_list(META_DIR):
        name = str(row.get("name") or "")
        if name.endswith(".json"):
            ids.append(name[:-5])
    return sorted(set(ids), reverse=True)


def list_video_ids() -> list[str]:
    ids = []
    for row in storage_list(VIDEO_DIR):
        name = str(row.get("name") or "")
        if name.endswith(".video"):
            ids.append(name[:-6])
    return sorted(set(ids), reverse=True)


# ============================================================
# FFmpeg frame extraction
# ============================================================
def ffmpeg_executable() -> str:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg

        candidate = str(imageio_ffmpeg.get_ffmpeg_exe() or "").strip()
        if candidate and os.path.exists(candidate):
            return candidate
    except Exception:
        pass
    return ""


def extract_all_frames(video_raw: bytes) -> list[dict]:
    """Extract every 0.1-second frame. No pre-AI quality filtering is performed."""
    exe = ffmpeg_executable()
    if not exe:
        raise RuntimeError("ffmpegを利用できません。requirements.txt に imageio-ffmpeg を追加してください。")

    with tempfile.TemporaryDirectory(prefix="burari_video_") as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "original.video"
        frame_pattern = tmpdir / "frame_%03d.jpg"
        input_path.write_bytes(video_raw)

        cmd = [
            exe,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
            "-t",
            str(VIDEO_ACCEPT_SECONDS),
            "-vf",
            f"fps={VIDEO_SAMPLE_FPS}",
            "-q:v",
            "2",
            str(frame_pattern),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, check=False)
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace")[-1600:]
            raise RuntimeError("動画から画像を切り出せませんでした。" + (f"\n{detail}" if detail else ""))

        paths = sorted(tmpdir.glob("frame_*.jpg"))
        if not paths:
            raise RuntimeError("動画から有効なフレームを取得できませんでした。")
        if len(paths) > VIDEO_MAX_FRAMES:
            raise RuntimeError("動画が長すぎます。最大15秒程度の動画にしてください。")

        frames = []
        for index, path in enumerate(paths, start=1):
            raw = path.read_bytes()
            if not raw:
                continue
            frames.append(
                {
                    "frame_id": f"F{index:03d}",
                    "timestamp_ms": (index - 1) * 100,
                    "image_bytes": raw,
                    "ai_bytes": make_ai_copy(raw),
                }
            )
        if not frames:
            raise RuntimeError("動画から有効なフレームを取得できませんでした。")
        return frames


def make_ai_copy(raw: bytes, max_side: int = 512, quality: int = 72) -> bytes:
    with Image.open(io.BytesIO(raw)) as img:
        rgb = img.convert("RGB")
        rgb.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        rgb.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()


def data_url_jpeg(raw: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


# ============================================================
# AI selection
# ============================================================
def response_args(model: str, input_value: list[dict], schema_name: str, schema: dict, max_output_tokens: int) -> dict:
    args = {
        "model": model,
        "input": input_value,
        "reasoning": {"effort": "none"},
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            }
        },
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    if USE_FAST_MODE:
        args["service_tier"] = "fast"
    return args


def create_ai_response(args: dict):
    """Call Responses API; if optional fast tier is unavailable, retry normally."""
    try:
        return openai_client().responses.create(**args)
    except Exception:
        if args.get("service_tier") == "fast":
            retry_args = dict(args)
            retry_args.pop("service_tier", None)
            return openai_client().responses.create(**retry_args)
        raise


def parse_json_response(response: Any) -> dict:
    text = str(getattr(response, "output_text", "") or "").strip()
    if not text:
        raise RuntimeError("AIの応答が空でした。")
    value = json.loads(text)
    if not isinstance(value, dict):
        raise RuntimeError("AIの応答形式が不正です。")
    return value


def evaluate_frame_batch(frames: list[dict]) -> dict[str, int]:
    """AI sees every frame in the batch. Returns an AI score for each frame."""
    if not frames:
        return {}

    schema = {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "minItems": len(frames),
                "maxItems": len(frames),
                "items": {
                    "type": "object",
                    "properties": {
                        "frame_id": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    },
                    "required": ["frame_id", "score"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["scores"],
        "additionalProperties": False,
    }

    ids = ", ".join(str(x["frame_id"]) for x in frames)
    prompt = (
        "短い動画から写真として残す『いい瞬間』を探します。"
        "このバッチに含まれる全フレームを必ず1枚ずつ評価してください。"
        "先に候補を間引かず、各画像について、ピント・ブレ・構図・光・色・被写体・表情や動作・決定的瞬間・写真としての魅力を総合して0〜100点を付けます。"
        "近い時刻の画像でも省略しないでください。"
        f"対象ID: {ids}。scoresには対象IDを重複なく全件返してください。"
    )

    content = [{"type": "input_text", "text": prompt}]
    for frame in frames:
        content.append({
            "type": "input_text",
            "text": f"{frame['frame_id']} / {int(frame['timestamp_ms'])}ms",
        })
        content.append({
            "type": "input_image",
            "image_url": data_url_jpeg(frame["ai_bytes"]),
            "detail": "low",
        })

    response = create_ai_response(
        response_args(
            VISION_MODEL,
            [{"role": "user", "content": content}],
            "video_frame_scores",
            schema,
            max_output_tokens=max(1200, len(frames) * 45),
        )
    )
    data = parse_json_response(response)
    allowed = {str(f["frame_id"]) for f in frames}
    scores: dict[str, int] = {}
    for item in data.get("scores") or []:
        if not isinstance(item, dict):
            continue
        frame_id = str(item.get("frame_id") or "").strip()
        if frame_id not in allowed or frame_id in scores:
            continue
        try:
            score = max(0, min(100, int(item.get("score") or 0)))
        except Exception:
            score = 0
        scores[frame_id] = score

    # The images were still shown to AI even if the provider omitted an item.
    # Missing output is assigned 0 so it can never outrank a scored frame.
    for frame_id in allowed:
        scores.setdefault(frame_id, 0)
    return scores


def choose_final_moments(finalists: list[dict]) -> list[str]:
    if not finalists:
        return []

    max_items = min(VIDEO_MAX_MOMENTS, len(finalists))
    schema = {
        "type": "object",
        "properties": {
            "selected": {
                "type": "array",
                "minItems": 1,
                "maxItems": max_items,
                "items": {
                    "type": "object",
                    "properties": {
                        "rank": {"type": "integer", "minimum": 1, "maximum": max_items},
                        "frame_id": {"type": "string"},
                    },
                    "required": ["rank", "frame_id"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["selected"],
        "additionalProperties": False,
    }

    prompt = (
        f"この候補群から、動画全体を代表する『いい瞬間』を最大{max_items}枚選んでください。"
        "写真としての見栄えを最優先にしつつ、ほぼ同じ瞬間・同じ構図を重複させないでください。"
        "表情、動作、構図、光、色、背景分離、被写体の見やすさ、決定的瞬間を総合してください。"
        "基本は十分な候補があれば9枚選びます。rankは1が最良です。"
    )

    content = [{"type": "input_text", "text": prompt}]
    for frame in finalists:
        content.append({
            "type": "input_text",
            "text": f"{frame['frame_id']} / {int(frame['timestamp_ms'])}ms / 一次AI評価 {int(frame['ai_score'])}点",
        })
        content.append({
            "type": "input_image",
            "image_url": data_url_jpeg(frame["ai_bytes"]),
            "detail": "low",
        })

    response = create_ai_response(
        response_args(
            VISION_MODEL,
            [{"role": "user", "content": content}],
            "video_final_selection",
            schema,
            max_output_tokens=900,
        )
    )
    data = parse_json_response(response)
    allowed = {str(f["frame_id"]) for f in finalists}
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for item in data.get("selected") or []:
        if not isinstance(item, dict):
            continue
        frame_id = str(item.get("frame_id") or "").strip()
        if frame_id not in allowed or frame_id in seen:
            continue
        try:
            rank = int(item.get("rank") or 999)
        except Exception:
            rank = 999
        seen.add(frame_id)
        ranked.append((rank, frame_id))
    ranked.sort(key=lambda x: x[0])
    return [frame_id for _, frame_id in ranked[:VIDEO_MAX_MOMENTS]]


def ai_select_all_frames(frames: list[dict], progress=None) -> list[dict]:
    """All frames go through AI before any narrowing takes place."""
    all_scores: dict[str, int] = {}
    batches = [frames[i : i + VIDEO_AI_BATCH_SIZE] for i in range(0, len(frames), VIDEO_AI_BATCH_SIZE)]

    for batch_index, batch in enumerate(batches, start=1):
        if progress is not None:
            progress.progress(
                min(0.78, 0.12 + (batch_index - 1) / max(1, len(batches)) * 0.62),
                text=f"全{len(frames)}フレームをAI評価中… {batch_index}/{len(batches)}",
            )
        all_scores.update(evaluate_frame_batch(batch))

    scored = []
    for frame in frames:
        item = dict(frame)
        item["ai_score"] = int(all_scores.get(str(frame["frame_id"]), 0))
        scored.append(item)

    # This is the first narrowing step, and it happens only after every frame has
    # already been evaluated by AI.
    finalists = sorted(
        scored,
        key=lambda x: (-int(x.get("ai_score") or 0), int(x.get("timestamp_ms") or 0)),
    )[: min(VIDEO_FINALIST_COUNT, len(scored))]

    if progress is not None:
        progress.progress(0.82, text="AI評価済み候補から最終9枚を選定中…")

    selected_ids = choose_final_moments(finalists)
    by_id = {str(x["frame_id"]): x for x in scored}
    selected = [by_id[x] for x in selected_ids if x in by_id]

    # Final selection output can occasionally be shorter than requested. Fill from
    # the already-AI-scored frames; this is still based exclusively on AI evaluation.
    if len(selected) < min(VIDEO_MAX_MOMENTS, len(scored)):
        chosen = {str(x["frame_id"]) for x in selected}
        for frame in sorted(scored, key=lambda x: (-int(x.get("ai_score") or 0), int(x.get("timestamp_ms") or 0))):
            if str(frame["frame_id"]) in chosen:
                continue
            selected.append(frame)
            chosen.add(str(frame["frame_id"]))
            if len(selected) >= min(VIDEO_MAX_MOMENTS, len(scored)):
                break

    return selected[:VIDEO_MAX_MOMENTS]


# ============================================================
# Processing state machine
# ============================================================
def initial_meta(video_id: str, *, source_path: str, mime_type: str = "", size_bytes: int = 0, duration_ms: int = 0) -> dict:
    return {
        "video_id": video_id,
        "source_path": source_path,
        "mime_type": str(mime_type or "video/webm"),
        "size_bytes": max(0, int(size_bytes or 0)),
        "duration_ms": max(0, int(duration_ms or 0)),
        "captured_at": now_iso(),
        "status": "uploaded",
        "stage": "saved",
        "attempts": 0,
        "processing_version": VIDEO_PROCESSING_VERSION,
        "frame_count": 0,
        "moments": [],
        "last_error": "",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


def clear_existing_moments(video_id: str) -> None:
    rows = storage_list(moment_folder(video_id))
    paths = []
    for row in rows:
        name = str(row.get("name") or "").strip()
        if name:
            paths.append(f"{moment_folder(video_id)}/{name}")
    storage_remove(paths)


def process_video(video_id: str, *, show_progress: bool = True) -> dict:
    meta = read_meta(video_id)
    if not meta:
        meta = initial_meta(video_id, source_path=video_path(video_id))

    if meta.get("status") == "done" and meta.get("moments"):
        return meta

    attempts = int(meta.get("attempts") or 0) + 1
    meta.update(
        {
            "status": "processing",
            "stage": "download",
            "attempts": attempts,
            "processing_version": VIDEO_PROCESSING_VERSION,
            "last_error": "",
            "started_at": now_iso(),
        }
    )
    write_meta(meta)

    progress = st.progress(0.03, text="保存済み動画を読み込んでいます…") if show_progress else None

    try:
        source_path = str(meta.get("source_path") or video_path(video_id)).strip()
        video_raw = storage_download(source_path)
        if not video_raw:
            raise RuntimeError("保存済み動画が空です。")
        if len(video_raw) > VIDEO_MAX_BYTES:
            raise RuntimeError("動画ファイルが大きすぎます。最大25MBです。")

        meta.update({"stage": "extract", "size_bytes": len(video_raw)})
        write_meta(meta)
        if progress is not None:
            progress.progress(0.08, text="0.1秒ごとの全フレームを切り出しています…")

        frames = extract_all_frames(video_raw)
        meta.update({"stage": "ai", "frame_count": len(frames)})
        write_meta(meta)

        selected = ai_select_all_frames(frames, progress=progress)
        if not selected:
            raise RuntimeError("AIが保存候補を選べませんでした。")

        meta.update({"stage": "save_moments"})
        write_meta(meta)
        if progress is not None:
            progress.progress(0.90, text="選ばれたいい瞬間を高画質で保存しています…")

        clear_existing_moments(video_id)
        moments = []
        for rank, frame in enumerate(selected, start=1):
            frame_id = str(frame["frame_id"])
            path = f"{moment_folder(video_id)}/{rank:02d}_{frame_id}.jpg"
            storage_upload(path, frame["image_bytes"], "image/jpeg", upsert=False)
            moments.append(
                {
                    "rank": rank,
                    "frame_id": frame_id,
                    "timestamp_ms": int(frame.get("timestamp_ms") or 0),
                    "ai_score": int(frame.get("ai_score") or 0),
                    "storage_path": path,
                }
            )

        meta.update(
            {
                "status": "done",
                "stage": "done",
                "moments": moments,
                "completed_at": now_iso(),
                "last_error": "",
            }
        )
        write_meta(meta)
        if progress is not None:
            progress.progress(1.0, text=f"完了：いい瞬間を{len(moments)}枚保存しました。")
            time.sleep(0.3)
            progress.empty()
        return meta
    except Exception as exc:
        meta.update(
            {
                "status": "error",
                "stage": str(meta.get("stage") or "processing"),
                "last_error": str(exc)[:1200],
                "failed_at": now_iso(),
            }
        )
        try:
            write_meta(meta)
        except Exception:
            pass
        if progress is not None:
            progress.empty()
        raise


def recover_orphan_video() -> str | None:
    """Create metadata for one uploaded video whose Streamlit callback was lost."""
    meta_ids = set(list_meta_ids())
    for video_id in list_video_ids()[:20]:
        if video_id in meta_ids:
            continue
        meta = initial_meta(video_id, source_path=video_path(video_id))
        meta["recovered_orphan"] = True
        write_meta(meta)
        return video_id
    return None


def resume_one_pending() -> str | None:
    """Resume one unfinished item during a normal Streamlit execution."""
    for video_id in list_meta_ids()[:20]:
        meta = read_meta(video_id)
        if not meta:
            continue
        status = str(meta.get("status") or "").lower()
        attempts = int(meta.get("attempts") or 0)
        if status in {"uploaded", "processing"}:
            return video_id
        if status == "error" and attempts < 2:
            return video_id
    return None


# ============================================================
# Browser recorder component
# ============================================================
RECORDER_HTML = """
<div class="recorder-shell">
  <video id="camera" playsinline autoplay muted hidden></video>
  <div id="timer" class="timer" hidden>● 0:00 / 0:15</div>
  <div class="actions">
    <button id="open" type="button">🎥 動画を撮る</button>
    <button id="record" type="button" hidden>● 録画開始</button>
    <button id="stop" type="button" hidden>■ 録画終了</button>
    <button id="close" type="button" hidden>カメラを閉じる</button>
  </div>
  <div id="status" class="status">最大15秒。録画終了後は自動保存し、そのまま「いい瞬間」を作成します。</div>
</div>
"""

RECORDER_CSS = """
.recorder-shell { width: 100%; }
#camera { width: 100%; max-height: 62vh; object-fit: contain; background: #000; border-radius: 18px; }
.actions { display: grid; grid-template-columns: 1fr; gap: 10px; margin-top: 10px; }
.actions button { min-height: 58px; border-radius: 16px; border: 1px solid rgba(128,128,128,.28); font-weight: 750; font-size: 16px; cursor: pointer; }
#open, #record { background: var(--st-primary-color); color: white; border: none; }
#stop { background: #a51d2d; color: white; border: none; }
.status { margin-top: 10px; padding: 10px 12px; border-radius: 12px; background: rgba(128,128,128,.10); line-height: 1.45; font-size: 13px; }
.timer { margin-top: 8px; font-weight: 800; color: #c62828; }
@media (max-width: 640px) { .actions button { min-height: 62px; } }
"""

RECORDER_JS = r"""
export default function(component) {
  const { parentElement, setTriggerValue, data } = component;
  const video = parentElement.querySelector('#camera');
  const openBtn = parentElement.querySelector('#open');
  const recordBtn = parentElement.querySelector('#record');
  const stopBtn = parentElement.querySelector('#stop');
  const closeBtn = parentElement.querySelector('#close');
  const status = parentElement.querySelector('#status');
  const timer = parentElement.querySelector('#timer');

  let stream = null;
  let recorder = null;
  let chunks = [];
  let startedAt = 0;
  let intervalId = null;
  let stopTimer = null;
  let busy = false;

  const signedUrl = String(data?.upload_url || '');
  const storagePath = String(data?.storage_path || '');
  const uploadId = String(data?.upload_id || '');
  const maxSeconds = Number(data?.max_seconds || 15.2);
  const maxBytes = Number(data?.max_bytes || 26214400);

  const setStatus = (text) => { status.textContent = text || ''; };
  const fmt = (seconds) => `0:${String(Math.max(0, Math.floor(seconds))).padStart(2, '0')}`;

  const clearTimers = () => {
    if (intervalId) clearInterval(intervalId);
    if (stopTimer) clearTimeout(stopTimer);
    intervalId = null;
    stopTimer = null;
  };

  const closeStream = () => {
    clearTimers();
    if (stream) stream.getTracks().forEach((track) => track.stop());
    stream = null;
    video.srcObject = null;
    video.hidden = true;
    timer.hidden = true;
    recordBtn.hidden = true;
    stopBtn.hidden = true;
    closeBtn.hidden = true;
    openBtn.hidden = false;
  };

  const chooseMime = () => {
    const values = [
      'video/mp4;codecs=h264,aac',
      'video/mp4',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ];
    for (const value of values) {
      try { if (MediaRecorder.isTypeSupported(value)) return value; } catch (_) {}
    }
    return '';
  };

  const xhrUpload = (blob, contentType) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', signedUrl, true);
    xhr.timeout = 120000;
    xhr.setRequestHeader('content-type', contentType || 'application/octet-stream');
    xhr.setRequestHeader('cache-control', 'max-age=3600');
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const pct = Math.max(0, Math.min(100, Math.round(event.loaded / event.total * 100)));
      setStatus(`動画を保存しています… ${pct}%`);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(true);
      else reject(new Error(`Supabase upload HTTP ${xhr.status}: ${String(xhr.responseText || '').slice(0, 300)}`));
    };
    xhr.onerror = () => reject(new Error('動画の送信中に通信エラーが発生しました。'));
    xhr.ontimeout = () => reject(new Error('動画の送信が時間切れになりました。'));
    xhr.send(blob);
  });

  const uploadWithRetry = async (blob, contentType) => {
    let last = null;
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try { return await xhrUpload(blob, contentType); }
      catch (err) { last = err; if (attempt === 0) await new Promise(r => setTimeout(r, 800)); }
    }
    throw last || new Error('動画を保存できませんでした。');
  };

  const stopRecording = () => {
    clearTimers();
    if (recorder && recorder.state !== 'inactive') {
      try { recorder.stop(); } catch (_) {}
    }
  };

  const openCamera = async () => {
    if (busy) return;
    if (!signedUrl || !storagePath || !uploadId) {
      setStatus('動画の保存先を準備できていません。ページを再読み込みしてください。');
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setStatus('このブラウザでは動画録画を利用できません。ChromeまたはSafariの最新版を使用してください。');
      return;
    }
    try {
      setStatus('カメラを開いています…');
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 30, max: 30 } },
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
        });
      } catch (audioErr) {
        // A denied/unavailable microphone must not block a video-only recording.
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 30, max: 30 } },
          audio: false
        });
      }
      video.srcObject = stream;
      video.hidden = false;
      await video.play();
      openBtn.hidden = true;
      recordBtn.hidden = false;
      closeBtn.hidden = false;
      setStatus('準備できました。「録画開始」を押してください。');
    } catch (err) {
      console.error(err);
      closeStream();
      const message = 'カメラを開けませんでした。ブラウザのカメラ許可を確認してください。';
      setStatus(message);
      setTriggerValue('error', { message, detail: String(err?.message || err || '') });
    }
  };

  const startRecording = async () => {
    if (!stream || busy) return;
    busy = true;
    chunks = [];
    const mime = chooseMime();
    const track = stream.getVideoTracks?.()[0];
    const settings = track?.getSettings ? track.getSettings() : {};
    const pixels = Number(settings.width || video.videoWidth || 1280) * Number(settings.height || video.videoHeight || 720);
    const videoBits = pixels >= 1700000 ? 6000000 : (pixels >= 800000 ? 4500000 : 3000000);
    const opts = { videoBitsPerSecond: videoBits, audioBitsPerSecond: 96000 };
    if (mime) opts.mimeType = mime;
    try {
      try { recorder = new MediaRecorder(stream, opts); }
      catch (_) { recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); }

      recorder.ondataavailable = (event) => { if (event.data?.size) chunks.push(event.data); };
      recorder.onerror = (event) => {
        console.error(event);
        busy = false;
        setStatus('録画中にエラーが発生しました。もう一度お試しください。');
      };
      recorder.onstop = async () => {
        const elapsedMs = Math.max(1, Date.now() - startedAt);
        const finalType = String(recorder?.mimeType || mime || 'video/webm');
        const blob = new Blob(chunks, { type: finalType });
        chunks = [];
        recordBtn.hidden = true;
        stopBtn.hidden = true;
        timer.hidden = true;
        try {
          if (!blob.size) throw new Error('録画データが空です。');
          if (blob.size > maxBytes) throw new Error('動画ファイルが大きすぎます。もう一度撮影してください。');
          setStatus('録画完了。動画を自動保存しています…');
          await uploadWithRetry(blob, String(finalType).split(';', 1)[0]);
          setStatus('動画を保存しました。いい瞬間を自動作成しています…');
          if (stream) stream.getTracks().forEach((track) => track.stop());
          stream = null;
          video.srcObject = null;
          video.hidden = true;
          closeBtn.hidden = true;
          setTriggerValue('uploaded', {
            upload_id: uploadId,
            storage_path: storagePath,
            size_bytes: blob.size,
            duration_ms: elapsedMs,
            mime_type: finalType,
            captured_at: new Date(Date.now() - elapsedMs).toISOString(),
            width: Number(settings.width || video.videoWidth || 0),
            height: Number(settings.height || video.videoHeight || 0),
            frame_rate: Number(settings.frameRate || 0)
          });
        } catch (err) {
          console.error(err);
          busy = false;
          closeStream();
          const message = '動画を保存できませんでした。';
          setStatus(`${message} ${String(err?.message || err || '')}`);
          setTriggerValue('error', { message, detail: String(err?.message || err || '') });
        }
      };

      recorder.start(1000);
      startedAt = Date.now();
      timer.hidden = false;
      recordBtn.hidden = true;
      stopBtn.hidden = false;
      closeBtn.hidden = true;
      setStatus('録画中です。15秒で自動終了します。');
      intervalId = setInterval(() => {
        const elapsed = Math.min(maxSeconds, Math.max(0, (Date.now() - startedAt) / 1000));
        timer.textContent = `● ${fmt(elapsed)} / 0:15`;
      }, 200);
      stopTimer = setTimeout(stopRecording, maxSeconds * 1000);
    } catch (err) {
      busy = false;
      closeStream();
      const message = '録画を開始できませんでした。';
      setStatus(message);
      setTriggerValue('error', { message, detail: String(err?.message || err || '') });
    }
  };

  openBtn.onclick = openCamera;
  recordBtn.onclick = startRecording;
  stopBtn.onclick = stopRecording;
  closeBtn.onclick = () => { busy = false; closeStream(); setStatus('カメラを閉じました。'); };

  return () => {
    try { if (recorder && recorder.state !== 'inactive') recorder.stop(); } catch (_) {}
    closeStream();
  };
}
"""

try:
    recorder_component = st.components.v2.component(
        "tokyo_burari_video_recorder_clean_v1",
        html=RECORDER_HTML,
        css=RECORDER_CSS,
        js=RECORDER_JS,
    )
except Exception:
    recorder_component = None


def get_upload_reservation() -> dict:
    current = st.session_state.get("_upload_reservation_v1")
    if isinstance(current, dict) and current.get("upload_url") and current.get("storage_path") and current.get("upload_id"):
        return current

    upload_id = new_video_id()
    path = video_path(upload_id)
    url = create_signed_upload(path)
    reservation = {
        "upload_id": upload_id,
        "storage_path": path,
        "upload_url": url,
        "created_at": now_iso(),
    }
    st.session_state["_upload_reservation_v1"] = reservation
    return reservation


def clear_upload_reservation() -> None:
    st.session_state.pop("_upload_reservation_v1", None)


# ============================================================
# UI
# ============================================================
def render_header() -> None:
    st.markdown(
        '<div class="burari-hero"><div class="burari-title">東京ぶらり旅</div>'
        '<div class="burari-sub">15秒動画を保存 → 全フレームをAI評価 → いい瞬間を最大9枚、自動保存</div></div>',
        unsafe_allow_html=True,
    )


def render_recorder() -> None:
    st.subheader("動画を撮る")
    st.caption("録画終了後の保存・切り取り・画像保存は自動です。追加操作は不要です。")

    if recorder_component is None:
        st.error("StreamlitのCustom Components v2を利用できません。requirements.txt を更新してください。")
        return

    try:
        reservation = get_upload_reservation()
    except Exception as exc:
        st.error("動画の保存先を準備できませんでした。")
        with st.expander("保護者向け詳細", expanded=True):
            st.code(str(exc))
        return

    result = recorder_component(
        data={
            "upload_id": reservation["upload_id"],
            "storage_path": reservation["storage_path"],
            "upload_url": reservation["upload_url"],
            "max_seconds": VIDEO_RECORD_SECONDS,
            "max_bytes": VIDEO_MAX_BYTES,
        },
        key=f"burari_recorder_{reservation['upload_id']}",
        on_uploaded_change=lambda: None,
        on_error_change=lambda: None,
    )

    error = getattr(result, "error", None)
    if error:
        message = error.get("message") if isinstance(error, dict) else str(error)
        detail = error.get("detail") if isinstance(error, dict) else ""
        if message:
            st.warning(message)
        if detail:
            with st.expander("保護者向け詳細"):
                st.code(str(detail))

    uploaded = getattr(result, "uploaded", None)
    if not isinstance(uploaded, dict):
        return

    upload_id = str(uploaded.get("upload_id") or "").strip()
    storage_path = str(uploaded.get("storage_path") or "").strip()
    if not upload_id or upload_id != reservation["upload_id"] or storage_path != reservation["storage_path"]:
        st.error("保存済み動画と現在の撮影情報が一致しません。ページを再読み込みしてください。")
        return

    processed_key = f"_processed_upload_{upload_id}"
    if st.session_state.get(processed_key):
        return

    # First persist a tiny sidecar. From this point onward the server can resume the
    # pipeline even if the browser closes or a Streamlit rerun occurs.
    meta = read_meta(upload_id)
    if not meta:
        meta = initial_meta(
            upload_id,
            source_path=storage_path,
            mime_type=str(uploaded.get("mime_type") or ""),
            size_bytes=int(uploaded.get("size_bytes") or 0),
            duration_ms=int(uploaded.get("duration_ms") or 0),
        )
        meta["captured_at"] = str(uploaded.get("captured_at") or now_iso())
        meta["capture"] = {
            "width": int(uploaded.get("width") or 0),
            "height": int(uploaded.get("height") or 0),
            "frame_rate": float(uploaded.get("frame_rate") or 0),
        }
        write_meta(meta)

    try:
        with st.spinner("動画は保存済みです。いい瞬間を自動作成しています…"):
            done = process_video(upload_id, show_progress=True)
        st.session_state[processed_key] = True
        clear_upload_reservation()
        st.success(f"完了しました。いい瞬間を{len(done.get('moments') or [])}枚、自動保存しました。")
        st.rerun()
    except Exception as exc:
        # The original video is already safe in Storage. The next normal app run
        # retries once automatically, so the user never needs a separate start button.
        clear_upload_reservation()
        st.error("元動画は保存済みですが、いい瞬間の自動作成でエラーが発生しました。次回の通常実行時に自動再試行します。")
        with st.expander("保護者向け詳細", expanded=True):
            st.code(str(exc))


def _status_label(meta: dict) -> str:
    status = str(meta.get("status") or "")
    if status == "done":
        return "完了"
    if status == "processing":
        return "自動処理中"
    if status == "uploaded":
        return "処理待ち"
    if status == "error":
        return "再試行待ち" if int(meta.get("attempts") or 0) < 2 else "エラー"
    return status or "不明"


def render_library() -> None:
    st.subheader("保存済み")
    ids = list_meta_ids()[:12]
    if not ids:
        st.info("まだ保存済み動画はありません。")
        return

    for video_id in ids:
        meta = read_meta(video_id)
        if not meta:
            continue
        captured = str(meta.get("captured_at") or meta.get("created_at") or video_id)
        title = f"{captured[:19].replace('T', ' ')}  /  {_status_label(meta)}"
        with st.expander(title, expanded=False):
            try:
                st.video(create_signed_download(str(meta.get("source_path") or video_path(video_id))))
            except Exception:
                st.caption("動画プレビューを作成できませんでした。元動画はStorageに保存されています。")

            moments = [x for x in (meta.get("moments") or []) if isinstance(x, dict)]
            if moments:
                st.caption(f"いい瞬間：{len(moments)}枚")
                cols = st.columns(3)
                for idx, item in enumerate(sorted(moments, key=lambda x: int(x.get("rank") or 999))):
                    path = str(item.get("storage_path") or "")
                    if not path:
                        continue
                    try:
                        url = create_signed_download(path)
                        cols[idx % 3].image(url, use_container_width=True)
                    except Exception:
                        cols[idx % 3].caption("画像を表示できません")
            else:
                st.caption(f"状態：{_status_label(meta)}")

            if str(meta.get("status") or "") == "error":
                with st.expander("エラー詳細"):
                    st.code(str(meta.get("last_error") or "不明なエラー"))


def auto_resume_before_ui() -> None:
    # 1) Browser upload may have succeeded while the Streamlit callback was lost.
    orphan = recover_orphan_video()
    if orphan:
        try:
            with st.spinner("保存済み動画を検出しました。いい瞬間を自動作成しています…"):
                process_video(orphan, show_progress=True)
            st.rerun()
        except Exception:
            return

    # 2) A server restart / closed browser can leave a sidecar unfinished.
    pending = resume_one_pending()
    if pending:
        try:
            with st.spinner("未完了の保存済み動画を自動処理しています…"):
                process_video(pending, show_progress=True)
            st.rerun()
        except Exception:
            return


# ============================================================
# Main
# ============================================================
require_setup()
require_pin()
render_header()

# This happens in the normal Streamlit execution, never in a detached background
# thread. It is intentionally before the camera UI so unfinished saved videos are
# recovered without the user pressing anything.
auto_resume_before_ui()

camera_tab, library_tab = st.tabs(["🎥 撮影", "🖼 保存済み"])
with camera_tab:
    render_recorder()
with library_tab:
    render_library()

st.caption(f"build: {APP_BUILD} / 0.1秒間隔・AI全フレーム評価・最大{VIDEO_MAX_MOMENTS}枚保存")
