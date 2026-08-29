import base64
import hashlib
import hmac
import html
import io
import json
import os
import random
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

# Cold-start priority: home and camera UI should not import AI/image/database clients
# until a feature actually needs them. Streamlit itself is the only eager app dependency.

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HOME_ICON_CANDIDATES = {
    "camera": [
        os.path.join(APP_DIR, "assets", "icons", "camera.png"),
        os.path.join(APP_DIR, "camera.png"),
    ],
    "diary": [
        os.path.join(APP_DIR, "assets", "icons", "diary.png"),
        os.path.join(APP_DIR, "diary.png"),
    ],
    "review": [
        os.path.join(APP_DIR, "assets", "icons", "review.png"),
        os.path.join(APP_DIR, "review.png"),
    ],
    "settings": [
        os.path.join(APP_DIR, "assets", "icons", "settings.png"),
        os.path.join(APP_DIR, "settings.png"),
    ],
    "settings_yamanote": [os.path.join(APP_DIR, "assets", "icons", "settings_yamanote.png")],
    "settings_keihin_tohoku": [os.path.join(APP_DIR, "assets", "icons", "settings_keihin_tohoku.png")],
    "settings_chuo_rapid": [os.path.join(APP_DIR, "assets", "icons", "settings_chuo_rapid.png")],
    "settings_chuo_sobu": [os.path.join(APP_DIR, "assets", "icons", "settings_chuo_sobu.png")],
    "settings_sotetsu": [os.path.join(APP_DIR, "assets", "icons", "settings_sotetsu.png")],
    "settings_shonan_shinjuku": [os.path.join(APP_DIR, "assets", "icons", "settings_shonan_shinjuku.png")],
    "train": [
        os.path.join(APP_DIR, "assets", "icons", "train.png"),
        os.path.join(APP_DIR, "train.png"),
    ],
    "train_yamanote": [os.path.join(APP_DIR, "assets", "icons", "train_yamanote.png")],
    "train_keihin_tohoku": [os.path.join(APP_DIR, "assets", "icons", "train_keihin_tohoku.png")],
    "train_chuo_rapid": [os.path.join(APP_DIR, "assets", "icons", "train_chuo_rapid.png")],
    "train_chuo_sobu": [os.path.join(APP_DIR, "assets", "icons", "train_chuo_sobu.png")],
    "train_sotetsu": [os.path.join(APP_DIR, "assets", "icons", "train_sotetsu.png")],
    "train_shonan_shinjuku": [os.path.join(APP_DIR, "assets", "icons", "train_shonan_shinjuku.png")],
    "camera_yamanote": [os.path.join(APP_DIR, "assets", "icons", "camera_yamanote.png")],
    "camera_keihin_tohoku": [os.path.join(APP_DIR, "assets", "icons", "camera_keihin_tohoku.png")],
    "camera_chuo_rapid": [os.path.join(APP_DIR, "assets", "icons", "camera_chuo_rapid.png")],
    "camera_chuo_sobu": [os.path.join(APP_DIR, "assets", "icons", "camera_chuo_sobu.png")],
    "camera_sotetsu": [os.path.join(APP_DIR, "assets", "icons", "camera_sotetsu.png")],
    "camera_shonan_shinjuku": [os.path.join(APP_DIR, "assets", "icons", "camera_shonan_shinjuku.png")],
    "diary_yamanote": [os.path.join(APP_DIR, "assets", "icons", "diary_yamanote.png")],
    "diary_keihin_tohoku": [os.path.join(APP_DIR, "assets", "icons", "diary_keihin_tohoku.png")],
    "diary_chuo_rapid": [os.path.join(APP_DIR, "assets", "icons", "diary_chuo_rapid.png")],
    "diary_chuo_sobu": [os.path.join(APP_DIR, "assets", "icons", "diary_chuo_sobu.png")],
    "diary_sotetsu": [os.path.join(APP_DIR, "assets", "icons", "diary_sotetsu.png")],
    "diary_shonan_shinjuku": [os.path.join(APP_DIR, "assets", "icons", "diary_shonan_shinjuku.png")],
}

# One route choice controls the train, camera and diary together so the home screen
# reads as one coherent visual theme. The camera/diary versions are deliberately
# lighter pastel variants of the route color.
HOME_ROUTE_THEMES = {
    "train_yamanote": {
        "line_name": "山手線",
        "camera_key": "camera_yamanote",
        "diary_key": "diary_yamanote",
        "settings_key": "settings_yamanote",
        "accent": "#7EBD52",
        "accent_rgb": "126,189,82",
        "accent2": "#BDEB91",
        "accent2_rgb": "189,235,145",
    },
    "train_keihin_tohoku": {
        "line_name": "京浜東北線",
        "camera_key": "camera_keihin_tohoku",
        "diary_key": "diary_keihin_tohoku",
        "settings_key": "settings_keihin_tohoku",
        "accent": "#62C5E5",
        "accent_rgb": "98,197,229",
        "accent2": "#B9EAF4",
        "accent2_rgb": "185,234,244",
    },
    "train_chuo_rapid": {
        "line_name": "中央本線快速",
        "camera_key": "camera_chuo_rapid",
        "diary_key": "diary_chuo_rapid",
        "settings_key": "settings_chuo_rapid",
        "accent": "#F3982D",
        "accent_rgb": "243,152,45",
        "accent2": "#FFD3A5",
        "accent2_rgb": "255,211,165",
    },
    "train_chuo_sobu": {
        "line_name": "中央・総武線",
        "camera_key": "camera_chuo_sobu",
        "diary_key": "diary_chuo_sobu",
        "settings_key": "settings_chuo_sobu",
        "accent": "#E4C72D",
        "accent_rgb": "228,199,45",
        "accent2": "#FFF0A4",
        "accent2_rgb": "255,240,164",
    },
    "train_sotetsu": {
        "line_name": "相鉄線",
        "camera_key": "camera_sotetsu",
        "diary_key": "diary_sotetsu",
        "settings_key": "settings_sotetsu",
        "accent": "#3D6FA6",
        "accent_rgb": "61,111,166",
        "accent2": "#B7CEEA",
        "accent2_rgb": "183,206,234",
    },
    "train_shonan_shinjuku": {
        "line_name": "湘南新宿ライン",
        "camera_key": "camera_shonan_shinjuku",
        "diary_key": "diary_shonan_shinjuku",
        "settings_key": "settings_shonan_shinjuku",
        "accent": "#65AE55",
        "accent_rgb": "101,174,85",
        "accent2": "#F0A15B",
        "accent2_rgb": "240,161,91",
    },
}

HOME_TRAIN_LINES = [(theme["line_name"], key) for key, theme in HOME_ROUTE_THEMES.items()]


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
      .home-hero-inner {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: .9rem;
      }
      .home-hero-copy {
        flex: 1 1 auto;
        min-width: 0;
      }
      .home-hero-train {
        flex: 0 0 auto;
        width: 92px;
        height: 76px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-right: -.18rem;
      }
      .home-hero-train img {
        display: block;
        width: 92px;
        height: 76px;
        object-fit: contain;
        filter: drop-shadow(0 5px 8px rgba(33, 75, 49, .08));
      }
      .home-eyebrow {
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .12em;
        opacity: .58;
        margin-bottom: .42rem;
      }
      .home-title {
        font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans JP", sans-serif;
        font-size: clamp(2.05rem, 5.5vw, 2.35rem);
        font-weight: 900;
        letter-spacing: .015em;
        line-height: 1.08;
        color: rgba(31, 38, 48, .97);
        text-wrap: nowrap;
        text-shadow: 0 1px 0 rgba(255,255,255,.70);
        margin-top: .02rem;
        margin-bottom: .12rem;
      }
      .home-tagline {
        margin-top: .52rem;
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
        white-space: nowrap !important;
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease;
      }
      .st-key-home_primary div.stButton > button {
        height: 5.35rem !important;
        min-height: 5.35rem !important;
        max-height: 5.35rem !important;
        border-radius: 24px !important;
        font-size: 1.34rem !important;
        font-weight: 840 !important;
        line-height: 1.18 !important;
        letter-spacing: .01em !important;
        padding: .62rem .88rem !important;
        display: grid !important;
        grid-template-columns: auto max-content !important;
        align-items: center !important;
        justify-content: center !important;
        column-gap: .50rem !important;
        text-align: left !important;
      }
      .st-key-home_secondary div.stButton > button {
        height: 4.75rem !important;
        min-height: 4.75rem !important;
        max-height: 4.75rem !important;
        border-radius: 21px !important;
        font-size: 1.22rem !important;
        font-weight: 800 !important;
        line-height: 1.16 !important;
        letter-spacing: .01em !important;
        padding: .56rem .78rem !important;
        display: grid !important;
        grid-template-columns: auto max-content !important;
        align-items: center !important;
        justify-content: center !important;
        column-gap: .46rem !important;
        text-align: left !important;
      }
      .st-key-home_primary div.stButton > button [data-testid="stMarkdownContainer"],
      .st-key-home_secondary div.stButton > button [data-testid="stMarkdownContainer"] {
        display: block !important;
        width: auto !important;
        min-width: max-content !important;
        max-width: none !important;
        margin: 0 !important;
        padding: 0 !important;
        justify-self: start !important;
      }
      .st-key-home_primary div.stButton > button p,
      .st-key-home_secondary div.stButton > button p {
        margin: 0 !important;
        width: auto !important;
        min-width: max-content !important;
        max-width: none !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        overflow-wrap: normal !important;
        writing-mode: horizontal-tb !important;
        text-orientation: mixed !important;
      }
      .st-key-home_camera div.stButton > button,
      .st-key-home_camera button,
      .st-key-home_diary div.stButton > button,
      .st-key-home_diary button {
        border: 1.8px solid rgba(115, 165, 232, .82) !important;
        background: linear-gradient(155deg, rgba(232, 244, 255, .98), rgba(245, 240, 255, .94)) !important;
        box-shadow: 0 10px 24px rgba(101, 150, 220, .11), 0 0 0 2px rgba(255,255,255,.34) inset !important;
      }
      .st-key-home_camera div.stButton > button:hover,
      .st-key-home_camera button:hover,
      .st-key-home_diary div.stButton > button:hover,
      .st-key-home_diary button:hover {
        transform: translateY(-1px);
        background: linear-gradient(155deg, rgba(220, 239, 255, 1), rgba(240, 233, 255, .98)) !important;
        box-shadow: 0 12px 26px rgba(101, 150, 220, .14), 0 0 0 2px rgba(255,255,255,.42) inset !important;
      }
      .st-key-home_review div.stButton > button,
      .st-key-home_review button {
        border: 1.8px solid rgba(237, 176, 84, .80) !important;
        background: linear-gradient(155deg, rgba(255, 247, 226, .98), rgba(255, 238, 214, .94)) !important;
        box-shadow: 0 9px 22px rgba(238, 178, 80, .10), 0 0 0 2px rgba(255,255,255,.30) inset !important;
      }
      .st-key-home_review div.stButton > button:hover,
      .st-key-home_review button:hover {
        transform: translateY(-1px);
        background: linear-gradient(155deg, rgba(255, 243, 215, 1), rgba(255, 232, 199, .98)) !important;
        box-shadow: 0 11px 24px rgba(238, 178, 80, .14), 0 0 0 2px rgba(255,255,255,.36) inset !important;
      }
      .st-key-home_settings div.stButton > button,
      .st-key-home_settings button {
        border: 1.6px solid rgba(176, 154, 227, .68) !important;
        background: linear-gradient(155deg, rgba(245, 241, 255, .98), rgba(238, 245, 255, .94)) !important;
        box-shadow: 0 8px 20px rgba(176, 154, 227, .08), 0 0 0 2px rgba(255,255,255,.30) inset !important;
      }
      .st-key-home_settings div.stButton > button:hover,
      .st-key-home_settings button:hover {
        transform: translateY(-1px);
        background: linear-gradient(155deg, rgba(241, 235, 255, 1), rgba(233, 242, 255, .98)) !important;
        box-shadow: 0 10px 22px rgba(176, 154, 227, .12), 0 0 0 2px rgba(255,255,255,.36) inset !important;
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
      [class*="st-key-ai_trip_summary_"] div.stButton > button,
      [class*="st-key-ai_trip_summary_"] button {
        border: 2px solid #C58BD8 !important;
        background: linear-gradient(135deg, rgba(255, 216, 235, .48), rgba(224, 214, 255, .46)) !important;
        color: inherit !important;
        border-radius: 18px !important;
        font-weight: 780 !important;
        box-shadow: 0 6px 16px rgba(197, 139, 216, .16), 0 0 0 2px rgba(255,255,255,.20) inset !important;
        transition: transform .12s ease, box-shadow .12s ease, background .12s ease, border-color .12s ease;
      }
      [class*="st-key-ai_trip_summary_"] div.stButton > button:hover,
      [class*="st-key-ai_trip_summary_"] button:hover {
        border-color: #B675CD !important;
        background: linear-gradient(135deg, rgba(255, 205, 230, .66), rgba(215, 201, 255, .62)) !important;
        box-shadow: 0 8px 20px rgba(197, 139, 216, .22), 0 0 0 2px rgba(255,255,255,.24) inset !important;
        transform: translateY(-1px);
      }
      [class*="st-key-summary_feedback_good_"] div.stButton > button,
      [class*="st-key-summary_feedback_good_"] button {
        border: 1.8px solid rgba(72, 166, 123, .72) !important;
        background: rgba(183, 236, 207, .28) !important;
        border-radius: 16px !important;
        font-weight: 760 !important;
      }
      [class*="st-key-summary_feedback_good_"] div.stButton > button:hover,
      [class*="st-key-summary_feedback_good_"] button:hover {
        background: rgba(183, 236, 207, .44) !important;
        border-color: rgba(49, 139, 97, .88) !important;
      }
      [class*="st-key-summary_feedback_bad_"] div.stButton > button,
      [class*="st-key-summary_feedback_bad_"] button {
        border: 1.8px solid rgba(218, 126, 137, .68) !important;
        background: rgba(255, 214, 219, .25) !important;
        border-radius: 16px !important;
        font-weight: 760 !important;
      }
      [class*="st-key-summary_feedback_bad_"] div.stButton > button:hover,
      [class*="st-key-summary_feedback_bad_"] button:hover {
        background: rgba(255, 214, 219, .42) !important;
        border-color: rgba(194, 91, 105, .88) !important;
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
      .st-key-history_home_nav button,
      .st-key-camera_home_nav div.stButton > button,
      .st-key-camera_home_nav button,
      .st-key-global_home_nav div.stButton > button,
      .st-key-global_home_nav button {
        border: 2px solid #2F9E73 !important;
        background: rgba(47, 158, 115, .08) !important;
        color: inherit !important;
        box-shadow: 0 0 0 2px rgba(47, 158, 115, .04) inset;
      }
      .st-key-history_home_nav div.stButton > button:hover,
      .st-key-history_home_nav button:hover,
      .st-key-camera_home_nav div.stButton > button:hover,
      .st-key-camera_home_nav button:hover,
      .st-key-global_home_nav div.stButton > button:hover,
      .st-key-global_home_nav button:hover {
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
          /* Keep the first app row below Streamlit's mobile toolbar.
             The extra safe-area term also covers phones with a display cutout. */
          padding-top: calc(3.35rem + env(safe-area-inset-top, 0px)) !important;
        }
        .home-hero {
          padding: 1rem 1rem .92rem;
          border-radius: 21px;
        }
        .home-hero-inner { gap: .45rem; }
        .home-hero-train { width: 76px; height: 64px; margin-right: -.12rem; }
        .home-hero-train img { width: 76px; height: 64px; }
        .home-title {
          font-size: clamp(1.86rem, 8.1vw, 2.04rem);
          letter-spacing: .01em;
          line-height: 1.08;
        }
        .home-tagline { font-size: .90rem; }
        .st-key-home_primary div.stButton > button {
          height: 4.95rem !important;
          min-height: 4.95rem !important;
          max-height: 4.95rem !important;
          border-radius: 21px !important;
          font-size: 1.20rem !important;
          line-height: 1.14 !important;
          padding: .52rem .64rem !important;
          column-gap: .42rem !important;
        }
        .st-key-home_secondary div.stButton > button {
          height: 4.45rem !important;
          min-height: 4.45rem !important;
          max-height: 4.45rem !important;
          border-radius: 18px !important;
          font-size: 1.10rem !important;
          line-height: 1.12 !important;
          padding: .46rem .58rem !important;
          column-gap: .36rem !important;
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
FAMILY_TABLE = "burari_families"
MEMBER_TABLE = "burari_members"


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

  <video id="live-camera-video" class="live-camera-video" playsinline autoplay muted hidden></video>

  <div id="camera-active-actions" class="camera-active-actions" hidden>
    <button id="live-camera-shoot" class="camera-shoot-button" type="button">● 撮影する</button>
    <button id="live-camera-stop" class="camera-sub-button" type="button">閉じる</button>
  </div>

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
}
.camera-active-actions {
  margin: 8px 0 0 0;
}
.camera-review-actions {
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

far_field_mic_component = None
_far_field_mic_component_initialized = False


def _get_far_field_mic_component():
    """Register the microphone component only when a diary/comment recorder is opened."""
    global far_field_mic_component, _far_field_mic_component_initialized
    if _far_field_mic_component_initialized:
        return far_field_mic_component
    _far_field_mic_component_initialized = True
    try:
        far_field_mic_component = st.components.v2.component(
            "tokyo_burari_far_field_mic",
            html=_FAR_FIELD_MIC_HTML,
            css=_FAR_FIELD_MIC_CSS,
            js=_FAR_FIELD_MIC_JS,
        )
    except Exception:
        far_field_mic_component = None
    return far_field_mic_component


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
.diary-photo-wrap {
  position: relative;
  min-width: 0;
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
.diary-photo-card.pending {
  border: 1px solid rgba(128,128,128,.16);
  background: transparent;
}
.diary-photo-card:active { transform: scale(.985); }
.diary-photo-card img {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 9px;
  background: rgba(128, 128, 128, .08);
}
.diary-photo-delete {
  position: absolute;
  top: 3px;
  right: 3px;
  z-index: 3;
  width: 25px;
  height: 25px;
  padding: 0;
  margin: 0;
  border-radius: 999px;
  border: 1.5px solid rgba(255,255,255,.92);
  background: rgba(49,54,63,.72);
  color: #fff;
  font-size: 18px;
  line-height: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 1px 5px rgba(0,0,0,.22);
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.diary-photo-delete:active { transform: scale(.94); }
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
  .diary-photo-delete { top: 2px; right: 2px; width: 23px; height: 23px; font-size: 17px; }
}
"""

_DIARY_GALLERY_JS = r"""
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const grid = parentElement.querySelector('#diary-photo-grid');
  if (!grid) return;

  grid.replaceChildren();
  const photos = Array.isArray(data?.photos) ? data.photos : [];
  const deleteOnly = Boolean(data?.delete_only);

  for (const photo of photos) {
    const wrap = document.createElement('div');
    wrap.className = 'diary-photo-wrap';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = `diary-photo-card ${deleteOnly ? 'pending' : (photo.talked ? 'talked' : 'untalked')}`;
    button.setAttribute(
      'aria-label',
      deleteOnly ? 'まだ日記になっていない写真' : (photo.talked ? '話した写真を開く' : 'まだ話していない写真を開く')
    );
    if (deleteOnly) button.style.cursor = 'default';

    const img = document.createElement('img');
    img.src = photo.src || '';
    img.alt = 'ぶらり旅の写真';
    img.loading = 'lazy';
    img.decoding = 'async';
    img.fetchPriority = 'low';
    button.appendChild(img);

    if (photo.location) {
      const location = document.createElement('div');
      location.className = 'diary-photo-location';
      location.textContent = `📍 ${photo.location}`;
      button.appendChild(location);
    }

    if (!deleteOnly) {
      button.addEventListener('click', () => {
        setTriggerValue('photo_id', String(photo.id));
      });
    }

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'diary-photo-delete';
    remove.textContent = '×';
    remove.setAttribute('aria-label', 'この写真を削除');
    remove.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      setTriggerValue('delete_photo_id', String(photo.id));
    });

    wrap.appendChild(button);
    wrap.appendChild(remove);
    grid.appendChild(wrap);
  }
}
"""

diary_gallery_component = None
_diary_gallery_component_initialized = False


def _get_diary_gallery_component():
    """Register the diary gallery only when a diary/photo grid is actually shown."""
    global diary_gallery_component, _diary_gallery_component_initialized
    if _diary_gallery_component_initialized:
        return diary_gallery_component
    _diary_gallery_component_initialized = True
    try:
        diary_gallery_component = st.components.v2.component(
            "tokyo_burari_diary_gallery",
            html=_DIARY_GALLERY_HTML,
            css=_DIARY_GALLERY_CSS,
            js=_DIARY_GALLERY_JS,
        )
    except Exception:
        diary_gallery_component = None
    return diary_gallery_component


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



def browser_auto_login_token(family_key, member_key, credential_hash):
    """Return an opaque browser credential bound to one personal account in a family."""
    family_key = str(family_key or "").strip()
    member_key = str(member_key or "").strip()
    credential_hash = str(credential_hash or "").strip()
    if not family_key or not member_key or not credential_hash:
        return ""
    signature = hmac.new(
        credential_hash.encode("utf-8"),
        f"tokyo-burari-auto-login-v3|{family_key}|{member_key}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{family_key}|{member_key}|{signature}"

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
    # OpenAI is not needed to draw home/camera. Import only for an AI action.
    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


@st.cache_resource(show_spinner=False)
def supabase_client():
    # Supabase is imported on the first real database operation instead of every
    # process cold start. This matters most when an authenticated Streamlit session
    # can show Home/Camera without touching the database.
    if not (SUPABASE_URL and SUPABASE_SECRET_KEY):
        return None
    try:
        from supabase import create_client as _create_client
    except Exception as exc:
        raise RuntimeError("Supabase ライブラリがありません。requirements.txt を確認してください。") from exc
    return _create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def now_jst():
    return datetime.now(ZoneInfo(APP_TIMEZONE))


def today_iso():
    return now_jst().date().isoformat()



@st.cache_data(ttl=1800, show_spinner=False)
def _verify_remote_schema_cached():
    """Cold-start schema probe only; repeated Streamlit reruns reuse the result."""
    client = supabase_client()
    # Two probes are enough to confirm the v44 personal-account migration. Avoid
    # touching every table on cold start; real page queries will surface any later
    # table-specific problem only when that page is actually opened.
    client.table(MEMBER_TABLE).select("family_key,member_key").limit(1).execute()
    client.table(TRIP_TABLE).select("id,family_key,member_key").limit(1).execute()
    return True


def verify_setup():
    """Fast startup validation. Remote schema is verified lazily by the first DB action."""
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY が設定されていません。Streamlit Secrets を確認してください。")
        st.stop()
    if not (SUPABASE_URL and SUPABASE_SECRET_KEY):
        st.error("SUPABASE_URL と SUPABASE_SECRET_KEY が設定されていません。")
        st.stop()

def _family_pin_hash(pin, salt):
    pin = str(pin or "")
    salt = str(salt or "")
    if not pin or not salt:
        return ""
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()


def _normalize_family_key(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if len(value) > 32:
        raise ValueError("家族IDは32文字以内にしてください。")
    if not all(ch.isalnum() or ch in {"-", "_"} for ch in value):
        raise ValueError("家族IDは文字・数字・ハイフン・アンダーバーで入力してください。")
    return value


def get_family_account(family_key):
    family_key = str(family_key or "").strip()
    if not family_key:
        return None
    result = (
        supabase_client()
        .table(FAMILY_TABLE)
        .select("*")
        .eq("family_key", family_key)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def list_family_accounts():
    result = (
        supabase_client()
        .table(FAMILY_TABLE)
        .select("family_key,display_name,created_at")
        .order("created_at")
        .execute()
    )
    return result.data or []



def create_family_account(family_key, display_name, member_key, member_name, pin):
    family_key = _normalize_family_key(family_key)
    display_name = str(display_name or "").strip()
    if not family_key:
        raise ValueError("家族IDを入力してください。")
    if not display_name:
        raise ValueError("家族名を入力してください。")
    if len(display_name) > 40:
        raise ValueError("家族名は40文字以内にしてください。")
    if get_family_account(family_key):
        raise ValueError("その家族IDはすでに使われています。")

    client = supabase_client()
    family_payload = {
        "family_key": family_key,
        "display_name": display_name,
        # v44以降、ログイン資格情報は個人アカウント側に置きます。
        "pin_salt": "",
        "pin_hash": "",
        "created_at": now_jst().isoformat(),
        "updated_at": now_jst().isoformat(),
    }
    client.table(FAMILY_TABLE).insert(family_payload).execute()
    try:
        member = create_member_account(member_key, member_name, pin, family_key=family_key)
    except Exception:
        # 個人アカウントが作れなければ、ログイン不能な空家族を残さない。
        try:
            client.table(FAMILY_TABLE).delete().eq("family_key", family_key).execute()
        except Exception:
            pass
        raise
    family_payload["first_member"] = member
    return family_payload


def update_current_family_name(display_name):
    display_name = str(display_name or "").strip()
    if not display_name:
        raise ValueError("家族名を入力してください。")
    if len(display_name) > 40:
        raise ValueError("家族名は40文字以内にしてください。")
    supabase_client().table(FAMILY_TABLE).update(
        {"display_name": display_name, "updated_at": now_jst().isoformat()}
    ).eq("family_key", current_family_key()).execute()
    st.session_state["_current_family_name"] = display_name
    return display_name


@st.cache_data(ttl=1800, show_spinner=False)
def ensure_default_family_account():
    """Ensure the original/default family container exists, at most once per cache TTL."""
    account = get_family_account("default")
    if account:
        return
    supabase_client().table(FAMILY_TABLE).insert(
        {
            "family_key": "default",
            "display_name": "家族1",
            "pin_salt": "",
            "pin_hash": "",
            "created_at": now_jst().isoformat(),
            "updated_at": now_jst().isoformat(),
        }
    ).execute()


def _normalize_member_key(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if len(value) > 32:
        raise ValueError("個人IDは32文字以内にしてください。")
    if not all(ch.isalnum() or ch in {"-", "_"} for ch in value):
        raise ValueError("個人IDは文字・数字・ハイフン・アンダーバーで入力してください。")
    return value


def get_member_account(family_key, member_key):
    family_key = str(family_key or "").strip()
    member_key = str(member_key or "").strip()
    if not family_key or not member_key:
        return None
    result = (
        supabase_client()
        .table(MEMBER_TABLE)
        .select("*")
        .eq("family_key", family_key)
        .eq("member_key", member_key)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def list_family_members(family_key=None):
    family_key = str(family_key or current_family_key()).strip()
    result = (
        supabase_client()
        .table(MEMBER_TABLE)
        .select("family_key,member_key,display_name,created_at")
        .eq("family_key", family_key)
        .order("created_at")
        .execute()
    )
    return result.data or []


def create_member_account(member_key, display_name, pin, family_key=None):
    family_key = _normalize_family_key(family_key or current_family_key())
    member_key = _normalize_member_key(member_key)
    display_name = str(display_name or "").strip()
    pin = str(pin or "").strip()
    if not family_key or not get_family_account(family_key):
        raise ValueError("家族アカウントが見つかりません。")
    if not member_key:
        raise ValueError("個人IDを入力してください。")
    if not display_name:
        raise ValueError("個人名を入力してください。")
    if len(display_name) > 40:
        raise ValueError("個人名は40文字以内にしてください。")
    if len(pin) < 4:
        raise ValueError("個人のあいことばは4文字以上にしてください。")
    if get_member_account(family_key, member_key):
        raise ValueError("その個人IDは、この家族ですでに使われています。")
    salt = uuid.uuid4().hex
    payload = {
        "family_key": family_key,
        "member_key": member_key,
        "display_name": display_name,
        "pin_salt": salt,
        "pin_hash": _family_pin_hash(pin, salt),
        "created_at": now_jst().isoformat(),
        "updated_at": now_jst().isoformat(),
    }
    supabase_client().table(MEMBER_TABLE).insert(payload).execute()
    return payload


def update_current_member_name(display_name):
    display_name = str(display_name or "").strip()
    if not display_name:
        raise ValueError("個人名を入力してください。")
    if len(display_name) > 40:
        raise ValueError("個人名は40文字以内にしてください。")
    (
        supabase_client()
        .table(MEMBER_TABLE)
        .update({"display_name": display_name, "updated_at": now_jst().isoformat()})
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .execute()
    )
    st.session_state["_current_member_name"] = display_name
    return display_name


def verify_current_member_pin(pin):
    """Check a candidate phrase without ever exposing the stored credential."""
    pin = str(pin or "").strip()
    if not pin:
        return False
    account = get_member_account(current_family_key(), current_member_key()) or {}
    salt = str(account.get("pin_salt") or "")
    expected = str(account.get("pin_hash") or "")
    actual = _family_pin_hash(pin, salt)
    return bool(expected and actual and hmac.compare_digest(actual, expected))


def update_current_member_pin(new_pin):
    """Replace the current personal account phrase and refresh this browser's auto-login token."""
    new_pin = str(new_pin or "").strip()
    if len(new_pin) < 4:
        raise ValueError("新しいあいことばは4文字以上にしてください。")
    if len(new_pin) > 64:
        raise ValueError("新しいあいことばは64文字以内にしてください。")

    family_key = current_family_key()
    member_key = current_member_key()
    if not get_member_account(family_key, member_key):
        raise ValueError("現在の個人アカウントが見つかりません。")

    salt = uuid.uuid4().hex
    pin_hash = _family_pin_hash(new_pin, salt)
    (
        supabase_client()
        .table(MEMBER_TABLE)
        .update(
            {
                "pin_salt": salt,
                "pin_hash": pin_hash,
                "updated_at": now_jst().isoformat(),
            }
        )
        .eq("family_key", family_key)
        .eq("member_key", member_key)
        .execute()
    )

    # Tokens on other browsers were derived from the old hash and become invalid.
    # Keep this already-authenticated browser convenient by replacing only its token.
    token = browser_auto_login_token(family_key, member_key, pin_hash)
    if token:
        write_browser_auto_login(token, key="browser_auto_login_after_pin_change")
    return True


@st.cache_data(ttl=1800, show_spinner=False)
def ensure_default_member_account():
    """Ensure legacy data has a matching `main` personal account for first login."""
    existing = get_member_account("default", "main")
    if existing:
        # A cumulative migration run on a pre-v43 database may have created main
        # before the app could copy FAMILY_PIN. Fill only an empty credential.
        if FAMILY_PIN and not str(existing.get("pin_hash") or "").strip():
            salt = str(existing.get("pin_salt") or "").strip() or uuid.uuid4().hex
            supabase_client().table(MEMBER_TABLE).update(
                {
                    "pin_salt": salt,
                    "pin_hash": _family_pin_hash(FAMILY_PIN, salt),
                    "updated_at": now_jst().isoformat(),
                }
            ).eq("family_key", "default").eq("member_key", "main").execute()
        return
    family = get_family_account("default") or {}
    # Prefer the old family credential if v43 had already populated it; otherwise
    # use the original FAMILY_PIN secret. This keeps existing users able to enter.
    legacy_salt = str(family.get("pin_salt") or "").strip()
    legacy_hash = str(family.get("pin_hash") or "").strip()
    if legacy_salt and legacy_hash:
        salt = legacy_salt
        pin_hash = legacy_hash
    elif FAMILY_PIN:
        salt = uuid.uuid4().hex
        pin_hash = _family_pin_hash(FAMILY_PIN, salt)
    else:
        salt = ""
        pin_hash = ""
    supabase_client().table(MEMBER_TABLE).insert(
        {
            "family_key": "default",
            "member_key": "main",
            "display_name": "メイン",
            "pin_salt": salt,
            "pin_hash": pin_hash,
            "created_at": now_jst().isoformat(),
            "updated_at": now_jst().isoformat(),
        }
    ).execute()



def current_family_key():
    return str(st.session_state.get("_current_family_key") or "default").strip() or "default"


def current_family_name():
    cached = str(st.session_state.get("_current_family_name") or "").strip()
    if cached:
        return cached
    try:
        account = get_family_account(current_family_key()) or {}
        name = str(account.get("display_name") or current_family_key()).strip()
    except Exception:
        name = current_family_key()
    st.session_state["_current_family_name"] = name
    return name


def current_member_key():
    return str(st.session_state.get("_current_member_key") or "main").strip() or "main"


def current_member_name():
    cached = str(st.session_state.get("_current_member_name") or "").strip()
    if cached:
        return cached
    try:
        account = get_member_account(current_family_key(), current_member_key()) or {}
        name = str(account.get("display_name") or current_member_key()).strip()
    except Exception:
        name = current_member_key()
    st.session_state["_current_member_name"] = name
    return name


# ============================================================
# Lightweight per-session DB cache
# ============================================================
def _session_cache_get(key, max_age_seconds=12):
    entry = st.session_state.get(key)
    if not isinstance(entry, dict):
        return None
    try:
        age = time.time() - float(entry.get("at") or 0.0)
    except Exception:
        return None
    if age < 0 or age > float(max_age_seconds):
        return None
    return entry.get("value")


def _session_cache_set(key, value):
    st.session_state[key] = {"at": time.time(), "value": value}
    return value


def _account_cache_key(name, *parts):
    suffix = "|".join(str(x) for x in parts)
    return f"_fastdb|{current_family_key()}|{current_member_key()}|{name}|{suffix}"


def _invalidate_fast_db_cache():
    """Clear only small account-scoped DB snapshots after a write."""
    for key in list(st.session_state.keys()):
        if str(key).startswith("_fastdb|"):
            st.session_state.pop(key, None)


def _set_authenticated_family(family_account, member_account, persist=False):
    family_account = family_account or {}
    member_account = member_account or {}
    family_key = str(family_account.get("family_key") or member_account.get("family_key") or "default")
    st.session_state["_family_authenticated"] = True
    st.session_state["_current_family_key"] = family_key
    family_name = str(family_account.get("display_name") or "").strip()
    if family_name:
        st.session_state["_current_family_name"] = family_name
    else:
        # Family display name is cosmetic. Load it lazily only on screens that show it.
        st.session_state.pop("_current_family_name", None)
    st.session_state["_current_member_key"] = str(member_account.get("member_key") or "main")
    st.session_state["_current_member_name"] = str(member_account.get("display_name") or member_account.get("member_key") or "個人")
    st.session_state["_family_pin_failures"] = 0
    st.session_state["_family_pin_locked_until"] = 0.0
    if persist:
        st.session_state["_persist_auto_login_pending"] = True


def logout_family_account():
    clear_browser_auto_login("browser_auto_login_person_logout")
    keep = {
        "_suppress_auto_login_once": True,
        "_last_family_key": current_family_key(),
        "_last_member_key": current_member_key(),
    }
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    st.session_state.update(keep)
    st.session_state["_family_authenticated"] = False


def require_family_pin():
    """Login to an independent personal account nested under a family account."""
    if (
        st.session_state.get("_family_authenticated", False)
        and st.session_state.get("_current_family_key")
        and st.session_state.get("_current_member_key")
    ):
        if st.session_state.pop("_persist_auto_login_pending", False):
            member = get_member_account(current_family_key(), current_member_key()) or {}
            token = browser_auto_login_token(
                current_family_key(), current_member_key(), member.get("pin_hash")
            )
            write_browser_auto_login(token)
        return

    suppress_auto = bool(st.session_state.pop("_suppress_auto_login_once", False))
    browser_state = None if suppress_auto else read_browser_persistence("browser_auto_login_gate")
    if isinstance(browser_state, dict):
        stored_token = str(browser_state.get("auth_token") or "")
        parts = stored_token.split("|")
        if len(parts) == 3:
            family_key, member_key, _ = parts
            try:
                # The personal account is sufficient to validate the credential.
                # Family display metadata is fetched lazily later only if a page shows it.
                member = get_member_account(family_key, member_key)
            except Exception:
                member = None
            if member:
                expected = browser_auto_login_token(
                    family_key, member_key, member.get("pin_hash")
                )
                if expected and hmac.compare_digest(stored_token, expected):
                    _set_authenticated_family({"family_key": family_key}, member, persist=False)
                    st.session_state["_browser_last_camera_open_at"] = browser_state.get("last_camera_open_at") or 0
                    st.rerun()

    # Legacy no-PIN installation: only probe the legacy account when the app truly
    # has no FAMILY_PIN. Normal PIN installations skip these four network requests.
    if not FAMILY_PIN:
        try:
            default_family = get_family_account("default") or {}
            default_member = get_member_account("default", "main") or {}
        except Exception:
            default_family = {}
            default_member = {}
        if default_family and default_member and not str(default_member.get("pin_hash") or "").strip():
            families = list_family_accounts()
            members = list_family_members("default")
            if len(families) == 1 and len(members) == 1:
                _set_authenticated_family(default_family, default_member, persist=False)
                return

    st.title("📷 東京ぶらり旅プロジェクト")
    st.caption("家族アカウントの中の、個人アカウントでログインしてください。")

    failures = int(st.session_state.get("_family_pin_failures", 0))
    locked_until = float(st.session_state.get("_family_pin_locked_until", 0.0))
    now = time.time()
    if locked_until > now:
        st.warning(f"入力回数が多いため、あと{max(1, int(locked_until - now))}秒ほど待ってください。")
        st.stop()

    family_key = st.text_input(
        "家族ID",
        value=str(st.session_state.get("_last_family_key") or "default"),
        max_chars=32,
        key="_family_account_input",
        autocomplete="organization",
    )
    member_key = st.text_input(
        "個人ID",
        value=str(st.session_state.get("_last_member_key") or "main"),
        max_chars=32,
        key="_member_account_input",
        autocomplete="username",
    )
    entered = st.text_input(
        "個人のあいことば",
        type="password",
        max_chars=64,
        key="_family_pin_input",
        autocomplete="current-password",
    )
    if st.button("はいる", type="primary", use_container_width=True):
        try:
            normalized_family = _normalize_family_key(family_key)
            normalized_member = _normalize_member_key(member_key)
            st.session_state["_last_family_key"] = normalized_family
            st.session_state["_last_member_key"] = normalized_member
            member = get_member_account(normalized_family, normalized_member)
            family = {"family_key": normalized_family} if member else None
            if normalized_family == "default" and normalized_member == "main" and not member:
                # Bootstrap only on the rare first login to a brand-new/legacy install,
                # instead of paying these checks on every normal app load.
                ensure_default_family_account()
                ensure_default_member_account()
                member = get_member_account(normalized_family, normalized_member)
                family = {"family_key": normalized_family} if member else None
        except Exception:
            family = None
            member = None

        valid = False
        if member:
            expected = str(member.get("pin_hash") or "")
            if expected:
                salt = str(member.get("pin_salt") or "")
                actual = _family_pin_hash(entered.strip(), salt) if entered else ""
                valid = bool(actual and hmac.compare_digest(actual, expected))
            else:
                valid = not entered

        if valid:
            _set_authenticated_family(family, member, persist=True)
            # Never reopen another person's recent camera session after switching accounts.
            st.session_state["_browser_last_camera_open_at"] = 0
            st.rerun()

        failures += 1
        if failures >= 5:
            st.session_state["_family_pin_failures"] = 0
            st.session_state["_family_pin_locked_until"] = time.time() + 60
            st.error("入力回数が多いため、1分ほど待ってからもう一度試してください。")
        else:
            st.session_state["_family_pin_failures"] = failures
            st.error("家族ID・個人ID・あいことばのいずれかが違います。")
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


def ask_json_with_images(prompt, image_items, name, schema, max_output_tokens=1000):
    """Ask the vision model with several labeled images in one request."""
    content = [{"type": "input_text", "text": prompt}]
    for label, image_bytes in image_items or []:
        label = str(label or "").strip()
        if label:
            content.append({"type": "input_text", "text": label})
        if image_bytes:
            content.append({"type": "input_image", "image_url": image_data_url(image_bytes)})
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
    component = _get_far_field_mic_component()
    if component is None:
        return st.audio_input(label, sample_rate=16000, key=f"{key}_fallback")

    result = component(
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


def unique_auto_diary_title(base_title, exclude_trip_id=None):
    """Add 2, 3, ... inside the parentheses when an automatic diary title is already used."""
    base_title = str(base_title or "").strip()
    if not (base_title.startswith("ぶらり旅（") and base_title.endswith("）")):
        return base_title

    try:
        rows = (
            supabase_client()
            .table(DIARY_TABLE)
            .select("trip_id,title")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        ).data or []
    except Exception:
        # Title de-duplication must never prevent the diary itself from being shown/saved.
        return base_title

    used_titles = {
        str(row.get("title") or "").strip()
        for row in rows
        if str(row.get("trip_id") or "") != str(exclude_trip_id or "")
        and str(row.get("title") or "").strip()
    }
    if base_title not in used_titles:
        return base_title

    stem = base_title[:-1]
    suffix = 2
    while f"{stem}{suffix}）" in used_titles:
        suffix += 1
    return f"{stem}{suffix}）"


def diary_display_title(diary, trip, photos=None):
    """Prefer the latest saved/custom title; unsaved automatic titles are numbered."""
    trip_id = str((trip or {}).get("id") or (diary or {}).get("trip_id") or "") or None
    if trip_id:
        # After a title edit, keep every part of the current Streamlit rerun on the
        # exact same value while Supabase-backed widgets are reconstructed.
        override = str(st.session_state.get(f"_diary_title_override_{trip_id}") or "").strip()
        if override:
            return override

    saved = str((diary or {}).get("title") or "").strip()
    if saved:
        return saved
    base_title = diary_title_for_trip(trip, photos=photos)
    return unique_auto_diary_title(base_title, exclude_trip_id=trip_id)


def update_diary_title(trip_id, title):
    """Persist a manual title and verify it before updating the UI."""
    value = str(title or "").strip()
    if not value:
        raise ValueError("タイトルを入力してください。")

    client = supabase_client()
    client.table(DIARY_TABLE).update(
        {"title": value, "updated_at": now_jst().isoformat()}
    ).eq("trip_id", trip_id).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()

    # Supabase update() can complete without raising even if no row matched. Read it
    # back so the user never sees a success message when the title was not stored.
    check = (
        client
        .table(DIARY_TABLE)
        .select("trip_id,title")
        .eq("trip_id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    row = (check.data or [None])[0]
    stored = str((row or {}).get("title") or "").strip()
    if stored != value:
        raise ValueError("タイトルの保存を確認できませんでした。")

    st.session_state[f"_diary_title_override_{trip_id}"] = stored
    st.session_state["_diary_selector_serial"] = int(
        st.session_state.get("_diary_selector_serial") or 0
    ) + 1
    _invalidate_fast_db_cache()
    return stored


def normalize_duplicate_saved_diary_titles():
    """Repair old duplicate automatic titles once per app session.

    v34 prevents new automatic duplicates, but diaries saved by older versions can
    already contain the same automatic title. Keep the oldest one unchanged and
    rename later duplicates as ぶらり旅（場所2）, ぶらり旅（場所3）, ... .
    Manual/custom titles outside the automatic ぶらり旅（...） form are untouched.
    """
    guard_key = f"_duplicate_saved_titles_checked_{current_family_key()}_{current_member_key()}"
    if st.session_state.get(guard_key, False):
        return
    st.session_state[guard_key] = True

    client = supabase_client()
    try:
        rows = (
            client
            .table(DIARY_TABLE)
            .select("id,trip_id,title,created_at")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .order("created_at")
            .execute()
        ).data or []
    except Exception:
        return

    used_titles = {
        str(row.get("title") or "").strip()
        for row in rows
        if str(row.get("title") or "").strip()
    }
    seen = set()
    changed = False

    for row in rows:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        if title not in seen:
            seen.add(title)
            continue
        if not (title.startswith("ぶらり旅（") and title.endswith("）")):
            continue

        stem = title[:-1]
        suffix = 2
        candidate = f"{stem}{suffix}）"
        while candidate in used_titles:
            suffix += 1
            candidate = f"{stem}{suffix}）"

        client.table(DIARY_TABLE).update(
            {"title": candidate, "updated_at": now_jst().isoformat()}
        ).eq("id", row.get("id")).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
        used_titles.add(candidate)
        seen.add(candidate)
        changed = True

    if changed:
        st.session_state["_diary_selector_serial"] = int(
            st.session_state.get("_diary_selector_serial") or 0
        ) + 1


# ============================================================
# Image helpers
# ============================================================
def normalize_photo(raw_bytes, max_side=1600, quality=84):
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(raw_bytes)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((max_side, max_side))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()


@st.cache_data(ttl=1800, max_entries=96, show_spinner=False)
def download_photo(storage_path):
    return supabase_client().storage.from_(PHOTO_BUCKET).download(storage_path)


@st.cache_data(ttl=1800, max_entries=192, show_spinner=False)
def thumbnail_photo_bytes(storage_path, max_px=420, quality=76):
    """Small immutable preview bytes for grids; avoids resending full photos on reruns."""
    image_bytes = download_photo(storage_path)
    try:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((int(max_px), int(max_px)))
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=int(quality), optimize=True)
            return out.getvalue()
    except Exception:
        return image_bytes


@st.cache_data(ttl=1800, max_entries=192, show_spinner=False)
def thumbnail_photo_data_url(storage_path, max_px=420, quality=76):
    return image_data_url(thumbnail_photo_bytes(storage_path, max_px=max_px, quality=quality))


def _signed_url_from_value(value):
    """Extract a Storage signed URL from supabase-py response variants."""
    if isinstance(value, str):
        url = value.strip()
    elif isinstance(value, dict):
        url = ""
        for key in ("signedURL", "signedUrl", "signed_url", "url"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                url = candidate.strip()
                break
        if not url and isinstance(value.get("data"), dict):
            return _signed_url_from_value(value.get("data"))
    else:
        url = ""
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/storage/v1/"):
        return SUPABASE_URL.rstrip("/") + url
    if url.startswith("/object/"):
        return SUPABASE_URL.rstrip("/") + "/storage/v1" + url
    return url


@st.cache_data(ttl=540, max_entries=128, show_spinner=False)
def signed_photo_url_map(storage_paths, expires_in=900):
    """Create short-lived private image URLs in one Storage request when possible.

    The browser can then fetch visible images in parallel and lazily instead of the
    Streamlit server downloading, resizing and base64-encoding every gallery image
    before the page is allowed to render.
    """
    paths = tuple(dict.fromkeys(str(x or "").strip() for x in (storage_paths or ()) if str(x or "").strip()))
    if not paths:
        return {}
    bucket = supabase_client().storage.from_(PHOTO_BUCKET)
    result = {}
    try:
        if hasattr(bucket, "create_signed_urls"):
            response = bucket.create_signed_urls(list(paths), int(expires_in))
            rows = response
            if isinstance(response, dict):
                rows = response.get("data") or response.get("signedURLs") or response.get("signed_urls") or []
            elif hasattr(response, "data"):
                rows = getattr(response, "data") or []
            if isinstance(rows, list):
                for idx, row in enumerate(rows):
                    path = ""
                    if isinstance(row, dict):
                        path = str(row.get("path") or row.get("name") or "").strip()
                    if not path and idx < len(paths):
                        path = paths[idx]
                    url = _signed_url_from_value(row)
                    if path and url:
                        result[path] = url
    except Exception:
        result = {}

    # Fallback for SDKs without batch signing. Missing items only are signed one by
    # one; if signing itself is unavailable callers fall back to cached thumbnails.
    for path in paths:
        if path in result:
            continue
        try:
            response = bucket.create_signed_url(path, int(expires_in))
            url = _signed_url_from_value(response)
            if url:
                result[path] = url
        except Exception:
            pass
    return result


def photo_display_url(photo, signed_map=None, max_px=420, quality=76):
    path = str((photo or {}).get("storage_path") or "").strip()
    if not path:
        return ""
    if isinstance(signed_map, dict) and signed_map.get(path):
        return str(signed_map[path])
    try:
        single = signed_photo_url_map((path,))
        if single.get(path):
            return str(single[path])
    except Exception:
        pass
    try:
        return thumbnail_photo_data_url(path, max_px=max_px, quality=quality)
    except Exception:
        return ""


def upload_photo(trip_id, image_bytes, location=None, captured_at=None, capture_source="camera"):
    active_snapshot = get_active_trip_fast(max_age_seconds=20) if st.session_state.get("active_trip_id") else None
    if not active_snapshot or str(active_snapshot.get("id") or "") != str(trip_id):
        if not get_trip(trip_id):
            raise ValueError("現在の個人アカウントのぶらり旅が見つかりません。")
    # Keep Storage upload as a raw binary body. In particular, do not send an
    # x-upsert header for new files.
    compressed = normalize_photo(image_bytes)
    if not compressed:
        raise ValueError("写真データが空です。")

    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    path = f"{current_family_key()}/{current_member_key()}/{trip_id}/{stamp}_{uuid.uuid4().hex[:8]}.jpg"
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
                    "family_key": current_family_key(),
                    "member_key": current_member_key(),
                    "storage_path": path,
                    "captured_at": str(captured_at or now_jst().isoformat()),
                    "reflection_json": reflection,
                    "signals_json": {},
                }
            )
            .execute()
        )
        download_photo.clear()
        _invalidate_fast_db_cache()
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
                "family_key": current_family_key(),
                "member_key": current_member_key(),
                "trip_date": today_iso(),
                "destination": str(destination or "").strip(),
                "status": "active",
                "started_at": now_jst().isoformat(),
            }
        )
        .execute()
    )
    created = (result.data or [None])[0]
    _invalidate_fast_db_cache()
    return created


def get_latest_active_trip():
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )

    try:
        photos = (
            client
            .table(PHOTO_TABLE)
            .select("id,reflection_json")
            .eq("trip_id", trip_id)
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
                    "gps_error_code": location.get("gps_error_code") if isinstance(location, dict) else "",
                }
                if destination
                else {
                    "source": "unavailable",
                    "place_label": "",
                    "gps_error_code": location.get("gps_error_code") if isinstance(location, dict) else "",
                }
            )
            (
                client
                .table(PHOTO_TABLE)
                .update({"reflection_json": reflection})
                .eq("id", photo["id"])
                .eq("family_key", current_family_key()).eq("member_key", current_member_key())
                .execute()
            )
    except Exception:
        pass
    updated = (result.data or [None])[0]
    if st.session_state.get("active_trip_id") == trip_id:
        snapshot = get_active_trip_fast(max_age_seconds=20) or {}
        snapshot = dict(snapshot)
        snapshot["destination"] = destination
        _cache_active_trip_snapshot(snapshot)
    _invalidate_fast_db_cache()
    return updated


def get_trip(trip_id):
    if not trip_id:
        return None
    cache_key = _account_cache_key("trip", trip_id)
    cached = _session_cache_get(cache_key, max_age_seconds=20)
    if cached is not None:
        return cached
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    return _session_cache_set(cache_key, (result.data or [None])[0])


def finish_trip(trip_id):
    (
        supabase_client()
        .table(TRIP_TABLE)
        .update({"status": "ready_for_diary", "ended_at": now_jst().isoformat()})
        .eq("id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    if st.session_state.get("active_trip_id") == trip_id:
        st.session_state.active_trip_id = None
        _invalidate_active_trip_snapshot()
    _invalidate_fast_db_cache()


def list_trip_photos(trip_id):
    if not trip_id:
        return []
    cache_key = _account_cache_key("trip_photos", trip_id)
    cached = _session_cache_get(cache_key, max_age_seconds=12)
    if cached is not None:
        return cached
    result = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("trip_id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .order("captured_at")
        .execute()
    )
    return _session_cache_set(cache_key, result.data or [])


def update_photo_reflection(photo_id, conversation, signals, done=None):
    client = supabase_client()
    current = (
        client
        .table(PHOTO_TABLE)
        .select("reflection_json")
        .eq("id", photo_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
        .update({"reflection_json": reflection, "signals_json": signals or {}})
        .eq("id", photo_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    _invalidate_fast_db_cache()


def list_recent_trips_for_diary(limit=40):
    result = (
        supabase_client()
        .table(TRIP_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("status", ["ready_for_diary", "diary_done"])
        .order("trip_date", desc=True)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def get_diary_for_trip(trip_id):
    if not trip_id:
        return None
    result = (
        supabase_client()
        .table(DIARY_TABLE)
        .select("*")
        .eq("trip_id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def diaries_for_trip_ids(trip_ids):
    """Fetch many diaries in one request instead of one request per trip."""
    ids = list(dict.fromkeys(str(x) for x in (trip_ids or []) if x))
    if not ids:
        return {}
    rows = (
        supabase_client()
        .table(DIARY_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("trip_id", ids)
        .execute()
    ).data or []
    return {str(row.get("trip_id")): row for row in rows if row.get("trip_id")}


def photos_for_trip_ids(trip_ids):
    """Fetch many trips' photo metadata in one request and group it locally."""
    ids = list(dict.fromkeys(str(x) for x in (trip_ids or []) if x))
    grouped = {trip_id: [] for trip_id in ids}
    if not ids:
        return grouped
    rows = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("trip_id", ids)
        .order("captured_at")
        .execute()
    ).data or []
    for row in rows:
        trip_id = str(row.get("trip_id") or "")
        if trip_id in grouped:
            grouped[trip_id].append(row)
    return grouped


def save_diary(trip_id, title, diary_text, raw_conversation, ai_meta):
    existing = get_diary_for_trip(trip_id)
    trip = get_trip(trip_id)
    if not trip:
        raise ValueError("現在の個人アカウントのぶらり旅が見つかりません。")
    existing_title = str((existing or {}).get("title") or "").strip()
    requested_title = str(title or "").strip()
    if existing_title:
        fixed_title = existing_title
    else:
        auto_title = requested_title or diary_title_for_trip(trip)
        fixed_title = unique_auto_diary_title(auto_title, exclude_trip_id=trip_id)

    incoming_meta = dict(ai_meta or {}) if isinstance(ai_meta or {}, dict) else {}
    existing_meta = (existing or {}).get("ai_meta") or {}
    if not isinstance(existing_meta, dict):
        existing_meta = {}
    if existing_meta.get("summary_feedback_history") and not incoming_meta.get("summary_feedback_history"):
        incoming_meta["summary_feedback_history"] = list(existing_meta.get("summary_feedback_history") or [])

    payload = {
        "trip_id": trip_id,
        "family_key": current_family_key(),
        "member_key": current_member_key(),
        "title": fixed_title,
        "diary_text": str(diary_text or "").strip(),
        "raw_conversation": raw_conversation,
        "ai_meta": incoming_meta,
        "updated_at": now_jst().isoformat(),
    }
    if existing:
        (
            supabase_client()
            .table(DIARY_TABLE)
            .update(payload)
            .eq("id", existing["id"])
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        )
    else:
        payload["created_at"] = now_jst().isoformat()
        supabase_client().table(DIARY_TABLE).insert(payload).execute()
    (
        supabase_client()
        .table(TRIP_TABLE)
        .update({"status": "diary_done", "ended_at": trip.get("ended_at") or now_jst().isoformat()})
        .eq("id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    _invalidate_fast_db_cache()
    return get_diary_for_trip(trip_id)


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
    client.table(PHOTO_TABLE).delete().eq("trip_id", trip_id).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
    client.table(DIARY_TABLE).delete().eq("trip_id", trip_id).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
    # Once its diary/photos are gone, remove the trip container as well so the
    # deleted day cannot reappear as an empty trip in diary/monthly screens.
    client.table(TRIP_TABLE).delete().eq("id", trip_id).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()

    # A saved monthly review can contain wording derived from the deleted diary.
    # Remove that month's snapshot so it cannot continue showing deleted material.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
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
        _invalidate_active_trip_snapshot()
    download_photo.clear()
    thumbnail_photo_bytes.clear()
    thumbnail_photo_data_url.clear()
    signed_photo_url_map.clear()
    _invalidate_fast_db_cache()

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



def delete_photo_and_related_data(
    trip_id,
    photo_id,
    known_photos=None,
    known_trip=None,
    skip_existing_diary_lookup=False,
):
    """Delete one photo; if it was the last image, remove the empty diary/trip too.

    Pending-diary grids already know the trip/photo metadata and know that no saved
    diary exists. Reusing that information avoids several Supabase round-trips.
    """
    client = supabase_client()
    trip = dict(known_trip) if isinstance(known_trip, dict) else (get_trip(trip_id) or {})
    photos = list(known_photos) if isinstance(known_photos, (list, tuple)) else list_trip_photos(trip_id)
    photo = next((p for p in photos if p.get("id") == photo_id), None)
    if not photo:
        raise ValueError("削除する画像が見つかりませんでした。")

    storage_path = str(photo.get("storage_path") or "").strip()
    if storage_path:
        client.storage.from_(PHOTO_BUCKET).remove([storage_path])

    client.table(PHOTO_TABLE).delete().eq("id", photo_id).eq("trip_id", trip_id).eq(
        "family_key", current_family_key()
    ).eq("member_key", current_member_key()).execute()

    # We already have the gallery's photo metadata, so normal deletions need no
    # second photo-list query. Only when it looks like the last image was removed do
    # one tiny verification query, protecting against another device adding a photo
    # at the same moment.
    remaining_photos = [p for p in photos if p.get("id") != photo_id]
    if not remaining_photos:
        remaining_photos = (
            client
            .table(PHOTO_TABLE)
            .select("id,trip_id,storage_path,captured_at,reflection_json,signals_json")
            .eq("trip_id", trip_id)
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .order("captured_at")
            .execute()
        ).data or []
    existing = None if skip_existing_diary_lookup else get_diary_for_trip(trip_id)
    diary_deleted = not remaining_photos

    if diary_deleted:
        # An image-less record has no source material in this app. Pending trips have
        # no diary row, so skip that unnecessary delete request in the fast path.
        if not skip_existing_diary_lookup:
            client.table(DIARY_TABLE).delete().eq("trip_id", trip_id).eq(
                "family_key", current_family_key()
            ).eq("member_key", current_member_key()).execute()
        client.table(TRIP_TABLE).delete().eq("id", trip_id).eq(
            "family_key", current_family_key()
        ).eq("member_key", current_member_key()).execute()
    elif existing:
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

        merged_signals = {}
        for remaining in remaining_photos:
            merged_signals = merge_signals(merged_signals, remaining.get("signals_json") or {})
        ai_meta["signals"] = merged_signals
        ai_meta["reflection_summary"] = ""
        ai_meta["trip_summary"] = ""
        _clear_summary_feedback_fields(ai_meta, clear_history=True)

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
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        )

    # A monthly summary may contain content from the removed image/comment.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key and not skip_existing_diary_lookup:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).eq(
            "family_key", current_family_key()
        ).eq("member_key", current_member_key()).execute()
        for key in (
            f"monthly_review_{month_key}",
            f"monthly_audio_{month_key}",
            f"monthly_audio_pending_{month_key}",
        ):
            st.session_state.pop(key, None)

    state_key = f"reflection_state_{trip_id}"
    state = st.session_state.get(state_key)
    if diary_deleted:
        st.session_state.pop(state_key, None)
    elif isinstance(state, dict):
        old_ids = list(state.get("photo_ids") or [])
        old_index = int(state.get("photo_index") or 0)
        if photo_id in old_ids:
            deleted_index = old_ids.index(photo_id)
            new_ids = [pid for pid in old_ids if pid != photo_id]
            state["photo_ids"] = new_ids
            items = state.get("items") or {}
            if isinstance(items, dict):
                items.pop(photo_id, None)
            if deleted_index < old_index:
                state["photo_index"] = max(0, old_index - 1)
            elif deleted_index == old_index:
                state["photo_index"] = min(old_index, len(new_ids) - 1)
            else:
                state["photo_index"] = min(old_index, len(new_ids) - 1)
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

    remaining_ids = [p.get("id") for p in remaining_photos if p.get("id")]
    selected_key = f"diary_selected_photo_{trip_id}"
    if remaining_ids:
        if st.session_state.get(selected_key) == photo_id:
            st.session_state[selected_key] = remaining_ids[0]
    else:
        st.session_state.pop(selected_key, None)

    st.session_state.pop(f"delete_photo_selector_{trip_id}", None)
    if st.session_state.get(f"diary_talk_photo_{trip_id}") == photo_id or diary_deleted:
        st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
    if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
        st.session_state.pop(state_key, None)

    if diary_deleted:
        st.session_state.pop(f"_diary_title_override_{trip_id}", None)
        if st.session_state.get("history_detail_trip_id") == trip_id:
            st.session_state.pop("history_detail_trip_id", None)
        if str(st.session_state.get("preferred_diary_trip_id") or "") == str(trip_id):
            st.session_state.preferred_diary_trip_id = None
        if str(st.session_state.get("active_trip_id") or "") == str(trip_id):
            st.session_state.active_trip_id = None
            _invalidate_active_trip_snapshot()
        st.session_state["_diary_selector_serial"] = int(
            st.session_state.get("_diary_selector_serial") or 0
        ) + 1

    # Clear only image/data caches affected by this deletion. This also prevents a
    # just-deleted image from lingering visually in a cached thumbnail.
    download_photo.clear()
    thumbnail_photo_bytes.clear()
    thumbnail_photo_data_url.clear()
    signed_photo_url_map.clear()
    _invalidate_fast_db_cache()
    return {
        "month_key": month_key,
        "diary_deleted": diary_deleted,
        "remaining_photo_count": len(remaining_photos),
    }

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
        ai_meta["trip_summary"] = ""
        _clear_summary_feedback_fields(ai_meta, clear_history=True)

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
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        )

    # A saved monthly review may contain wording from this photo conversation.
    trip_date = str(trip.get("trip_date") or "")
    month_key = trip_date[:7] if len(trip_date) >= 7 else ""
    if month_key:
        first_day, _ = month_bounds(month_key)
        client.table(MONTHLY_TABLE).delete().eq("review_month", first_day).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
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
def confirm_photo_delete_dialog(trip_id, photo_id, photos=None, is_pending=False, trip=None):
    photos = list(photos) if isinstance(photos, (list, tuple)) else list_trip_photos(trip_id)
    photo_ids = [p.get("id") for p in photos]
    if photo_id not in photo_ids:
        st.warning("この画像はすでに削除されています。")
        if st.button("閉じる", use_container_width=True, key=f"dialog_photo_missing_{trip_id}"):
            st.rerun(scope="app")
        return

    photo_number = photo_ids.index(photo_id) + 1
    st.write(f"**写真 {photo_number} / {len(photo_ids)}** を削除します。")
    if len(photo_ids) == 1:
        if is_pending:
            st.warning(
                "この画像は、まだ日記になっていないこのぶらり旅の最後の1枚です。"
                "削除すると写真が0枚になるため、この未日記の記録も自動的に削除します。"
            )
        else:
            st.warning(
                "この画像はこの日記の最後の1枚です。画像とコメントを削除すると、"
                "画像が0枚になるため、この日記も自動的に削除します。"
            )
    else:
        if is_pending:
            st.warning("この画像と、この画像について話したコメントを削除します。")
        else:
            st.warning(
                "この画像と、この画像について話したコメントを削除します。"
                "保存済みの日記本文そのものは残ります。"
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
                result = delete_photo_and_related_data(
                    trip_id,
                    photo_id,
                    known_photos=photos,
                    known_trip=trip,
                    skip_existing_diary_lookup=bool(is_pending),
                )
                if result.get("diary_deleted"):
                    if is_pending:
                        st.session_state["_diary_notice"] = "最後の画像を削除したため、この未日記のぶらり旅も削除しました。"
                    else:
                        st.session_state["_diary_notice"] = "最後の画像を削除したため、この日記も自動的に削除しました。"
                else:
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
            confirm_photo_delete_dialog(trip_id, selected_photo_id, photos=photos)

    if st.button(
        "🗑 この日記を削除",
        use_container_width=True,
        key=f"diary_page_delete_{trip_id}",
    ):
        confirm_diary_delete_dialog(trip_id, len(photos))


def _list_recent_diaries_uncached(limit=60):
    """Load diaries and their trip metadata in one PostgREST request when available."""
    client = supabase_client()
    try:
        relation = TRIP_TABLE
        rows = (
            client
            .table(DIARY_TABLE)
            .select(f"*,{relation}(*)")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        bundled = []
        for diary in rows:
            trip = diary.pop(relation, None) if isinstance(diary, dict) else None
            if isinstance(trip, list):
                trip = trip[0] if trip else None
            if isinstance(trip, dict) and trip.get("id"):
                bundled.append({"diary": diary, "trip": trip})
        if bundled or not rows:
            return bundled
    except Exception:
        pass

    # Compatibility fallback for PostgREST schemas where relationship embedding is
    # not exposed yet. Still batched: two requests total, never N+1.
    result = (
        client
        .table(DIARY_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    diaries = result.data or []
    if not diaries:
        return []
    trip_ids = list({d["trip_id"] for d in diaries if d.get("trip_id")})
    trip_result = (
        client
        .table(TRIP_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("id", trip_ids)
        .execute()
    )
    trip_map = {t["id"]: t for t in (trip_result.data or [])}
    return [
        {"diary": d, "trip": trip_map.get(d["trip_id"], {})}
        for d in diaries
        if d.get("trip_id") in trip_map
    ]


def list_recent_diaries(limit=60):
    cache_key = _account_cache_key("recent_diaries", int(limit))
    cached = _session_cache_get(cache_key, max_age_seconds=15)
    if cached is not None:
        return cached
    return _session_cache_set(cache_key, _list_recent_diaries_uncached(limit=limit))


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
    client = supabase_client()
    try:
        rows = (
            client
            .table(TRIP_TABLE)
            .select(
                f"*,{DIARY_TABLE}(*),"
                f"{PHOTO_TABLE}(id,trip_id,captured_at,reflection_json,signals_json)"
            )
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .gte("trip_date", start)
            .lt("trip_date", end)
            .order("trip_date")
            .execute()
        ).data or []
        trips, diaries, photos = [], [], []
        for row in rows:
            if not isinstance(row, dict):
                continue
            trip = dict(row)
            embedded_diaries = trip.pop(DIARY_TABLE, []) or []
            embedded_photos = trip.pop(PHOTO_TABLE, []) or []
            if isinstance(embedded_diaries, dict):
                embedded_diaries = [embedded_diaries]
            if isinstance(embedded_photos, dict):
                embedded_photos = [embedded_photos]
            trips.append(trip)
            diaries.extend(x for x in embedded_diaries if isinstance(x, dict))
            photos.extend(x for x in embedded_photos if isinstance(x, dict))
        return {"trips": trips, "diaries": diaries, "photos": photos}
    except Exception:
        pass

    trips_result = (
        client
        .table(TRIP_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
        client
        .table(DIARY_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("trip_id", trip_ids)
        .execute()
    )
    photos_result = (
        client
        .table(PHOTO_TABLE)
        .select("id,trip_id,captured_at,reflection_json,signals_json")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .eq("review_month", first_day)
        .limit(1)
        .execute()
    )
    return (result.data or [None])[0]


def save_monthly_review(month_key, review_json):
    first_day, _ = month_bounds(month_key)
    existing = get_saved_monthly_review(month_key)
    payload = {
        "family_key": current_family_key(),
        "member_key": current_member_key(),
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
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
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
    total_photo_count = len(photo_states)
    commented_photo_count = sum(
        1
        for item in photo_states
        if any(
            isinstance(turn, dict)
            and turn.get("role") == "child"
            and str(turn.get("text") or "").strip()
            for turn in item.get("conversation", [])
        )
    )
    feedback_guidance = build_summary_feedback_guidance()
    prompt = f"""
5〜6歳の子どもが東京ぶらり旅のあとに話した内容から、本人の日記を作ります。
AIが新しい出来事や感情を足してはいけません。

日付: {trip.get('trip_date', '')}
行き先メモ: {destination or 'なし'}
保存されている写真: {total_photo_count}枚
本人のコメントがある写真: {commented_photo_count}枚
本人のコメントがない写真: {max(0, total_photo_count - commented_photo_count)}枚
子どもが写真を見ながら話した言葉:
{evidence}

{feedback_guidance}

ルール:
- diary は3〜7文程度。発言が少なければ無理に長くしない。
- 子どもの語彙や言い回しをできるだけ残し、読みやすい順番に整える。
- 「楽しかった」「不便だった」などを、本人が言っていないのに補わない。
- コメントがない写真について、写真の内容・出来事・感情を推測して文章を作らない。写真枚数そのものは事実として書いてよい。
- 本人のコメントが1つもない場合は、写真を残した事実と「コメントはまだない」ことだけを短く書く。
- 大人っぽい抽象語へ変換しすぎない。
- title はシステム側で「ぶらり旅（地名）」に固定するため、内容は diary に集中する。
- reflection_summary は保護者向けに、本人が入力・発話したコメントを第一の根拠として分析する。単なる発言の言い換えではなく、その日に何へ興味・注意が向いていたか、どのように比べたり理由を考えたりしていたかなど、コメントから自然に読み取れる部分だけを2〜4文程度で簡潔にまとめる。
- 疑問やWant（どうしたい・こうなってほしい等）は必須項目ではない。本人が明示していなくても、それまでの本人コメントの流れからかなり自然に推測できる場合は、「〜を気にしていたようです」「〜したい方向がうかがえます」のように推測だと分かる弱い表現で書いてよい。
- 疑問やWantをコメントから自然に読み取れない場合は、その項目自体に触れない。「疑問は見られない」「Wantは確認できない」「判断材料がない」など、欠けている項目をわざわざ報告しない。項目を網羅しようとしない。
- reflection_summary は、興味や思考を示す根拠がどのコメントにあるかを意識し、根拠が弱い場合は断定しない。
- reflection_summary は性格診断・能力評価・将来予測にしない。「〜な子だ」と固定せず、「この日は〜に目が向いていた」「〜と考えていた」のようにその日の発言の範囲で書く。
- reflection_summary で本人が言っていない感情・意図を事実として断定しない。書ける分析だけを自然な文章として残す。
- child_points はAIの解釈ではなく、日記と reflection_summary の根拠になった本人の発言を短く3つ以内で抜き出す。
- signals は本人が実際に話した内容だけを整理し、推測を足さない。
""".strip()
    result = ask_json(prompt, "compose_burari_diary", schema, 1100)
    result["title"] = diary_title_for_trip(trip)
    result["signals"] = merge_signals(all_signals, result.get("signals", {}))
    return result, raw


def _vision_ready_photo(image_bytes, max_side=720, quality=76):
    """Shrink a stored photo for the AI summary request without changing the saved original."""
    try:
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((max_side, max_side))
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=quality, optimize=True)
            return out.getvalue()
    except Exception:
        return image_bytes


SUMMARY_FEEDBACK_HISTORY_LIMIT = 12
SUMMARY_FEEDBACK_SCAN_LIMIT = 80
SUMMARY_GOOD_EXAMPLE_LIMIT = 3
SUMMARY_BAD_EXAMPLE_LIMIT = 2


def _summary_generation_key(meta):
    if not isinstance(meta, dict):
        return ""
    saved_key = str(meta.get("photo_comment_summary_updated_at") or "").strip()
    if saved_key:
        return saved_key
    source = "\n".join(
        [
            str(meta.get("trip_summary") or "").strip(),
            str(meta.get("reflection_summary") or "").strip(),
        ]
    ).strip()
    if not source:
        return ""
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def _clear_summary_feedback_fields(meta, clear_history=False):
    """Remove current Good/Bad state; optionally erase all learned examples too."""
    if not isinstance(meta, dict):
        return meta
    for key in (
        "summary_feedback",
        "summary_feedback_at",
        "summary_feedback_generation_key",
        "summary_feedback_example",
    ):
        meta.pop(key, None)
    if clear_history:
        meta.pop("summary_feedback_history", None)
    return meta


def _apply_summary_feedback_to_meta(meta, rating):
    """Attach one rating to the exact summary that is currently visible."""
    rating = str(rating or "").strip().lower()
    if rating not in {"good", "bad"}:
        raise ValueError("評価は Good または Bad を指定してください。")
    meta = dict(meta or {}) if isinstance(meta or {}, dict) else {}
    trip_summary = str(meta.get("trip_summary") or "").strip()
    reflection_summary = str(meta.get("reflection_summary") or "").strip()
    if not (trip_summary or reflection_summary):
        raise ValueError("評価できるAIまとめがありません。")

    generation_key = _summary_generation_key(meta)
    if not generation_key:
        generation_key = hashlib.sha1(
            f"{trip_summary}\n{reflection_summary}".encode("utf-8")
        ).hexdigest()
    now_value = now_jst().isoformat()
    entry = {
        "rating": rating,
        "generation_key": generation_key,
        "trip_summary": trip_summary,
        "reflection_summary": reflection_summary,
        "at": now_value,
    }

    history = meta.get("summary_feedback_history") or []
    if not isinstance(history, list):
        history = []
    # Pressing the other button changes the rating for this output instead of
    # creating duplicate training examples for one generation.
    history = [
        item for item in history
        if not isinstance(item, dict) or str(item.get("generation_key") or "") != generation_key
    ]
    history.append(entry)
    meta["summary_feedback_history"] = history[-SUMMARY_FEEDBACK_HISTORY_LIMIT:]
    meta["summary_feedback"] = rating
    meta["summary_feedback_at"] = now_value
    meta["summary_feedback_generation_key"] = generation_key
    meta["summary_feedback_example"] = {
        "trip_summary": trip_summary,
        "reflection_summary": reflection_summary,
    }
    return meta


def _summary_feedback_entries(limit=SUMMARY_FEEDBACK_SCAN_LIMIT):
    """Collect recent persisted ratings without needing a new Supabase table."""
    try:
        rows = (
            supabase_client()
            .table(DIARY_TABLE)
            .select("id,trip_id,ai_meta,updated_at")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
    except Exception:
        return []

    entries = []
    seen = set()
    for row in rows:
        meta = row.get("ai_meta") or {}
        if not isinstance(meta, dict):
            continue
        history = meta.get("summary_feedback_history") or []
        if isinstance(history, list):
            for item in reversed(history):
                if not isinstance(item, dict):
                    continue
                rating = str(item.get("rating") or "").lower()
                if rating not in {"good", "bad"}:
                    continue
                generation_key = str(item.get("generation_key") or "")
                dedupe_key = (str(row.get("id") or ""), generation_key, str(item.get("at") or ""))
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                entries.append(
                    {
                        "rating": rating,
                        "trip_summary": str(item.get("trip_summary") or "").strip(),
                        "reflection_summary": str(item.get("reflection_summary") or "").strip(),
                        "at": str(item.get("at") or row.get("updated_at") or ""),
                    }
                )

        # Backward-compatible fallback if a current rating exists without history.
        if not history:
            rating = str(meta.get("summary_feedback") or "").lower()
            if rating in {"good", "bad"}:
                example = meta.get("summary_feedback_example") or {}
                if not isinstance(example, dict):
                    example = {}
                entries.append(
                    {
                        "rating": rating,
                        "trip_summary": str(example.get("trip_summary") or meta.get("trip_summary") or "").strip(),
                        "reflection_summary": str(example.get("reflection_summary") or meta.get("reflection_summary") or "").strip(),
                        "at": str(meta.get("summary_feedback_at") or row.get("updated_at") or ""),
                    }
                )

    # Unsaved draft feedback should also have a small immediate effect during the
    # current session. Once saved, it becomes part of the persisted diary history.
    for state_key in list(st.session_state.keys()):
        if not str(state_key).startswith("reflection_state_"):
            continue
        state = st.session_state.get(state_key)
        if not isinstance(state, dict):
            continue
        draft_meta = state.get("draft_meta") or {}
        if not isinstance(draft_meta, dict):
            continue
        draft_history = draft_meta.get("summary_feedback_history") or []
        if not isinstance(draft_history, list):
            continue
        for item in reversed(draft_history):
            if not isinstance(item, dict):
                continue
            rating = str(item.get("rating") or "").lower()
            if rating not in {"good", "bad"}:
                continue
            entries.append(
                {
                    "rating": rating,
                    "trip_summary": str(item.get("trip_summary") or "").strip(),
                    "reflection_summary": str(item.get("reflection_summary") or "").strip(),
                    "at": str(item.get("at") or ""),
                }
            )

    entries.sort(key=lambda item: str(item.get("at") or ""), reverse=True)
    return entries


def get_summary_feedback_status():
    entries = _summary_feedback_entries()
    good = [item for item in entries if item.get("rating") == "good"]
    bad = [item for item in entries if item.get("rating") == "bad"]
    return {
        "good_count": len(good),
        "bad_count": len(bad),
        "good_examples": good[:SUMMARY_GOOD_EXAMPLE_LIMIT],
        "bad_examples": bad[:SUMMARY_BAD_EXAMPLE_LIMIT],
    }


def _feedback_example_text(item, max_chars=560):
    parts = []
    trip_summary = str((item or {}).get("trip_summary") or "").strip()
    reflection_summary = str((item or {}).get("reflection_summary") or "").strip()
    if trip_summary:
        parts.append("ぶらり旅のまとめ: " + trip_summary)
    if reflection_summary:
        parts.append("興味・考えのまとめ: " + reflection_summary)
    text = "\n".join(parts).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def build_summary_feedback_guidance():
    """Return a deliberately weak few-shot preference hint from Good/Bad history."""
    status = get_summary_feedback_status()
    good = status.get("good_examples") or []
    bad = status.get("bad_examples") or []
    if not good and not bad:
        return ""

    lines = [
        "過去のGood/Bad評価による弱い調整:",
        "- 以下は過去の事実を今回へ持ち込むための資料ではなく、文章のまとめ方・分析の粒度・言い回しだけの弱い参考です。",
        "- 今回の写真と本人コメントを最優先し、過去文の内容や固有名詞をコピーしないでください。",
        "- Good例に少しだけ近い書き方を選び、Bad例に近い書き方は少しだけ避けてください。基本ルールを変えるほど強く寄せないでください。",
    ]
    if good:
        lines.append("Goodとして評価された最近の例:")
        for idx, item in enumerate(good, start=1):
            text = _feedback_example_text(item)
            if text:
                lines.append(f"[Good {idx}]\n{text}")
    if bad:
        lines.append("Badとして評価された最近の例（内容ではなく書き方だけを弱く避ける）:")
        for idx, item in enumerate(bad, start=1):
            text = _feedback_example_text(item)
            if text:
                lines.append(f"[Bad {idx}]\n{text}")
    return "\n".join(lines)


def save_summary_feedback(trip_id, rating):
    diary = get_diary_for_trip(trip_id)
    if not diary:
        raise ValueError("日記が見つかりませんでした。")
    meta = _apply_summary_feedback_to_meta(diary.get("ai_meta") or {}, rating)
    (
        supabase_client()
        .table(DIARY_TABLE)
        .update({"ai_meta": meta, "updated_at": now_jst().isoformat()})
        .eq("trip_id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    _invalidate_fast_db_cache()
    return meta


def reset_summary_feedback_learning():
    """Return AI summary generation to its pre-feedback behavior without deleting summaries."""
    client = supabase_client()
    rows = (
        client.table(DIARY_TABLE)
        .select("id,ai_meta")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    ).data or []
    changed = 0
    for row in rows:
        meta = row.get("ai_meta") or {}
        if not isinstance(meta, dict):
            continue
        before = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        _clear_summary_feedback_fields(meta, clear_history=True)
        after = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        (
            client
            .table(DIARY_TABLE)
            .update({"ai_meta": meta, "updated_at": now_jst().isoformat()})
            .eq("id", row["id"])
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        )
        changed += 1

    # Also clear unsaved feedback in any in-progress diary draft in this session.
    for key in list(st.session_state.keys()):
        if not str(key).startswith("reflection_state_"):
            continue
        state = st.session_state.get(key)
        if not isinstance(state, dict):
            continue
        draft_meta = state.get("draft_meta")
        if isinstance(draft_meta, dict):
            _clear_summary_feedback_fields(draft_meta, clear_history=True)
    _invalidate_fast_db_cache()
    return changed


@st.dialog("AIまとめのGood/Bad反映をリセットしますか？")
def confirm_summary_feedback_reset_dialog():
    st.write("Good/Badから学習した『まとめ方の好み』だけを消して、標準の出力方法に戻します。")
    st.caption("保存済みの日記・写真・AIまとめ本文は削除しません。Good/Badの評価履歴は消えます。")
    reset_col, cancel_col = st.columns(2)
    with reset_col:
        if st.button("リセットする", type="primary", use_container_width=True, key="summary_feedback_reset_yes"):
            try:
                reset_summary_feedback_learning()
                st.session_state["_settings_notice"] = "AIまとめのGood/Bad反映をリセットしました。"
                st.rerun(scope="app")
            except Exception as exc:
                st.error("リセットできませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with cancel_col:
        if st.button("キャンセル", use_container_width=True, key="summary_feedback_reset_no"):
            st.rerun(scope="app")


def render_summary_feedback_controls(meta, trip_id, key_prefix, draft_state=None):
    """Render Good/Bad for one visible AI summary and persist or stage the rating."""
    if not isinstance(meta, dict):
        return
    if not (str(meta.get("trip_summary") or "").strip() or str(meta.get("reflection_summary") or "").strip()):
        return

    current = str(meta.get("summary_feedback") or "").lower()
    st.caption("上のAIまとめを評価します。次回以降のまとめ方に少しだけ反映されます。")
    good_col, bad_col = st.columns(2)
    with good_col:
        good_label = "👍 Good ✓" if current == "good" else "👍 Good"
        if st.button(
            good_label,
            use_container_width=True,
            key=f"summary_feedback_good_{key_prefix}_{trip_id}",
        ):
            try:
                if draft_state is None:
                    save_summary_feedback(trip_id, "good")
                else:
                    draft_state["draft_meta"] = _apply_summary_feedback_to_meta(
                        draft_state.get("draft_meta") or {}, "good"
                    )
                st.rerun()
            except Exception as exc:
                st.error("Good評価を保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with bad_col:
        bad_label = "👎 Bad ✓" if current == "bad" else "👎 Bad"
        if st.button(
            bad_label,
            use_container_width=True,
            key=f"summary_feedback_bad_{key_prefix}_{trip_id}",
        ):
            try:
                if draft_state is None:
                    save_summary_feedback(trip_id, "bad")
                else:
                    draft_state["draft_meta"] = _apply_summary_feedback_to_meta(
                        draft_state.get("draft_meta") or {}, "bad"
                    )
                st.rerun()
            except Exception as exc:
                st.error("Bad評価を保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))


def summarize_burari_from_photos(trip, photos):
    """Summarize one trip from the actual photos plus the child's saved comments."""
    comment_lines = []
    image_items = []
    child_points = []

    for idx, photo in enumerate(photos or [], start=1):
        conversation = _stored_photo_conversation(photo)
        child_comments = [
            str(turn.get("text") or "").strip()
            for turn in conversation
            if isinstance(turn, dict)
            and turn.get("role") == "child"
            and str(turn.get("text") or "").strip()
        ]
        location = str(photo_location_label(photo) or "").strip()
        joined = " / ".join(child_comments) if child_comments else "本人コメントなし"
        comment_lines.append(f"写真{idx}（{location or '場所不明'}）: {joined}")
        for value in child_comments:
            if value not in child_points:
                child_points.append(value)
        try:
            raw = download_photo(photo.get("storage_path"))
            if raw:
                image_items.append((f"写真{idx}", _vision_ready_photo(raw)))
        except Exception:
            # One unreadable image must not prevent the other photos/comments from being summarized.
            pass

    schema = {
        "type": "object",
        "properties": {
            "trip_summary": {"type": "string"},
            "reflection_summary": {"type": "string"},
            "child_points": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["trip_summary", "reflection_summary", "child_points"],
        "additionalProperties": False,
    }
    comments_text = "\n".join(comment_lines) if comment_lines else "写真・コメントなし"
    feedback_guidance = build_summary_feedback_guidance()
    prompt = f"""
5〜6歳の子どもの「東京ぶらり旅」1回分をまとめてください。
入力には、その日に保存された写真と、各写真について本人が話したコメントがあります。

日付: {(trip or {}).get('trip_date', '')}
行き先メモ: {str((trip or {}).get('destination') or '').strip() or 'なし'}
写真ごとの本人コメント:
{comments_text}

{feedback_guidance}

出力ルール:
- trip_summary は、そのぶらり旅全体を2〜4文で簡潔にまとめる。写真から確認できる対象と、本人が実際に話した内容を結びつけてよい。
- 写真に写っていない出来事や、本人が言っていない感情・意図を作らない。
- reflection_summary は本人のコメントを第一の根拠として、その日に何へ興味・注意が向いていたか、どのように比較・理由づけをしていたかなど、自然に読み取れる部分だけを2〜4文で分析する。項目を網羅する必要はない。
- 疑問やWant（どうしたい・こうなってほしい等）は必須ではない。本人が直接言っていなくても、それまでの本人コメント全体からかなり自然に推測できる場合は、「〜を気にしていたようです」「〜したい方向がうかがえます」のような控えめな表現で含めてよい。
- 疑問やWantを自然に推測できない場合は完全に省略する。「疑問はない」「Wantは確認できない」「判断材料が少ない」など、欠けている項目について説明しない。
- reflection_summary は単なるコメントの言い換えではなく、その日の興味や思考の向きを整理する。ただし性格診断・能力評価・将来予測はしない。
- 写真はコメントの対象を理解するための補助根拠として使う。写真だけから本人の感情・疑問・Wantを新たに作らない。
- child_points は分析の根拠になった本人の言葉を3つ以内で短く抜き出す。本人コメントがなければ空配列にする。
""".strip()

    # When every photo failed to download, comments alone are still sufficient for a cautious summary.
    if image_items:
        result = ask_json_with_images(
            prompt,
            image_items,
            "summarize_burari_photos_and_comments",
            schema,
            1000,
        )
    else:
        result = ask_json(
            prompt,
            "summarize_burari_comments_only",
            schema,
            1000,
        )
    result["child_points"] = list(result.get("child_points") or [])[:3]
    return result


def save_burari_ai_summary(trip_id, result):
    """Persist the on-demand AI trip summary inside the existing diary ai_meta."""
    diary = get_diary_for_trip(trip_id)
    if not diary:
        raise ValueError("先に日記を保存してください。")
    meta = diary.get("ai_meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    _clear_summary_feedback_fields(meta, clear_history=False)
    meta["trip_summary"] = str((result or {}).get("trip_summary") or "").strip()
    meta["reflection_summary"] = str((result or {}).get("reflection_summary") or "").strip()
    points = list((result or {}).get("child_points") or [])[:3]
    if points:
        meta["child_points"] = points
    meta["photo_comment_summary_updated_at"] = now_jst().isoformat()
    (
        supabase_client()
        .table(DIARY_TABLE)
        .update({"ai_meta": meta, "updated_at": now_jst().isoformat()})
        .eq("trip_id", trip_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    _invalidate_fast_db_cache()
    return meta


def render_burari_trip_summary(meta):
    if not isinstance(meta, dict):
        return
    summary = str(meta.get("trip_summary") or "").strip()
    if not summary:
        return
    st.markdown("#### AIによる、このぶらり旅のまとめ")
    st.markdown(
        f"""
        <div class="talk-card">
          <div class="small-note">写真と本人のコメントを一緒に見て、このぶらり旅全体をまとめています。</div>
          <div class="big-text" style="margin-top:.45rem;">{html.escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
def _cache_active_trip_snapshot(trip):
    trip = trip if isinstance(trip, dict) else None
    st.session_state["_active_trip_snapshot"] = trip
    st.session_state["_active_trip_snapshot_at"] = time.time()
    if trip and trip.get("id"):
        st.session_state.active_trip_id = trip["id"]
    return trip


def _invalidate_active_trip_snapshot():
    st.session_state.pop("_active_trip_snapshot", None)
    st.session_state.pop("_active_trip_snapshot_at", None)


def get_active_trip_fast(max_age_seconds=20):
    trip_id = st.session_state.get("active_trip_id")
    if not trip_id:
        return None
    snapshot = st.session_state.get("_active_trip_snapshot")
    snapshot_at = float(st.session_state.get("_active_trip_snapshot_at") or 0.0)
    if (
        isinstance(snapshot, dict)
        and str(snapshot.get("id") or "") == str(trip_id)
        and (time.time() - snapshot_at) <= float(max_age_seconds)
    ):
        return snapshot
    trip = get_trip(trip_id)
    return _cache_active_trip_snapshot(trip)


def init_state():
    defaults = {
        "main_page": "home",
        "active_trip_id": None,
        "capture_serial": 0,
        "preferred_diary_trip_id": None,
        "show_home_destination_editor": False,
        "_diary_selector_serial": 0,
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

    today = today_iso()
    # Do not query Supabase during startup merely to rediscover today's trip.
    # If we already have a local snapshot and it is clearly from another day, clear it.
    # Otherwise the first data-requiring action (saving a photo, opening diary, etc.)
    # resolves the database state lazily.
    if st.session_state.active_trip_id:
        snapshot = st.session_state.get("_active_trip_snapshot")
        if isinstance(snapshot, dict) and str(snapshot.get("id") or "") == str(st.session_state.active_trip_id):
            if snapshot.get("status") != "active" or snapshot.get("trip_date") != today:
                st.session_state.active_trip_id = None
                _invalidate_active_trip_snapshot()



VALID_APP_PAGES = {"home", "camera", "diary", "review", "settings"}


def restore_recent_camera_session():
    """Reopen a recently used camera without an extra browser-storage component call."""
    if st.session_state.get("_recent_camera_restore_checked", False):
        return
    st.session_state["_recent_camera_restore_checked"] = True

    # A fresh auto-login already read browser persistence and stored this value.
    # If it is unavailable, skip restoration rather than delaying the Home screen.
    last_open = st.session_state.get("_browser_last_camera_open_at")
    if last_open is None:
        return
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
    current = st.session_state.get("main_page")
    if current != target:
        # Opening Diary from another page should start with no saved diary selected.
        # This avoids downloading any saved-diary photos until the user explicitly
        # chooses a trip, and it also makes the screen less visually busy.
        if target == "diary":
            st.session_state.preferred_diary_trip_id = None
            st.session_state["_diary_selector_serial"] = int(
                st.session_state.get("_diary_selector_serial") or 0
            ) + 1
            for key in list(st.session_state.keys()):
                if str(key).startswith("diary_trip_selector_"):
                    st.session_state.pop(key, None)
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
    trip = get_active_trip_fast(max_age_seconds=20) if st.session_state.active_trip_id else None
    if trip and trip.get("status") == "active" and trip.get("trip_date") == today_iso():
        return trip
    trip = get_today_active_trip()
    if not trip:
        trip = create_trip("")
    _cache_active_trip_snapshot(trip)
    st.session_state["_today_active_lookup_key"] = (
        f"{current_family_key()}|{current_member_key()}|{today_iso()}"
    )
    return trip


def render_home_button(label, page_name, key, ensure_trip=False):
    if st.button(label, key=key, use_container_width=True):
        if page_name == "camera":
            # The user's click is a valid browser gesture: use it to request the camera
            # immediately on the next render. Do not block on a trip lookup first.
            st.session_state["_camera_auto_start"] = True
        elif ensure_trip:
            ensure_today_trip()
        go_page(page_name)


@st.cache_data(show_spinner=False)
def _local_icon_data_uri(path):
    """Return a local icon as a data URI without decoding/re-encoding it."""
    if not path or not os.path.exists(path):
        return ""
    try:
        suffix = os.path.splitext(path)[1].lower()
        mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/png"
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return ""


def _home_icon_uri(name):
    for path in HOME_ICON_CANDIDATES.get(name, []):
        uri = _local_icon_data_uri(path)
        if uri:
            return uri
    return ""


def _home_theme_for_session():
    """Choose one route theme and keep train/camera/diary coordinated for the session."""
    valid_keys = set(HOME_ROUTE_THEMES)
    selected_key = str(st.session_state.get("_home_train_icon_key") or "")
    if selected_key not in valid_keys:
        selected_key = random.choice(list(HOME_ROUTE_THEMES.keys()))
        st.session_state["_home_train_icon_key"] = selected_key
    theme = dict(HOME_ROUTE_THEMES[selected_key])
    theme["train_key"] = selected_key
    st.session_state["_home_train_line_name"] = theme["line_name"]
    return theme


def _home_train_for_session():
    """Backward-compatible helper returning the selected route name and train image."""
    theme = _home_theme_for_session()
    return theme["line_name"], _home_icon_uri(theme["train_key"]) or _home_icon_uri("train")


def inject_home_icon_css():
    theme = _home_theme_for_session()
    camera_uri = _home_icon_uri(theme["camera_key"]) or _home_icon_uri("camera")
    diary_uri = _home_icon_uri(theme["diary_key"]) or _home_icon_uri("diary")
    review_uri = _home_icon_uri("review")
    settings_uri = _home_icon_uri(theme["settings_key"]) or _home_icon_uri("settings")
    accent = theme["accent"]
    rgb1 = theme["accent_rgb"]
    rgb2 = theme["accent2_rgb"]

    css_chunks = [
        ".st-key-home_camera div.stButton > button::before,"
        ".st-key-home_diary div.stButton > button::before,"
        ".st-key-home_review div.stButton > button::before,"
        ".st-key-home_settings div.stButton > button::before{content:'';display:block;background-repeat:no-repeat;background-position:center;background-size:contain;flex-shrink:0;margin:0 !important;}",
        ".st-key-home_camera div.stButton > button::before,.st-key-home_diary div.stButton > button::before{width:54px;height:54px;}",
        ".st-key-home_review div.stButton > button::before,.st-key-home_settings div.stButton > button::before{width:46px;height:46px;}",
        "@media (max-width: 640px){.st-key-home_camera div.stButton > button::before,.st-key-home_diary div.stButton > button::before{width:42px;height:42px;}.st-key-home_review div.stButton > button::before,.st-key-home_settings div.stButton > button::before{width:36px;height:36px;}}",
        f'.home-title-accent{{color:color-mix(in srgb, {accent} 80%, rgba(31, 38, 48, .96) 20%);text-shadow:0 1px 0 rgba(255,255,255,.72);}}',
        f'.st-key-home_camera div.stButton > button,.st-key-home_diary div.stButton > button{{border-color:{accent} !important;background:linear-gradient(155deg,rgba({rgb2},.25),rgba({rgb1},.07)) !important;box-shadow:0 9px 22px rgba({rgb1},.10),0 0 0 2px rgba(255,255,255,.34) inset !important;}}',
        f'.st-key-home_camera div.stButton > button:hover,.st-key-home_diary div.stButton > button:hover{{border-color:{accent} !important;background:linear-gradient(155deg,rgba({rgb2},.34),rgba({rgb1},.11)) !important;box-shadow:0 11px 24px rgba({rgb1},.14),0 0 0 2px rgba(255,255,255,.40) inset !important;}}',
        f'.st-key-home_settings div.stButton > button{{border-color:rgba({rgb1},.46) !important;background:linear-gradient(155deg,rgba({rgb2},.18),rgba({rgb1},.035)) !important;box-shadow:0 8px 20px rgba({rgb1},.07),0 0 0 2px rgba(255,255,255,.30) inset !important;}}',
        f'.st-key-home_settings div.stButton > button:hover{{border-color:rgba({rgb1},.62) !important;background:linear-gradient(155deg,rgba({rgb2},.25),rgba({rgb1},.065)) !important;box-shadow:0 10px 22px rgba({rgb1},.10),0 0 0 2px rgba(255,255,255,.35) inset !important;}}',
    ]
    if camera_uri:
        css_chunks.append(f'.st-key-home_camera div.stButton > button::before{{background-image:url("{camera_uri}") !important;}}')
    if diary_uri:
        css_chunks.append(f'.st-key-home_diary div.stButton > button::before{{background-image:url("{diary_uri}") !important;}}')
    if review_uri:
        css_chunks.append(f'.st-key-home_review div.stButton > button::before{{background-image:url("{review_uri}") !important;}}')
    if settings_uri:
        css_chunks.append(f'.st-key-home_settings div.stButton > button::before{{background-image:url("{settings_uri}") !important;}}')

    if css_chunks:
        st.markdown("<style>" + "\n".join(css_chunks) + "</style>", unsafe_allow_html=True)

def render_global_bottom_home_button(page_name):
    """Keep a full-width route to Home at the very bottom of major subpages."""
    st.divider()
    with st.container(key="global_home_nav"):
        if st.button(
            "トップページに戻る",
            use_container_width=True,
            key=f"global_bottom_home_{page_name}",
        ):
            go_page("home")


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


def finalize_previous_days_into_diaries():
    """Rescue photos from older unfinished trips and create a provisional diary.

    A trip can remain ``active`` when the user takes photos and closes the app
    without explicitly creating a diary. Older active trips are not shown by the
    normal diary selector, which can make those photos look as if they disappeared.
    On the first authenticated render of each calendar day, move every older trip
    that still has photos into the diary flow and save a diary immediately.

    Only the child's already-saved words are used for prose/analysis. Photos with
    no child comment are kept in the diary gallery but never receive invented
    events, feelings, or intentions.
    """
    today = today_iso()
    guard_key = f"_stale_rollover_checked_for_{current_family_key()}_{current_member_key()}"
    if st.session_state.get(guard_key) == today:
        return
    st.session_state[guard_key] = today

    client = supabase_client()
    try:
        result = (
            client
            .table(TRIP_TABLE)
            .select("*")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .in_("status", ["active", "ready_for_diary"])
            .lt("trip_date", today)
            .order("trip_date")
            .order("started_at")
            .execute()
        )
        stale_trips = result.data or []
    except Exception as exc:
        st.session_state["_rollover_warning"] = (
            "前日までの写真の確認に失敗しました。写真データは削除していません。"
        )
        st.session_state["_rollover_warning_detail"] = str(exc)
        return

    created_count = 0
    rescued_count = 0
    failed_count = 0

    for trip in stale_trips:
        trip_id = trip.get("id")
        if not trip_id:
            continue

        try:
            photos = list_trip_photos(trip_id)
        except Exception:
            failed_count += 1
            continue
        if not photos:
            # Do not create an empty diary just because an old empty trip row exists.
            continue

        existing = get_diary_for_trip(trip_id)
        if existing:
            if trip.get("status") != "diary_done":
                client.table(TRIP_TABLE).update({"status": "diary_done"}).eq("id", trip_id).eq("family_key", current_family_key()).eq("member_key", current_member_key()).execute()
            continue

        # First make the photos visible in the normal diary selector. Even if the
        # AI step fails later, the photos are no longer stranded in an old active trip.
        if trip.get("status") == "active":
            ended_at = str(photos[-1].get("captured_at") or now_jst().isoformat())
            (
                client
                .table(TRIP_TABLE)
                .update({"status": "ready_for_diary", "ended_at": ended_at})
                .eq("id", trip_id)
                .eq("family_key", current_family_key()).eq("member_key", current_member_key())
                .execute()
            )
            rescued_count += 1

        photo_states = []
        child_comments = []
        raw = {}
        merged_signals = {}
        for photo in photos:
            pid = photo.get("id")
            conversation = _stored_photo_conversation(photo)
            signals = photo.get("signals_json") or {}
            if not isinstance(signals, dict):
                signals = {}
            photo_states.append(
                {
                    "photo_id": pid,
                    "conversation": conversation,
                    "signals": signals,
                }
            )
            raw[str(pid)] = conversation
            merged_signals = merge_signals(merged_signals, signals)
            for turn in conversation:
                if not isinstance(turn, dict) or turn.get("role") != "child":
                    continue
                value = str(turn.get("text") or "").strip()
                if value:
                    child_comments.append(value)

        try:
            if child_comments:
                try:
                    composed, raw = compose_diary(trip, photo_states)
                    diary_text = str(composed.get("diary") or "").strip()
                    reflection_summary = str(composed.get("reflection_summary") or "").strip()
                    child_points = list(composed.get("child_points") or [])[:3]
                    merged_signals = merge_signals(merged_signals, composed.get("signals", {}))
                except Exception:
                    # The photos must still survive day rollover even if the AI call is
                    # temporarily unavailable. Keep a factual diary from the saved words.
                    diary_text = f"この日は写真を{len(photos)}枚残しました。写真を見ながら話した言葉も保存しています。"
                    reflection_summary = (
                        "本人のコメントは保存されています。AIによる興味・考えのまとめは、"
                        "この日記を作り直すと更新できます。"
                    )
                    child_points = child_comments[:3]
            else:
                diary_text = (
                    f"この日は写真を{len(photos)}枚残しました。"
                    "写真についての本人のコメントはまだありません。"
                )
                reflection_summary = (
                    "本人のコメントがまだないため、この記録だけから興味や考え方は判断していません。"
                )
                child_points = []

            ai_meta = {
                "child_points": child_points,
                "signals": merged_signals,
                "reflection_summary": reflection_summary,
                "auto_rollover": True,
                "auto_rollover_reason": "day_changed_before_diary_creation",
                "photo_count": len(photos),
                "commented_photo_count": sum(
                    1 for state in photo_states if _conversation_has_child_words(state.get("conversation", []))
                ),
            }
            save_diary(
                trip_id,
                diary_title_for_trip(trip, photos=photos),
                diary_text,
                raw,
                ai_meta,
            )
            created_count += 1
        except Exception:
            # It is already ready_for_diary, so the user can still see and finish it
            # manually instead of losing access to the previous day's photos.
            failed_count += 1

    if created_count:
        st.session_state["_rollover_notice"] = (
            f"前日までに残っていた写真を {created_count}件の日記に自動でまとめました。"
        )
    elif rescued_count:
        st.session_state["_rollover_notice"] = (
            "前日までの写真を日記画面から確認できる状態に戻しました。"
        )
    if failed_count:
        st.session_state["_rollover_warning"] = (
            "一部の日記は自動作成できませんでしたが、写真は日記画面から確認できます。"
        )


def _list_pending_photo_trips_uncached(limit=40):
    """Return trips with photos but no diary, normally in one PostgREST request."""
    client = supabase_client()
    try:
        rows = (
            client
            .table(TRIP_TABLE)
            .select(
                f"*,{DIARY_TABLE}(id,trip_id,title),"
                f"{PHOTO_TABLE}(id,trip_id,storage_path,captured_at,reflection_json,signals_json)"
            )
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .in_("status", ["active", "ready_for_diary", "diary_done"])
            .order("trip_date", desc=True)
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        pending = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            trip = dict(row)
            embedded_diary = trip.pop(DIARY_TABLE, []) or []
            photos = trip.pop(PHOTO_TABLE, []) or []
            if isinstance(embedded_diary, dict):
                embedded_diary = [embedded_diary]
            if isinstance(photos, dict):
                photos = [photos]
            if embedded_diary or not photos:
                continue
            photos = sorted(
                [p for p in photos if isinstance(p, dict)],
                key=lambda p: str(p.get("captured_at") or ""),
            )
            if photos:
                pending.append({"trip": trip, "photos": photos})
        return pending
    except Exception:
        pass

    # Relationship embedding fallback for older PostgREST metadata caches.
    result = (
        client
        .table(TRIP_TABLE)
        .select("*")
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .in_("status", ["active", "ready_for_diary", "diary_done"])
        .order("trip_date", desc=True)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    trips = result.data or []
    if not trips:
        return []
    trip_ids = [str(trip.get("id")) for trip in trips if trip.get("id")]
    diary_map = diaries_for_trip_ids(trip_ids)
    pending_trips = [trip for trip in trips if str(trip.get("id")) not in diary_map]
    pending_ids = [str(trip.get("id")) for trip in pending_trips if trip.get("id")]
    photo_map = photos_for_trip_ids(pending_ids)
    return [
        {"trip": trip, "photos": photo_map.get(str(trip.get("id")), [])}
        for trip in pending_trips
        if photo_map.get(str(trip.get("id")), [])
    ]


def list_pending_photo_trips(limit=40):
    cache_key = _account_cache_key("pending_photo_trips", int(limit))
    cached = _session_cache_get(cache_key, max_age_seconds=10)
    if cached is not None:
        return cached
    return _session_cache_set(cache_key, _list_pending_photo_trips_uncached(limit=limit))


def _title_against_used(base_title, used_titles):
    base_title = str(base_title or "").strip()
    if not (base_title.startswith("ぶらり旅（") and base_title.endswith("）")):
        return base_title
    if base_title not in used_titles:
        return base_title
    stem = base_title[:-1]
    suffix = 2
    while f"{stem}{suffix}）" in used_titles:
        suffix += 1
    return f"{stem}{suffix}）"


def pending_diary_titles(pending_rows, used_titles=None):
    """Number pending titles too, reusing already-loaded diary titles when available."""
    if used_titles is None:
        saved = (
            supabase_client()
            .table(DIARY_TABLE)
            .select("title")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .execute()
        ).data or []
        used = {str(row.get("title") or "").strip() for row in saved if str(row.get("title") or "").strip()}
    else:
        used = {str(value or "").strip() for value in used_titles if str(value or "").strip()}
    result = {}
    # Oldest first gets the unnumbered base name; later trips get 2, 3, ... .
    ordered = sorted(
        pending_rows or [],
        key=lambda item: (
            str((item.get("trip") or {}).get("trip_date") or ""),
            str((item.get("trip") or {}).get("started_at") or ""),
        ),
    )
    for item in ordered:
        trip = item.get("trip") or {}
        photos = item.get("photos") or []
        base = diary_title_for_trip(trip, photos=photos)
        title = _title_against_used(base, used)
        result[str(trip.get("id") or "")] = title
        if title:
            used.add(title)
    return result


def create_and_save_diary_from_photos(trip, photos, requested_title=None, reason="manual_create"):
    """Create a diary from already-saved child comments and persist it immediately."""
    trip = trip or {}
    photos = photos or []
    if not trip.get("id") or not photos:
        raise ValueError("日記にする写真がありません。")

    photo_states = []
    child_comments = []
    raw = {}
    merged_signals = {}
    for photo in photos:
        pid = photo.get("id")
        conversation = _stored_photo_conversation(photo)
        signals = photo.get("signals_json") or {}
        if not isinstance(signals, dict):
            signals = {}
        photo_states.append({"photo_id": pid, "conversation": conversation, "signals": signals})
        raw[str(pid)] = conversation
        merged_signals = merge_signals(merged_signals, signals)
        for turn in conversation:
            if isinstance(turn, dict) and turn.get("role") == "child":
                value = str(turn.get("text") or "").strip()
                if value:
                    child_comments.append(value)

    if child_comments:
        try:
            result, raw = compose_diary(trip, photo_states)
            diary_text = str(result.get("diary") or "").strip()
            reflection_summary = str(result.get("reflection_summary") or "").strip()
            child_points = list(result.get("child_points") or [])[:3]
            merged_signals = merge_signals(merged_signals, result.get("signals", {}))
        except Exception:
            diary_text = f"この日は写真を{len(photos)}枚残しました。写真について話した言葉も保存しています。"
            reflection_summary = "本人のコメントは保存されています。AIの分析は、あとから『AIにまとめてもらう』で更新できます。"
            child_points = child_comments[:3]
    else:
        diary_text = f"この日は写真を{len(photos)}枚残しました。写真についての本人のコメントはまだありません。"
        reflection_summary = ""
        child_points = []

    meta = {
        "reflection_summary": reflection_summary,
        "child_points": child_points,
        "signals": merged_signals,
        "photo_count": len(photos),
        "commented_photo_count": sum(
            1 for item in photo_states if _conversation_has_child_words(item.get("conversation", []))
        ),
        "created_from_photo_list": True,
        "create_reason": str(reason or "manual_create"),
    }
    title = requested_title or diary_title_for_trip(trip, photos=photos)
    return save_diary(trip["id"], title, diary_text, raw, meta)


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



def render_pending_thumbnail_grid(trip_id, photos, max_count=None, trip=None):
    """Three-across pending thumbnails. Talked photos are orange and every photo opens its talk screen."""
    subset = list(photos or [])
    if max_count is not None:
        subset = subset[: max(0, int(max_count))]
    if not subset:
        return None

    paths = tuple(str(photo.get("storage_path") or "") for photo in subset if photo.get("storage_path"))
    signed = signed_photo_url_map(paths) if paths else {}
    cards = []
    photo_ids = []
    for photo in subset:
        pid = str(photo.get("id") or "")
        if not pid:
            continue
        conversation = _stored_photo_conversation(photo)
        talked = _conversation_has_child_words(conversation)
        src = photo_display_url(photo, signed, max_px=360, quality=74)
        cards.append(
            {
                "id": pid,
                "src": src,
                "talked": bool(talked),
                "location": str(photo_location_label(photo) or ""),
            }
        )
        photo_ids.append(pid)

    if not cards:
        return None

    gallery_component = _get_diary_gallery_component()
    if gallery_component is not None:
        serial_key = f"pending_gallery_serial_{trip_id}"
        serial = int(st.session_state.get(serial_key) or 0)
        result = gallery_component(
            data={"photos": cards},
            key=f"pending_gallery_{trip_id}_{serial}",
            on_photo_id_change=lambda: None,
            on_delete_photo_id_change=lambda: None,
        )
        delete_clicked = str(getattr(result, "delete_photo_id", "") or "")
        if delete_clicked in photo_ids:
            st.session_state[serial_key] = serial + 1
            confirm_photo_delete_dialog(
                trip_id,
                delete_clicked,
                photos=subset,
                is_pending=True,
                trip=trip,
            )
            return None

        clicked = str(getattr(result, "photo_id", "") or "")
        if clicked in photo_ids:
            st.session_state[serial_key] = serial + 1
            return clicked
        return None

    # Fallback for old component runtimes. Preserve the same orange/gray meaning and make photos openable.
    cols = st.columns(3)
    for idx, card in enumerate(cards):
        with cols[idx % 3]:
            border = "#F59E0B" if card["talked"] else "#AEB6C2"
            background = "rgba(245,158,11,.18)" if card["talked"] else "rgba(174,182,194,.20)"
            if card["src"]:
                st.markdown(
                    f'<div style="padding:4px;border:3px solid {border};background:{background};border-radius:12px;">'
                    f'<img src="{html.escape(card["src"], quote=True)}" style="display:block;width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;" />'
                    '</div>',
                    unsafe_allow_html=True,
                )
            if st.button(
                "写真を開く",
                use_container_width=True,
                key=f"pending_photo_fallback_open_{trip_id}_{card['id']}",
            ):
                return card["id"]
            if st.button(
                "×",
                key=f"pending_photo_fallback_delete_{trip_id}_{card['id']}",
                help="この写真を削除",
            ):
                confirm_photo_delete_dialog(
                    trip_id,
                    card["id"],
                    photos=subset,
                    is_pending=True,
                    trip=trip,
                )
    return None

def render_small_gallery(photos, max_count=None, columns=3):
    """Render history photos lazily; the browser downloads visible images in parallel."""
    subset = list(photos or [])
    if max_count is not None:
        subset = subset[:max_count]
    if not subset:
        return
    column_count = max(1, min(int(columns or 3), 3))
    paths = tuple(str(photo.get("storage_path") or "") for photo in subset if photo.get("storage_path"))
    signed = signed_photo_url_map(paths) if paths else {}
    cards = []
    for photo in subset:
        src = photo_display_url(photo, signed, max_px=520, quality=78)
        if not src:
            continue
        location = str(photo_location_label(photo) or "").strip()
        location_html = (
            f'<div style="font-size:10px;opacity:.65;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">📍 {html.escape(location)}</div>'
            if location else ""
        )
        cards.append(
            f'<div style="min-width:0;"><img src="{html.escape(src, quote=True)}" loading="lazy" decoding="async" fetchpriority="low" '
            f'style="display:block;width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;" />{location_html}</div>'
        )
    if cards:
        st.markdown(
            f'<div style="display:grid;grid-template-columns:repeat({column_count},minmax(0,1fr));gap:6px;width:100%;">'
            + "".join(cards) + "</div>",
            unsafe_allow_html=True,
        )

def render_diary_photo_gallery(trip_id, photos, state=None):
    """Show all photos in a three-column clickable grid."""
    if not photos:
        return None

    st.markdown("#### この日の写真")
    st.caption("オレンジ：話した写真　／　グレー：まだ話していない写真")

    paths = tuple(str(photo.get("storage_path") or "") for photo in photos if photo.get("storage_path"))
    signed = signed_photo_url_map(paths) if paths else {}
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
        src = photo_display_url(photo, signed, max_px=420, quality=76)

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

    gallery_component = _get_diary_gallery_component()
    if gallery_component is not None:
        serial_key = f"diary_gallery_serial_{trip_id}"
        serial = int(st.session_state.get(serial_key) or 0)
        result = gallery_component(
            data={"photos": cards},
            key=f"diary_gallery_{trip_id}_{serial}",
            on_photo_id_change=lambda: None,
            on_delete_photo_id_change=lambda: None,
        )
        delete_clicked = str(getattr(result, "delete_photo_id", "") or "")
        if delete_clicked in photo_ids:
            # Reset the component immediately so the same delete event is not emitted
            # again while the confirmation dialog is open.
            st.session_state[serial_key] = serial + 1
            confirm_photo_delete_dialog(trip_id, delete_clicked, photos=photos)
            return None

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
            action_cols = st.columns([1, 3])
            with action_cols[0]:
                if st.button("×", key=f"diary_photo_fallback_delete_{trip_id}_{card['id']}", help="この写真を削除"):
                    confirm_photo_delete_dialog(trip_id, card["id"], photos=photos)
            with action_cols[1]:
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
    inject_home_icon_css()
    fast_family_name = str(st.session_state.get("_current_family_name") or current_family_key())
    fast_member_name = str(st.session_state.get("_current_member_name") or current_member_key())
    st.caption(f"{fast_family_name} ／ 個人：{fast_member_name}（{current_member_key()}）")
    # The hero train keeps the same track-equipped illustration, but varies by route on each new session.
    train_line_name, train_uri = _home_train_for_session()
    train_html = (
        f'<div class="home-hero-train" title="{html.escape(train_line_name)}">'
        f'<img src="{train_uri}" alt="{html.escape(train_line_name)}をイメージした電車アイコン"></div>'
        if train_uri
        else ""
    )
    st.markdown(
        f"""
        <div class="home-hero">
          <div class="home-hero-inner">
            <div class="home-hero-copy">
              <div class="home-eyebrow">BURARI</div>
              <div class="home-title"><span class="home-title-accent">ぶらり</span>旅</div>
              <div class="home-tagline">思った。感じた。をそのまま残そう</div>
            </div>
            {train_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Home is intentionally DB-free. Counts/place are updated in session immediately
    # after a successful capture; a fresh browser session shows a neutral status until
    # the first data action instead of delaying every launch with two network requests.
    active = st.session_state.get("_active_trip_snapshot")
    if not isinstance(active, dict) or active.get("trip_date") != today_iso() or active.get("status") != "active":
        active = None
    cached_count = st.session_state.get("_home_today_photo_count")
    active_place = str(st.session_state.get("_home_today_place") or (active or {}).get("destination") or "").strip()
    if cached_count is None:
        status_main = "今日の記録"
    else:
        try:
            count_value = max(0, int(cached_count))
        except Exception:
            count_value = 0
        status_main = f"今日の写真 {count_value}枚" if count_value else "今日はまだ写真なし"
    status_sub = active_place or "写真を撮ると、ここに今日の記録が表示されます"
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
            render_home_button("写真を撮る", "camera", "home_camera")
        with primary_right:
            render_home_button("日記にする・見る", "diary", "home_diary")

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
            render_home_button("振り返り（たまに）", "review", "home_review")
        with secondary_right:
            render_home_button("設定", "settings", "home_settings")

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
                saved_title = update_diary_title(trip_id, edited_title)
                # Preserve the diary being viewed while the selectbox is rebuilt with
                # a fresh key, so its visible label changes immediately on mobile too.
                st.session_state.preferred_diary_trip_id = trip_id
                st.session_state["_diary_notice"] = f"日記のタイトルを「{saved_title}」に変更しました。"
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
    preview_src = photo_display_url(photo)
    if preview_src:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:.25rem 0 .45rem;">
              <img src="{html.escape(preview_src, quote=True)}" alt="今撮った写真" loading="lazy" decoding="async"
                   style="display:block;max-width:min(72vw,320px);max-height:34dvh;width:auto;height:auto;object-fit:contain;border-radius:14px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("写真のプレビューを表示できませんでした。コメントは続けられます。")

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
            image_bytes = download_photo(photo["storage_path"])
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

    notice = st.session_state.pop("_camera_notice", None)
    if notice:
        st.success(notice)

    if live_camera_component is None:
        st.error("ライブカメラ機能に必要なStreamlitのバージョンが古いです。requirements.txtを更新してください。")
        return

    # Critical path: mount/start camera first. No Supabase call occurs above this line.
    auto_start = bool(st.session_state.pop("_camera_auto_start", False))
    active_snapshot = st.session_state.get("_active_trip_snapshot")
    if not isinstance(active_snapshot, dict) or active_snapshot.get("trip_date") != today_iso() or active_snapshot.get("status") != "active":
        active_snapshot = None
    camera_trip_key = str((active_snapshot or {}).get("id") or "pending")
    result = live_camera_component(
        data={"auto_start": auto_start},
        key=f"live_camera_{camera_trip_key}_{st.session_state.capture_serial}",
        on_photo_change=lambda: None,
        on_camera_error_change=lambda: None,
    )

    with st.container(key="camera_home_nav"):
        if st.button(
            "トップページに戻る",
            use_container_width=True,
            key="camera_home_button",
        ):
            go_page("home")

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
            digest_key = "saved_camera_digest_current"
            if st.session_state.get(digest_key) != digest:
                # The DB work begins only after the user has actually captured/saved a photo.
                trip = ensure_today_trip()
                capture_source = str(payload.get("source") or "camera")
                location = build_photo_location(
                    payload.get("location"),
                    trip,
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

                # Update Home's lightweight display without rereading today's photo list.
                previous_count = st.session_state.get("_home_today_photo_count")
                try:
                    previous_count = int(previous_count) if previous_count is not None else 0
                except Exception:
                    previous_count = 0
                st.session_state["_home_today_photo_count"] = previous_count + 1
                place_label = str((location or {}).get("place_label") or trip.get("destination") or "").strip()
                if place_label:
                    st.session_state["_home_today_place"] = place_label

                st.session_state.capture_serial += 1
                st.session_state["_camera_notice"] = "写真を保存しました。"
                st.rerun()
        except Exception as exc:
            st.error("写真を保存できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    # Recent-photo comment UI is available after a save, using only the in-session snapshot.
    trip = st.session_state.get("_active_trip_snapshot")
    if isinstance(trip, dict) and trip.get("id"):
        render_recent_camera_photo_comment(trip)


# ============================================================
# Page: Diary conversation
# ============================================================
def page_diary():
    page_top(
        "📖 日記",
        "まだ日記になっていない写真を一覧で確認できます。日記作成後も写真を開いて本人の言葉を追加できます。",
    )
    # Old unfinished trips are already shown by list_pending_photo_trips(), so no
    # AI rollover or historical title scan is needed before the page can appear.
    notice = st.session_state.pop("_diary_notice", None)
    if notice:
        st.success(notice)

    # One diary+trip request is shared by the pending-title numbering and the
    # saved-diary selector below, instead of loading the same diary metadata twice.
    recent_rows = list_recent_diaries(limit=80)
    saved_titles = [
        str((row.get("diary") or {}).get("title") or "").strip()
        for row in recent_rows
        if str((row.get("diary") or {}).get("title") or "").strip()
    ]
    pending_rows = list_pending_photo_trips()
    pending_open_id = str(st.session_state.get("_pending_diary_open_trip_id") or "")
    if pending_rows and not pending_open_id:
        st.markdown("#### まだ日記になっていない写真")
        st.caption("撮影済みで、まだ日記として保存されていないぶらり旅です。『日記を作る』を押した時点で保存します。")
        pending_titles = pending_diary_titles(pending_rows, used_titles=saved_titles)
        for item in pending_rows:
            pending_trip = item.get("trip") or {}
            pending_photos = item.get("photos") or []
            pending_id = str(pending_trip.get("id") or "")
            pending_title = pending_titles.get(pending_id) or diary_title_for_trip(pending_trip, pending_photos)
            commented_count = sum(
                1 for photo in pending_photos if _conversation_has_child_words(_stored_photo_conversation(photo))
            )
            st.markdown(f"**{html.escape(str(pending_trip.get('trip_date') or ''))}　{html.escape(pending_title)}**　・ 写真 {len(pending_photos)}枚")
            st.caption(f"本人コメントあり：{commented_count} / {len(pending_photos)}枚")
            clicked_pending_pid = render_pending_thumbnail_grid(
                pending_id,
                pending_photos,
                trip=pending_trip,
            )
            if clicked_pending_pid:
                pending_state = reflection_state(pending_id, pending_photos)
                st.session_state["_pending_diary_open_trip_id"] = pending_id
                if open_diary_photo_talk(pending_id, clicked_pending_pid, pending_state):
                    st.rerun()
            if st.button(
                "📖 この写真で日記を作る",
                type="primary",
                use_container_width=True,
                key=f"create_pending_diary_{pending_id}",
            ):
                try:
                    with st.spinner("写真と本人のコメントから日記を作って保存しています…"):
                        create_and_save_diary_from_photos(
                            pending_trip,
                            pending_photos,
                            requested_title=pending_title,
                            reason="diary_page_pending_button",
                        )
                    if st.session_state.get("active_trip_id") == pending_id:
                        st.session_state.active_trip_id = None
                    st.session_state.preferred_diary_trip_id = pending_id
                    st.session_state.pop(f"reflection_state_{pending_id}", None)
                    if st.session_state.get("_pending_diary_open_trip_id") == pending_id:
                        st.session_state.pop("_pending_diary_open_trip_id", None)
                    st.session_state["_diary_notice"] = "日記を作成して、そのまま保存しました。"
                    st.rerun()
                except Exception as exc:
                    st.error("日記を作成できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
            st.divider()

    diary_map = {
        str((row.get("diary") or {}).get("trip_id") or ""): row.get("diary") or {}
        for row in recent_rows
        if (row.get("diary") or {}).get("trip_id")
    }

    # A pending photo can be opened directly from the top grid without first creating a diary.
    pending_open_row = next(
        (
            row for row in pending_rows
            if str((row.get("trip") or {}).get("id") or "") == pending_open_id
        ),
        None,
    )

    if pending_open_row is not None:
        trip = pending_open_row.get("trip") or {}
        trip_id = str(trip.get("id") or pending_open_id)
        photos = pending_open_row.get("photos") or []
        existing = None
        if st.button(
            "← 日記一覧へ戻る",
            use_container_width=True,
            key=f"pending_diary_back_{trip_id}",
        ):
            st.session_state.pop("_pending_diary_open_trip_id", None)
            st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
            st.session_state.pop(f"reflection_state_{trip_id}", None)
            st.rerun()
    else:
        trips = [row.get("trip") or {} for row in recent_rows if (row.get("trip") or {}).get("id")]
        if not trips:
            if not pending_rows:
                st.info("まだ日記はありません。")
            return

        ids = [str(t["id"]) for t in trips]
        trip_map = {str(t["id"]): t for t in trips}
        label_map = {
            trip_id_value: f"{trip_map[trip_id_value].get('trip_date', '')}　"
            f"{diary_display_title(diary_map.get(trip_id_value), trip_map[trip_id_value], photos=None)}"
            for trip_id_value in ids
        }
        preferred = st.session_state.preferred_diary_trip_id
        default_index = ids.index(str(preferred)) if str(preferred) in ids else None
        selector_serial = int(st.session_state.get("_diary_selector_serial") or 0)
        trip_id = st.selectbox(
            "振り返る日",
            ids,
            index=default_index,
            placeholder="振り返る日を選んでください",
            format_func=lambda x: label_map.get(str(x), str(x)),
            key=f"diary_trip_selector_{selector_serial}",
        )
        if trip_id is None:
            st.caption("振り返る日を選ぶと、そのぶらり旅の日記と写真を表示します。")
            return

        trip_id = str(trip_id)
        trip = trip_map[trip_id]
        # Do not fetch any saved-diary photos until a specific trip is selected. This
        # keeps the initial diary page substantially lighter on mobile connections.
        photos = list_trip_photos(trip_id)
        existing = diary_map.get(trip_id)

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
        existing_meta = existing.get("ai_meta") or {}
        if photos and st.button(
            "AIにまとめてもらう",
            use_container_width=True,
            key=f"ai_trip_summary_{trip_id}",
        ):
            try:
                with st.spinner("写真とコメントを見て、このぶらり旅をまとめています…"):
                    summary_result = summarize_burari_from_photos(trip, photos)
                    save_burari_ai_summary(trip_id, summary_result)
                st.session_state["_diary_notice"] = "写真とコメントからAIのまとめを更新しました。"
                st.rerun()
            except Exception as exc:
                st.error("AIのまとめを作れませんでした。もう一度試してください。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        render_burari_trip_summary(existing_meta)
        render_diary_reflection_summary(existing_meta)
        render_summary_feedback_controls(existing_meta, trip_id, "saved")
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
    if (not in_talk_mode) and (all_done or bool(state.get("draft"))):
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
                    # '日記をつくる' means create AND persist. No second save step is required.
                    saved = save_diary(
                        trip_id,
                        state["draft_title"],
                        state["draft"],
                        state.get("raw_conversation", {}),
                        state.get("draft_meta", {}),
                    )
                    state["draft_title"] = diary_display_title(saved, trip, photos=photos)
                    state["draft_saved"] = True
                    st.session_state["_diary_notice"] = "日記を作成して、そのまま保存しました。"
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
        if photos and st.button(
            "AIにまとめてもらう",
            use_container_width=True,
            key=f"ai_trip_summary_draft_{trip_id}",
        ):
            try:
                with st.spinner("写真とコメントを見て、このぶらり旅をまとめています…"):
                    summary_result = summarize_burari_from_photos(trip, photos)
                draft_meta = state.setdefault("draft_meta", {})
                _clear_summary_feedback_fields(draft_meta, clear_history=False)
                draft_meta["trip_summary"] = str(summary_result.get("trip_summary") or "").strip()
                draft_meta["reflection_summary"] = str(summary_result.get("reflection_summary") or "").strip()
                draft_meta["photo_comment_summary_updated_at"] = now_jst().isoformat()
                points = list(summary_result.get("child_points") or [])[:3]
                if points:
                    draft_meta["child_points"] = points
                if get_diary_for_trip(trip_id):
                    saved_meta = save_burari_ai_summary(trip_id, summary_result)
                    state["draft_meta"] = saved_meta
                st.rerun()
            except Exception as exc:
                st.error("AIのまとめを作れませんでした。もう一度試してください。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        persisted_diary = get_diary_for_trip(trip_id)
        if persisted_diary:
            persisted_meta = persisted_diary.get("ai_meta") or {}
            if isinstance(persisted_meta, dict) and persisted_meta:
                state["draft_meta"] = persisted_meta
        render_burari_trip_summary(state.get("draft_meta") or {})
        render_diary_reflection_summary(state.get("draft_meta") or {})
        render_summary_feedback_controls(
            state.get("draft_meta") or {},
            trip_id,
            "draft",
            draft_state=None if persisted_diary else state,
        )
        if state.get("draft_audio"):
            st.audio(
                state["draft_audio"],
                format="audio/wav",
                autoplay=bool(state.get("draft_audio_pending")),
            )
            state["draft_audio_pending"] = False

        st.markdown("#### 直したいところはある？")
        st.caption("日記はすでに保存されています。直した内容も自動で保存します。")
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
                    save_diary(
                        trip_id,
                        state.get("draft_title") or fixed_title,
                        state["draft"],
                        state.get("raw_conversation", {}),
                        state.get("draft_meta", {}),
                    )
                    state["draft_saved"] = True
                    st.session_state[correction_digest_key] = digest
                    st.session_state["_diary_notice"] = "修正した日記を自動で保存しました。"
                    st.rerun()
                except Exception as exc:
                    st.error("修正を反映できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))

        st.success("この日記はすでに保存されています。")
        if st.button("日記を確認する", use_container_width=True, key=f"close_saved_diary_{trip_id}"):
            st.session_state.pop(f"reflection_state_{trip_id}", None)
            st.session_state.preferred_diary_trip_id = trip_id
            st.rerun()

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

    diary_photo_src = photo_display_url(photo)
    if diary_photo_src:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:.25rem 0 .45rem;">
              <img src="{html.escape(diary_photo_src, quote=True)}" alt="日記の写真" loading="lazy" decoding="async"
                   style="display:block;max-width:min(72vw,320px);max-height:34dvh;width:auto;height:auto;object-fit:contain;border-radius:14px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("写真のプレビューを表示できませんでした。会話は続けられます。")

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

        photo_ids = list(state.get("photo_ids") or [])
        current_index = photo_ids.index(pid) if pid in photo_ids else -1
        has_next_photo = 0 <= current_index < len(photo_ids) - 1

        if has_next_photo:
            if st.button(
                "次の写真にする",
                use_container_width=True,
                key=f"next_photo_after_talk_{trip_id}_{pid}",
            ):
                next_photo_id = photo_ids[current_index + 1]
                if open_diary_photo_talk(trip_id, next_photo_id, state):
                    st.rerun()

        has_child_evidence = any(
            _conversation_has_child_words(state.get("items", {}).get(state_pid, {}).get("conversation", []))
            for state_pid in photo_ids
        )
        if has_child_evidence and st.button(
            "これでAIにまとめてもらう",
            type="primary",
            use_container_width=True,
            key=f"finish_and_compose_diary_{trip_id}_{pid}",
        ):
            try:
                photo_states = []
                for state_pid in photo_ids:
                    state_item = state.get("items", {}).get(state_pid, {})
                    photo_states.append(
                        {
                            "photo_id": state_pid,
                            "conversation": state_item.get("conversation", []),
                            "signals": state_item.get("signals", {}),
                        }
                    )
                with st.spinner("ここまで話したことを日記にまとめています…"):
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
                saved = save_diary(
                    trip_id,
                    state["draft_title"],
                    state["draft"],
                    state.get("raw_conversation", {}),
                    state.get("draft_meta", {}),
                )
                state["draft_title"] = diary_display_title(saved, trip, photos=photos)
                state["draft_saved"] = True
                st.session_state.pop(talk_key, None)
                st.session_state["_diary_notice"] = "ここまで話した内容で日記を作成して保存しました。"
                st.rerun()
            except Exception as exc:
                st.error("日記をまとめられませんでした。もう一度試してください。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

        render_diary_delete_controls(trip_id, photos, current_photo_id=pid, show_photo_navigation=False)
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
                        image_bytes = download_photo(photo["storage_path"])
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
                    image_bytes = download_photo(photo["storage_path"])
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
        render_burari_trip_summary(meta)
        render_diary_reflection_summary(meta)
        render_summary_feedback_controls(meta, trip_id, "history")
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
        # Saved diaries already carry their final title. Avoid one photo query per row.
        daily_title = diary_display_title(diary, trip, photos=None)
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
    # st.tabs executes both tab bodies on every rerun. A radio keeps the same two
    # choices but loads only the page the user is actually viewing.
    review_view = st.radio(
        "振り返りの表示",
        ["📚 これまでの日記", "🔍 今月の発見"],
        horizontal=True,
        label_visibility="collapsed",
        key="review_view_selector",
    )
    if review_view == "📚 これまでの日記":
        page_history(embedded=True)
    else:
        page_monthly(embedded=True)



def page_settings():
    # Settings already has the shared full-width Home button at the bottom, so do
    # not render the top back/Home control here. This also avoids the mobile top
    # toolbar overlap that can make the upper control hard to tap.
    st.subheader("⚙️ 設定")
    st.caption("家族と個人アカウント、旅の設定を管理します。")

    settings_notice = st.session_state.pop("_settings_notice", None)
    if settings_notice:
        st.success(settings_notice)

    st.markdown("#### ログイン情報を確認")
    st.write(f"家族ID：`{current_family_key()}`")
    st.write(f"個人ID：`{current_member_key()}`")
    st.caption(
        "あいことばは安全のため元の文字列を保存していないので、画面に表示することはできません。"
        "思い当たるあいことばが合っているか確認するか、ログイン中に新しいあいことばへ再設定できます。"
    )

    check_pin = st.text_input(
        "確認したいあいことば",
        type="password",
        key="settings_check_current_member_pin",
        placeholder="思い当たるあいことばを入力",
    )
    if st.button(
        "このあいことばで合っているか確認",
        use_container_width=True,
        key="settings_verify_current_member_pin",
    ):
        if verify_current_member_pin(check_pin):
            st.success("このあいことばで合っています。")
        else:
            st.error("このあいことばではありません。")

    with st.expander("あいことばを変更・再設定"):
        st.caption("現在のあいことばを忘れていても、ログイン中であれば新しく設定できます。")
        new_pin = st.text_input(
            "新しいあいことば",
            type="password",
            key="settings_new_member_pin",
        )
        new_pin_confirm = st.text_input(
            "新しいあいことば（確認）",
            type="password",
            key="settings_new_member_pin_confirm",
        )
        if st.button(
            "新しいあいことばに変更",
            use_container_width=True,
            key="settings_change_member_pin",
        ):
            try:
                if new_pin != new_pin_confirm:
                    raise ValueError("確認用のあいことばが一致していません。")
                update_current_member_pin(new_pin)
                st.session_state.pop("settings_check_current_member_pin", None)
                st.session_state.pop("settings_new_member_pin", None)
                st.session_state.pop("settings_new_member_pin_confirm", None)
                st.session_state["_settings_notice"] = "あいことばを変更しました。"
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    st.markdown("#### 個人アカウント")
    st.write(
        f"現在：**{current_member_name()}**　（個人ID：`{current_member_key()}`）  "
        f"／ 家族：**{current_family_name()}**（`{current_family_key()}`）"
    )
    st.caption(
        "ログイン、写真、日記、月ごとの振り返り、AIまとめのGood/Bad学習は個人アカウントごとに分かれます。"
        "同じ家族の別の個人アカウントから、この個人の写真や日記は表示されません。"
    )
    with st.expander("現在の個人名を変更"):
        renamed_member = st.text_input(
            "個人名",
            value=current_member_name(),
            key="rename_current_member_name",
        )
        if st.button("個人名を保存", use_container_width=True, key="save_current_member_name"):
            try:
                saved_name = update_current_member_name(renamed_member)
                st.session_state["_settings_notice"] = f"個人名を『{saved_name}』に変更しました。"
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander("この家族に個人アカウントを追加"):
        new_member_name = st.text_input("個人名", placeholder="例：大嘉、父、母", key="new_member_display_name")
        new_member_key = st.text_input("個人ID", placeholder="例：taiga", key="new_member_key")
        new_member_pin = st.text_input("個人のあいことば", type="password", key="new_member_pin")
        if st.button("個人アカウントを作成", use_container_width=True, key="create_member_account_button"):
            try:
                created = create_member_account(new_member_key, new_member_name, new_member_pin)
                st.session_state["_settings_notice"] = (
                    f"個人アカウント『{created['display_name']}』を作成しました。"
                    "切り替えるときは下のログアウトを押してください。"
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    members = list_family_members()
    with st.expander("この家族の個人アカウント"):
        for member in members:
            marker = " ← 現在" if str(member.get("member_key")) == current_member_key() else ""
            st.write(
                f"・{member.get('display_name') or member.get('member_key')}"
                f"（個人ID: {member.get('member_key')}）{marker}"
            )

    if st.button("ログアウトして個人アカウントを切り替える", use_container_width=True, key="personal_account_logout"):
        logout_family_account()
        st.rerun()

    st.divider()
    st.markdown("#### 家族アカウント")
    st.write(f"家族：**{current_family_name()}**　（家族ID：`{current_family_key()}`）")
    st.caption("家族アカウントは個人アカウントをまとめる入れ物です。写真や日記の所有者は個人アカウントです。")
    with st.expander("現在の家族名を変更"):
        renamed_family = st.text_input(
            "家族名",
            value=current_family_name(),
            key="rename_current_family_name",
        )
        if st.button("家族名を保存", use_container_width=True, key="save_current_family_name"):
            try:
                saved_name = update_current_family_name(renamed_family)
                st.session_state["_settings_notice"] = f"家族名を『{saved_name}』に変更しました。"
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander("新しい家族アカウントを作る"):
        st.caption("新しい家族には、最初の個人アカウントも同時に作ります。")
        new_family_name = st.text_input("家族名", placeholder="例：原田家", key="new_family_display_name")
        new_family_key = st.text_input("家族ID", placeholder="例：harada2", key="new_family_key")
        first_member_name = st.text_input("最初の個人名", placeholder="例：父", key="new_family_first_member_name")
        first_member_key = st.text_input("最初の個人ID", placeholder="例：father", key="new_family_first_member_key")
        first_member_pin = st.text_input("最初の個人のあいことば", type="password", key="new_family_first_member_pin")
        if st.button("家族＋個人アカウントを作成", use_container_width=True, key="create_family_account_button"):
            try:
                created = create_family_account(
                    new_family_key,
                    new_family_name,
                    first_member_key,
                    first_member_name,
                    first_member_pin,
                )
                st.session_state["_settings_notice"] = (
                    f"家族『{created['display_name']}』と最初の個人アカウントを作成しました。"
                    "切り替えるときはログアウトしてください。"
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.divider()
    active = get_active_trip_fast(max_age_seconds=20) if st.session_state.active_trip_id else None
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
    st.markdown("#### AIまとめの調整")
    feedback_status = get_summary_feedback_status()
    good_count = int(feedback_status.get("good_count") or 0)
    bad_count = int(feedback_status.get("bad_count") or 0)
    if good_count == 0 and bad_count == 0:
        st.write("現在は**標準のまとめ方**です。Good/Badの影響はありません。")
    else:
        st.write(f"これまでの評価：**Good {good_count}件** ／ **Bad {bad_count}件**")
        st.caption(
            "次回のAIまとめでは、この個人アカウントの直近Good最大3件を少しだけ参考にし、"
            "Bad最大2件に近い書き方を少しだけ避けます。写真と本人コメント、基本ルールを常に優先します。"
        )
        with st.expander("現在参考にしているGood / Badを見る"):
            good_examples = feedback_status.get("good_examples") or []
            bad_examples = feedback_status.get("bad_examples") or []
            if good_examples:
                st.markdown("**Goodとして参考にしている例**")
                for idx, item in enumerate(good_examples, start=1):
                    value = _feedback_example_text(item, max_chars=360)
                    if value:
                        st.write(f"{idx}. {value}")
            if bad_examples:
                st.markdown("**Badとして弱く避けている例**")
                for idx, item in enumerate(bad_examples, start=1):
                    value = _feedback_example_text(item, max_chars=360)
                    if value:
                        st.write(f"{idx}. {value}")
    if st.button(
        "Good/Bad反映前の標準に戻す",
        use_container_width=True,
        key="settings_reset_summary_feedback",
    ):
        confirm_summary_feedback_reset_dialog()

    st.divider()
    st.markdown("#### 自動ログイン")
    st.caption("この端末では、一度個人アカウントへログインすると次回から同じ個人で自動ログインします。")
    if st.button("この端末の自動ログインを解除", use_container_width=True, key="settings_clear_auto_login"):
        clear_browser_auto_login()
        st.success("この端末の自動ログインを解除しました。次回は個人IDとあいことばが必要です。")

    st.divider()
    st.markdown("#### カメラについて")
    st.write(
        "『カメラで撮る』画面では、ブラウザのライブカメラを直接開いて撮影します。"
        "初回だけ、このサイトへのカメラ使用を『許可』してください。"
    )
    st.caption(
        "初回はカメラとは別に位置情報の許可も求められます。位置情報がオフ・拒否・取得不能の場合は、"
        "ホームの地名表示（未登録なら『地名：登録なし（自動取得）』）を押して入力した内容を写真の場所として使います。"
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
# Daily rollover and old-title repair can touch many rows. They are diary/history
# maintenance, not startup requirements, so home/camera opens no longer wait for them.
restore_recent_camera_session()

rollover_notice = st.session_state.pop("_rollover_notice", None)
if rollover_notice:
    st.success(rollover_notice)
rollover_warning = st.session_state.pop("_rollover_warning", None)
if rollover_warning:
    st.warning(rollover_warning)
    rollover_detail = st.session_state.pop("_rollover_warning_detail", None)
    if rollover_detail:
        with st.expander("保護者向け詳細"):
            st.code(str(rollover_detail))

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


# Update browser history after the visible page has been queued, so an invisible
# bridge never sits ahead of Home/Camera on the perceived critical path.
sync_browser_history()

# Camera already has its Home button directly under the camera form. For the
# other major pages, keep a consistent Home route at the absolute bottom even
# when the page body returned early from one of its internal flows.
if page in {"diary", "review", "settings"}:
    render_global_bottom_home_button(page)
