import base64
import hashlib
import hmac
import html
import io
import json
import os
import tempfile
import time
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st
from openai import OpenAI
from PIL import Image, ImageOps

try:
    from supabase import create_client
except Exception:
    create_client = None


# ============================================================
# Basic settings
# ============================================================
st.set_page_config(
    page_title="東京ぶらり旅プロジェクト",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {
        max-width: 760px;
        padding-top: 1rem;
        padding-bottom: 5rem;
      }
      div.stButton > button {
        min-height: 3.2rem;
        border-radius: 16px;
        font-size: 1.03rem;
        font-weight: 650;
      }
      .hero-card, .photo-card, .diary-card, .monthly-card, .talk-card {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 20px;
        padding: 1rem 1.05rem;
        margin: .45rem 0 .85rem;
      }
      .hero-title {
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.45;
      }
      .big-text {
        font-size: 1.15rem;
        line-height: 1.7;
        font-weight: 700;
      }
      .small-note {
        font-size: .92rem;
        line-height: 1.55;
        opacity: .78;
      }
      .ai-line {
        border-left: 5px solid rgba(80, 160, 220, .45);
        padding: .55rem .8rem;
        margin: .4rem 0;
        border-radius: 0 14px 14px 0;
        background: rgba(80,160,220,.055);
      }
      .child-line {
        border-left: 5px solid rgba(240, 170, 60, .55);
        padding: .55rem .8rem;
        margin: .4rem 0;
        border-radius: 0 14px 14px 0;
        background: rgba(240,170,60,.055);
      }
      .muted-pill {
        display: inline-block;
        border: 1px solid rgba(128,128,128,.2);
        border-radius: 999px;
        padding: .2rem .55rem;
        margin: .1rem .15rem .1rem 0;
        font-size: .85rem;
      }
      .st-key-home_menu div.stButton > button {
        min-height: 8.2rem;
        border-radius: 22px;
        font-size: 1.30rem;
        font-weight: 800;
        line-height: 1.45;
        white-space: pre-line;
      }
      .st-key-home_menu [data-testid="stHorizontalBlock"] {
        gap: .75rem;
      }
      .st-key-mobile_capture [data-testid="stFileUploaderDropzone"] {
        padding: 1rem;
        border-radius: 20px;
      }
      .st-key-mobile_capture [data-testid="stFileUploaderDropzone"] button {
        min-height: 4.8rem;
        width: 100%;
        border-radius: 18px;
        font-size: 0;
        font-weight: 800;
      }
      .st-key-mobile_capture [data-testid="stFileUploaderDropzone"] button::after {
        content: "📷 写真を撮る・選ぶ";
        font-size: 1.10rem;
        font-weight: 800;
      }
      @media (max-width: 640px) {
        .block-container {
          padding-left: .75rem;
          padding-right: .75rem;
        }
        .st-key-home_menu div.stButton > button {
          min-height: 7.4rem;
          font-size: 1.16rem;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


OPENAI_API_KEY = secret("OPENAI_API_KEY")
TEXT_MODEL = secret("TEXT_MODEL", "gpt-5.6-luna")
VISION_MODEL = secret("VISION_MODEL", TEXT_MODEL)
TRANSCRIBE_MODEL = secret("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = secret("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = secret("TTS_VOICE", "coral")
FAMILY_PIN = str(secret("FAMILY_PIN", "")).strip()
APP_TIMEZONE = secret("APP_TIMEZONE", "Asia/Tokyo")
SUPABASE_URL = secret("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = secret("SUPABASE_SECRET_KEY", "")
PHOTO_BUCKET = secret("PHOTO_BUCKET", "burari-photos")
USE_FAST_MODE = str(secret("USE_FAST_MODE", "true")).lower() in {"1", "true", "yes", "on"}

TRIP_TABLE = "burari_trips"
PHOTO_TABLE = "burari_photos"
DIARY_TABLE = "burari_diaries"
MONTHLY_TABLE = "burari_monthly_reviews"


# ============================================================
# Native mobile camera component
# ============================================================
# Streamlit's built-in st.camera_input uses getUserMedia and therefore depends
# on browser camera permissions. This component instead uses a normal HTML
# file input with capture="environment", which asks a mobile browser to hand
# off to the phone's rear camera app. The captured image is resized in the
# browser before it is sent back to Python.
_NATIVE_CAMERA_HTML = """
<div class="native-camera-wrap">
  <input id="native-camera-input" type="file" accept="image/*" capture="environment" />
  <label class="native-camera-button" for="native-camera-input">
    <span class="camera-icon">📷</span>
    <span class="camera-title">いま写真を撮る</span>
    <span class="camera-sub">スマホのカメラを開きます</span>
  </label>
  <div id="native-camera-status" class="camera-status" aria-live="polite"></div>
</div>
"""

_NATIVE_CAMERA_CSS = """
.native-camera-wrap {
  width: 100%;
  font-family: var(--st-font);
}
#native-camera-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.native-camera-button {
  min-height: 112px;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 2px solid var(--st-primary-color);
  border-radius: 20px;
  background: color-mix(in srgb, var(--st-primary-color) 8%, transparent);
  color: var(--st-text-color);
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}
.native-camera-button:active {
  transform: scale(.985);
}
.camera-icon {
  font-size: 34px;
  line-height: 1;
}
.camera-title {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.25;
}
.camera-sub {
  font-size: 12px;
  opacity: .72;
}
.camera-status {
  min-height: 20px;
  margin-top: 7px;
  text-align: center;
  font-size: 13px;
  opacity: .75;
}
"""

_NATIVE_CAMERA_JS = r"""
export default function(component) {
  const { parentElement, setTriggerValue } = component;
  const input = parentElement.querySelector('#native-camera-input');
  const status = parentElement.querySelector('#native-camera-status');

  const fileToDataUrl = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

  const loadImage = (file) => new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (err) => {
      URL.revokeObjectURL(url);
      reject(err);
    };
    img.src = url;
  });

  const preparePhoto = async (file) => {
    const img = await loadImage(file);
    const maxSide = 1600;
    const srcW = img.naturalWidth || img.width;
    const srcH = img.naturalHeight || img.height;
    const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
    const width = Math.max(1, Math.round(srcW * scale));
    const height = Math.max(1, Math.round(srcH * scale));

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { alpha: false });
    ctx.drawImage(img, 0, 0, width, height);

    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/jpeg', 0.84);
    });
    if (!blob) throw new Error('camera image conversion failed');
    return await fileToDataUrl(blob);
  };

  const onChange = async () => {
    const file = input.files && input.files[0];
    if (!file) return;
    status.textContent = '写真を準備しています…';
    try {
      const dataUrl = await preparePhoto(file);
      setTriggerValue('photo', {
        data_url: dataUrl,
        name: file.name || 'camera.jpg',
        captured_at: new Date().toISOString(),
      });
      status.textContent = '写真を受け取りました。';
    } catch (err) {
      console.error(err);
      status.textContent = '写真を読み込めませんでした。もう一度撮ってください。';
      setTriggerValue('camera_error', '画像を読み込めませんでした');
    } finally {
      input.value = '';
    }
  };

  input.addEventListener('change', onChange);
  return () => input.removeEventListener('change', onChange);
}
"""

try:
    native_camera_component = st.components.v2.component(
        "tokyo_burari_native_camera",
        html=_NATIVE_CAMERA_HTML,
        css=_NATIVE_CAMERA_CSS,
        js=_NATIVE_CAMERA_JS,
    )
except Exception:
    native_camera_component = None


def decode_camera_data_url(data_url):
    """Decode a trusted data URL emitted by the native camera component."""
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        raise ValueError("カメラ画像の形式が不正です。")
    try:
        header, encoded = data_url.split(",", 1)
    except ValueError as exc:
        raise ValueError("カメラ画像を読み込めません。") from exc
    if ";base64" not in header:
        raise ValueError("カメラ画像の形式が不正です。")
    return base64.b64decode(encoded, validate=True)


# ============================================================
# Clients / setup
# ============================================================
@st.cache_resource(show_spinner=False)
def openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)


@st.cache_resource(show_spinner=False)
def supabase_client():
    if not (create_client and SUPABASE_URL and SUPABASE_SECRET_KEY):
        return None
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def now_jst():
    return datetime.now(ZoneInfo(APP_TIMEZONE))


def today_iso():
    return now_jst().date().isoformat()


def verify_setup():
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY が設定されていません。Streamlit Secrets を確認してください。")
        st.stop()
    if create_client is None:
        st.error("Supabase ライブラリがありません。requirements.txt を確認してください。")
        st.stop()
    if not (SUPABASE_URL and SUPABASE_SECRET_KEY):
        st.error("SUPABASE_URL と SUPABASE_SECRET_KEY が設定されていません。")
        st.stop()
    try:
        supabase_client().table(TRIP_TABLE).select("id").limit(1).execute()
    except Exception as exc:
        st.error("Supabase の初期設定が完了していません。supabase_schema.sql を1回実行してください。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        st.stop()


def require_family_pin():
    if not FAMILY_PIN:
        return
    if st.session_state.get("_family_authenticated", False):
        return

    st.title("📷 東京ぶらり旅プロジェクト")
    st.caption("家族用のあいことばを入れてください。")

    failures = int(st.session_state.get("_family_pin_failures", 0))
    locked_until = float(st.session_state.get("_family_pin_locked_until", 0.0))
    now = time.time()

    if locked_until > now:
        st.warning(f"入力回数が多いため、あと{max(1, int(locked_until - now))}秒ほど待ってください。")
        st.stop()

    entered = st.text_input(
        "あいことば",
        type="password",
        max_chars=32,
        key="_family_pin_input",
        autocomplete="off",
    )
    if st.button("はいる", type="primary", use_container_width=True):
        if entered and hmac.compare_digest(entered.strip(), FAMILY_PIN):
            st.session_state["_family_authenticated"] = True
            st.session_state["_family_pin_failures"] = 0
            st.session_state["_family_pin_locked_until"] = 0.0
            st.rerun()
        failures += 1
        if failures >= 5:
            st.session_state["_family_pin_failures"] = 0
            st.session_state["_family_pin_locked_until"] = time.time() + 60
            st.error("入力回数が多いため、1分ほど待ってからもう一度試してください。")
        else:
            st.session_state["_family_pin_failures"] = failures
            st.error("あいことばが違います。")
    st.stop()


# ============================================================
# OpenAI helpers
# ============================================================
def response_args(model, input_value, schema_name, schema, max_output_tokens=900):
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


def ask_json(prompt, name, schema, max_output_tokens=900):
    result = openai_client().responses.create(
        **response_args(TEXT_MODEL, prompt, name, schema, max_output_tokens)
    )
    return json.loads(result.output_text)


def image_data_url(image_bytes):
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def ask_json_with_image(prompt, image_bytes, name, schema, max_output_tokens=800):
    content = [
        {"type": "input_text", "text": prompt},
        {"type": "input_image", "image_url": image_data_url(image_bytes)},
    ]
    input_value = [{"role": "user", "content": content}]
    result = openai_client().responses.create(
        **response_args(VISION_MODEL, input_value, name, schema, max_output_tokens)
    )
    return json.loads(result.output_text)


def transcribe_audio(audio_file, context=""):
    audio_file.seek(0)
    prompt = (
        "5〜6歳の子どもの日本語の発話です。"
        "子どもらしい言い回しを大人の表現に直しすぎず、聞こえた内容を自然な日本語として文字起こししてください。"
        "言い直しがあるときは、最後に言い直した内容を優先してください。"
    )
    if context:
        prompt += " 文脈: " + context[:1200]
    result = openai_client().audio.transcriptions.create(
        model=TRANSCRIBE_MODEL,
        file=audio_file,
        language="ja",
        prompt=prompt,
    )
    return result.text.strip()


def speech_bytes(text):
    if not str(text or "").strip():
        return None
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
        with openai_client().audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=str(text),
            instructions=(
                "5〜6歳の日本語話者の子どもに話しかけます。"
                "少しゆっくり、明瞭に、落ち着いて親しみやすく話してください。"
                "先生のように評価せず、会話相手として自然に話してください。"
                "大げさな演技や過剰な褒め方は避けてください。"
            ),
            response_format="wav",
        ) as response:
            response.stream_to_file(temp_path)
        with open(temp_path, "rb") as f:
            return f.read()
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def audio_digest(uploaded_file):
    if uploaded_file is None:
        return ""
    try:
        uploaded_file.seek(0)
        data = uploaded_file.read()
        uploaded_file.seek(0)
        return hashlib.sha1(data).hexdigest()
    except Exception:
        return ""


# ============================================================
# Image helpers
# ============================================================
def normalize_photo(raw_bytes, max_side=1600, quality=84):
    with Image.open(io.BytesIO(raw_bytes)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((max_side, max_side))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()


@st.cache_data(ttl=120, show_spinner=False)
def download_photo(storage_path):
    return supabase_client().storage.from_(PHOTO_BUCKET).download(storage_path)


def upload_photo(trip_id, image_bytes):
    compressed = normalize_photo(image_bytes)
    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    path = f"{trip_id}/{stamp}_{uuid.uuid4().hex[:8]}.jpg"
    file_obj = io.BytesIO(compressed)
    file_obj.name = "photo.jpg"
    try:
        supabase_client().storage.from_(PHOTO_BUCKET).upload(
            path=path,
            file=file_obj,
            file_options={
                "content-type": "image/jpeg",
                "cache-control": "3600",
                "upsert": "false",
            },
        )
        result = (
            supabase_client()
            .table(PHOTO_TABLE)
            .insert(
                {
                    "trip_id": trip_id,
                    "storage_path": path,
                    "captured_at": now_jst().isoformat(),
                    "reflection_json": {},
                    "signals_json": {},
                }
            )
            .execute()
        )
        download_photo.clear()
        return (result.data or [None])[0]
    except Exception:
        try:
            supabase_client().storage.from_(PHOTO_BUCKET).remove([path])
        except Exception:
            pass
        raise


# ============================================================
# Database helpers
# ============================================================
def create_trip(destination=""):
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .insert(
            {
                "trip_date": today_iso(),
                "destination": str(destination or "").strip(),
                "status": "active",
                "started_at": now_jst().isoformat(),
            }
        )
        .execute()
    )
    return (result.data or [None])[0]


def get_latest_active_trip():
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("status", "active")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def get_today_active_trip():
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("status", "active")
        .eq("trip_date", today_iso())
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def update_trip_destination(trip_id, destination):
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .update({"destination": str(destination or "").strip()})
        .eq("id", trip_id)
        .execute()
    )
    return (result.data or [None])[0]


def get_trip(trip_id):
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("id", trip_id)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def finish_trip(trip_id):
    (
        supabase_client()
        .table(TRIP_TABLE)
        .update({"status": "ready_for_diary", "ended_at": now_jst().isoformat()})
        .eq("id", trip_id)
        .execute()
    )


def list_trip_photos(trip_id):
    result = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("trip_id", trip_id)
        .order("captured_at")
        .execute()
    )
    return result.data or []


def update_photo_reflection(photo_id, conversation, signals):
    (
        supabase_client()
        .table(PHOTO_TABLE)
        .update(
            {
                "reflection_json": {"conversation": conversation},
                "signals_json": signals or {},
            }
        )
        .eq("id", photo_id)
        .execute()
    )


def list_recent_trips_for_diary(limit=20):
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .in_("status", ["ready_for_diary", "diary_done"])
        .order("trip_date", desc=True)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_diary_for_trip(trip_id):
    result = (
        supabase_client()
        .table(DIARY_TABLE)
        .select("*")
        .eq("trip_id", trip_id)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def save_diary(trip_id, title, diary_text, raw_conversation, ai_meta):
    existing = get_diary_for_trip(trip_id)
    payload = {
        "trip_id": trip_id,
        "title": str(title or "").strip(),
        "diary_text": str(diary_text or "").strip(),
        "raw_conversation": raw_conversation,
        "ai_meta": ai_meta or {},
        "updated_at": now_jst().isoformat(),
    }
    if existing:
        (
            supabase_client()
            .table(DIARY_TABLE)
            .update(payload)
            .eq("id", existing["id"])
            .execute()
        )
    else:
        payload["created_at"] = now_jst().isoformat()
        supabase_client().table(DIARY_TABLE).insert(payload).execute()
    (
        supabase_client()
        .table(TRIP_TABLE)
        .update({"status": "diary_done"})
        .eq("id", trip_id)
        .execute()
    )


def list_recent_diaries(limit=60):
    result = (
        supabase_client()
        .table(DIARY_TABLE)
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    diaries = result.data or []
    if not diaries:
        return []
    trip_ids = list({d["trip_id"] for d in diaries})
    trip_result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .in_("id", trip_ids)
        .execute()
    )
    trip_map = {t["id"]: t for t in (trip_result.data or [])}
    return [{"diary": d, "trip": trip_map.get(d["trip_id"], {})} for d in diaries]


def month_bounds(month_key):
    year, month = [int(x) for x in month_key.split("-")]
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start.isoformat(), end.isoformat()


def get_month_bundle(month_key):
    start, end = month_bounds(month_key)
    trips_result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .gte("trip_date", start)
        .lt("trip_date", end)
        .order("trip_date")
        .execute()
    )
    trips = trips_result.data or []
    if not trips:
        return {"trips": [], "diaries": [], "photos": []}
    trip_ids = [t["id"] for t in trips]
    diaries_result = (
        supabase_client()
        .table(DIARY_TABLE)
        .select("*")
        .in_("trip_id", trip_ids)
        .execute()
    )
    photos_result = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("id,trip_id,captured_at,reflection_json,signals_json")
        .in_("trip_id", trip_ids)
        .order("captured_at")
        .execute()
    )
    return {
        "trips": trips,
        "diaries": diaries_result.data or [],
        "photos": photos_result.data or [],
    }


def get_saved_monthly_review(month_key):
    first_day, _ = month_bounds(month_key)
    result = (
        supabase_client()
        .table(MONTHLY_TABLE)
        .select("*")
        .eq("review_month", first_day)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def save_monthly_review(month_key, review_json):
    first_day, _ = month_bounds(month_key)
    existing = get_saved_monthly_review(month_key)
    payload = {
        "review_month": first_day,
        "review_json": review_json,
        "updated_at": now_jst().isoformat(),
    }
    if existing:
        (
            supabase_client()
            .table(MONTHLY_TABLE)
            .update(payload)
            .eq("id", existing["id"])
            .execute()
        )
    else:
        payload["created_at"] = now_jst().isoformat()
        supabase_client().table(MONTHLY_TABLE).insert(payload).execute()


# ============================================================
# AI diary conversation
# ============================================================
SIGNAL_SCHEMA = {
    "type": "object",
    "properties": {
        "like": {"type": "array", "items": {"type": "string"}},
        "dislike": {"type": "array", "items": {"type": "string"}},
        "curiosity": {"type": "array", "items": {"type": "string"}},
        "convenient": {"type": "array", "items": {"type": "string"}},
        "inconvenient": {"type": "array", "items": {"type": "string"}},
        "people": {"type": "array", "items": {"type": "string"}},
        "wish": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["like", "dislike", "curiosity", "convenient", "inconvenient", "people", "wish"],
    "additionalProperties": False,
}


def initial_photo_question(image_bytes):
    schema = {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
        "additionalProperties": False,
    }
    prompt = """
あなたは5〜6歳の子どもと「東京ぶらり旅」の写真を振り返る会話相手です。
写真を見て、子どもがなぜこの写真を撮ったのかを本人の言葉で話せる、短い質問を1つだけ作ってください。

重要:
- 写真の意味を決めつけない。
- 「不便だったんだね」「楽しかったんだね」のように感情や評価を誘導しない。
- 正解を求めない。
- 5〜6歳が一度で理解できる短い日本語にする。
- 基本形は「この写真、何が気になって撮ったの？」だが、写真に合わせて少し自然に変えてよい。
- 質問以外は書かない。
""".strip()
    try:
        return ask_json_with_image(prompt, image_bytes, "initial_photo_question", schema, 180)["question"]
    except Exception:
        return "この写真、何が気になって撮ったの？"


def conversation_text(conversation):
    lines = []
    for item in conversation:
        label = "AI" if item.get("role") == "assistant" else "子ども"
        lines.append(f"{label}: {item.get('text', '')}")
    return "\n".join(lines)


def next_photo_turn(image_bytes, conversation, child_turn_count):
    force_done = child_turn_count >= 3
    schema = {
        "type": "object",
        "properties": {
            "reply": {"type": "string"},
            "next_question": {"type": "string"},
            "done": {"type": "boolean"},
            "signals": SIGNAL_SCHEMA,
        },
        "required": ["reply", "next_question", "done", "signals"],
        "additionalProperties": False,
    }
    prompt = f"""
あなたは5〜6歳の子どもと「東京ぶらり旅」の写真を振り返っています。
写真と、ここまでの会話を見て、次の応答を作ってください。

会話:
{conversation_text(conversation)}

子どもの回答回数: {child_turn_count}

目的は日記の材料を集めることですが、尋問や学習課題にしません。
大切なのは「本人が何に気づいたか」「どう感じたか」「なぜ気になったか」を本人の言葉で残すことです。

ルール:
- reply は子どもの発言を受け止める短い一言。過剰に褒めない。
- next_question は必要な場合だけ1問。5〜6歳向けに短くする。
- 写真や発言から感情を決めつけない。
- 「便利？不便？」「困った？」のように選択肢へ誘導しすぎない。
- すでに理由と気持ちが分かれば、2回答目以降は done=true にしてよい。
- 「こうだったらもっといい」という発想が自然に出そうなときだけ、それを尋ねてよい。
- 子どもが話したくなさそうなら早めに終える。
- {"今回は必ず done=true。next_question は空文字にする。" if force_done else "最大3回答で終える。"}
- signals は子どもが実際に話した内容だけを分類する。推測は入れない。
- signals に該当がなければ空配列。
- done=true のとき next_question は空文字。
""".strip()
    result = ask_json_with_image(prompt, image_bytes, "next_photo_turn", schema, 700)
    if force_done:
        result["done"] = True
        result["next_question"] = ""
    return result


def merge_signals(old, new):
    result = {k: list(v or []) for k, v in (old or {}).items()}
    for key in ["like", "dislike", "curiosity", "convenient", "inconvenient", "people", "wish"]:
        result.setdefault(key, [])
        for value in (new or {}).get(key, []) or []:
            value = str(value or "").strip()
            if value and value not in result[key]:
                result[key].append(value)
    return result


def compose_diary(trip, photo_states):
    evidence_parts = []
    all_signals = {}
    raw = {}
    for idx, item in enumerate(photo_states, start=1):
        conv = item.get("conversation", [])
        raw[str(item.get("photo_id"))] = conv
        child_lines = [x.get("text", "") for x in conv if x.get("role") == "child"]
        if child_lines:
            evidence_parts.append(f"写真{idx}: " + " / ".join(child_lines))
        all_signals = merge_signals(all_signals, item.get("signals", {}))

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "diary": {"type": "string"},
            "child_points": {"type": "array", "items": {"type": "string"}},
            "signals": SIGNAL_SCHEMA,
        },
        "required": ["title", "diary", "child_points", "signals"],
        "additionalProperties": False,
    }
    destination = str(trip.get("destination") or "").strip()
    evidence = "\n".join(evidence_parts) if evidence_parts else "子どもの発言はほとんどありません。"
    prompt = f"""
5〜6歳の子どもが東京ぶらり旅のあとに話した内容から、本人の日記を作ります。
AIが新しい出来事や感情を足してはいけません。

日付: {trip.get('trip_date', '')}
行き先メモ: {destination or 'なし'}
子どもが写真を見ながら話した言葉:
{evidence}

ルール:
- diary は3〜7文程度。発言が少なければ無理に長くしない。
- 子どもの語彙や言い回しをできるだけ残し、読みやすい順番に整える。
- 「楽しかった」「不便だった」などを、本人が言っていないのに補わない。
- 大人っぽい抽象語へ変換しすぎない。
- title は短く、内容に忠実にする。
- child_points はAIの解釈ではなく、日記の根拠になった本人の発言を短く3つ以内で抜き出す。
- signals は本人が実際に話した内容だけを整理し、推測を足さない。
""".strip()
    result = ask_json(prompt, "compose_burari_diary", schema, 1100)
    result["signals"] = merge_signals(all_signals, result.get("signals", {}))
    return result, raw


def revise_diary(draft, correction, child_evidence):
    schema = {
        "type": "object",
        "properties": {
            "diary": {"type": "string"},
            "note": {"type": "string"},
        },
        "required": ["diary", "note"],
        "additionalProperties": False,
    }
    prompt = f"""
子どもの日記を、本人の修正希望に沿って直してください。
新しい出来事や感情をAIが足してはいけません。

現在の日記:
{draft}

本人の修正希望:
{correction}

元になった本人の発言:
{child_evidence}

本人の修正希望が元の発言と矛盾しても、最新の本人の修正を優先してください。
文章は5〜6歳らしい自然な日本語を保ってください。
note は「こう直したよ」のような短い説明にしてください。
""".strip()
    return ask_json(prompt, "revise_burari_diary", schema, 700)


# ============================================================
# Monthly review AI
# ============================================================
def build_month_evidence(bundle):
    trip_map = {t["id"]: t for t in bundle["trips"]}
    lines = []
    for d in sorted(bundle["diaries"], key=lambda x: trip_map.get(x["trip_id"], {}).get("trip_date", "")):
        trip = trip_map.get(d["trip_id"], {})
        lines.append(
            f"[{trip.get('trip_date', '')} / {trip.get('destination') or '行き先メモなし'}] 日記: {d.get('diary_text', '')}"
        )
    for p in bundle["photos"]:
        trip = trip_map.get(p["trip_id"], {})
        reflection = p.get("reflection_json") or {}
        conv = reflection.get("conversation", []) if isinstance(reflection, dict) else []
        child = [x.get("text", "") for x in conv if x.get("role") == "child"]
        if child:
            lines.append(f"[{trip.get('trip_date', '')} / 写真] 本人の発言: " + " / ".join(child))
    return "\n".join(lines)


def make_monthly_review(month_key, bundle):
    schema = {
        "type": "object",
        "properties": {
            "opening": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "theme": {"type": "string"},
                        "evidence": {"type": "string"},
                        "ask_child": {"type": "string"},
                    },
                    "required": ["theme", "evidence", "ask_child"],
                    "additionalProperties": False,
                },
            },
            "repeated_notices": {"type": "array", "items": {"type": "string"}},
            "wishes": {"type": "array", "items": {"type": "string"}},
            "one_question": {"type": "string"},
            "parent_note": {"type": "string"},
        },
        "required": ["opening", "findings", "repeated_notices", "wishes", "one_question", "parent_note"],
        "additionalProperties": False,
    }
    evidence = build_month_evidence(bundle)
    prompt = f"""
「東京ぶらり旅プロジェクト」の{month_key}の記録を振り返ります。
対象は5〜6歳の子どもです。

記録:
{evidence}

この振り返りの役割は、子どもを評価・分類することではなく、過去の本人の言葉を鏡のように返し、本人が自分の「気になる」に気づけるようにすることです。

厳守:
- 「観察力が高い」「社会課題に関心が強い」「○○タイプ」のような能力評価・性格診断をしない。
- 点数をつけない。
- 記録にないことを推測しない。
- evidence は具体的な日記・発言の事実にする。
- findings は最大3件。共通点が弱ければ無理に3件にしない。
- repeated_notices は、別の日にも繰り返し現れた本人の気づきだけ。なければ空配列。
- wishes は本人が実際に言った「こうだったら」「またやりたい」等だけ。なければ空配列。
- ask_child と one_question は、答えを誘導しない短い質問にする。
- opening は子ども向けに短く自然に。
- parent_note は保護者向けに、件数・日付・発言など観察可能な事実を中心に1〜3文でまとめる。
""".strip()
    return ask_json(prompt, "burari_monthly_review", schema, 1400)


def monthly_speech_text(review):
    parts = [review.get("opening", "")]
    for item in review.get("findings", [])[:3]:
        theme = str(item.get("theme", "")).strip()
        evidence = str(item.get("evidence", "")).strip()
        question = str(item.get("ask_child", "")).strip()
        if theme:
            parts.append(theme + "。")
        if evidence:
            parts.append(evidence)
        if question:
            parts.append(question)
    if review.get("one_question"):
        parts.append("最後にひとつ聞いてもいい？ " + review["one_question"])
    return " ".join(x for x in parts if x)


# ============================================================
# Session helpers
# ============================================================
def init_state():
    defaults = {
        "main_page": "home",
        "active_trip_id": None,
        "capture_serial": 0,
        "preferred_diary_trip_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Older deployed versions used the visible menu labels as state values.
    legacy_pages = {
        "📷 ぶらり旅": "camera",
        "📖 今日の日記": "diary",
        "📚 これまで": "review",
        "🔍 今月の発見": "review",
    }
    current_page = st.session_state.get("main_page")
    if current_page in legacy_pages:
        st.session_state["main_page"] = legacy_pages[current_page]

    next_page = st.session_state.pop("_next_page", None)
    if next_page:
        st.session_state["main_page"] = legacy_pages.get(next_page, next_page)

    if st.session_state.active_trip_id:
        active = get_trip(st.session_state.active_trip_id)
        if not active or active.get("status") != "active" or active.get("trip_date") != today_iso():
            st.session_state.active_trip_id = None

    if not st.session_state.active_trip_id:
        active = get_today_active_trip()
        if active:
            st.session_state.active_trip_id = active["id"]


def go_page(page_name):
    st.session_state["main_page"] = page_name
    st.rerun()


def ensure_today_trip():
    trip = get_trip(st.session_state.active_trip_id) if st.session_state.active_trip_id else None
    if trip and trip.get("status") == "active" and trip.get("trip_date") == today_iso():
        return trip
    trip = get_today_active_trip()
    if not trip:
        trip = create_trip("")
    st.session_state.active_trip_id = trip["id"]
    return trip


def render_home_button(label, page_name, key, ensure_trip=False):
    if st.button(label, key=key, use_container_width=True):
        if ensure_trip:
            ensure_today_trip()
        go_page(page_name)


def page_top(title, caption=""):
    c1, c2 = st.columns([1, 5], vertical_alignment="center")
    with c1:
        if st.button("←", key=f"home_back_{title}", help="ホームへ戻る", use_container_width=True):
            go_page("home")
    with c2:
        st.subheader(title)
    if caption:
        st.caption(caption)


def reflection_state(trip_id, photos):
    key = f"reflection_state_{trip_id}"
    photo_ids = [p["id"] for p in photos]
    if key not in st.session_state:
        st.session_state[key] = {
            "photo_ids": photo_ids,
            "photo_index": 0,
            "items": {},
            "audio_bytes": None,
            "audio_pending": False,
            "answer_serial": 0,
            "draft": None,
            "draft_title": None,
            "draft_meta": {},
            "raw_conversation": {},
            "draft_audio": None,
            "draft_audio_pending": False,
            "revision_serial": 0,
        }
    state = st.session_state[key]
    state["photo_ids"] = photo_ids
    for pid in photo_ids:
        state["items"].setdefault(
            pid,
            {"conversation": [], "signals": {}, "done": False, "started": False},
        )
    return state


def all_child_evidence(state):
    lines = []
    for pid in state.get("photo_ids", []):
        item = state.get("items", {}).get(pid, {})
        for turn in item.get("conversation", []):
            if turn.get("role") == "child":
                lines.append(str(turn.get("text", "")))
    return "\n".join(lines)


# ============================================================
# Rendering helpers
# ============================================================
def render_conversation(conversation):
    for turn in conversation:
        text = html.escape(str(turn.get("text", "")))
        if turn.get("role") == "assistant":
            st.markdown(f'<div class="ai-line"><b>AI</b><br>{text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="child-line"><b>ぼく</b><br>{text}</div>', unsafe_allow_html=True)


def trip_label(trip):
    destination = str(trip.get("destination") or "").strip()
    return f"{trip.get('trip_date', '')}　{destination or 'ぶらり旅'}"


def render_small_gallery(photos, max_count=4):
    subset = photos[:max_count]
    if not subset:
        return
    cols = st.columns(min(2, len(subset)))
    for idx, photo in enumerate(subset):
        try:
            image = download_photo(photo["storage_path"])
            with cols[idx % len(cols)]:
                st.image(image, use_container_width=True)
        except Exception:
            pass


# ============================================================
# Page: Home
# ============================================================
def page_home():
    st.title("📷 東京ぶらり旅")
    st.caption("答えを教える旅ではなく、自分なりの『気になる』を増やす旅。")

    active = get_trip(st.session_state.active_trip_id) if st.session_state.active_trip_id else None
    if active and active.get("status") == "active" and active.get("trip_date") == today_iso():
        photos = list_trip_photos(active["id"])
        destination = str(active.get("destination") or "").strip()
        label = destination or "今日のぶらり旅"
        st.caption(f"{label}　／　写真 {len(photos)}枚")

    with st.container(key="home_menu"):
        row1_left, row1_right = st.columns(2)
        with row1_left:
            render_home_button("📷\nカメラで撮る", "camera", "home_camera", ensure_trip=True)
        with row1_right:
            render_home_button("📖\n日記", "diary", "home_diary")

        row2_left, row2_right = st.columns(2)
        with row2_left:
            render_home_button("🔍\n振り返り", "review", "home_review")
        with row2_right:
            render_home_button("⚙️\n設定", "settings", "home_settings")

    st.caption("写真は何枚撮っても、0枚でも構いません。気になったときだけ使います。")


# ============================================================
# Page: Trip / camera
# ============================================================
def page_trip():
    page_top(
        "📷 カメラで撮る",
        "気になったものだけ残します。便利・不便を探す必要も、何枚か撮る必要もありません。",
    )

    trip = ensure_today_trip()
    photos = list_trip_photos(trip["id"])
    destination = str(trip.get("destination") or "").strip()
    st.markdown(f"**{trip.get('trip_date', '')}　{destination or '今日のぶらり旅'}**　／　写真 {len(photos)}枚")

    st.markdown("#### 写真を追加")
    st.caption("『いま写真を撮る』はスマホ標準のカメラアプリを起動する方式です。ブラウザ内カメラの権限画面は使いません。")

    pending_key = f"pending_camera_photo_{trip['id']}"
    digest_key = f"pending_camera_digest_{trip['id']}"
    pending = st.session_state.get(pending_key)

    if pending is None:
        if native_camera_component is not None:
            result = native_camera_component(
                key=f"native_camera_{trip['id']}_{st.session_state.capture_serial}",
                on_photo_change=lambda: None,
                on_camera_error_change=lambda: None,
            )
            payload = getattr(result, "photo", None)
            camera_error = getattr(result, "camera_error", None)
            if camera_error:
                st.warning("カメラから写真を受け取れませんでした。もう一度試してください。")
            if isinstance(payload, dict) and payload.get("data_url"):
                try:
                    raw = decode_camera_data_url(payload["data_url"])
                    digest = hashlib.sha1(raw).hexdigest()
                    if st.session_state.get(digest_key) != digest:
                        st.session_state[pending_key] = raw
                        st.session_state[digest_key] = digest
                        pending = raw
                except Exception as exc:
                    st.error("撮影した写真を読み込めませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
        else:
            st.error("スマホカメラ機能に必要なStreamlitのバージョンが古いです。requirements.txtを更新してください。")

    if pending is not None:
        st.image(pending, caption="この写真を残す？", use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("この写真を残す", type="primary", use_container_width=True, key="save_native_camera"):
                try:
                    with st.spinner("写真を残しています…"):
                        upload_photo(trip["id"], pending)
                    st.session_state.pop(pending_key, None)
                    st.session_state.pop(digest_key, None)
                    st.session_state.capture_serial += 1
                    st.rerun()
                except Exception as exc:
                    st.error("写真を保存できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
        with c2:
            if st.button("撮りなおす", use_container_width=True, key="retry_native_camera"):
                st.session_state.pop(pending_key, None)
                st.session_state.pop(digest_key, None)
                st.session_state.capture_serial += 1
                st.rerun()

    with st.expander("🖼 すでに撮った写真から選ぶ"):
        st.caption("カメラではなく、スマホの写真フォルダにある画像を使う場合はこちらです。")
        upload = st.file_uploader(
            "写真を選ぶ",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=False,
            key=f"gallery_photo_{trip['id']}_{st.session_state.capture_serial}",
        )
        if upload is not None:
            st.image(upload, caption="この写真を残す？", use_container_width=True)
            g1, g2 = st.columns(2)
            with g1:
                if st.button(
                    "この写真を残す",
                    type="primary",
                    use_container_width=True,
                    key=f"save_gallery_{st.session_state.capture_serial}",
                ):
                    try:
                        with st.spinner("写真を残しています…"):
                            upload_photo(trip["id"], upload.getvalue())
                        st.session_state.capture_serial += 1
                        st.rerun()
                    except Exception as exc:
                        st.error("写真を保存できませんでした。")
                        with st.expander("保護者向け詳細"):
                            st.code(str(exc))
            with g2:
                if st.button(
                    "選びなおす",
                    use_container_width=True,
                    key=f"retry_gallery_{st.session_state.capture_serial}",
                ):
                    st.session_state.capture_serial += 1
                    st.rerun()

    if photos:
        st.markdown("#### 今日の写真")
        render_small_gallery(list(reversed(photos)), max_count=6)

    st.caption("人の顔・住所・学校名など、個人が分かる情報は必要以上に撮らないようにしてください。")

    if photos and st.button("撮影を終えて日記へ", type="primary", use_container_width=True):
        try:
            finish_trip(trip["id"])
            st.session_state.preferred_diary_trip_id = trip["id"]
            st.session_state.active_trip_id = None
            st.session_state["_next_page"] = "diary"
            st.rerun()
        except Exception as exc:
            st.error("旅を終了できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

# ============================================================
# Page: Diary conversation
# ============================================================
def page_diary():
    page_top(
        "📖 日記",
        "写真を見ながらAIと少し話します。AIは本人が話していない内容を日記に足しません。",
    )

    active = get_trip(st.session_state.active_trip_id) if st.session_state.active_trip_id else None
    if active and active.get("status") == "active" and active.get("trip_date") == today_iso():
        active_photos = list_trip_photos(active["id"])
        if active_photos:
            st.info(f"今日のぶらり旅に写真が {len(active_photos)}枚あります。日記を作るなら、ここで旅を区切ります。")
            if st.button("今日の写真で日記をつくる", type="primary", use_container_width=True):
                try:
                    finish_trip(active["id"])
                    st.session_state.preferred_diary_trip_id = active["id"]
                    st.session_state.active_trip_id = None
                    st.rerun()
                except Exception as exc:
                    st.error("日記の準備ができませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
        else:
            st.caption("今日のぶらり旅は始まっていますが、まだ写真はありません。")

    trips = list_recent_trips_for_diary()
    if not trips:
        st.info("まだ振り返れるぶらり旅がありません。")
        return

    ids = [t["id"] for t in trips]
    preferred = st.session_state.preferred_diary_trip_id
    default_index = ids.index(preferred) if preferred in ids else 0
    trip_id = st.selectbox(
        "振り返る日",
        ids,
        index=default_index,
        format_func=lambda x: trip_label(next(t for t in trips if t["id"] == x)),
        key="diary_trip_selector",
    )
    trip = next(t for t in trips if t["id"] == trip_id)
    photos = list_trip_photos(trip_id)
    existing = get_diary_for_trip(trip_id)

    if existing and f"reflection_state_{trip_id}" not in st.session_state:
        st.markdown(
            f"""
            <div class="diary-card">
              <div class="hero-title">{html.escape(existing.get('title') or 'ぶらり旅の日記')}</div>
              <div class="big-text">{html.escape(existing.get('diary_text') or '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("この日の写真から、もう一度日記をつくる", use_container_width=True):
            st.session_state[f"reflection_state_{trip_id}"] = {
                "photo_ids": [p["id"] for p in photos],
                "photo_index": 0,
                "items": {},
                "audio_bytes": None,
                "audio_pending": False,
                "answer_serial": 0,
                "draft": None,
                "draft_title": None,
                "draft_meta": {},
                "raw_conversation": {},
                "draft_audio": None,
                "draft_audio_pending": False,
                "revision_serial": 0,
            }
            st.rerun()
        return

    if not photos:
        st.warning("このぶらり旅には写真がありません。写真のある旅を選んでください。")
        return

    state = reflection_state(trip_id, photos)
    photo_map = {p["id"]: p for p in photos}

    # All photos reviewed -> draft diary
    if state["photo_index"] >= len(state["photo_ids"]):
        if not state.get("draft"):
            st.success("写真のお話はここまで。日記にまとめられます。")
            if st.button("AIと日記をつくる", type="primary", use_container_width=True):
                try:
                    photo_states = []
                    for pid in state["photo_ids"]:
                        item = state["items"].get(pid, {})
                        photo_states.append(
                            {
                                "photo_id": pid,
                                "conversation": item.get("conversation", []),
                                "signals": item.get("signals", {}),
                            }
                        )
                    with st.spinner("話したことを日記にまとめています…"):
                        result, raw = compose_diary(trip, photo_states)
                        audio = speech_bytes(result["diary"])
                    state["draft"] = result["diary"]
                    state["draft_title"] = result["title"]
                    state["draft_meta"] = {
                        "child_points": result.get("child_points", []),
                        "signals": result.get("signals", {}),
                    }
                    state["raw_conversation"] = raw
                    state["draft_audio"] = audio
                    state["draft_audio_pending"] = True
                    st.rerun()
                except Exception as exc:
                    st.error("日記をまとめられませんでした。もう一度試してください。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
            return

        st.markdown(
            f"""
            <div class="diary-card">
              <div class="hero-title">{html.escape(state.get('draft_title') or '今日のぶらり旅')}</div>
              <div class="big-text">{html.escape(state.get('draft') or '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if state.get("draft_audio"):
            st.audio(
                state["draft_audio"],
                format="audio/wav",
                autoplay=bool(state.get("draft_audio_pending")),
            )
            state["draft_audio_pending"] = False

        st.markdown("#### 直したいところはある？")
        st.caption("なければ、そのまま保存してOKです。")
        correction_audio = st.audio_input(
            "直したいことを話してね",
            sample_rate=16000,
            key=f"diary_revision_{trip_id}_{state['revision_serial']}",
        )
        correction_digest_key = f"diary_revision_digest_{trip_id}_{state['revision_serial']}"
        if correction_audio is not None:
            digest = audio_digest(correction_audio)
            if digest and st.session_state.get(correction_digest_key) != digest:
                try:
                    audio_file = io.BytesIO(correction_audio.getvalue())
                    audio_file.name = "revision.wav"
                    with st.spinner("聞いています…"):
                        correction = transcribe_audio(
                            audio_file,
                            "東京ぶらり旅の日記を読み、子どもが直したいところを話しています。",
                        )
                        revised = revise_diary(
                            state["draft"],
                            correction,
                            all_child_evidence(state),
                        )
                        new_audio = speech_bytes(revised["diary"])
                    state["draft"] = revised["diary"]
                    state["draft_audio"] = new_audio
                    state["draft_audio_pending"] = True
                    state["revision_serial"] += 1
                    st.session_state[correction_digest_key] = digest
                    st.rerun()
                except Exception as exc:
                    st.error("修正を反映できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))

        if st.button("この日記を保存する", type="primary", use_container_width=True):
            try:
                save_diary(
                    trip_id,
                    state.get("draft_title") or "ぶらり旅の日記",
                    state["draft"],
                    state.get("raw_conversation", {}),
                    state.get("draft_meta", {}),
                )
                st.session_state.pop(f"reflection_state_{trip_id}", None)
                st.session_state.preferred_diary_trip_id = None
                st.session_state["_next_page"] = "review"
                st.rerun()
            except Exception as exc:
                st.error("日記を保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        return

    # Current photo conversation
    pid = state["photo_ids"][state["photo_index"]]
    photo = photo_map[pid]
    item = state["items"][pid]
    st.markdown(f"#### 写真 {state['photo_index'] + 1} / {len(state['photo_ids'])}")
    try:
        image_bytes = download_photo(photo["storage_path"])
        st.image(image_bytes, use_container_width=True)
    except Exception as exc:
        st.error("写真を読み込めませんでした。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        return

    if not item.get("started"):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("この写真について話す", type="primary", use_container_width=True):
                try:
                    with st.spinner("写真を見ています…"):
                        question = initial_photo_question(image_bytes)
                        audio = speech_bytes(question)
                    item["conversation"] = [{"role": "assistant", "text": question}]
                    item["started"] = True
                    state["audio_bytes"] = audio
                    state["audio_pending"] = True
                    state["answer_serial"] += 1
                    st.rerun()
                except Exception as exc:
                    st.error("写真について話し始められませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
        with c2:
            if st.button("この写真はとばす", use_container_width=True):
                item["done"] = True
                item["started"] = True
                update_photo_reflection(pid, [], {})
                state["photo_index"] += 1
                st.rerun()
        return

    render_conversation(item.get("conversation", []))
    if state.get("audio_bytes"):
        st.audio(
            state["audio_bytes"],
            format="audio/wav",
            autoplay=bool(state.get("audio_pending")),
        )
        state["audio_pending"] = False

    if item.get("done"):
        if st.button("つぎの写真へ", type="primary", use_container_width=True):
            state["photo_index"] += 1
            state["audio_bytes"] = None
            state["audio_pending"] = False
            state["answer_serial"] += 1
            st.rerun()
        return

    answer_audio = st.audio_input(
        "マイクを押して話してね",
        sample_rate=16000,
        key=f"photo_answer_{trip_id}_{pid}_{state['answer_serial']}",
    )
    digest_key = f"photo_answer_digest_{trip_id}_{pid}_{state['answer_serial']}"
    if answer_audio is not None:
        digest = audio_digest(answer_audio)
        if digest and st.session_state.get(digest_key) != digest:
            try:
                audio_file = io.BytesIO(answer_audio.getvalue())
                audio_file.name = "child_answer.wav"
                with st.spinner("声を聞いています…"):
                    transcript = transcribe_audio(
                        audio_file,
                        "東京ぶらり旅の写真を見ながら、AIの短い質問に子どもが答えています。",
                    )
                    if not transcript:
                        raise ValueError("文字起こしが空でした。")
                    item["conversation"].append({"role": "child", "text": transcript})
                    child_turns = sum(1 for x in item["conversation"] if x.get("role") == "child")
                    result = next_photo_turn(image_bytes, item["conversation"], child_turns)
                    assistant_text = str(result.get("reply", "")).strip()
                    if result.get("next_question"):
                        assistant_text = (assistant_text + " " + str(result["next_question"]).strip()).strip()
                    if not assistant_text:
                        assistant_text = "教えてくれてありがとう。"
                    item["conversation"].append({"role": "assistant", "text": assistant_text})
                    item["signals"] = merge_signals(item.get("signals", {}), result.get("signals", {}))
                    item["done"] = bool(result.get("done"))
                    update_photo_reflection(pid, item["conversation"], item["signals"])
                    audio = speech_bytes(assistant_text)
                state["audio_bytes"] = audio
                state["audio_pending"] = True
                state["answer_serial"] += 1
                st.session_state[digest_key] = digest
                st.rerun()
            except Exception as exc:
                st.error("うまく聞き取れませんでした。もう一度話してください。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    if st.button("この写真のお話はここまで", use_container_width=True):
        item["done"] = True
        update_photo_reflection(pid, item.get("conversation", []), item.get("signals", {}))
        state["audio_bytes"] = speech_bytes("教えてくれてありがとう。つぎの写真にいこう。")
        state["audio_pending"] = True
        st.rerun()


# ============================================================
# Page: History
# ============================================================
def page_history(embedded=False):
    if not embedded:
        page_top("📚 これまでの日記")
    rows = list_recent_diaries()
    if not rows:
        st.info("まだ日記はありません。")
        return

    for row in rows:
        diary = row["diary"]
        trip = row["trip"]
        title = f"{trip.get('trip_date', '')}　{diary.get('title') or trip.get('destination') or 'ぶらり旅'}"
        with st.expander(title):
            photos = list_trip_photos(diary["trip_id"])
            render_small_gallery(photos, max_count=4)
            st.markdown(
                f"""
                <div class="diary-card">
                  <div class="big-text">{html.escape(diary.get('diary_text') or '')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            meta = diary.get("ai_meta") or {}
            child_points = meta.get("child_points", []) if isinstance(meta, dict) else []
            if child_points:
                with st.expander("この日記のもとになった言葉"):
                    for point in child_points[:3]:
                        st.write("・" + str(point))


# ============================================================
# Page: Monthly review
# ============================================================
def page_monthly(embedded=False):
    if not embedded:
        page_top("🔍 今月の発見")
    st.caption("AIが評価するのではなく、これまでの本人の言葉をつないで返します。")

    recent = list_recent_diaries(limit=120)
    month_keys = []
    for row in recent:
        trip_date = str(row.get("trip", {}).get("trip_date") or "")
        if len(trip_date) >= 7:
            key = trip_date[:7]
            if key not in month_keys:
                month_keys.append(key)
    current_month = now_jst().strftime("%Y-%m")
    if current_month not in month_keys:
        month_keys.insert(0, current_month)
    if not month_keys:
        month_keys = [current_month]

    month_key = st.selectbox("振り返る月", month_keys, key="monthly_selector")
    bundle = get_month_bundle(month_key)
    completed_count = len(bundle["diaries"])
    st.write(f"この月の日記：**{completed_count}回**")
    if completed_count == 0:
        st.info("この月には、まだ保存された日記がありません。")
        return

    saved = get_saved_monthly_review(month_key)
    session_key = f"monthly_review_{month_key}"
    if session_key not in st.session_state and saved:
        st.session_state[session_key] = saved.get("review_json") or {}
    review = st.session_state.get(session_key)

    button_label = "AIと今月を振り返る" if not review else "今の記録でもう一度まとめる"
    if st.button(button_label, type="primary" if not review else "secondary", use_container_width=True):
        try:
            with st.spinner("今月の言葉をつないでいます…"):
                review = make_monthly_review(month_key, bundle)
                save_monthly_review(month_key, review)
                audio = speech_bytes(monthly_speech_text(review))
            st.session_state[session_key] = review
            st.session_state[f"monthly_audio_{month_key}"] = audio
            st.session_state[f"monthly_audio_pending_{month_key}"] = True
            st.rerun()
        except Exception as exc:
            st.error("今月の振り返りを作れませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    review = st.session_state.get(session_key)
    if not review:
        return

    st.markdown(
        f'<div class="monthly-card"><div class="big-text">{html.escape(review.get("opening", ""))}</div></div>',
        unsafe_allow_html=True,
    )
    audio = st.session_state.get(f"monthly_audio_{month_key}")
    if audio:
        st.audio(
            audio,
            format="audio/wav",
            autoplay=bool(st.session_state.get(f"monthly_audio_pending_{month_key}", False)),
        )
        st.session_state[f"monthly_audio_pending_{month_key}"] = False

    for idx, finding in enumerate(review.get("findings", []), start=1):
        st.markdown(f"#### {idx}. {finding.get('theme', '')}")
        st.write(finding.get("evidence", ""))
        if finding.get("ask_child"):
            st.info(f"聞いてみる：{finding['ask_child']}")

    repeated = review.get("repeated_notices", []) or []
    if repeated:
        st.markdown("#### 前にも出てきた『気になる』")
        for item in repeated:
            st.write("・" + str(item))

    wishes = review.get("wishes", []) or []
    if wishes:
        st.markdown("#### 『こうだったらいいな』の記録")
        for item in wishes:
            st.write("・" + str(item))

    if review.get("one_question"):
        st.markdown("#### 最後にひとつ")
        st.info(review["one_question"])

    with st.expander("保護者向けメモ"):
        st.write(review.get("parent_note", ""))
        st.caption("能力評価や性格診断ではなく、保存された発言・日記の範囲でまとめています。")


# ============================================================
# Page: Review / Settings
# ============================================================
def page_review():
    page_top(
        "🔍 振り返り",
        "過去の日記を読み返したり、1か月分の『気になる』をAIとつないだりします。",
    )
    tab_history, tab_month = st.tabs(["📚 これまでの日記", "🔍 今月の発見"])
    with tab_history:
        page_history(embedded=True)
    with tab_month:
        page_monthly(embedded=True)


def page_settings():
    page_top("⚙️ 設定", "旅の行き先メモや区切りを保護者が調整できます。")

    active = get_trip(st.session_state.active_trip_id) if st.session_state.active_trip_id else None
    if active and active.get("status") == "active" and active.get("trip_date") == today_iso():
        photos = list_trip_photos(active["id"])
        st.markdown("#### 今日のぶらり旅")
        st.write(f"日付：**{active.get('trip_date', '')}**　／　写真：**{len(photos)}枚**")
        destination = st.text_input(
            "行き先メモ（任意）",
            value=str(active.get("destination") or ""),
            placeholder="例：神楽坂、浅草のあたり",
            key=f"settings_destination_{active['id']}",
        )
        if st.button("行き先メモを保存", use_container_width=True):
            try:
                update_trip_destination(active["id"], destination)
                st.success("保存しました。")
            except Exception as exc:
                st.error("保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

        if photos and st.button("この旅を区切って日記へ", type="primary", use_container_width=True):
            try:
                finish_trip(active["id"])
                st.session_state.preferred_diary_trip_id = active["id"]
                st.session_state.active_trip_id = None
                st.session_state["_next_page"] = "diary"
                st.rerun()
            except Exception as exc:
                st.error("旅を区切れませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    else:
        st.info("今日はまだぶらり旅を始めていません。")
        if st.button("今日のぶらり旅を始める", type="primary", use_container_width=True):
            ensure_today_trip()
            go_page("camera")

    st.divider()
    st.markdown("#### カメラについて")
    st.write(
        "通常は『カメラで撮る』画面の『写真を撮る・選ぶ』を使います。"
        "これはスマホの写真選択機能を使うため、Streamlit画面内のカメラ権限が使えない端末でも動きやすい方式です。"
    )
    st.caption("ブラウザの直接カメラは任意機能として残しています。Safari/Chromeでカメラ権限を許可した場合だけ使えます。")

    st.divider()
    st.markdown("#### プロジェクトの考え方")
    st.caption("写真の枚数や『便利・不便を見つけること』を課題にはしません。本人が気になったものを残し、あとから本人の言葉で振り返ります。")


# ============================================================
# Main UI
# ============================================================
verify_setup()
require_family_pin()
init_state()

page = st.session_state.get("main_page", "home")
if page == "home":
    page_home()
elif page == "camera":
    page_trip()
elif page == "diary":
    page_diary()
elif page == "review":
    page_review()
elif page == "settings":
    page_settings()
else:
    st.session_state["main_page"] = "home"
    st.rerun()
