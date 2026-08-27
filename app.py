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
import wave
import sys
from array import array
from urllib.parse import urlencode
from urllib.request import Request, urlopen
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
      /* ---------------- Home: calm, mobile-first dashboard ---------------- */
      .home-hero {
        margin: .15rem 0 1rem;
        padding: 1.15rem 1.2rem 1.05rem;
        border-radius: 24px;
        border: 1px solid rgba(74, 144, 226, .14);
        background:
          radial-gradient(circle at 92% 0%, rgba(74, 144, 226, .12), transparent 34%),
          linear-gradient(145deg, rgba(74, 144, 226, .055), rgba(255,255,255,0));
        box-shadow: 0 10px 30px rgba(30, 58, 95, .055);
      }
      .home-eyebrow {
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .12em;
        opacity: .58;
        margin-bottom: .35rem;
      }
      .home-title {
        font-size: 1.9rem;
        font-weight: 850;
        letter-spacing: -.02em;
        line-height: 1.18;
      }
      .home-tagline {
        margin-top: .45rem;
        font-size: .96rem;
        line-height: 1.55;
        opacity: .70;
      }
      .home-status {
        display: flex;
        align-items: center;
        gap: .55rem;
        flex-wrap: wrap;
        margin: -.25rem 0 1.05rem;
        padding: .68rem .82rem;
        border: 1px solid rgba(128,128,128,.14);
        border-radius: 16px;
        background: rgba(128,128,128,.035);
        font-size: .88rem;
        line-height: 1.35;
      }
      .home-status-badge {
        display: inline-flex;
        align-items: center;
        min-height: 1.7rem;
        padding: .16rem .48rem;
        border-radius: 999px;
        background: rgba(74, 144, 226, .10);
        font-size: .76rem;
        font-weight: 800;
        white-space: nowrap;
      }
      .home-status-main { font-weight: 800; }
      .home-status-sub { opacity: .66; }
      .home-section-label {
        margin: .2rem 0 .5rem;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .08em;
        opacity: .55;
      }
      .st-key-home_primary [data-testid="stHorizontalBlock"],
      .st-key-home_secondary [data-testid="stHorizontalBlock"] {
        gap: .72rem;
      }
      .st-key-home_primary div.stButton > button,
      .st-key-home_secondary div.stButton > button {
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
        white-space: pre-line !important;
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
      }
      .st-key-home_primary div.stButton > button {
        height: 6.45rem !important;
        min-height: 6.45rem !important;
        max-height: 6.45rem !important;
        border-radius: 24px !important;
        font-size: 1.18rem !important;
        font-weight: 820 !important;
        line-height: 1.35 !important;
      }
      .st-key-home_secondary div.stButton > button {
        height: 4.85rem !important;
        min-height: 4.85rem !important;
        max-height: 4.85rem !important;
        border-radius: 20px !important;
        font-size: 1.03rem !important;
        font-weight: 760 !important;
        line-height: 1.3 !important;
      }
      .st-key-home_camera div.stButton > button,
      .st-key-home_camera button,
      .st-key-home_diary div.stButton > button,
      .st-key-home_diary button {
        border: 1.5px solid rgba(74, 144, 226, .66) !important;
        background: linear-gradient(145deg, rgba(74, 144, 226, .11), rgba(74, 144, 226, .035)) !important;
        box-shadow: 0 7px 18px rgba(74, 144, 226, .08) !important;
      }
      .st-key-home_camera div.stButton > button:hover,
      .st-key-home_diary div.stButton > button:hover {
        transform: translateY(-1px);
        background: linear-gradient(145deg, rgba(74, 144, 226, .16), rgba(74, 144, 226, .055)) !important;
        box-shadow: 0 9px 22px rgba(74, 144, 226, .12) !important;
      }
      .st-key-home_review div.stButton > button,
      .st-key-home_review button {
        border: 1.5px solid rgba(245, 158, 11, .62) !important;
        background: linear-gradient(145deg, rgba(245, 158, 11, .10), rgba(245, 158, 11, .025)) !important;
        box-shadow: 0 5px 15px rgba(245, 158, 11, .055) !important;
      }
      .st-key-home_settings div.stButton > button,
      .st-key-home_settings button {
        border: 1px solid rgba(128,128,128,.22) !important;
        background: rgba(128,128,128,.035) !important;
      }
      .st-key-home_destination {
        margin-top: .42rem;
      }
      .st-key-home_destination div.stButton > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        height: auto !important;
        max-height: none !important;
        border-radius: 14px !important;
        border: 1px solid rgba(128,128,128,.16) !important;
        background: rgba(128,128,128,.025) !important;
        font-size: .86rem !important;
        font-weight: 670 !important;
        line-height: 1.25 !important;
        opacity: .78;
        padding: .52rem .66rem !important;
      }
      .st-key-home_destination div.stButton > button:hover {
        opacity: 1;
        background: rgba(74, 144, 226, .055) !important;
        border-color: rgba(74, 144, 226, .28) !important;
      }
      .home-footer-note {
        margin-top: 1rem;
        text-align: center;
        font-size: .78rem;
        line-height: 1.45;
        opacity: .48;
      }
      .st-key-diary_photo_nav div.stButton > button,
      .st-key-diary_photo_nav button {
        border: 2px solid #4A90E2 !important;
        background: rgba(74, 144, 226, .08) !important;
        color: inherit !important;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, .04) inset;
      }
      .st-key-diary_photo_nav div.stButton > button:hover,
      .st-key-diary_photo_nav button:hover {
        background: rgba(74, 144, 226, .13) !important;
        border-color: #3B82C4 !important;
      }
      .st-key-history_back_nav div.stButton > button,
      .st-key-history_back_nav button {
        border: 2px solid #4A90E2 !important;
        background: rgba(74, 144, 226, .08) !important;
        color: inherit !important;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, .04) inset;
      }
      .st-key-history_back_nav div.stButton > button:hover,
      .st-key-history_back_nav button:hover {
        background: rgba(74, 144, 226, .13) !important;
        border-color: #3B82C4 !important;
      }
      .st-key-history_home_nav div.stButton > button,
      .st-key-history_home_nav button {
        border: 2px solid #2F9E73 !important;
        background: rgba(47, 158, 115, .08) !important;
        color: inherit !important;
        box-shadow: 0 0 0 2px rgba(47, 158, 115, .04) inset;
      }
      .st-key-history_home_nav div.stButton > button:hover,
      .st-key-history_home_nav button:hover {
        background: rgba(47, 158, 115, .13) !important;
        border-color: #278663 !important;
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
        .home-hero {
          padding: 1rem 1rem .92rem;
          border-radius: 21px;
        }
        .home-title { font-size: 1.72rem; }
        .home-tagline { font-size: .90rem; }
        .st-key-home_primary div.stButton > button {
          height: 5.95rem !important;
          min-height: 5.95rem !important;
          max-height: 5.95rem !important;
          border-radius: 21px !important;
          font-size: 1.05rem !important;
        }
        .st-key-home_secondary div.stButton > button {
          height: 4.45rem !important;
          min-height: 4.45rem !important;
          max-height: 4.45rem !important;
          border-radius: 18px !important;
          font-size: .94rem !important;
        }
        .st-key-home_destination div.stButton > button {
          min-height: 2.55rem !important;
          font-size: .80rem !important;
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
# Live mobile camera component
# ============================================================
# Use getUserMedia so the app opens a live camera preview instead of handing
# control to the OS file picker. Browser permission is still required; no web
# app can bypass a camera permission that the user/browser has denied.
_LIVE_CAMERA_HTML = """
<div class="live-camera-wrap">
  <canvas id="live-camera-canvas" hidden></canvas>

  <div id="camera-menu" class="camera-menu">
    <button id="live-camera-start" class="camera-menu-button" type="button">📷 カメラを開く</button>
    <input id="gallery-photo-input" class="gallery-photo-input" type="file" accept="image/*" />
    <label class="camera-menu-button gallery-button" for="gallery-photo-input">🖼 すでに撮った写真から選ぶ</label>
  </div>

  <div id="camera-active-actions" class="camera-active-actions" hidden>
    <button id="live-camera-shoot" class="camera-shoot-button" type="button">● 撮影する</button>
    <button id="live-camera-stop" class="camera-sub-button" type="button">閉じる</button>
  </div>

  <video id="live-camera-video" class="live-camera-video" playsinline autoplay muted hidden></video>

  <div id="camera-review" class="camera-review" hidden>
    <div class="camera-review-actions">
      <button id="camera-review-save" class="camera-save-button" type="button">この写真を残す</button>
      <button id="camera-review-retry" class="camera-retry-button" type="button">撮りなおす／選びなおす</button>
    </div>
    <img id="camera-review-image" class="camera-review-image" alt="撮影した写真の確認" />
  </div>

  <div id="live-camera-status" class="camera-status" aria-live="polite" hidden></div>
</div>
"""

_LIVE_CAMERA_CSS = """
.live-camera-wrap {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--st-font);
  padding: 0;
  margin: 0;
}
.camera-menu[hidden],
.camera-active-actions[hidden],
.live-camera-video[hidden],
.camera-review[hidden],
.camera-status[hidden] {
  display: none !important;
}
.camera-menu {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin: 0;
}
.gallery-photo-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.camera-menu-button,
.gallery-button,
.camera-shoot-button,
.camera-sub-button,
.camera-save-button,
.camera-retry-button {
  width: 100%;
  min-height: 72px;
  box-sizing: border-box;
  border-radius: 18px;
  font-size: 18px;
  font-weight: 800;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 12px 16px;
}
.camera-menu-button,
.gallery-button {
  border: 2px solid var(--st-primary-color);
  background: color-mix(in srgb, var(--st-primary-color) 8%, transparent);
  color: var(--st-text-color);
}
.gallery-button {
  border-color: rgba(128,128,128,.28);
  background: transparent;
}
.live-camera-video,
.camera-review-image {
  width: 100%;
  max-height: 58dvh;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  box-sizing: border-box;
  border-radius: 16px;
  background: #000;
  margin: 0;
}
.camera-active-actions,
.camera-review-actions {
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 8px;
  margin: 0 0 8px 0;
}
.camera-shoot-button {
  border: 2px solid var(--st-primary-color);
  background: var(--st-primary-color);
  color: white;
}
.camera-save-button {
  border: 2px solid #15803d;
  background: #16a34a;
  color: white;
  box-shadow: 0 0 0 3px rgba(22, 163, 74, .14);
}
.camera-save-button:hover,
.camera-save-button:focus-visible {
  border-color: #166534;
  background: #15803d;
}
.camera-sub-button,
.camera-retry-button {
  border: 1px solid rgba(128,128,128,.28);
  background: transparent;
  color: var(--st-text-color);
}
.camera-review {
  width: 100%;
  margin: 0;
}
.camera-status {
  margin: 8px 0 0 0;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 193, 7, .12);
  font-size: 13px;
  line-height: 1.45;
}
@media (max-width: 640px) {
  .camera-menu-button,
  .gallery-button {
    min-height: 68px;
    font-size: 17px;
  }
  .camera-active-actions,
  .camera-review-actions {
    grid-template-columns: 3fr 1fr;
  }
  .camera-shoot-button,
  .camera-sub-button,
  .camera-save-button,
  .camera-retry-button {
    min-height: 58px;
    font-size: 15px;
    padding-left: 8px;
    padding-right: 8px;
  }
}
"""

_LIVE_CAMERA_JS = r"""
export default function(component) {
  const { parentElement, setTriggerValue, data } = component;
  const video = parentElement.querySelector('#live-camera-video');
  const canvas = parentElement.querySelector('#live-camera-canvas');
  const menu = parentElement.querySelector('#camera-menu');
  const startButton = parentElement.querySelector('#live-camera-start');
  const galleryInput = parentElement.querySelector('#gallery-photo-input');
  const activeActions = parentElement.querySelector('#camera-active-actions');
  const shootButton = parentElement.querySelector('#live-camera-shoot');
  const stopButton = parentElement.querySelector('#live-camera-stop');
  const review = parentElement.querySelector('#camera-review');
  const reviewImage = parentElement.querySelector('#camera-review-image');
  const reviewSave = parentElement.querySelector('#camera-review-save');
  const reviewRetry = parentElement.querySelector('#camera-review-retry');
  const status = parentElement.querySelector('#live-camera-status');

  let stream = null;
  let pendingPhoto = null;

  const setStatus = (message) => {
    if (!status) return;
    status.textContent = message || '';
    status.hidden = !message;
  };

  const hideReview = () => {
    if (review) review.hidden = true;
    if (reviewImage) reviewImage.removeAttribute('src');
  };

  const showMenu = () => {
    if (menu) menu.hidden = false;
    if (activeActions) activeActions.hidden = true;
    if (video) video.hidden = true;
    hideReview();
  };

  const showCameraActions = () => {
    if (menu) menu.hidden = true;
    if (activeActions) activeActions.hidden = false;
    if (video) video.hidden = false;
    hideReview();
  };

  const showReview = (dataUrl) => {
    if (menu) menu.hidden = true;
    if (activeActions) activeActions.hidden = true;
    // Hide only the preview element. The MediaStream itself keeps running so a
    // camera retry is immediate and does not require reopening the camera.
    if (video) video.hidden = true;
    if (reviewImage) reviewImage.src = dataUrl;
    if (review) review.hidden = false;
  };

  const stopStream = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (video) {
      video.pause();
      video.srcObject = null;
      video.hidden = true;
    }
    pendingPhoto = null;
    showMenu();
  };

  const errorMessage = (err) => {
    const name = (err && err.name) ? err.name : '';
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
      return 'カメラが許可されていません。ブラウザのサイト設定でカメラを「許可」にして、このページを再読み込みしてください。';
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') return '利用できるカメラが見つかりませんでした。';
    if (name === 'NotReadableError' || name === 'TrackStartError') return 'カメラを開けませんでした。ほかのアプリがカメラを使っていないか確認してください。';
    if (name === 'SecurityError') return 'ブラウザのセキュリティ設定でカメラがブロックされています。';
    return 'カメラを開けませんでした。ブラウザのカメラ権限を確認してください。';
  };

  const startCamera = async () => {
    stopStream();
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const message = 'このブラウザでは直接カメラを開けません。ChromeまたはSafariの最新版で開いてください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'Unsupported', message });
      return;
    }

    setStatus('カメラの使用を許可してください…');
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      video.srcObject = stream;
      await video.play();
      shootButton.disabled = false;
      showCameraActions();
      try {
        localStorage.setItem('tokyo_burari_last_camera_open_v1', String(Date.now()));
      } catch (_) {}
      setStatus('');
    } catch (err) {
      console.error(err);
      stopStream();
      const message = errorMessage(err);
      setStatus(message);
      setTriggerValue('camera_error', {
        name: (err && err.name) ? err.name : 'CameraError',
        message,
        detail: (err && err.message) ? String(err.message) : ''
      });
    }
  };

  const blobToDataUrl = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

  const getLocationAtCapture = () => new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({
        ok: false,
        error_code: 'UNSUPPORTED',
        error_message: 'このブラウザでは位置情報を取得できません。'
      });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          ok: true,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy_m: position.coords.accuracy,
          altitude_m: position.coords.altitude,
          heading_deg: position.coords.heading,
          speed_mps: position.coords.speed,
          measured_at: new Date(position.timestamp).toISOString()
        });
      },
      (error) => {
        let code = 'POSITION_ERROR';
        let message = '位置情報を取得できませんでした。';
        if (error && error.code === 1) {
          code = 'PERMISSION_DENIED';
          message = '位置情報が許可されていません。';
        } else if (error && error.code === 2) {
          code = 'POSITION_UNAVAILABLE';
          message = '端末の位置情報を利用できません。';
        } else if (error && error.code === 3) {
          code = 'TIMEOUT';
          message = '位置情報の取得が時間切れになりました。';
        }
        resolve({ ok: false, error_code: code, error_message: message });
      },
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 15000 }
    );
  });

  const prepareImageFile = async (file) => {
    const url = URL.createObjectURL(file);
    try {
      const img = await new Promise((resolve, reject) => {
        const node = new Image();
        node.onload = () => resolve(node);
        node.onerror = reject;
        node.src = url;
      });
      const srcW = img.naturalWidth || img.width;
      const srcH = img.naturalHeight || img.height;
      const maxSide = 1600;
      const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
      const width = Math.max(1, Math.round(srcW * scale));
      const height = Math.max(1, Math.round(srcH * scale));
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d', { alpha: false });
      ctx.drawImage(img, 0, 0, width, height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.86));
      if (!blob) throw new Error('image conversion failed');
      return await blobToDataUrl(blob);
    } finally {
      URL.revokeObjectURL(url);
    }
  };

  const takePhoto = async () => {
    if (!stream || !video.videoWidth || !video.videoHeight) return;
    shootButton.disabled = true;
    const capturedAt = new Date().toISOString();
    try {
      const locationPromise = getLocationAtCapture();
      const srcW = video.videoWidth;
      const srcH = video.videoHeight;
      const maxSide = 1600;
      const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
      const width = Math.max(1, Math.round(srcW * scale));
      const height = Math.max(1, Math.round(srcH * scale));
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d', { alpha: false });
      ctx.drawImage(video, 0, 0, width, height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.86));
      if (!blob) throw new Error('canvas conversion failed');
      const dataUrl = await blobToDataUrl(blob);

      setStatus('位置情報を確認しています…');
      const location = await locationPromise;
      pendingPhoto = {
        data_url: dataUrl,
        name: 'camera.jpg',
        source: 'camera',
        captured_at: capturedAt,
        location
      };
      showReview(dataUrl);
      setStatus('');
    } catch (err) {
      console.error(err);
      shootButton.disabled = false;
      const message = '撮影した画像を作れませんでした。もう一度お試しください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'CaptureError', message });
    }
  };

  const chooseGalleryPhoto = async () => {
    const file = galleryInput.files && galleryInput.files[0];
    if (!file) return;
    try {
      const dataUrl = await prepareImageFile(file);
      pendingPhoto = {
        data_url: dataUrl,
        name: file.name || 'gallery.jpg',
        source: 'gallery',
        captured_at: new Date().toISOString(),
        location: {
          ok: false,
          error_code: 'GALLERY',
          error_message: '写真フォルダから選んだ画像の撮影位置は自動取得しません。'
        }
      };
      showReview(dataUrl);
      setStatus('');
    } catch (err) {
      console.error(err);
      const message = '写真を読み込めませんでした。別の写真を選んでください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'GalleryError', message });
    } finally {
      galleryInput.value = '';
    }
  };

  const savePendingPhoto = () => {
    if (!pendingPhoto) return;
    reviewSave.disabled = true;
    reviewRetry.disabled = true;
    const photoToSave = pendingPhoto;
    setStatus('写真を保存しています…');
    // Saving ends this capture. A retry, in contrast, never stops a live camera.
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    setTriggerValue('photo', photoToSave);
  };

  const retryPendingPhoto = async () => {
    if (!pendingPhoto) return;
    const source = pendingPhoto.source;
    pendingPhoto = null;
    reviewSave.disabled = false;
    reviewRetry.disabled = false;
    setStatus('');

    if (source === 'camera' && stream && stream.getTracks().some((track) => track.readyState === 'live')) {
      // The stream was deliberately kept alive while the captured still image was
      // being reviewed. Return to it immediately without another getUserMedia call.
      if (video.srcObject !== stream) video.srcObject = stream;
      await video.play();
      shootButton.disabled = false;
      showCameraActions();
      return;
    }

    // Gallery retry (or an unexpectedly ended stream) returns to the source menu.
    showMenu();
  };

  const closeCamera = () => {
    stopStream();
    setStatus('');
  };

  startButton.addEventListener('click', startCamera);
  shootButton.addEventListener('click', takePhoto);
  stopButton.addEventListener('click', closeCamera);
  galleryInput.addEventListener('change', chooseGalleryPhoto);
  reviewSave.addEventListener('click', savePendingPhoto);
  reviewRetry.addEventListener('click', retryPendingPhoto);

  // If the app was opened again within one hour of the last successful camera
  // activation, Python passes auto_start=true once. Browsers that still require a
  // user gesture will simply leave the normal 'カメラを開く' button available.
  if (data?.auto_start) {
    queueMicrotask(() => startCamera());
  }

  return () => {
    startButton.removeEventListener('click', startCamera);
    shootButton.removeEventListener('click', takePhoto);
    stopButton.removeEventListener('click', closeCamera);
    galleryInput.removeEventListener('change', chooseGalleryPhoto);
    reviewSave.removeEventListener('click', savePendingPhoto);
    reviewRetry.removeEventListener('click', retryPendingPhoto);
    stopStream();
  };
}
"""

try:
    live_camera_component = st.components.v2.component(
        "tokyo_burari_live_camera",
        html=_LIVE_CAMERA_HTML,
        css=_LIVE_CAMERA_CSS,
        js=_LIVE_CAMERA_JS,
    )
except Exception:
    live_camera_component = None


# ============================================================
# Far-field mobile microphone component
# ============================================================
# The standard Streamlit audio widget does not expose browser microphone
# processing controls. This component is tuned for a child speaking from a
# short distance away: request automatic gain, avoid aggressive noise
# suppression, boost quiet input in Web Audio, and show a live level meter.
_FAR_FIELD_MIC_HTML = """
<div class="far-mic-wrap">
  <button id="far-mic-toggle" class="far-mic-button" type="button">🎙 録音する</button>
  <div id="far-mic-status" class="far-mic-status">スマホから少し離れて話しても拾いやすい録音モードです。</div>
  <div class="far-mic-meter" aria-hidden="true">
    <div id="far-mic-meter-fill" class="far-mic-meter-fill"></div>
  </div>
  <div class="far-mic-meter-label">声の大きさ</div>
</div>
"""

_FAR_FIELD_MIC_CSS = """
.far-mic-wrap {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--st-font);
  margin: .2rem 0 .65rem;
}
.far-mic-button {
  width: 100%;
  min-height: 64px;
  border-radius: 18px;
  border: 2px solid #2563eb;
  background: rgba(37, 99, 235, .10);
  color: var(--st-text-color);
  font-size: 18px;
  font-weight: 800;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.far-mic-button.recording {
  border-color: #dc2626;
  background: #dc2626;
  color: white;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, .12);
}
.far-mic-button:disabled {
  opacity: .62;
  cursor: default;
}
.far-mic-status {
  margin-top: 7px;
  font-size: 13px;
  line-height: 1.45;
  opacity: .82;
}
.far-mic-meter {
  width: 100%;
  height: 12px;
  margin-top: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(128, 128, 128, .18);
}
.far-mic-meter-fill {
  width: 2%;
  height: 100%;
  border-radius: inherit;
  background: #22c55e;
  transition: width 90ms linear;
}
.far-mic-meter-label {
  margin-top: 2px;
  text-align: right;
  font-size: 10px;
  opacity: .55;
}
@media (max-width: 640px) {
  .far-mic-button {
    min-height: 62px;
    font-size: 17px;
  }
}
"""

_FAR_FIELD_MIC_JS = r"""
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const button = parentElement.querySelector('#far-mic-toggle');
  const status = parentElement.querySelector('#far-mic-status');
  const meterFill = parentElement.querySelector('#far-mic-meter-fill');
  if (!button || !status || !meterFill) return;

  let inputStream = null;
  let audioContext = null;
  let source = null;
  let highpass = null;
  let analyser = null;
  let gainNode = null;
  let compressor = null;
  let destination = null;
  let recorder = null;
  let chunks = [];
  let meterTimer = null;
  let maxTimer = null;
  let startedAt = 0;
  let recording = false;
  let cancelled = false;
  let peakRms = 0;

  const label = String(data?.label || '録音');

  const setStatus = (text) => {
    status.textContent = text || '';
  };

  const setMeter = (percent) => {
    const safe = Math.max(2, Math.min(100, Number(percent) || 2));
    meterFill.style.width = `${safe}%`;
  };

  const errorMessage = (err) => {
    const name = (err && err.name) ? err.name : '';
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
      return 'マイクが許可されていません。ブラウザのサイト設定でマイクを「許可」にしてください。';
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') return '利用できるマイクが見つかりませんでした。';
    if (name === 'NotReadableError' || name === 'TrackStartError') return 'マイクを開けませんでした。ほかのアプリがマイクを使っていないか確認してください。';
    return 'マイクを開けませんでした。ChromeまたはSafariの最新版でお試しください。';
  };

  const chooseMimeType = () => {
    if (!window.MediaRecorder) return '';
    const candidates = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus'
    ];
    for (const candidate of candidates) {
      try {
        if (MediaRecorder.isTypeSupported(candidate)) return candidate;
      } catch (_) {}
    }
    return '';
  };

  const extensionFor = (mime) => {
    const value = String(mime || '').toLowerCase();
    if (value.includes('mp4')) return 'm4a';
    if (value.includes('ogg')) return 'ogg';
    if (value.includes('wav')) return 'wav';
    return 'webm';
  };

  const blobToDataUrl = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });

  const stopTracksAndGraph = async () => {
    if (meterTimer) {
      clearInterval(meterTimer);
      meterTimer = null;
    }
    if (maxTimer) {
      clearTimeout(maxTimer);
      maxTimer = null;
    }
    if (inputStream) {
      inputStream.getTracks().forEach((track) => track.stop());
      inputStream = null;
    }
    try { source && source.disconnect(); } catch (_) {}
    try { highpass && highpass.disconnect(); } catch (_) {}
    try { analyser && analyser.disconnect(); } catch (_) {}
    try { gainNode && gainNode.disconnect(); } catch (_) {}
    try { compressor && compressor.disconnect(); } catch (_) {}
    source = null;
    highpass = null;
    analyser = null;
    gainNode = null;
    compressor = null;
    destination = null;
    if (audioContext) {
      try { await audioContext.close(); } catch (_) {}
      audioContext = null;
    }
    setMeter(2);
  };

  const updateLevelAndGain = () => {
    if (!recording || !analyser || !gainNode || !audioContext) return;
    const values = new Float32Array(analyser.fftSize);
    analyser.getFloatTimeDomainData(values);
    let sum = 0;
    for (let i = 0; i < values.length; i++) sum += values[i] * values[i];
    const rms = Math.sqrt(sum / Math.max(1, values.length));
    peakRms = Math.max(peakRms, rms);

    // Logarithmic meter: roughly -60 dB to -15 dB maps to 0-100%.
    const db = 20 * Math.log10(Math.max(rms, 0.000001));
    const meter = Math.max(2, Math.min(100, ((db + 60) / 45) * 100));
    setMeter(meter);

    // Distant voices tend to arrive quietly. Raise them before encoding, but
    // keep a compressor after the gain stage so a sudden close voice does not clip.
    let targetGain = 1.25;
    if (rms < 0.006) targetGain = 4.5;
    else if (rms < 0.012) targetGain = 4.0;
    else if (rms < 0.025) targetGain = 3.0;
    else if (rms < 0.05) targetGain = 2.0;
    gainNode.gain.setTargetAtTime(targetGain, audioContext.currentTime, 0.12);
  };

  const finishRecording = async () => {
    const mime = (recorder && recorder.mimeType) || chooseMimeType() || 'audio/webm';
    const blob = new Blob(chunks, { type: mime });
    const durationMs = Math.max(0, Date.now() - startedAt);
    await stopTracksAndGraph();
    recording = false;
    button.classList.remove('recording');
    button.disabled = false;
    button.textContent = '🎙 録音する';

    if (cancelled || !blob.size) {
      cancelled = false;
      setStatus('録音を開始できます。');
      return;
    }

    try {
      const dataUrl = await blobToDataUrl(blob);
      setStatus('声を送っています…');
      button.disabled = true;
      setTriggerValue('audio', {
        data_url: dataUrl,
        mime_type: mime,
        name: `speech.${extensionFor(mime)}`,
        duration_ms: durationMs,
        peak_rms: peakRms
      });
    } catch (err) {
      console.error(err);
      setStatus('録音データを作れませんでした。もう一度お試しください。');
      button.disabled = false;
      setTriggerValue('audio_error', { name: 'EncodeError', message: String(err?.message || err || '') });
    }
  };

  const stopRecording = () => {
    if (!recording || !recorder) return;
    button.disabled = true;
    setStatus('録音を止めています…');
    if (maxTimer) {
      clearTimeout(maxTimer);
      maxTimer = null;
    }
    try {
      if (recorder.state !== 'inactive') recorder.stop();
    } catch (err) {
      console.error(err);
      cancelled = true;
      stopTracksAndGraph();
      recording = false;
      button.classList.remove('recording');
      button.disabled = false;
      button.textContent = '🎙 録音する';
      setStatus('録音を止められませんでした。もう一度お試しください。');
    }
  };

  const startRecording = async () => {
    if (recording) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      const message = 'このブラウザでは距離対応マイクを利用できません。ChromeまたはSafariの最新版でお試しください。';
      setStatus(message);
      setTriggerValue('audio_error', { name: 'Unsupported', message });
      return;
    }

    button.disabled = true;
    setStatus('マイクを準備しています…');
    cancelled = false;
    peakRms = 0;
    chunks = [];

    try {
      inputStream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
          channelCount: { ideal: 1 },
          sampleRate: { ideal: 48000 },
          autoGainControl: { ideal: true },
          noiseSuppression: { ideal: false },
          echoCancellation: { ideal: false }
        }
      });

      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) throw new Error('AudioContext is unavailable');
      try {
        audioContext = new AudioContextCtor({ sampleRate: 48000 });
      } catch (_) {
        audioContext = new AudioContextCtor();
      }
      await audioContext.resume();

      source = audioContext.createMediaStreamSource(inputStream);
      highpass = audioContext.createBiquadFilter();
      highpass.type = 'highpass';
      highpass.frequency.value = 80;
      highpass.Q.value = 0.7;

      analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.65;

      gainNode = audioContext.createGain();
      gainNode.gain.value = 2.5;

      compressor = audioContext.createDynamicsCompressor();
      compressor.threshold.value = -18;
      compressor.knee.value = 24;
      compressor.ratio.value = 4;
      compressor.attack.value = 0.003;
      compressor.release.value = 0.25;

      destination = audioContext.createMediaStreamDestination();
      source.connect(highpass);
      highpass.connect(analyser);
      highpass.connect(gainNode);
      gainNode.connect(compressor);
      compressor.connect(destination);

      const mimeType = chooseMimeType();
      const options = { audioBitsPerSecond: 96000 };
      if (mimeType) options.mimeType = mimeType;
      recorder = new MediaRecorder(destination.stream, options);
      recorder.addEventListener('dataavailable', (event) => {
        if (event.data && event.data.size > 0) chunks.push(event.data);
      });
      recorder.addEventListener('stop', finishRecording, { once: true });
      recorder.addEventListener('error', (event) => {
        const err = event?.error || event;
        console.error(err);
        setTriggerValue('audio_error', { name: 'RecorderError', message: String(err?.message || err || '') });
      });

      recorder.start(250);
      recording = true;
      startedAt = Date.now();
      button.disabled = false;
      button.classList.add('recording');
      button.textContent = '■ 録音を止める';
      setStatus(`${label}：録音中。少し離れた声は自動で持ち上げます。`);
      meterTimer = setInterval(updateLevelAndGain, 100);
      maxTimer = setTimeout(stopRecording, 60000);
    } catch (err) {
      console.error(err);
      await stopTracksAndGraph();
      recording = false;
      button.classList.remove('recording');
      button.disabled = false;
      button.textContent = '🎙 録音する';
      const message = errorMessage(err);
      setStatus(message);
      setTriggerValue('audio_error', {
        name: (err && err.name) ? err.name : 'MicrophoneError',
        message,
        detail: (err && err.message) ? String(err.message) : ''
      });
    }
  };

  const onToggle = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  button.addEventListener('click', onToggle);

  return () => {
    button.removeEventListener('click', onToggle);
    cancelled = true;
    if (recorder && recorder.state !== 'inactive') {
      try { recorder.stop(); } catch (_) {}
    }
    stopTracksAndGraph();
  };
}
"""

try:
    far_field_mic_component = st.components.v2.component(
        "tokyo_burari_far_field_mic",
        html=_FAR_FIELD_MIC_HTML,
        css=_FAR_FIELD_MIC_CSS,
        js=_FAR_FIELD_MIC_JS,
    )
except Exception:
    far_field_mic_component = None


# ============================================================
# Clickable diary photo gallery
# ============================================================
_DIARY_GALLERY_HTML = """
<div id="diary-photo-grid" class="diary-photo-grid"></div>
"""

_DIARY_GALLERY_CSS = """
.diary-photo-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  box-sizing: border-box;
}
.diary-photo-card {
  appearance: none;
  -webkit-appearance: none;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 5px;
  border-radius: 14px;
  box-sizing: border-box;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  overflow: hidden;
}
.diary-photo-card.talked {
  border: 3px solid #F59E0B;
  background: rgba(245, 158, 11, .18);
  box-shadow: 0 0 0 1px rgba(245, 158, 11, .08) inset;
}
.diary-photo-card.untalked {
  border: 3px solid #AEB6C2;
  background: rgba(174, 182, 194, .20);
  box-shadow: 0 0 0 1px rgba(174, 182, 194, .08) inset;
}
.diary-photo-card:active {
  transform: scale(.985);
}
.diary-photo-card img {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 9px;
  background: rgba(128, 128, 128, .08);
}
.diary-photo-location {
  margin-top: 4px;
  font-size: 10px;
  line-height: 1.25;
  color: var(--st-text-color);
  opacity: .78;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 640px) {
  .diary-photo-grid { gap: 6px; }
  .diary-photo-card { padding: 4px; border-radius: 12px; }
  .diary-photo-card img { border-radius: 8px; }
  .diary-photo-location { font-size: 9px; }
}
"""

_DIARY_GALLERY_JS = r"""
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const grid = parentElement.querySelector('#diary-photo-grid');
  if (!grid) return;

  grid.replaceChildren();
  const photos = Array.isArray(data?.photos) ? data.photos : [];

  for (const photo of photos) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `diary-photo-card ${photo.talked ? 'talked' : 'untalked'}`;
    button.setAttribute(
      'aria-label',
      photo.talked ? '話した写真を開く' : 'まだ話していない写真を開く'
    );

    const img = document.createElement('img');
    img.src = photo.src || '';
    img.alt = 'ぶらり旅の写真';
    button.appendChild(img);

    if (photo.location) {
      const location = document.createElement('div');
      location.className = 'diary-photo-location';
      location.textContent = `📍 ${photo.location}`;
      button.appendChild(location);
    }

    button.addEventListener('click', () => {
      setTriggerValue('photo_id', String(photo.id));
    });

    grid.appendChild(button);
  }
}
"""

try:
    diary_gallery_component = st.components.v2.component(
        "tokyo_burari_diary_gallery",
        html=_DIARY_GALLERY_HTML,
        css=_DIARY_GALLERY_CSS,
        js=_DIARY_GALLERY_JS,
    )
except Exception:
    diary_gallery_component = None


# ============================================================
# Browser history bridge
# ============================================================
# Streamlit session-state navigation does not create browser history entries by
# itself. This small component mirrors each app screen into window.history so
# Chrome/Safari back and forward buttons move between app screens first.
_HISTORY_JS = r"""
export default function(component) {
  const { data, setTriggerValue } = component;
  const validPages = new Set(['home', 'camera', 'diary', 'review', 'settings']);
  const marker = '__tokyo_burari_page__';
  const requestedPage = validPages.has(data?.page) ? data.page : 'home';
  const action = data?.action || 'sync';

  const pageFromUrl = () => {
    try {
      const value = new URL(window.location.href).searchParams.get('view');
      return validPages.has(value) ? value : 'home';
    } catch (_) {
      return 'home';
    }
  };

  const pageFromHistory = () => {
    const value = window.history.state && window.history.state[marker];
    return validPages.has(value) ? value : pageFromUrl();
  };

  const urlFor = (page) => {
    const url = new URL(window.location.href);
    if (page === 'home') {
      url.searchParams.delete('view');
    } else {
      url.searchParams.set('view', page);
    }
    return url.pathname + url.search + url.hash;
  };

  let currentPage = pageFromHistory();
  const state = window.history.state || {};

  // Mark the entry used to open the app as the app's home/current entry.
  if (!validPages.has(state[marker])) {
    const initialPage = pageFromUrl();
    window.history.replaceState(
      { ...state, [marker]: initialPage },
      '',
      urlFor(initialPage)
    );
    currentPage = initialPage;
  }

  if (action === 'push' && currentPage !== requestedPage) {
    window.history.pushState(
      { ...(window.history.state || {}), [marker]: requestedPage },
      '',
      urlFor(requestedPage)
    );
    currentPage = requestedPage;
  } else if (action === 'replace' && currentPage !== requestedPage) {
    window.history.replaceState(
      { ...(window.history.state || {}), [marker]: requestedPage },
      '',
      urlFor(requestedPage)
    );
    currentPage = requestedPage;
  } else if (action === 'sync' && currentPage !== requestedPage) {
    // This covers a page reload or a browser-restored tab whose URL/history
    // already points at an internal app screen.
    queueMicrotask(() => setTriggerValue('page', currentPage));
  }

  const onPopState = (event) => {
    const statePage = event.state && event.state[marker];
    const target = validPages.has(statePage) ? statePage : pageFromUrl();
    setTriggerValue('page', validPages.has(target) ? target : 'home');
  };

  window.addEventListener('popstate', onPopState);
  return () => window.removeEventListener('popstate', onPopState);
}
"""

try:
    browser_history_component = st.components.v2.component(
        'tokyo_burari_browser_history',
        js=_HISTORY_JS,
    )
except Exception:
    browser_history_component = None


# ============================================================
# Browser persistence: auto login + recent camera session
# ============================================================
_BROWSER_PERSISTENCE_HTML = """
<div id="tokyo-burari-browser-persistence" hidden></div>
"""

_BROWSER_PERSISTENCE_JS = r"""
// Streamlit v2's component parentElement is not guaranteed to expose HTMLElement.dataset
// on every browser/runtime. Keep component-local bookkeeping in a global registry instead.
const registry = globalThis.__tokyoBurariPersistenceRegistry ||
  (globalThis.__tokyoBurariPersistenceRegistry = new Map());

export default function(component) {
  const { data, setTriggerValue } = component;
  const authKey = 'tokyo_burari_auto_login_v1';
  const cameraKey = 'tokyo_burari_last_camera_open_v1';
  const instanceKey = String(data?.instance_key || 'default');
  const runtime = registry.get(instanceKey) || { lastState: '', lastError: '' };
  registry.set(instanceKey, runtime);

  try {
    const storeToken = String(data?.store_auth_token || '');
    if (storeToken) localStorage.setItem(authKey, storeToken);
    if (data?.clear_auth_token) localStorage.removeItem(authKey);

    const state = {
      auth_token: localStorage.getItem(authKey) || '',
      last_camera_open_at: Number(localStorage.getItem(cameraKey) || 0),
    };
    const serialized = JSON.stringify(state);
    if (runtime.lastState !== serialized) {
      runtime.lastState = serialized;
      runtime.lastError = '';
      queueMicrotask(() => setTriggerValue('browser_state', state));
    }
  } catch (err) {
    const message = (err && err.message) ? String(err.message) : 'browser storage unavailable';
    if (runtime.lastError !== message) {
      runtime.lastError = message;
      // Do not touch DOM-specific properties here. Report the failure as data only.
      queueMicrotask(() => setTriggerValue('browser_error', message));
    }
  }
}
"""

try:
    browser_persistence_component = st.components.v2.component(
        "tokyo_burari_browser_persistence",
        html=_BROWSER_PERSISTENCE_HTML,
        js=_BROWSER_PERSISTENCE_JS,
    )
except Exception:
    browser_persistence_component = None


def browser_auto_login_token():
    """Return a browser-storable credential that becomes invalid if FAMILY_PIN changes."""
    if not FAMILY_PIN:
        return ""
    return hmac.new(
        FAMILY_PIN.encode("utf-8"),
        b"tokyo-burari-auto-login-v1",
        hashlib.sha256,
    ).hexdigest()


def read_browser_persistence(key):
    if browser_persistence_component is None:
        return None
    result = browser_persistence_component(
        data={"instance_key": key},
        key=key,
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )
    state = getattr(result, "browser_state", None)
    return state if isinstance(state, dict) else None


def write_browser_auto_login(token, key="browser_auto_login_store"):
    if browser_persistence_component is None or not token:
        return
    browser_persistence_component(
        data={"store_auth_token": token, "instance_key": key},
        key=key,
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )


def clear_browser_auto_login(key="browser_auto_login_clear"):
    if browser_persistence_component is None:
        return
    browser_persistence_component(
        data={"clear_auth_token": True, "instance_key": key},
        key=key,
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )


def decode_camera_data_url(data_url):
    """Decode a trusted data URL emitted by the live camera component."""
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

    token = browser_auto_login_token()

    if st.session_state.get("_family_authenticated", False):
        if st.session_state.pop("_persist_auto_login_pending", False):
            write_browser_auto_login(token)
        return

    # First try the credential saved on this browser. The component reports once
    # after localStorage is available; if it matches, no PIN screen is required.
    browser_state = read_browser_persistence("browser_auto_login_gate")
    if isinstance(browser_state, dict):
        stored_token = str(browser_state.get("auth_token") or "")
        if stored_token and hmac.compare_digest(stored_token, token):
            st.session_state["_family_authenticated"] = True
            st.session_state["_family_pin_failures"] = 0
            st.session_state["_family_pin_locked_until"] = 0.0
            st.session_state["_browser_last_camera_open_at"] = browser_state.get("last_camera_open_at") or 0
            st.rerun()

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
            # Store the derived token on the next render, after authentication.
            st.session_state["_persist_auto_login_pending"] = True
            if isinstance(browser_state, dict):
                st.session_state["_browser_last_camera_open_at"] = browser_state.get("last_camera_open_at") or 0
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


def enhance_audio_for_transcription(audio_file):
    """Normalize quiet PCM WAV recordings before transcription.

    Streamlit's microphone widget does not expose hardware microphone gain.
    This keeps the original recording format but gently raises quiet speech so
    the transcription model receives a clearer signal. Unsupported WAV formats
    simply fall back to the original bytes.
    """
    try:
        audio_file.seek(0)
        raw = audio_file.read()
        if not raw:
            return audio_file

        with wave.open(io.BytesIO(raw), "rb") as reader:
            params = reader.getparams()
            frames = reader.readframes(reader.getnframes())

        if params.sampwidth != 2 or not frames:
            fallback = io.BytesIO(raw)
            fallback.name = getattr(audio_file, "name", "speech.wav")
            return fallback

        samples = array("h")
        samples.frombytes(frames)
        if sys.byteorder != "little":
            samples.byteswap()
        peak = max((abs(v) for v in samples), default=0)
        if peak <= 0:
            fallback = io.BytesIO(raw)
            fallback.name = getattr(audio_file, "name", "speech.wav")
            return fallback

        # Do not over-amplify normal recordings. Quiet voices can be raised up to 4x.
        target_peak = 28000
        gain = min(4.0, target_peak / peak) if peak < 18000 else 1.0
        if gain > 1.05:
            for i, value in enumerate(samples):
                samples[i] = max(-32768, min(32767, int(round(value * gain))))

        if sys.byteorder != "little":
            samples.byteswap()
        out = io.BytesIO()
        with wave.open(out, "wb") as writer:
            writer.setparams(params)
            writer.writeframes(samples.tobytes())
        out.seek(0)
        out.name = getattr(audio_file, "name", "speech.wav")
        return out
    except Exception:
        try:
            audio_file.seek(0)
        except Exception:
            pass
        return audio_file


def transcribe_audio(audio_file, context=""):
    audio_file = enhance_audio_for_transcription(audio_file)
    audio_file.seek(0)
    prompt = (
        "5〜6歳の子どもの日本語の発話です。"
        "幼児の小さい声や少し不明瞭な発音も、前後の文脈を使って丁寧に聞き取ってください。"
        "ただし聞こえない語を推測で作らないでください。"
        "子どもらしい言い回しを大人の表現に直しすぎず、聞こえた内容を自然な日本語として文字起こししてください。"
        "言い直しがあるときは、最後に言い直した内容を優先してください。"
    )
    if context:
        prompt += " 文脈: " + context[:1600]
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


def decode_audio_data_url(payload, fallback_name="speech.webm"):
    """Turn the far-field browser recorder payload into an OpenAI upload file."""
    if not isinstance(payload, dict):
        return None
    data_url = str(payload.get("data_url") or "")
    if not data_url.startswith("data:audio/"):
        raise ValueError("録音データの形式が不正です。")
    try:
        header, encoded = data_url.split(",", 1)
    except ValueError as exc:
        raise ValueError("録音データを読み込めません。") from exc
    if ";base64" not in header:
        raise ValueError("録音データの形式が不正です。")
    raw = base64.b64decode(encoded, validate=True)
    if not raw:
        raise ValueError("録音データが空です。")

    mime_type = str(payload.get("mime_type") or header[5:].split(";", 1)[0]).lower()
    if "mp4" in mime_type:
        extension = "m4a"
    elif "ogg" in mime_type:
        extension = "ogg"
    elif "wav" in mime_type:
        extension = "wav"
    else:
        extension = "webm"

    audio_file = io.BytesIO(raw)
    requested_name = str(payload.get("name") or "").strip()
    audio_file.name = requested_name if requested_name else fallback_name.rsplit(".", 1)[0] + "." + extension
    return audio_file


def far_field_audio_input(label, key):
    """Record speech with browser-side gain tuned for a child a short distance away."""
    if far_field_mic_component is None:
        return st.audio_input(label, sample_rate=16000, key=f"{key}_fallback")

    result = far_field_mic_component(
        data={"label": str(label or "録音")},
        key=key,
        on_audio_change=lambda: None,
        on_audio_error_change=lambda: None,
    )
    error = getattr(result, "audio_error", None)
    if error:
        message = ""
        if isinstance(error, dict):
            message = str(error.get("message") or "").strip()
        if message:
            st.warning(message)
        st.caption("距離対応マイクが使えない場合は、下の予備マイクを使えます。")
        return st.audio_input("予備のマイク", sample_rate=16000, key=f"{key}_fallback")

    payload = getattr(result, "audio", None)
    if not payload:
        return None
    try:
        return decode_audio_data_url(payload)
    except Exception as exc:
        st.error("録音データを読み込めませんでした。もう一度録音してください。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        return None


# ============================================================
# Location helpers
# ============================================================
@st.cache_data(ttl=86400, show_spinner=False)
def reverse_geocode_rough(latitude, longitude):
    """Best-effort coarse place label. Exact address is intentionally not shown."""
    try:
        lat = round(float(latitude), 4)
        lon = round(float(longitude), 4)
    except (TypeError, ValueError):
        return ""

    params = urlencode(
        {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 15,
            "addressdetails": 1,
            "accept-language": "ja",
        }
    )
    req = Request(
        f"https://nominatim.openstreetmap.org/reverse?{params}",
        headers={
            "User-Agent": "TokyoBurariApp/1.0 (family-use reverse geocoding)",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=3.5) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return ""

    address = data.get("address") if isinstance(data, dict) else {}
    if not isinstance(address, dict):
        address = {}

    # Keep the child-facing label intentionally coarse. Do not expose a street
    # address or house number even if the geocoder returns one.
    for key in (
        "neighbourhood",
        "quarter",
        "suburb",
        "city_district",
        "town",
        "village",
        "city",
        "municipality",
    ):
        value = str(address.get(key) or "").strip()
        if value:
            return value if value.endswith("付近") else f"{value}付近"
    return ""


def build_photo_location(raw_location, trip, capture_source="camera"):
    """Normalize browser GPS and fall back to the trip's manual destination."""
    destination = str((trip or {}).get("destination") or "").strip()
    source = str(capture_source or "camera").strip().lower()

    if source == "camera" and isinstance(raw_location, dict) and raw_location.get("ok"):
        try:
            latitude = float(raw_location.get("latitude"))
            longitude = float(raw_location.get("longitude"))
        except (TypeError, ValueError):
            latitude = longitude = None

        if latitude is not None and longitude is not None:
            accuracy = raw_location.get("accuracy_m")
            try:
                accuracy = round(float(accuracy), 1) if accuracy is not None else None
            except (TypeError, ValueError):
                accuracy = None

            place_label = reverse_geocode_rough(latitude, longitude)
            return {
                "source": "gps",
                "latitude": latitude,
                "longitude": longitude,
                "accuracy_m": accuracy,
                "measured_at": raw_location.get("measured_at"),
                "place_label": place_label,
                "place_provider": "OpenStreetMap Nominatim" if place_label else "",
            }

    if destination:
        return {
            "source": "manual_destination",
            "place_label": destination,
            "gps_error_code": (
                raw_location.get("error_code") if isinstance(raw_location, dict) else ""
            ),
        }

    return {
        "source": "unavailable",
        "place_label": "",
        "gps_error_code": (
            raw_location.get("error_code") if isinstance(raw_location, dict) else ""
        ),
    }


def get_photo_location(photo):
    reflection = (photo or {}).get("reflection_json") or {}
    if not isinstance(reflection, dict):
        return {}
    location = reflection.get("location") or {}
    return location if isinstance(location, dict) else {}


def photo_location_label(photo):
    location = get_photo_location(photo)
    label = str(location.get("place_label") or "").strip()
    if label:
        return label
    if location.get("source") == "gps":
        return "位置情報あり"
    return ""


def photo_location_preview(location):
    if not isinstance(location, dict):
        return ""
    source = location.get("source")
    label = str(location.get("place_label") or "").strip()
    if source == "gps":
        accuracy = location.get("accuracy_m")
        accuracy_text = f"（精度 ±{int(round(accuracy))}m）" if isinstance(accuracy, (int, float)) else ""
        return f"📍 GPS位置情報を取得しました{accuracy_text}"
    if source == "manual_destination" and label:
        return f"📍 {label}"
    return "📍 位置情報を取得できませんでした。ホームの地名表示を押して手入力できます。"


def trip_place_label(trip, photos=None):
    """Return the best coarse place name already registered for a trip."""
    trip = trip or {}
    destination = str(trip.get("destination") or "").strip()
    if destination:
        return destination

    trip_id = trip.get("id")
    if photos is None and trip_id:
        try:
            photos = list_trip_photos(trip_id)
        except Exception:
            photos = []

    for photo in photos or []:
        label = photo_location_label(photo)
        if label and label != "位置情報あり":
            return label
    return ""


def diary_title_for_trip(trip, photos=None):
    """Build the diary title from a manual destination, otherwise the first photo GPS label."""
    trip = trip or {}
    destination = str(trip.get("destination") or "").strip()
    if destination:
        return f"ぶらり旅（{destination}）"

    trip_id = trip.get("id")
    if photos is None and trip_id:
        try:
            photos = list_trip_photos(trip_id)
        except Exception:
            photos = []

    # When no place was entered manually, use the same place label shown on the
    # first photo in the diary UI. This keeps the title consistent with the visible
    # "📍 place" caption even if older saved rows used a slightly different source tag.
    if photos:
        first_photo = photos[0]
        place = str(photo_location_label(first_photo) or "").strip()
        if place and place != "位置情報あり":
            return f"ぶらり旅（{place}）"

        # If GPS coordinates exist but the coarse label was not persisted, try the
        # reverse geocoder once more before falling back to an unregistered title.
        first_location = get_photo_location(first_photo)
        if isinstance(first_location, dict):
            lat = first_location.get("latitude")
            lon = first_location.get("longitude")
            if lat is not None and lon is not None:
                place = str(reverse_geocode_rough(lat, lon) or "").strip()
                if place:
                    return f"ぶらり旅（{place}）"

    return "ぶらり旅（場所未登録）"


def diary_display_title(diary, trip, photos=None):
    """Prefer a saved/custom diary title, falling back to the automatic place title."""
    saved = str((diary or {}).get("title") or "").strip()
    return saved or diary_title_for_trip(trip, photos=photos)


def update_diary_title(trip_id, title):
    value = str(title or "").strip()
    if not value:
        raise ValueError("タイトルを入力してください。")
    (
        supabase_client()
        .table(DIARY_TABLE)
        .update({"title": value, "updated_at": now_jst().isoformat()})
        .eq("trip_id", trip_id)
        .execute()
    )
    return value


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


def upload_photo(trip_id, image_bytes, location=None, captured_at=None, capture_source="camera"):
    # Keep Storage upload as a raw binary body. In particular, do not send an
    # x-upsert header for new files.
    compressed = normalize_photo(image_bytes)
    if not compressed:
        raise ValueError("写真データが空です。")

    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    path = f"{trip_id}/{stamp}_{uuid.uuid4().hex[:8]}.jpg"
    client = supabase_client()

    reflection = {
        "capture_source": str(capture_source or "camera"),
        "location": location if isinstance(location, dict) else {},
    }

    storage_saved = False
    try:
        client.storage.from_(PHOTO_BUCKET).upload(
            path=path,
            file=compressed,
            file_options={
                "content-type": "image/jpeg",
                "cache-control": "3600",
            },
        )
        storage_saved = True

        result = (
            client
            .table(PHOTO_TABLE)
            .insert(
                {
                    "trip_id": trip_id,
                    "storage_path": path,
                    "captured_at": str(captured_at or now_jst().isoformat()),
                    "reflection_json": reflection,
                    "signals_json": {},
                }
            )
            .execute()
        )
        download_photo.clear()
        return (result.data or [None])[0]
    except Exception as exc:
        if storage_saved:
            try:
                client.storage.from_(PHOTO_BUCKET).remove([path])
            except Exception:
                pass
        raise RuntimeError(f"写真保存処理でエラーが発生しました: {exc}") from exc


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
    destination = str(destination or "").strip()
    client = supabase_client()
    result = (
        client
        .table(TRIP_TABLE)
        .update({"destination": destination})
        .eq("id", trip_id)
        .execute()
    )

    # If GPS was unavailable, a destination entered later should also become the
    # fallback label for photos already saved on today's trip. Never overwrite GPS.
    try:
        photos = (
            client
            .table(PHOTO_TABLE)
            .select("id,reflection_json")
            .eq("trip_id", trip_id)
            .execute()
        ).data or []
        for photo in photos:
            reflection = photo.get("reflection_json") or {}
            if not isinstance(reflection, dict):
                reflection = {}
            location = reflection.get("location") or {}
            if isinstance(location, dict) and location.get("source") == "gps":
                continue
            reflection["location"] = (
                {
                    "source": "manual_destination",
                    "place_label": destination,
                    "gps_error_code": (
                        location.get("gps_error_code") if isinstance(location, dict) else ""
                    ),
                }
                if destination
                else {
                    "source": "unavailable",
                    "place_label": "",
                    "gps_error_code": (
                        location.get("gps_error_code") if isinstance(location, dict) else ""
                    ),
                }
            )
            (
                client
                .table(PHOTO_TABLE)
                .update({"reflection_json": reflection})
                .eq("id", photo["id"])
                .execute()
            )
    except Exception:
        # The destination itself is more important than the optional backfill.
        # Do not fail the manual save if a legacy photo cannot be updated.
        pass

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


def update_photo_reflection(photo_id, conversation, signals, done=None):
    client = supabase_client()
    current = (
        client
        .table(PHOTO_TABLE)
        .select("reflection_json")
        .eq("id", photo_id)
        .limit(1)
        .execute()
    )
    row = (current.data or [None])[0] or {}
    reflection = row.get("reflection_json") or {}
    if not isinstance(reflection, dict):
        reflection = {}
    reflection["conversation"] = conversation
    child_comments = [
        str(turn.get("text") or "").strip()
        for turn in (conversation or [])
        if isinstance(turn, dict) and turn.get("role") == "child" and str(turn.get("text") or "").strip()
    ]
    reflection["child_comment"] = " / ".join(child_comments)
    if done is not None:
        reflection["conversation_done"] = bool(done)

    (
        client
        .table(PHOTO_TABLE)
        .update(
            {
                "reflection_json": reflection,
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
    trip = get_trip(trip_id) or {}
    # If the parent renamed a saved diary, recreating the diary must not overwrite
    # that custom title with the automatically detected place name.
    existing_title = str((existing or {}).get("title") or "").strip()
    requested_title = str(title or "").strip()
    fixed_title = existing_title or requested_title or diary_title_for_trip(trip)
    payload = {
        "trip_id": trip_id,
        "title": fixed_title,
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


def delete_diary_and_related_data(trip_id):
    """Delete one saved diary plus all photos and photo conversations for that trip."""
    client = supabase_client()
    trip = get_trip(trip_id) or {}
    photos = list_trip_photos(trip_id)
    storage_paths = [str(p.get("storage_path") or "").strip() for p in photos]
    storage_paths = [path for path in storage_paths if path]

    # Remove the binary photo files first. If Storage cannot be reached, abort the
    # deletion so the visible database records are not left pointing to missing files.
    if storage_paths:
        client.storage.from_(PHOTO_BUCKET).remove(storage_paths)

    # A photo's reflection_json contains the per-photo conversation/comments, so
    # deleting the photo rows deletes those comments together with the photo record.
    client.table(PHOTO_TABLE).delete().eq("trip_id", trip_id).execute()
    client.table(DIARY_TABLE).delete().eq("trip_id", trip_id).execute()
    # Once its diary/photos are gone, remove the trip container as well so the
    # deleted day cannot reappear as an empty trip in diary/monthly screens.
    client.table(TRIP_TABLE).delete().eq("id", trip_id).execute()

    # A saved monthly review can contain wording derived from the deleted diary.
    # Remove that month's snapshot so it cannot continue showing deleted material.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).execute()
        for key in (
            f"monthly_review_{month_key}",
            f"monthly_audio_{month_key}",
            f"monthly_audio_pending_{month_key}",
        ):
            st.session_state.pop(key, None)

    # Clear any in-progress diary state for the deleted trip.
    st.session_state.pop(f"reflection_state_{trip_id}", None)
    st.session_state.pop(f"diary_selected_photo_{trip_id}", None)
    st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
    st.session_state.pop(f"diary_existing_photo_view_{trip_id}", None)
    st.session_state.pop("diary_trip_selector", None)
    if st.session_state.get("history_detail_trip_id") == trip_id:
        st.session_state.pop("history_detail_trip_id", None)
    if st.session_state.get("preferred_diary_trip_id") == trip_id:
        st.session_state.preferred_diary_trip_id = None
    if st.session_state.get("active_trip_id") == trip_id:
        st.session_state.active_trip_id = None
    download_photo.clear()

    return {"photo_count": len(photos), "month_key": month_key}


@st.dialog("この日記を削除しますか？")
def confirm_diary_delete_dialog(trip_id, photo_count):
    trip = get_trip(trip_id) or {}
    photos = list_trip_photos(trip_id)
    diary = get_diary_for_trip(trip_id)
    title = diary_display_title(diary, trip, photos=photos)
    st.write(f"**{title}** を削除します。")
    st.warning(
        f"この日の記録、写真 {photo_count}枚、写真について話したコメントをすべて削除します。"
        "日記が未完成の場合は、途中までの内容も削除されます。この操作は元に戻せません。"
    )
    delete_col, cancel_col = st.columns(2)
    with delete_col:
        if st.button(
            "削除する",
            type="primary",
            use_container_width=True,
            key=f"dialog_delete_yes_{trip_id}",
        ):
            try:
                result = delete_diary_and_related_data(trip_id)
                st.session_state["_diary_notice"] = (
                    f"日記と写真 {result['photo_count']}枚、関連するコメントを削除しました。"
                )
                st.rerun(scope="app")
            except Exception as exc:
                st.error("日記を削除できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with cancel_col:
        if st.button(
            "キャンセル",
            use_container_width=True,
            key=f"dialog_delete_no_{trip_id}",
        ):
            st.rerun(scope="app")



def delete_photo_and_related_data(trip_id, photo_id):
    """Delete one photo plus its per-photo conversation/comment data."""
    client = supabase_client()
    trip = get_trip(trip_id) or {}
    photos = list_trip_photos(trip_id)
    photo = next((p for p in photos if p.get("id") == photo_id), None)
    if not photo:
        raise ValueError("削除する画像が見つかりませんでした。")

    storage_path = str(photo.get("storage_path") or "").strip()
    if storage_path:
        client.storage.from_(PHOTO_BUCKET).remove([storage_path])

    # reflection_json contains the conversation/comments for this photo, so deleting
    # the photo row removes those records together with the image metadata.
    client.table(PHOTO_TABLE).delete().eq("id", photo_id).eq("trip_id", trip_id).execute()

    # If a completed diary exists, remove the deleted photo's copied raw conversation
    # from the diary record as well. The diary prose itself is intentionally kept.
    existing = get_diary_for_trip(trip_id)
    if existing:
        raw = existing.get("raw_conversation") or {}
        if not isinstance(raw, dict):
            raw = {}
        raw.pop(str(photo_id), None)
        raw.pop(photo_id, None)

        ai_meta = existing.get("ai_meta") or {}
        if not isinstance(ai_meta, dict):
            ai_meta = {}
        remaining_child_points = []
        for conversation in raw.values():
            if not isinstance(conversation, list):
                continue
            for turn in conversation:
                if isinstance(turn, dict) and turn.get("role") == "child":
                    value = str(turn.get("text") or "").strip()
                    if value and value not in remaining_child_points:
                        remaining_child_points.append(value)
        ai_meta["child_points"] = remaining_child_points[:3]

        remaining_photos = [p for p in list_trip_photos(trip_id) if p.get("id") != photo_id]
        merged_signals = {}
        for remaining in remaining_photos:
            merged_signals = merge_signals(merged_signals, remaining.get("signals_json") or {})
        ai_meta["signals"] = merged_signals
        # This analysis may have referred to the deleted comment. Hide it until the
        # diary is rebuilt from the remaining child comments.
        ai_meta["reflection_summary"] = ""

        (
            client
            .table(DIARY_TABLE)
            .update(
                {
                    "raw_conversation": raw,
                    "ai_meta": ai_meta,
                    "updated_at": now_jst().isoformat(),
                }
            )
            .eq("id", existing["id"])
            .execute()
        )

    # A monthly summary may have used this photo's comments as evidence. Clear the
    # saved snapshot so a later monthly review is rebuilt from the remaining data.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).execute()
        for key in (
            f"monthly_review_{month_key}",
            f"monthly_audio_{month_key}",
            f"monthly_audio_pending_{month_key}",
        ):
            st.session_state.pop(key, None)

    # Keep an unfinished diary session consistent after removing the current image.
    state = st.session_state.get(f"reflection_state_{trip_id}")
    if isinstance(state, dict):
        old_ids = list(state.get("photo_ids") or [])
        old_index = int(state.get("photo_index") or 0)
        if photo_id in old_ids:
            deleted_index = old_ids.index(photo_id)
            new_ids = [pid for pid in old_ids if pid != photo_id]
            state["photo_ids"] = new_ids
            items = state.get("items") or {}
            if isinstance(items, dict):
                items.pop(photo_id, None)
            if not new_ids:
                state["photo_index"] = 0
            elif deleted_index < old_index:
                state["photo_index"] = max(0, old_index - 1)
            elif deleted_index == old_index:
                state["photo_index"] = min(old_index, len(new_ids) - 1)
            else:
                state["photo_index"] = min(old_index, len(new_ids) - 1)

            # Any unsaved draft was based on the old set of photos, so rebuild it.
            state["draft"] = None
            state["draft_title"] = None
            state["draft_meta"] = {}
            state["raw_conversation"] = {}
            state["draft_audio"] = None
            state["draft_audio_pending"] = False
            state["audio_bytes"] = None
            state["audio_pending"] = False
            state["answer_serial"] = int(state.get("answer_serial") or 0) + 1
            if state.get("selected_photo_id") == photo_id:
                state["selected_photo_id"] = new_ids[0] if new_ids else None

    selected_key = f"diary_selected_photo_{trip_id}"
    if st.session_state.get(selected_key) == photo_id:
        remaining_ids = [p.get("id") for p in list_trip_photos(trip_id) if p.get("id")]
        if remaining_ids:
            st.session_state[selected_key] = remaining_ids[0]
        else:
            st.session_state.pop(selected_key, None)

    st.session_state.pop(f"delete_photo_selector_{trip_id}", None)
    if st.session_state.get(f"diary_talk_photo_{trip_id}") == photo_id:
        st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
    if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
        st.session_state.pop(f"reflection_state_{trip_id}", None)
    download_photo.clear()
    return {"month_key": month_key}


def reset_photo_conversation(trip_id, photo_id):
    """Clear only the conversation/signals for one photo while keeping the image."""
    client = supabase_client()
    trip = get_trip(trip_id) or {}

    # update_photo_reflection preserves capture/location metadata in reflection_json.
    update_photo_reflection(photo_id, [], {}, done=False)

    # If a completed diary already exists, the copied raw conversation and AI
    # analysis must not keep showing a comment that was just reset. Keep the diary
    # prose itself, matching the existing reset behavior.
    existing = get_diary_for_trip(trip_id)
    if existing:
        raw = existing.get("raw_conversation") or {}
        if not isinstance(raw, dict):
            raw = {}
        raw.pop(str(photo_id), None)
        raw.pop(photo_id, None)

        ai_meta = existing.get("ai_meta") or {}
        if not isinstance(ai_meta, dict):
            ai_meta = {}
        remaining_child_points = []
        for conversation in raw.values():
            if not isinstance(conversation, list):
                continue
            for turn in conversation:
                if isinstance(turn, dict) and turn.get("role") == "child":
                    value = str(turn.get("text") or "").strip()
                    if value and value not in remaining_child_points:
                        remaining_child_points.append(value)
        ai_meta["child_points"] = remaining_child_points[:3]
        ai_meta["reflection_summary"] = ""

        remaining_photos = list_trip_photos(trip_id)
        merged_signals = {}
        for remaining in remaining_photos:
            if remaining.get("id") == photo_id:
                continue
            merged_signals = merge_signals(merged_signals, remaining.get("signals_json") or {})
        ai_meta["signals"] = merged_signals

        (
            client
            .table(DIARY_TABLE)
            .update(
                {
                    "raw_conversation": raw,
                    "ai_meta": ai_meta,
                    "updated_at": now_jst().isoformat(),
                }
            )
            .eq("id", existing["id"])
            .execute()
        )

    # A saved monthly review may contain wording from this photo conversation.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).execute()
        for key in (
            f"monthly_review_{month_key}",
            f"monthly_audio_{month_key}",
            f"monthly_audio_pending_{month_key}",
        ):
            st.session_state.pop(key, None)

    state = st.session_state.get(f"reflection_state_{trip_id}")
    if isinstance(state, dict):
        items = state.setdefault("items", {})
        items[photo_id] = {
            "conversation": [],
            "signals": {},
            "done": False,
            "started": False,
        }
        state["selected_photo_id"] = photo_id
        photo_ids = list(state.get("photo_ids") or [])
        if photo_id in photo_ids:
            state["photo_index"] = photo_ids.index(photo_id)
        state["audio_bytes"] = None
        state["audio_pending"] = False
        state["answer_serial"] = int(state.get("answer_serial") or 0) + 1
        # Any unsaved draft was based on the old conversation, so require rebuilding it.
        state["draft"] = None
        state["draft_title"] = None
        state["draft_meta"] = {}
        state["raw_conversation"] = {}
        state["draft_audio"] = None
        state["draft_audio_pending"] = False

    st.session_state[f"diary_selected_photo_{trip_id}"] = photo_id
    return {"month_key": month_key}


@st.dialog("この画像の会話をリセットしますか？")
def confirm_photo_conversation_reset_dialog(trip_id, photo_id):
    photos = list_trip_photos(trip_id)
    photo_ids = [p.get("id") for p in photos]
    if photo_id not in photo_ids:
        st.warning("この画像は見つかりません。")
        if st.button("閉じる", use_container_width=True, key=f"dialog_reset_missing_{trip_id}"):
            st.rerun(scope="app")
        return

    photo_number = photo_ids.index(photo_id) + 1
    st.write(f"**写真 {photo_number} / {len(photo_ids)}** の会話をリセットします。")
    st.warning(
        "この画像について保存した本人の発言、AIとの会話、感情・Wantの記録を消します。"
        "画像そのものと保存済みの日記本文は残ります。"
    )
    reset_col, cancel_col = st.columns(2)
    with reset_col:
        if st.button(
            "リセットする",
            type="primary",
            use_container_width=True,
            key=f"dialog_photo_reset_yes_{trip_id}_{photo_id}",
        ):
            try:
                reset_photo_conversation(trip_id, photo_id)
                st.session_state["_diary_notice"] = "この画像の会話をリセットしました。もう一度、最初から話せます。"
                st.rerun(scope="app")
            except Exception as exc:
                st.error("会話をリセットできませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with cancel_col:
        if st.button(
            "キャンセル",
            use_container_width=True,
            key=f"dialog_photo_reset_no_{trip_id}_{photo_id}",
        ):
            st.rerun(scope="app")


@st.dialog("この画像を削除しますか？")
def confirm_photo_delete_dialog(trip_id, photo_id):
    photos = list_trip_photos(trip_id)
    photo_ids = [p.get("id") for p in photos]
    if photo_id not in photo_ids:
        st.warning("この画像はすでに削除されています。")
        if st.button("閉じる", use_container_width=True, key=f"dialog_photo_missing_{trip_id}"):
            st.rerun(scope="app")
        return

    photo_number = photo_ids.index(photo_id) + 1
    st.write(f"**写真 {photo_number} / {len(photo_ids)}** を削除します。")
    st.warning(
        "この画像と、この画像について話したコメントを削除します。"
        "保存済みの日記本文そのものは削除しません。"
    )
    delete_col, cancel_col = st.columns(2)
    with delete_col:
        if st.button(
            "削除する",
            type="primary",
            use_container_width=True,
            key=f"dialog_photo_delete_yes_{trip_id}_{photo_id}",
        ):
            try:
                delete_photo_and_related_data(trip_id, photo_id)
                st.session_state["_diary_notice"] = "画像と、その画像について話したコメントを削除しました。"
                st.rerun(scope="app")
            except Exception as exc:
                st.error("画像を削除できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with cancel_col:
        if st.button(
            "キャンセル",
            use_container_width=True,
            key=f"dialog_photo_delete_no_{trip_id}_{photo_id}",
        ):
            st.rerun(scope="app")


def render_diary_delete_controls(
    trip_id,
    photos,
    current_photo_id=None,
    show_photo_navigation=False,
):
    """Render photo navigation/reset/delete controls and whole-day delete at the bottom."""
    st.divider()

    photo_ids = [p.get("id") for p in photos if p.get("id")]
    selected_key = f"diary_selected_photo_{trip_id}"
    selected_photo_id = current_photo_id if current_photo_id in photo_ids else st.session_state.get(selected_key)
    if selected_photo_id not in photo_ids:
        selected_photo_id = photo_ids[0] if photo_ids else None
        if selected_photo_id:
            st.session_state[selected_key] = selected_photo_id

    if selected_photo_id:
        photo_index = photo_ids.index(selected_photo_id)
        photo_number = photo_index + 1
        st.caption(f"対象：写真 {photo_number} / {len(photo_ids)}（上の一覧で選択できます）")

        if show_photo_navigation:
            has_next_photo = photo_index < len(photo_ids) - 1
            nav_label = "次の写真へ" if has_next_photo else "前の画面に戻る"
            with st.container(key="diary_photo_nav"):
                if st.button(
                    nav_label,
                    use_container_width=True,
                    key=f"diary_photo_nav_button_{trip_id}_{selected_photo_id}",
                ):
                    if has_next_photo:
                        next_photo_id = photo_ids[photo_index + 1]
                        state = st.session_state.get(f"reflection_state_{trip_id}")
                        if isinstance(state, dict):
                            open_diary_photo_talk(trip_id, next_photo_id, state)
                        else:
                            st.session_state[selected_key] = next_photo_id
                            st.session_state[f"diary_talk_photo_{trip_id}"] = next_photo_id
                        st.rerun()
                    else:
                        st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
                        if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
                            st.session_state.pop(f"reflection_state_{trip_id}", None)
                        st.rerun()

        if st.button(
            "↻ この画像の会話をリセット",
            use_container_width=True,
            key=f"diary_photo_reset_{trip_id}_{selected_photo_id}",
        ):
            confirm_photo_conversation_reset_dialog(trip_id, selected_photo_id)
        if st.button(
            "🗑 この画像を削除",
            use_container_width=True,
            key=f"diary_photo_delete_{trip_id}_{selected_photo_id}",
        ):
            confirm_photo_delete_dialog(trip_id, selected_photo_id)

    if st.button(
        "🗑 この日記を削除",
        use_container_width=True,
        key=f"diary_page_delete_{trip_id}",
    ):
        confirm_diary_delete_dialog(trip_id, len(photos))


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
        "surprise": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["like", "dislike", "curiosity", "convenient", "inconvenient", "people", "wish", "surprise"],
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
    """Analyze the child's words and enforce a very short diary conversation.

    Normal case: finish after the child's first free comment.
    Exception 1: if the first comment has no subjective feeling/reaction, ask once
    how the child felt/thought about it.
    Exception 2: if a negative reaction appears and no Want has been stated yet,
    ask once what the child wants to do/change. After that answer, always finish.
    """
    schema = {
        "type": "object",
        "properties": {
            "first_has_feeling": {"type": "boolean"},
            "latest_has_feeling": {"type": "boolean"},
            "any_negative": {"type": "boolean"},
            "has_want": {"type": "boolean"},
            "signals": SIGNAL_SCHEMA,
        },
        "required": [
            "first_has_feeling",
            "latest_has_feeling",
            "any_negative",
            "has_want",
            "signals",
        ],
        "additionalProperties": False,
    }
    prompt = f"""
あなたは5〜6歳の子どもの「東京ぶらり旅」の写真について、本人の発言だけを分類します。
写真は文脈として見てもよいですが、感情・評価・Wantは必ず本人の言葉だけから判定してください。
写真から感情を推測してはいけません。

会話:
{conversation_text(conversation)}

子どもの発話回数: {child_turn_count}

必ず確認する項目:
1. first_has_feeling
   最初の子どもの自由発話に、本人の主観的な感じ方・反応が明示されているか。
   「楽しい、好き、いい、うれしい、おもしろい、いや、怖い、困った、悲しい、変だと思った、気になった、びっくりした、なぜだろうと思った、便利、不便」などを含む。
   単なる物や出来事の説明（「電車があった」「赤かった」「人がいた」等）だけなら false。
   Wantだけがあって感情・評価・反応がない場合も、first_has_feeling は false とする。
2. latest_has_feeling
   直近の子どもの発話に同様の主観的な感じ方・反応が明示されているか。
3. any_negative
   子どもの発言のどこかに、明確にネガティブ寄りの感じ方・評価があるか。
   例: いや、嫌い、怖い、悲しい、困った、汚い、危ない、うるさい、不便、よくない、残念、直したいほど不満。
   単なる疑問・驚き・「変だと思った」だけでは原則 false。写真から推測しない。
4. has_want
   子ども自身が「こうしたい」「こうなってほしい」「増やしたい」「なくしたい」「直したい」など、今後どうしたいかを明示しているか。

signals:
- 本人が実際に言った内容だけを記録する。推測は禁止。
- like=よい/好き、dislike=いや/悪い、curiosity=疑問、wish=こうしたい/こうなってほしい/改善したい、surprise=驚き。
- convenient / inconvenient / people も本人が明示した場合だけ入れる。
- 該当しなければ各配列は空。
""".strip()

    analysis = ask_json_with_image(prompt, image_bytes, "analyze_photo_turn", schema, 520)

    first_has_feeling = bool(analysis.get("first_has_feeling"))
    any_negative = bool(analysis.get("any_negative"))
    has_want = bool(analysis.get("has_want"))

    # Because our own follow-up wording is fixed, the previous question tells us
    # exactly which branch the child is currently answering.
    previous_ai = ""
    for turn in reversed(conversation[:-1]):
        if turn.get("role") == "assistant":
            previous_ai = str(turn.get("text") or "")
            break
    answered_feeling_question = "どう思った" in previous_ai
    answered_want_question = "どうしたい" in previous_ai

    next_question = ""
    done = True

    if child_turn_count <= 1:
        # Always inspect the first free comment. Most photos end here.
        if not first_has_feeling:
            next_question = "それ、どう思った？"
            done = False
        elif any_negative and not has_want:
            next_question = "どうしたい？"
            done = False
    elif answered_feeling_question:
        # The one allowed feeling follow-up has now been answered. Only a newly
        # surfaced negative feeling may justify one final Want question.
        if any_negative and not has_want:
            next_question = "どうしたい？"
            done = False
    elif answered_want_question:
        # Want has been asked once. End even if the answer is brief or unclear.
        done = True
        next_question = ""
    else:
        # Safety valve for older saved conversations or unexpected states.
        done = True
        next_question = ""

    # Absolute cap: first comment + feeling question + Want question.
    if child_turn_count >= 3:
        done = True
        next_question = ""

    return {
        "reply": "ありがとう。" if done else "うん。",
        "next_question": next_question,
        "done": done,
        "signals": analysis.get("signals") or {},
    }


def merge_signals(old, new):
    result = {k: list(v or []) for k, v in (old or {}).items()}
    for key in ["like", "dislike", "curiosity", "convenient", "inconvenient", "people", "wish", "surprise"]:
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
            "reflection_summary": {"type": "string"},
            "child_points": {"type": "array", "items": {"type": "string"}},
            "signals": SIGNAL_SCHEMA,
        },
        "required": ["title", "diary", "reflection_summary", "child_points", "signals"],
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
- title はシステム側で「ぶらり旅（地名）」に固定するため、内容は diary に集中する。
- reflection_summary は保護者向けに、その日の本人の発言だけを根拠として「何に興味・注意が向いていたか」「どんな疑問や比較、理由づけ、改善の発想があったか」「どんなWantがあったか」を2〜4文程度で簡潔にまとめる。
- reflection_summary は性格診断・能力評価・将来予測にしない。「〜な子だ」と固定せず、「この日は〜に目が向いていた」「〜と考えていた」のようにその日の発言の範囲で書く。
- reflection_summary で本人が言っていない感情・意図を断定しない。推測が必要な場合は「〜に関心が向いていたようです」のように弱く表現する。材料が少なければ、そのことを短く明記する。
- child_points はAIの解釈ではなく、日記と reflection_summary の根拠になった本人の発言を短く3つ以内で抜き出す。
- signals は本人が実際に話した内容だけを整理し、推測を足さない。
""".strip()
    result = ask_json(prompt, "compose_burari_diary", schema, 1100)
    result["title"] = diary_title_for_trip(trip)
    result["signals"] = merge_signals(all_signals, result.get("signals", {}))
    return result, raw


def render_diary_reflection_summary(meta):
    """Show a cautious AI summary grounded only in the child's saved comments."""
    if not isinstance(meta, dict):
        return
    summary = str(meta.get("reflection_summary") or "").strip()
    if not summary:
        return
    st.markdown("#### AIによる、この日の興味・考えのまとめ")
    st.markdown(
        f"""
        <div class="talk-card">
          <div class="small-note">本人が写真について話したコメントだけをもとにした、その日の振り返りです。性格や能力の評価ではありません。</div>
          <div class="big-text" style="margin-top:.45rem;">{html.escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            where = photo_location_label(p) or trip.get("destination") or "場所メモなし"
            lines.append(
                f"[{trip.get('trip_date', '')} / 写真 / {where}] 本人の発言: "
                + " / ".join(child)
            )
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
        "show_home_destination_editor": False,
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
        target_page = legacy_pages.get(next_page, next_page)
        if target_page != st.session_state.get("main_page"):
            st.session_state["main_page"] = target_page
            st.session_state["_history_action"] = "push"

    if st.session_state.active_trip_id:
        active = get_trip(st.session_state.active_trip_id)
        if not active or active.get("status") != "active" or active.get("trip_date") != today_iso():
            st.session_state.active_trip_id = None

    if not st.session_state.active_trip_id:
        active = get_today_active_trip()
        if active:
            st.session_state.active_trip_id = active["id"]


VALID_APP_PAGES = {"home", "camera", "diary", "review", "settings"}


def restore_recent_camera_session():
    """On a new browser session, reopen the camera if it was used within one hour."""
    if st.session_state.get("_recent_camera_restore_checked", False):
        return

    last_open = st.session_state.get("_browser_last_camera_open_at")
    if last_open is None:
        browser_state = read_browser_persistence("browser_recent_camera_restore")
        if browser_state is None:
            return
        last_open = browser_state.get("last_camera_open_at") or 0
        st.session_state["_browser_last_camera_open_at"] = last_open

    st.session_state["_recent_camera_restore_checked"] = True
    try:
        last_open_ms = float(last_open or 0)
    except Exception:
        last_open_ms = 0.0

    age_ms = time.time() * 1000.0 - last_open_ms
    if last_open_ms > 0 and 0 <= age_ms <= 60 * 60 * 1000:
        st.session_state["main_page"] = "camera"
        st.session_state["_camera_auto_start"] = True
        st.session_state["_history_action"] = "replace"
        st.rerun()


def go_page(page_name, history_mode="push"):
    target = page_name if page_name in VALID_APP_PAGES else "home"
    if st.session_state.get("main_page") != target:
        st.session_state["main_page"] = target
        st.session_state["_history_action"] = (
            history_mode if history_mode in {"push", "replace"} else "push"
        )
    st.rerun()


def sync_browser_history():
    """Keep Chrome/Safari Back/Forward aligned with the app's internal pages."""
    if browser_history_component is None:
        return

    page = st.session_state.get("main_page", "home")
    if page not in VALID_APP_PAGES:
        page = "home"
        st.session_state["main_page"] = page

    action = st.session_state.pop("_history_action", "sync")
    result = browser_history_component(
        data={"page": page, "action": action},
        key="tokyo_burari_browser_history_instance",
        on_page_change=lambda: None,
    )
    browser_page = getattr(result, "page", None)
    if browser_page in VALID_APP_PAGES and browser_page != page:
        st.session_state["main_page"] = browser_page
        # A browser Back/Forward event has already changed window.history. Do not
        # push a new entry while reflecting that event back into Streamlit.
        st.session_state.pop("_history_action", None)
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


def _stored_photo_conversation(photo):
    reflection = (photo or {}).get("reflection_json") or {}
    if not isinstance(reflection, dict):
        return []
    conversation = reflection.get("conversation") or []
    return conversation if isinstance(conversation, list) else []


def _conversation_has_child_words(conversation):
    for turn in conversation or []:
        if not isinstance(turn, dict) or turn.get("role") != "child":
            continue
        if str(turn.get("text") or "").strip():
            return True
    return False


def reflection_state(trip_id, photos):
    key = f"reflection_state_{trip_id}"
    photo_ids = [p["id"] for p in photos]
    if key not in st.session_state:
        st.session_state[key] = {
            "photo_ids": photo_ids,
            "photo_index": 0,
            "selected_photo_id": None,
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

    photo_map = {p["id"]: p for p in photos}
    for pid in photo_ids:
        photo = photo_map[pid]
        reflection = photo.get("reflection_json") or {}
        if not isinstance(reflection, dict):
            reflection = {}
        stored_conversation = _stored_photo_conversation(photo)
        stored_signals = photo.get("signals_json") or {}
        stored_done = reflection.get("conversation_done")
        if stored_done is None:
            stored_done = _conversation_has_child_words(stored_conversation)

        if pid not in state["items"]:
            state["items"][pid] = {
                "conversation": list(stored_conversation),
                "signals": stored_signals if isinstance(stored_signals, dict) else {},
                "done": bool(stored_done),
                "started": bool(stored_conversation),
            }
        else:
            item = state["items"][pid]
            if not item.get("conversation") and stored_conversation:
                item["conversation"] = list(stored_conversation)
                item["started"] = True
            if not item.get("signals") and isinstance(stored_signals, dict):
                item["signals"] = stored_signals
            if stored_done:
                item["done"] = True

    for pid in list(state.get("items", {}).keys()):
        if pid not in photo_ids:
            state["items"].pop(pid, None)

    selected_key = f"diary_selected_photo_{trip_id}"
    selected = st.session_state.get(selected_key) or state.get("selected_photo_id")
    if selected not in photo_ids:
        selected = next(
            (pid for pid in photo_ids if not state["items"].get(pid, {}).get("done")),
            photo_ids[0] if photo_ids else None,
        )
    state["selected_photo_id"] = selected
    if selected:
        st.session_state[selected_key] = selected
        state["photo_index"] = photo_ids.index(selected)
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
    """Label a diary candidate, including a custom saved title when present."""
    trip = trip or {}
    trip_id = trip.get("id")
    photos = []
    diary = None
    if trip_id:
        try:
            photos = list_trip_photos(trip_id)
        except Exception:
            photos = []
        try:
            diary = get_diary_for_trip(trip_id)
        except Exception:
            diary = None
    title = diary_display_title(diary, trip, photos=photos)
    return f"{trip.get('trip_date', '')}　{title}"


def render_small_gallery(photos, max_count=None, columns=3):
    """Render diary photos in a compact grid; history uses three per row."""
    subset = list(photos or [])
    if max_count is not None:
        subset = subset[:max_count]
    if not subset:
        return

    column_count = max(1, min(int(columns or 3), 3))
    cols = st.columns(column_count)
    for idx, photo in enumerate(subset):
        try:
            image = download_photo(photo["storage_path"])
            with cols[idx % column_count]:
                st.image(image, use_container_width=True)
                location_label = photo_location_label(photo)
                if location_label:
                    st.caption(f"📍 {location_label}")
        except Exception:
            pass



def render_diary_photo_gallery(trip_id, photos, state=None):
    """Show all photos in a three-column clickable grid."""
    if not photos:
        return None

    st.markdown("#### この日の写真")
    st.caption("オレンジ：話した写真　／　グレー：まだ話していない写真")

    cards = []
    photo_ids = []
    for photo in photos:
        pid = photo.get("id")
        if not pid:
            continue
        item = (state or {}).get("items", {}).get(pid, {}) if isinstance(state, dict) else {}
        conversation = item.get("conversation") or _stored_photo_conversation(photo)
        talked = _conversation_has_child_words(conversation)
        location_label = photo_location_label(photo)
        try:
            image_bytes = download_photo(photo["storage_path"])
            encoded = base64.b64encode(image_bytes).decode("ascii")
            src = f"data:image/jpeg;base64,{encoded}"
        except Exception:
            src = ""

        cards.append(
            {
                "id": str(pid),
                "src": src,
                "talked": bool(talked),
                "location": str(location_label or ""),
            }
        )
        photo_ids.append(str(pid))

    if not cards:
        return None

    if diary_gallery_component is not None:
        serial_key = f"diary_gallery_serial_{trip_id}"
        serial = int(st.session_state.get(serial_key) or 0)
        result = diary_gallery_component(
            data={"photos": cards},
            key=f"diary_gallery_{trip_id}_{serial}",
            on_photo_id_change=lambda: None,
        )
        clicked = str(getattr(result, "photo_id", "") or "")
        if clicked in photo_ids:
            # Reset the component before the gallery is shown again so the previous
            # click does not immediately reopen the same photo.
            st.session_state[serial_key] = serial + 1
            return clicked
        return None

    # Fallback for environments where the v2 component is unavailable.
    cols = st.columns(3)
    for idx, card in enumerate(cards):
        with cols[idx % 3]:
            if card["src"]:
                st.markdown(
                    f'<img src="{card["src"]}" style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;" />',
                    unsafe_allow_html=True,
                )
            if st.button("写真を開く", use_container_width=True, key=f"diary_photo_fallback_{trip_id}_{card['id']}"):
                return card["id"]
    return None


def open_diary_photo_talk(trip_id, photo_id, state):
    """Switch from the gallery to one photo's conversation screen."""
    photo_ids = list(state.get("photo_ids") or [])
    if photo_id not in photo_ids:
        return False
    state["selected_photo_id"] = photo_id
    state["photo_index"] = photo_ids.index(photo_id)
    state["audio_bytes"] = None
    state["audio_pending"] = False
    state["answer_serial"] = int(state.get("answer_serial") or 0) + 1
    st.session_state[f"diary_selected_photo_{trip_id}"] = photo_id
    st.session_state[f"diary_talk_photo_{trip_id}"] = photo_id
    return True


# ============================================================
# Page: Home
# ============================================================
def page_home():
    st.markdown(
        """
        <div class="home-hero">
          <div class="home-eyebrow">TOKYO BURARI</div>
          <div class="home-title">東京ぶらり旅</div>
          <div class="home-tagline">気になったものを残して、あとで自分の言葉にする。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    active = get_trip(st.session_state.active_trip_id) if st.session_state.active_trip_id else None
    active_photos = []
    active_place = ""
    if active and active.get("status") == "active" and active.get("trip_date") == today_iso():
        active_photos = list_trip_photos(active["id"])
        active_place = trip_place_label(active, photos=active_photos)

    status_main = f"今日の写真 {len(active_photos)}枚" if active_photos else "今日はまだ写真なし"
    status_sub = active_place or "地名は写真から自動取得できます"
    st.markdown(
        f"""
        <div class="home-status">
          <span class="home-status-badge">今日</span>
          <span class="home-status-main">{html.escape(status_main)}</span>
          <span class="home-status-sub">{html.escape(status_sub)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="home-section-label">いつもの記録</div>', unsafe_allow_html=True)
    with st.container(key="home_primary"):
        primary_left, primary_right = st.columns(2)
        with primary_left:
            render_home_button("📷\nカメラで撮る", "camera", "home_camera", ensure_trip=True)
        with primary_right:
            render_home_button("📖\n日記", "diary", "home_diary")

    # Manual fallback for cases where the phone/browser cannot provide GPS.
    with st.container(key="home_destination"):
        place_button_label = f"📍 地名：{active_place}" if active_place else "📍 地名：自動取得（必要なら手入力）"
        if st.button(place_button_label, key="home_destination_toggle", use_container_width=True):
            st.session_state.show_home_destination_editor = not bool(
                st.session_state.get("show_home_destination_editor")
            )
            st.rerun()

        if st.session_state.get("show_home_destination_editor"):
            trip = ensure_today_trip()
            current_trip = get_trip(trip["id"]) or trip
            current_photos = list_trip_photos(trip["id"])
            current_place = trip_place_label(current_trip, photos=current_photos)
            destination = st.text_input(
                "地名",
                value=str(current_trip.get("destination") or current_place),
                placeholder="例：神楽坂、浅草のあたり",
                key=f"home_destination_input_{trip['id']}",
                label_visibility="collapsed",
            )
            save_col, close_col = st.columns([2, 1])
            with save_col:
                if st.button(
                    "保存",
                    type="primary",
                    use_container_width=True,
                    key=f"home_destination_save_{trip['id']}",
                ):
                    try:
                        update_trip_destination(trip["id"], destination)
                        st.session_state.show_home_destination_editor = False
                        st.rerun()
                    except Exception as exc:
                        st.error("地名を保存できませんでした。")
                        with st.expander("保護者向け詳細"):
                            st.code(str(exc))
            with close_col:
                if st.button(
                    "閉じる",
                    use_container_width=True,
                    key=f"home_destination_close_{trip['id']}",
                ):
                    st.session_state.show_home_destination_editor = False
                    st.rerun()

    st.markdown('<div class="home-section-label" style="margin-top:1rem;">たまに使う</div>', unsafe_allow_html=True)
    with st.container(key="home_secondary"):
        secondary_left, secondary_right = st.columns([1.2, 1])
        with secondary_left:
            render_home_button("🔍\n振り返り（たまに）", "review", "home_review")
        with secondary_right:
            render_home_button("⚙️\n設定", "settings", "home_settings")

    st.markdown(
        '<div class="home-footer-note">写真は0枚でも大丈夫。気になったときだけ使います。</div>',
        unsafe_allow_html=True,
    )


def render_diary_title_editor(trip_id, current_title, key_prefix):
    with st.expander("タイトルを変更"):
        edited_title = st.text_input(
            "日記タイトル",
            value=str(current_title or ""),
            key=f"{key_prefix}_title_input_{trip_id}",
        )
        if st.button(
            "タイトルを保存",
            use_container_width=True,
            key=f"{key_prefix}_title_save_{trip_id}",
        ):
            try:
                update_diary_title(trip_id, edited_title)
                st.session_state["_diary_notice"] = "日記のタイトルを変更しました。"
                st.rerun()
            except Exception as exc:
                st.error("タイトルを変更できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))


def render_recent_camera_photo_comment(trip):
    """Show the just-saved photo below the camera and let the child comment immediately."""
    trip_id = (trip or {}).get("id")
    if not trip_id:
        return
    recent_key = f"_camera_recent_photo_{trip_id}"
    photo_id = st.session_state.get(recent_key)
    if not photo_id:
        return

    photos = list_trip_photos(trip_id)
    photo = next((p for p in photos if p.get("id") == photo_id), None)
    if not photo:
        st.session_state.pop(recent_key, None)
        return

    st.divider()
    st.markdown("#### 今撮った写真")
    try:
        image_bytes = download_photo(photo["storage_path"])
        # Keep the just-saved preview compact so the photo and microphone can fit
        # together on a phone screen. The full image is still stored unchanged.
        preview_src = image_data_url(image_bytes)
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:.25rem 0 .45rem;">
              <img src="{preview_src}" alt="今撮った写真"
                   style="display:block;max-width:min(72vw,320px);max-height:34dvh;width:auto;height:auto;object-fit:contain;border-radius:14px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.error("今撮った写真を表示できませんでした。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        return

    location_label = photo_location_label(photo)
    if location_label:
        st.caption(f"📍 {location_label}")

    reflection = photo.get("reflection_json") or {}
    if not isinstance(reflection, dict):
        reflection = {}
    conversation = _stored_photo_conversation(photo)
    signals = photo.get("signals_json") or {}
    if not isinstance(signals, dict):
        signals = {}
    done = bool(reflection.get("conversation_done"))

    if conversation:
        render_conversation(conversation)

    audio_state_key = f"quick_photo_audio_{photo_id}"
    audio_pending_key = f"quick_photo_audio_pending_{photo_id}"
    if st.session_state.get(audio_state_key):
        st.audio(
            st.session_state[audio_state_key],
            format="audio/wav",
            autoplay=bool(st.session_state.get(audio_pending_key, False)),
        )
        st.session_state[audio_pending_key] = False

    if done:
        st.success("コメントを保存しました。")
        return

    child_turns = sum(1 for x in conversation if x.get("role") == "child")
    if child_turns == 0:
        st.caption("この写真について、まず自由に1回話してね。")
        mic_label = "今撮った写真について話してね"
    else:
        mic_label = "AIの質問に答えてね"

    serial_key = f"quick_photo_answer_serial_{photo_id}"
    serial = int(st.session_state.get(serial_key) or 0)
    answer_audio = far_field_audio_input(
        mic_label,
        key=f"quick_photo_answer_{photo_id}_{serial}",
    )
    digest_key = f"quick_photo_answer_digest_{photo_id}_{serial}"
    if answer_audio is None:
        return

    digest = audio_digest(answer_audio)
    if not digest or st.session_state.get(digest_key) == digest:
        return

    try:
        with st.spinner("声を聞いています…"):
            transcript = transcribe_audio(
                answer_audio,
                f"東京ぶらり旅で今撮った写真について、子どもが自由に説明しています。場所は{location_label or '不明'}です。",
            )
            if not transcript:
                raise ValueError("文字起こしが空でした。")
            conversation = list(conversation)
            conversation.append({"role": "child", "text": transcript})
            child_turns = sum(1 for x in conversation if x.get("role") == "child")
            result = next_photo_turn(image_bytes, conversation, child_turns)
            assistant_text = str(result.get("reply", "")).strip()
            next_question = str(result.get("next_question", "")).strip()
            if next_question:
                assistant_text = (assistant_text + " " + next_question).strip()
            if not assistant_text:
                assistant_text = "ありがとう。"
            conversation.append({"role": "assistant", "text": assistant_text})
            signals = merge_signals(signals, result.get("signals", {}))
            done = bool(result.get("done"))
            update_photo_reflection(photo_id, conversation, signals, done=done)
            audio = speech_bytes(assistant_text)

        st.session_state[audio_state_key] = audio
        st.session_state[audio_pending_key] = True
        st.session_state[serial_key] = serial + 1
        st.session_state[digest_key] = digest
        st.rerun()
    except Exception as exc:
        st.error("うまく聞き取れませんでした。もう一度話してください。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))


# ============================================================
# Page: Trip / camera
# ============================================================
def page_trip():
    if st.button("←", key="camera_back_home", help="ホームへ戻る"):
        go_page("home")

    trip = ensure_today_trip()
    digest_key = f"saved_camera_digest_{trip['id']}"

    notice = st.session_state.pop("_camera_notice", None)
    if notice:
        st.success(notice)

    if live_camera_component is None:
        st.error("ライブカメラ機能に必要なStreamlitのバージョンが古いです。requirements.txtを更新してください。")
        render_recent_camera_photo_comment(trip)
        return

    auto_start = bool(st.session_state.pop("_camera_auto_start", False))
    result = live_camera_component(
        data={"auto_start": auto_start},
        key=f"live_camera_{trip['id']}_{st.session_state.capture_serial}",
        on_photo_change=lambda: None,
        on_camera_error_change=lambda: None,
    )
    payload = getattr(result, "photo", None)
    camera_error = getattr(result, "camera_error", None)

    if camera_error:
        message = camera_error.get("message") if isinstance(camera_error, dict) else str(camera_error)
        if message:
            st.warning(message)

    if isinstance(payload, dict) and payload.get("data_url"):
        try:
            raw = decode_camera_data_url(payload["data_url"])
            digest = hashlib.sha1(raw).hexdigest()
            if st.session_state.get(digest_key) != digest:
                capture_source = str(payload.get("source") or "camera")
                fresh_trip = get_trip(trip["id"]) or trip
                location = build_photo_location(
                    payload.get("location"),
                    fresh_trip,
                    capture_source=capture_source,
                )

                with st.spinner("写真を残しています…"):
                    saved_photo = upload_photo(
                        trip["id"],
                        raw,
                        location=location,
                        captured_at=payload.get("captured_at"),
                        capture_source=capture_source,
                    )

                st.session_state[digest_key] = digest
                if isinstance(saved_photo, dict) and saved_photo.get("id"):
                    st.session_state[f"_camera_recent_photo_{trip['id']}"] = saved_photo["id"]
                st.session_state.capture_serial += 1
                st.session_state["_camera_notice"] = "写真を保存しました。"
                st.rerun()
        except Exception as exc:
            st.error("写真を保存できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    # Keep the camera choices at the top, then show the just-saved photo and its
    # comment recorder directly underneath.
    render_recent_camera_photo_comment(trip)


# ============================================================
# Page: Diary conversation
# ============================================================
def page_diary():
    page_top(
        "📖 日記",
        "写真を見ながらAIと少し話します。AIは本人が話していない内容を日記に足しません。",
    )

    notice = st.session_state.pop("_diary_notice", None)
    if notice:
        st.success(notice)

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

    talk_key = f"diary_talk_photo_{trip_id}"

    if existing and f"reflection_state_{trip_id}" not in st.session_state:
        clicked_pid = render_diary_photo_gallery(trip_id, photos, state=None) if photos else None
        if clicked_pid:
            state = reflection_state(trip_id, photos)
            st.session_state[f"diary_existing_photo_view_{trip_id}"] = True
            if open_diary_photo_talk(trip_id, clicked_pid, state):
                st.rerun()

        existing_title = diary_display_title(existing, trip, photos=photos)
        st.markdown(
            f"""
            <div class="diary-card">
              <div class="hero-title">{html.escape(existing_title)}</div>
              <div class="big-text">{html.escape(existing.get('diary_text') or '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_diary_reflection_summary(existing.get("ai_meta") or {})
        render_diary_title_editor(trip_id, existing_title, "diary_existing")
        if photos and st.button("この日の写真から、もう一度日記をつくる", use_container_width=True):
            reflection_state(trip_id, photos)
            st.session_state.pop(f"diary_existing_photo_view_{trip_id}", None)
            st.session_state.pop(talk_key, None)
            st.rerun()

        render_diary_delete_controls(trip_id, photos)
        return

    if not photos:
        st.warning("このぶらり旅には写真がありません。")
        render_diary_delete_controls(trip_id, photos)
        return

    state = reflection_state(trip_id, photos)
    photo_map = {p["id"]: p for p in photos}
    selected_pid = st.session_state.get(talk_key)
    in_talk_mode = selected_pid in photo_map

    if not in_talk_mode:
        st.session_state.pop(talk_key, None)
        clicked_pid = render_diary_photo_gallery(trip_id, photos, state=state)
        if clicked_pid and open_diary_photo_talk(trip_id, clicked_pid, state):
            st.rerun()
        selected_pid = state.get("selected_photo_id")

    all_done = bool(state["photo_ids"]) and all(
        bool(state["items"].get(pid, {}).get("done")) for pid in state["photo_ids"]
    )
    if (not in_talk_mode) and all_done:
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
                    state["draft_title"] = diary_display_title(existing, trip, photos=photos)
                    state["draft_meta"] = {
                        "reflection_summary": str(result.get("reflection_summary") or "").strip(),
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
            render_diary_delete_controls(trip_id, photos, current_photo_id=selected_pid)
            return

        fixed_title = diary_display_title(existing, trip, photos=photos)
        state["draft_title"] = fixed_title
        st.markdown(
            f"""
            <div class="diary-card">
              <div class="hero-title">{html.escape(fixed_title)}</div>
              <div class="big-text">{html.escape(state.get('draft') or '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_diary_reflection_summary(state.get("draft_meta") or {})
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
                    fixed_title,
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

        render_diary_delete_controls(trip_id, photos, current_photo_id=selected_pid)
        return

    if not in_talk_mode:
        render_diary_delete_controls(trip_id, photos)
        return

    if selected_pid not in photo_map:
        render_diary_delete_controls(trip_id, photos)
        return

    pid = selected_pid
    photo = photo_map[pid]
    item = state["items"][pid]

    if st.button("← 写真一覧へ", use_container_width=True, key=f"back_to_diary_gallery_{trip_id}_{pid}"):
        st.session_state.pop(talk_key, None)
        if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
            st.session_state.pop(f"reflection_state_{trip_id}", None)
        st.rerun()

    try:
        image_bytes = download_photo(photo["storage_path"])
        st.image(image_bytes, use_container_width=True)
    except Exception as exc:
        st.error("写真を読み込めませんでした。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        render_diary_delete_controls(trip_id, photos, current_photo_id=pid, show_photo_navigation=True)
        return

    location_label = photo_location_label(photo)
    if location_label:
        st.caption(f"📍 {location_label}")

    if item.get("done"):
        render_conversation(item.get("conversation", []))
        st.info("この写真のお話は完了しています。")
        if st.button("この写真についてもう少し話す", use_container_width=True, key=f"reopen_photo_{trip_id}_{pid}"):
            item["done"] = False
            update_photo_reflection(pid, item.get("conversation", []), item.get("signals", {}), done=False)
            st.rerun()
        render_diary_delete_controls(trip_id, photos, current_photo_id=pid, show_photo_navigation=True)
        return

    if not item.get("started"):
        st.markdown("#### まず、この写真について話してね")
        st.caption("まず自由に1回話してね。基本はこれで終わりです。気持ちが分からないときだけ一度聞き、ネガティブな気持ちが出たときだけ『どうしたい？』まで聞きます。")
        first_audio = far_field_audio_input(
            "まず自由に話してね",
            key=f"photo_first_answer_{trip_id}_{pid}_{state['answer_serial']}",
        )
        first_digest_key = f"photo_first_digest_{trip_id}_{pid}_{state['answer_serial']}"
        if first_audio is not None:
            digest = audio_digest(first_audio)
            if digest and st.session_state.get(first_digest_key) != digest:
                try:
                    audio_file = first_audio
                    with st.spinner("声を聞いています…"):
                        transcript = transcribe_audio(
                            audio_file,
                            f"東京ぶらり旅の写真について、子どもがAIに聞かれる前に自由に説明しています。場所は{location_label or '不明'}です。",
                        )
                        if not transcript:
                            raise ValueError("文字起こしが空でした。")
                        item["conversation"] = [{"role": "child", "text": transcript}]
                        item["started"] = True
                        item["done"] = False
                        result = next_photo_turn(image_bytes, item["conversation"], 1)
                        assistant_text = str(result.get("reply", "")).strip()
                        next_question = str(result.get("next_question", "")).strip()
                        if next_question:
                            assistant_text = (assistant_text + " " + next_question).strip()
                        if not assistant_text:
                            assistant_text = "ありがとう。"
                        item["conversation"].append({"role": "assistant", "text": assistant_text})
                        item["signals"] = merge_signals(item.get("signals", {}), result.get("signals", {}))
                        item["done"] = bool(result.get("done"))
                        update_photo_reflection(
                            pid,
                            item["conversation"],
                            item["signals"],
                            done=item["done"],
                        )
                        audio = speech_bytes(assistant_text)
                    state["audio_bytes"] = audio
                    state["audio_pending"] = True
                    state["answer_serial"] += 1
                    st.session_state[first_digest_key] = digest
                    st.rerun()
                except Exception as exc:
                    st.error("うまく聞き取れませんでした。もう一度話してください。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))

        if st.button("この写真はとばす", use_container_width=True, key=f"skip_photo_{trip_id}_{pid}"):
            item["done"] = True
            item["started"] = True
            update_photo_reflection(pid, [], {}, done=True)
            st.session_state.pop(talk_key, None)
            if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
                st.session_state.pop(f"reflection_state_{trip_id}", None)
            st.rerun()
        render_diary_delete_controls(trip_id, photos, current_photo_id=pid, show_photo_navigation=True)
        return

    render_conversation(item.get("conversation", []))
    if state.get("audio_bytes"):
        st.audio(
            state["audio_bytes"],
            format="audio/wav",
            autoplay=bool(state.get("audio_pending")),
        )
        state["audio_pending"] = False

    answer_audio = far_field_audio_input(
        "AIの質問に答えてね",
        key=f"photo_answer_{trip_id}_{pid}_{state['answer_serial']}",
    )
    digest_key = f"photo_answer_digest_{trip_id}_{pid}_{state['answer_serial']}"
    if answer_audio is not None:
        digest = audio_digest(answer_audio)
        if digest and st.session_state.get(digest_key) != digest:
            try:
                audio_file = answer_audio
                with st.spinner("声を聞いています…"):
                    transcript = transcribe_audio(
                        audio_file,
                        f"東京ぶらり旅の写真を見ながら、AIの短い質問に子どもが答えています。場所は{location_label or '不明'}です。",
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
                        assistant_text = "ありがとう。"
                    item["conversation"].append({"role": "assistant", "text": assistant_text})
                    item["signals"] = merge_signals(item.get("signals", {}), result.get("signals", {}))
                    item["done"] = bool(result.get("done"))
                    update_photo_reflection(
                        pid,
                        item["conversation"],
                        item["signals"],
                        done=item["done"],
                    )
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

    if st.button("この写真のお話はここまで", use_container_width=True, key=f"finish_photo_talk_{trip_id}_{pid}"):
        item["done"] = True
        update_photo_reflection(pid, item.get("conversation", []), item.get("signals", {}), done=True)
        state["audio_bytes"] = None
        state["audio_pending"] = False
        st.session_state.pop(talk_key, None)
        if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
            st.session_state.pop(f"reflection_state_{trip_id}", None)
        st.rerun()

    render_diary_delete_controls(trip_id, photos, current_photo_id=pid, show_photo_navigation=True)


# ============================================================
# Page: History
# ============================================================
def page_history(embedded=False):
    if not embedded:
        page_top("📚 これまでの日記")

    notice = st.session_state.pop("_diary_notice", None)
    if notice:
        st.success(notice)

    rows = list_recent_diaries()
    if not rows:
        st.session_state.pop("history_detail_trip_id", None)
        st.info("まだ日記はありません。")
        return

    detail_trip_id = st.session_state.get("history_detail_trip_id")
    detail_row = next(
        (row for row in rows if row.get("diary", {}).get("trip_id") == detail_trip_id),
        None,
    )
    if detail_trip_id and detail_row is None:
        st.session_state.pop("history_detail_trip_id", None)
        detail_trip_id = None

    # A diary title opens a dedicated detail screen. This makes the bottom
    # navigation unambiguous on a phone: back returns to the history list.
    if detail_row is not None:
        diary = detail_row["diary"]
        trip = detail_row["trip"]
        trip_id = diary["trip_id"]
        photos = list_trip_photos(trip_id)
        daily_title = diary_display_title(diary, trip, photos=photos)
        title = f"{trip.get('trip_date', '')}　{daily_title}"

        st.markdown(f"### {html.escape(title)}")
        render_diary_title_editor(trip_id, daily_title, "history_detail")
        render_small_gallery(photos, max_count=None, columns=3)
        st.markdown(
            f"""
            <div class="diary-card">
              <div class="big-text">{html.escape(diary.get('diary_text') or '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta = diary.get("ai_meta") or {}
        render_diary_reflection_summary(meta)
        child_points = meta.get("child_points", []) if isinstance(meta, dict) else []
        if child_points:
            with st.expander("この日記のもとになった言葉"):
                for point in child_points[:3]:
                    st.write("・" + str(point))

        st.divider()
        back_col, home_col = st.columns(2)
        with back_col:
            with st.container(key="history_back_nav"):
                if st.button(
                    "← 前の画面に戻る",
                    use_container_width=True,
                    key=f"history_back_{trip_id}",
                ):
                    st.session_state.pop("history_detail_trip_id", None)
                    st.rerun()
        with home_col:
            with st.container(key="history_home_nav"):
                if st.button(
                    "トップ画面に戻る",
                    use_container_width=True,
                    key=f"history_home_{trip_id}",
                ):
                    st.session_state.pop("history_detail_trip_id", None)
                    go_page("home")

        if st.button(
            "🗑 この日記を削除",
            use_container_width=True,
            key=f"history_delete_{trip_id}",
        ):
            confirm_diary_delete_dialog(trip_id, len(photos))
        return

    st.caption("読みたい日記を選んでください。")
    for row in rows:
        diary = row["diary"]
        trip = row["trip"]
        trip_id = diary["trip_id"]
        photos = list_trip_photos(trip_id)
        daily_title = diary_display_title(diary, trip, photos=photos)
        title = f"{trip.get('trip_date', '')}　{daily_title}"
        if st.button(
            title,
            use_container_width=True,
            key=f"history_open_{trip_id}",
        ):
            st.session_state["history_detail_trip_id"] = trip_id
            st.rerun()


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
    st.markdown("#### 自動ログイン")
    st.caption("この端末では、一度あいことばを入力すると次回から自動でログインします。")
    if st.button("この端末の自動ログインを解除", use_container_width=True, key="settings_clear_auto_login"):
        clear_browser_auto_login()
        st.success("この端末の自動ログインを解除しました。次回はあいことばが必要です。")

    st.divider()
    st.markdown("#### カメラについて")
    st.write(
        "『カメラで撮る』画面では、ブラウザのライブカメラを直接開いて撮影します。"
        "初回だけ、このサイトへのカメラ使用を『許可』してください。"
    )
    st.caption(
        "初回はカメラとは別に位置情報の許可も求められます。位置情報がオフ・拒否・取得不能の場合は、"
        "ホームの地名表示（未登録なら「地名：登録なし（自動取得）」）を押して入力した内容を写真の場所として使います。"
    )

    st.divider()
    st.markdown("#### プロジェクトの考え方")
    st.caption("写真の枚数や『便利・不便を見つけること』を課題にはしません。本人が気になったものを残し、あとから本人の言葉で振り返ります。")


# ============================================================
# Main UI
# ============================================================
verify_setup()
require_family_pin()
init_state()
restore_recent_camera_session()
sync_browser_history()

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
