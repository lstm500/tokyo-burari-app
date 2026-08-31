import base64
import hashlib
import hmac
import html
import io
import json
import math
import os
import random
import shutil
import subprocess
import tempfile
import time
import uuid
import wave
import zipfile
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
from array import array
from urllib.parse import urlencode, urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

APP_BUILD = "v145"

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
      .home-account {
        margin: 0 0 .38rem;
        font-size: .76rem;
        line-height: 1.25;
        opacity: .62;
      }
      .home-hero {
        margin: .10rem 0 .78rem;
        padding: 1rem 1.08rem .90rem;
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
        width: 84px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-right: -.18rem;
      }
      .home-hero-train img {
        display: block;
        width: 84px;
        height: 70px;
        object-fit: contain;
        filter: drop-shadow(0 5px 8px rgba(33, 75, 49, .08));
      }
      .home-eyebrow {
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .12em;
        opacity: .58;
        margin-bottom: .32rem;
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
        margin-top: .40rem;
        font-size: .92rem;
        line-height: 1.55;
        opacity: .70;
      }
      .home-status {
        display: flex;
        align-items: center;
        gap: .55rem;
        flex-wrap: wrap;
        margin: -.12rem 0 .80rem;
        padding: .56rem .70rem;
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
        margin: .12rem 0 .36rem;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .08em;
        opacity: .55;
      }
      .st-key-home_primary [data-testid="stHorizontalBlock"],
      .st-key-home_secondary [data-testid="stHorizontalBlock"] {
        gap: .56rem;
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
        height: 4.90rem !important;
        min-height: 4.90rem !important;
        max-height: 4.90rem !important;
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
        height: 4.35rem !important;
        min-height: 4.35rem !important;
        max-height: 4.35rem !important;
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
        margin-top: .30rem;
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
        margin-top: .72rem;
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
          padding-left: .68rem;
          padding-right: .68rem;
          /* Keep the first app row below Streamlit's mobile toolbar.
             The extra safe-area term also covers phones with a display cutout. */
          padding-top: calc(3.35rem + env(safe-area-inset-top, 0px)) !important;
        }
        .home-account {
          margin-bottom: .26rem;
          font-size: .70rem;
          line-height: 1.18;
        }
        .home-hero {
          margin-bottom: .58rem;
          padding: .76rem .84rem .70rem;
          border-radius: 19px;
        }
        .home-hero-inner { gap: .34rem; }
        .home-hero-train { width: 66px; height: 56px; margin-right: -.10rem; }
        .home-hero-train img { width: 66px; height: 56px; }
        .home-eyebrow {
          font-size: .69rem;
          margin-bottom: .20rem;
        }
        .home-title {
          font-size: clamp(1.72rem, 7.4vw, 1.90rem);
          letter-spacing: .01em;
          line-height: 1.04;
        }
        .home-tagline {
          margin-top: .28rem;
          font-size: .82rem;
          line-height: 1.38;
        }
        .home-status {
          gap: .40rem;
          margin: -.05rem 0 .58rem;
          padding: .46rem .58rem;
          border-radius: 14px;
          font-size: .80rem;
          line-height: 1.25;
        }
        .home-status-badge {
          min-height: 1.48rem;
          padding: .10rem .40rem;
          font-size: .70rem;
        }
        .home-section-label {
          margin: .08rem 0 .26rem;
          font-size: .72rem;
        }
        .st-key-home_primary [data-testid="stHorizontalBlock"],
        .st-key-home_secondary [data-testid="stHorizontalBlock"] {
          gap: .42rem;
        }
        .st-key-home_primary div.stButton > button {
          height: 4.42rem !important;
          min-height: 4.42rem !important;
          max-height: 4.42rem !important;
          border-radius: 19px !important;
          font-size: 1.10rem !important;
          line-height: 1.10 !important;
          padding: .42rem .52rem !important;
          column-gap: .34rem !important;
        }
        .st-key-home_secondary div.stButton > button {
          height: 3.92rem !important;
          min-height: 3.92rem !important;
          max-height: 3.92rem !important;
          border-radius: 17px !important;
          font-size: 1.00rem !important;
          line-height: 1.08 !important;
          padding: .38rem .46rem !important;
          column-gap: .28rem !important;
        }
        .st-key-home_destination {
          margin-top: .22rem;
        }
        .st-key-home_destination div.stButton > button {
          min-height: 2.28rem !important;
          font-size: .76rem !important;
          padding: .40rem .52rem !important;
        }
        .home-footer-note {
          margin-top: .55rem;
          font-size: .72rem;
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
try:
    VIDEO_STORAGE_QUOTA_MB = max(0, int(str(secret("VIDEO_STORAGE_QUOTA_MB", "0") or "0").strip()))
except Exception:
    VIDEO_STORAGE_QUOTA_MB = 0

VIDEO_MAX_SECONDS = 15
VIDEO_PROCESSING_MAX_SECONDS = 20
# v142 quality-first source recording. Never lower source quality merely to satisfy
# an app-side file cap. 18 MiB fits a 15-second 1080p recording at up to ~8 Mbps
# plus audio/container overhead while remaining below the recommended 20 MiB bucket cap.
VIDEO_MAX_BYTES = 18 * 1024 * 1024
VIDEO_AI_MAX_SELECTIONS = 9
VIDEO_AI_SAMPLE_INTERVAL_MS = 100
VIDEO_AI_MAX_CANDIDATES = 150
# Every 0.1-second frame is evaluated by AI. Batching is only an API payload
# boundary; it is not a non-AI quality filter.
VIDEO_AI_BATCH_SIZE = 5
VIDEO_AI_BATCH_KEEP = 1
VIDEO_AI_BATCH_WORKERS = 5
# Background AI must never remain in "processing" indefinitely.
# One provider call is bounded, and a stale Streamlit worker can be relaunched.
VIDEO_AI_REQUEST_TIMEOUT_SECONDS = 20
VIDEO_AI_STALE_SECONDS = 240

# Best-effort post-save video stabilization. The original recording is never
# overwritten. A lightly stabilized MP4 proxy is created when ffmpeg/deshake is
# available; playback and AI frame extraction prefer that proxy. Any failure falls
# back to the original without blocking video preservation or Good Moments.
VIDEO_STABILIZATION_VERSION = "v135_deshake_light"
VIDEO_STABILIZATION_TIMEOUT_SECONDS = 90
VIDEO_STABILIZATION_RX = 16
VIDEO_STABILIZATION_RY = 16

TRIP_TABLE = "burari_trips"
PHOTO_TABLE = "burari_photos"
DIARY_TABLE = "burari_diaries"
MONTHLY_TABLE = "burari_monthly_reviews"
MUSIC_LIBRARY_REVIEW_DATE = "1900-01-01"
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
    <button id="live-camera-start" class="camera-menu-button" type="button">📷 写真を撮る</button>
    <button id="live-video-start" class="camera-menu-button video-menu-button" type="button">🎥 動画を撮る</button>
    <input id="gallery-photo-input" class="gallery-photo-input" type="file" accept="image/*" />
    <label class="camera-menu-button gallery-button" for="gallery-photo-input">🖼 すでに撮った写真から選ぶ</label>
  </div>

  <video id="live-camera-video" class="live-camera-video" playsinline autoplay muted hidden></video>

  <div id="camera-recording-status" class="camera-recording-status" hidden>● 録画中 0:00 / 0:30</div>

  <div id="camera-active-actions" class="camera-active-actions" hidden>
    <button id="live-camera-shoot" class="camera-shoot-button" type="button">● 撮影する</button>
    <button id="live-camera-mode-switch" class="camera-mode-switch-button" type="button">🎥 動画へ</button>
    <button id="live-camera-stop" class="camera-sub-button" type="button">閉じる</button>
  </div>

  <div id="camera-review" class="camera-review" hidden>
    <div class="camera-review-actions">
      <button id="camera-review-save" class="camera-save-button" type="button">この写真を残す</button>
      <button id="camera-review-retry" class="camera-retry-button" type="button">撮りなおす／選びなおす</button>
    </div>
    <button id="camera-review-find-moments" class="camera-find-button" type="button" hidden>✨ いい瞬間を探す</button>
    <div id="camera-review-build" class="camera-review-build" hidden>camera v105</div>
    <img id="camera-review-image" class="camera-review-image" alt="撮影した写真の確認" />
    <video id="camera-review-video" class="camera-review-video" playsinline controls hidden></video>
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
.camera-review-image[hidden],
.camera-review-video[hidden],
.camera-find-button[hidden],
.camera-review-build[hidden],
.camera-recording-status[hidden],
.camera-status[hidden] {
  display: none !important;
}
.camera-menu {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
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
.camera-mode-switch-button,
.camera-sub-button,
.camera-save-button,
.camera-retry-button,
.camera-find-button {
  width: 100%;
  min-height: 68px;
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
.video-menu-button {
  border-color: #7c3aed;
  background: rgba(124, 58, 237, .10);
}
.gallery-button {
  border-color: rgba(128,128,128,.28);
  background: transparent;
}
.live-camera-video,
.camera-review-image,
.camera-review-video {
  width: 100%;
  max-height: 58dvh;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  box-sizing: border-box;
  border-radius: 16px;
  background: #000;
  margin: 0;
}
.camera-review-video { object-fit: contain; }
.camera-active-actions,
.camera-review-actions {
  display: grid;
  gap: 8px;
}
.camera-active-actions { grid-template-columns: 2.2fr 1.2fr .8fr; }
.camera-review-actions { grid-template-columns: 3fr 1fr; }
.camera-active-actions { margin: 8px 0 0 0; }
.camera-review-actions { margin: 0 0 8px 0; }
.camera-find-button {
  margin: 0 0 8px 0;
  border: 2px solid #7c3aed;
  background: rgba(124, 58, 237, .10);
  color: var(--st-text-color);
}
.camera-find-button:hover,
.camera-find-button:focus-visible {
  background: rgba(124, 58, 237, .16);
}
.camera-review-build {
  margin: -2px 0 8px 0;
  text-align: right;
  font-size: 10px;
  line-height: 1;
  opacity: .38;
  user-select: none;
}
.camera-find-button:disabled {
  opacity: .62;
  cursor: default;
}
.camera-recording-status {
  margin: 8px 0 0;
  padding: 8px 10px;
  text-align: center;
  border-radius: 12px;
  background: rgba(220, 38, 38, .11);
  border: 1px solid rgba(220, 38, 38, .25);
  color: #b91c1c;
  font-size: 14px;
  font-weight: 800;
}
.camera-shoot-button {
  border: 2px solid var(--st-primary-color);
  background: var(--st-primary-color);
  color: white;
}
.camera-shoot-button.recording {
  border-color: #b91c1c;
  background: #dc2626;
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
.camera-mode-switch-button,
.camera-sub-button,
.camera-retry-button {
  border: 1px solid rgba(128,128,128,.28);
  background: transparent;
  color: var(--st-text-color);
}
.camera-review { width: 100%; margin: 0; }
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
    min-height: 62px;
    font-size: 16px;
  }
  .camera-active-actions { grid-template-columns: 2fr 1.1fr .8fr; }
  .camera-review-actions { grid-template-columns: 3fr 1fr; }
  .camera-shoot-button,
  .camera-mode-switch-button,
  .camera-sub-button,
  .camera-save-button,
  .camera-retry-button {
    min-height: 56px;
    font-size: 14px;
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
  const videoStartButton = parentElement.querySelector('#live-video-start');
  const galleryInput = parentElement.querySelector('#gallery-photo-input');
  const activeActions = parentElement.querySelector('#camera-active-actions');
  const shootButton = parentElement.querySelector('#live-camera-shoot');
  const modeSwitchButton = parentElement.querySelector('#live-camera-mode-switch');
  const stopButton = parentElement.querySelector('#live-camera-stop');
  const recordingStatus = parentElement.querySelector('#camera-recording-status');
  const review = parentElement.querySelector('#camera-review');
  const reviewImage = parentElement.querySelector('#camera-review-image');
  const reviewVideo = parentElement.querySelector('#camera-review-video');
  const reviewSave = parentElement.querySelector('#camera-review-save');
  const reviewRetry = parentElement.querySelector('#camera-review-retry');
  const reviewFindMoments = parentElement.querySelector('#camera-review-find-moments');
  const reviewBuild = parentElement.querySelector('#camera-review-build');
  const status = parentElement.querySelector('#live-camera-status');

  const VIDEO_MAX_SECONDS = 15;
  // v107: the browser uploads the video blob straight to a short-lived Supabase
  // signed upload URL. The multi-megabyte video is never serialized through a
  // Streamlit component trigger value.
  const videoUploadSignedUrl = String(data?.video_upload_signed_url || '');
  const videoUploadStoragePath = String(data?.video_upload_storage_path || '');
  const videoUploadToken = String(data?.video_upload_token || '');
  const videoTusEndpoint = String(data?.video_tus_endpoint || '');
  const videoUploadBucket = String(data?.video_upload_bucket || '');
  const candidateSheetSignedUrl = String(data?.video_candidate_sheet_signed_url || '');
  const candidateSheetStoragePath = String(data?.video_candidate_sheet_storage_path || '');
  const videoUnavailableReason = String(data?.video_unavailable_reason || '');
  const videoAllowed = data?.video_allowed !== false && Boolean(videoUploadSignedUrl && videoUploadStoragePath);
  const videoCapacityMessage = String(
    data?.video_capacity_message || '動画の保存容量または保存先を確認できないため、最大15秒の動画を撮影できません。'
  );
  const unavailableSuffix = videoUnavailableReason === 'quota'
    ? '容量不足'
    : (videoUnavailableReason === 'storage_setup' ? '保存先エラー' : '利用不可');
  if (!videoAllowed && videoStartButton) {
    videoStartButton.disabled = true;
    videoStartButton.textContent = `🎥 動画を撮る（${unavailableSuffix}）`;
    videoStartButton.title = videoCapacityMessage;
  }
  let stream = null;
  let cameraMode = 'photo';
  let pendingMedia = null;
  let pendingVideoBlob = null;
  let reviewVideoUrl = '';
  let mediaRecorder = null;
  let recordedChunks = [];
  let recordingStartedAt = 0;
  let recordingCapturedAt = '';
  let recordingLocationPromise = null;
  let recordingTimer = null;
  let recordingMaxTimer = null;
  let recordingCandidateTimer = null;
  let recordingCandidateBusy = false;
  let recordingCandidateFrames = [];
  let recordingCancelled = false;
  // Good-moments search is a separate review action. The button remains hidden
  // briefly after recording stops, so the stop gesture cannot fall through to it.
  let videoReviewGeneration = 0;
  let goodMomentsRevealTimer = null;

  const setStatus = (message) => {
    if (!status) return;
    status.textContent = message || '';
    status.hidden = !message;
  };

  const clearRecordingTimers = () => {
    if (recordingTimer) {
      clearInterval(recordingTimer);
      recordingTimer = null;
    }
    if (recordingMaxTimer) {
      clearTimeout(recordingMaxTimer);
      recordingMaxTimer = null;
    }
    if (recordingCandidateTimer) {
      clearInterval(recordingCandidateTimer);
      recordingCandidateTimer = null;
    }
  };

  const setRecordingUi = (recording) => {
    if (recordingStatus) recordingStatus.hidden = !recording;
    if (!shootButton) return;
    if (recording) {
      shootButton.textContent = '■ 録画を止める';
      shootButton.classList.add('recording');
    } else {
      shootButton.classList.remove('recording');
      shootButton.textContent = cameraMode === 'video' ? '● 録画を開始' : '● 写真を撮る';
    }
    if (modeSwitchButton) {
      modeSwitchButton.disabled = Boolean(recording) || (cameraMode !== 'video' && !videoAllowed);
      modeSwitchButton.textContent = cameraMode === 'video'
        ? '📷 写真へ'
        : (videoAllowed ? '🎥 動画へ' : `🎥 動画へ（${unavailableSuffix}）`);
      modeSwitchButton.title = (!videoAllowed && cameraMode !== 'video') ? videoCapacityMessage : '';
    }
  };

  const updateRecordingClock = () => {
    if (!recordingStatus || !recordingStartedAt) return;
    const elapsed = Math.min(VIDEO_MAX_SECONDS, Math.max(0, Math.floor((Date.now() - recordingStartedAt) / 1000)));
    const mm = Math.floor(elapsed / 60);
    const ss = String(elapsed % 60).padStart(2, '0');
    recordingStatus.textContent = `● 録画中 ${mm}:${ss} / 0:${String(VIDEO_MAX_SECONDS).padStart(2, '0')}`;
  };

  const clearGoodMomentsRevealTimer = () => {
    if (goodMomentsRevealTimer) {
      clearTimeout(goodMomentsRevealTimer);
      goodMomentsRevealTimer = null;
    }
  };

  const disarmGoodMomentsButton = () => {
    clearGoodMomentsRevealTimer();
    if (!reviewFindMoments) return;
    reviewFindMoments.dataset.armedGeneration = '';
    reviewFindMoments.hidden = true;
    reviewFindMoments.disabled = false;
    reviewFindMoments.textContent = '\u2728 \u3044\u3044\u77ac\u9593\u3092\u63a2\u3059';
  };

  const revokeReviewVideoUrl = () => {
    if (reviewVideoUrl) {
      try { URL.revokeObjectURL(reviewVideoUrl); } catch (_) {}
      reviewVideoUrl = '';
    }
  };

  const hideReview = () => {
    disarmGoodMomentsButton();
    if (review) review.hidden = true;
    if (reviewImage) {
      reviewImage.hidden = true;
      reviewImage.removeAttribute('src');
    }
    if (reviewVideo) {
      try { reviewVideo.pause(); } catch (_) {}
      reviewVideo.hidden = true;
      reviewVideo.removeAttribute('src');
      try { reviewVideo.load(); } catch (_) {}
    }
    revokeReviewVideoUrl();
    if (reviewFindMoments) {
      reviewFindMoments.dataset.armedGeneration = '';
      reviewFindMoments.hidden = true;
      reviewFindMoments.disabled = false;
      reviewFindMoments.textContent = '✨ いい瞬間を探す';
    }
    if (reviewBuild) reviewBuild.hidden = true;
  };

  const showMenu = () => {
    if (menu) menu.hidden = false;
    if (activeActions) activeActions.hidden = true;
    if (video) video.hidden = true;
    setRecordingUi(false);
    hideReview();
  };

  const showCameraActions = () => {
    if (menu) menu.hidden = true;
    if (activeActions) activeActions.hidden = false;
    if (video) video.hidden = false;
    hideReview();
    setRecordingUi(false);
  };

  const showPhotoReview = (dataUrl) => {
    if (menu) menu.hidden = true;
    if (activeActions) activeActions.hidden = true;
    if (video) video.hidden = true;
    hideReview();
    if (reviewImage) {
      reviewImage.src = dataUrl;
      reviewImage.hidden = false;
    }
    reviewSave.textContent = 'この写真を残す';
    reviewRetry.textContent = '撮りなおす／選びなおす';
    if (reviewFindMoments) reviewFindMoments.hidden = true;
    if (reviewBuild) reviewBuild.hidden = true;
    if (review) review.hidden = false;
  };

  const showVideoReview = (blob) => {
    if (menu) menu.hidden = true;
    if (activeActions) activeActions.hidden = true;
    if (video) video.hidden = true;
    hideReview();
    reviewVideoUrl = URL.createObjectURL(blob);
    if (reviewVideo) {
      reviewVideo.src = reviewVideoUrl;
      reviewVideo.hidden = false;
      reviewVideo.currentTime = 0;
    }
    reviewSave.textContent = 'この動画を残す';
    reviewRetry.textContent = '撮りなおす';
    videoReviewGeneration += 1;
    const reviewGeneration = videoReviewGeneration;
    disarmGoodMomentsButton();
    if (reviewBuild) reviewBuild.hidden = false;
    if (review) review.hidden = false;
    setStatus('');

    // Important: do not extract frames here. Only reveal and arm the button
    // after the recording-stop interaction has fully ended.
    goodMomentsRevealTimer = setTimeout(() => {
      goodMomentsRevealTimer = null;
      if (reviewGeneration !== videoReviewGeneration) return;
      if (!review || review.hidden || !reviewFindMoments) return;
      if (!pendingMedia || pendingMedia.kind !== 'video' || !pendingVideoBlob) return;
      reviewFindMoments.dataset.armedGeneration = String(reviewGeneration);
      reviewFindMoments.hidden = false;
      reviewFindMoments.disabled = false;
      reviewFindMoments.textContent = '\u2728 \u3044\u3044\u77ac\u9593\u3092\u63a2\u3059';
    }, 700);
  };

  const stopActiveRecorderSilently = () => {
    clearRecordingTimers();
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      recordingCancelled = true;
      try { mediaRecorder.stop(); } catch (_) {}
    }
    mediaRecorder = null;
    recordedChunks = [];
    recordingStartedAt = 0;
    setRecordingUi(false);
  };

  const stopStream = () => {
    stopActiveRecorderSilently();
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (video) {
      video.pause();
      video.srcObject = null;
      video.hidden = true;
    }
    pendingMedia = null;
    pendingVideoBlob = null;
    showMenu();
  };

  const errorMessage = (err, mode = cameraMode) => {
    const name = (err && err.name) ? err.name : '';
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
      return mode === 'video'
        ? 'カメラまたはマイクが許可されていません。ブラウザのサイト設定でカメラとマイクを「許可」にしてください。'
        : 'カメラが許可されていません。ブラウザのサイト設定でカメラを「許可」にして、このページを再読み込みしてください。';
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') return '利用できるカメラが見つかりませんでした。';
    if (name === 'NotReadableError' || name === 'TrackStartError') return 'カメラを開けませんでした。ほかのアプリがカメラを使っていないか確認してください。';
    if (name === 'SecurityError') return 'ブラウザのセキュリティ設定でカメラがブロックされています。';
    return 'カメラを開けませんでした。ブラウザのカメラ・マイク権限を確認してください。';
  };

  const startCamera = async (mode = 'photo') => {
    const requestedMode = mode === 'video' ? 'video' : 'photo';
    if (requestedMode === 'video' && !videoAllowed) {
      setStatus(videoCapacityMessage);
      return;
    }
    stopStream();
    cameraMode = requestedMode;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const message = 'このブラウザでは直接カメラを開けません。ChromeまたはSafariの最新版で開いてください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'Unsupported', message });
      return;
    }
    if (cameraMode === 'video' && typeof MediaRecorder === 'undefined') {
      const message = 'このブラウザでは動画録画に対応していません。ChromeまたはSafariの最新版で開いてください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'MediaRecorderUnsupported', message });
      return;
    }

    setStatus(cameraMode === 'video' ? 'カメラとマイクの使用を許可してください…' : 'カメラの使用を許可してください…');
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: cameraMode === 'video' ? {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } : false,
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30, max: 30 },
          aspectRatio: { ideal: 1.7777777778 }
        }
      });
      video.srcObject = stream;
      await video.play();
      // Prefer the phone/browser's own stabilization when it exposes a compatible
      // media-track constraint. Unknown constraints are never forced, so devices
      // without this capability continue normally.
      if (cameraMode === 'video') {
        try {
          const supported = (navigator.mediaDevices && navigator.mediaDevices.getSupportedConstraints)
            ? navigator.mediaDevices.getSupportedConstraints()
            : {};
          const track = stream.getVideoTracks && stream.getVideoTracks()[0];
          if (track && track.applyConstraints && supported && supported.imageStabilization) {
            await track.applyConstraints({ advanced: [{ imageStabilization: true }] });
          }
        } catch (stabilizationErr) {
          console.warn('camera hardware stabilization unavailable', stabilizationErr);
        }
      }
      shootButton.disabled = false;
      shootButton.textContent = cameraMode === 'video' ? '● 録画を開始' : '● 写真を撮る';
      showCameraActions();
      try {
        const openedAt = Date.now();
        localStorage.setItem('tokyo_burari_last_camera_open_v1', String(openedAt));
        localStorage.setItem('tokyo_burari_last_camera_mode_v1', cameraMode === 'video' ? 'video' : 'photo');
      } catch (_) {}
      setStatus(cameraMode === 'video' ? '動画は最大15秒です。音声も一緒に記録します。' : '');
    } catch (err) {
      console.error(err);
      stopStream();
      const message = errorMessage(err, cameraMode);
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

  const xhrUpload = (method, url, headers, body, timeoutMs, progressHandler) => new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.timeout = Math.max(1000, Number(timeoutMs || 120000));
    Object.entries(headers || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && String(value) !== '') xhr.setRequestHeader(key, String(value));
    });
    if (xhr.upload && typeof progressHandler === 'function') {
      xhr.upload.onprogress = (event) => {
        if (event && event.lengthComputable) progressHandler(event.loaded, event.total);
      };
    }
    xhr.onload = () => {
      const status = Number(xhr.status || 0);
      if (status >= 200 && status < 300) {
        resolve({ status, xhr });
        return;
      }
      const detail = String(xhr.responseText || '').replace(/\s+/g, ' ').trim().slice(0, 260);
      reject(new Error(`Storage ${status || 'error'}${detail ? `: ${detail}` : ''}`));
    };
    xhr.onerror = () => reject(new Error('Storageへの通信に失敗しました'));
    xhr.ontimeout = () => reject(new Error('Storageへの送信がタイムアウトしました'));
    xhr.onabort = () => reject(new Error('Storageへの送信が中断されました'));
    try { xhr.send(body === undefined ? null : body); } catch (err) { reject(err); }
  });

  const uploadRawBlobToSignedUrl = async (blob, signedUrl, contentType, label) => {
    if (!signedUrl) throw new Error(`${label || 'ファイル'}のアップロード先がありません`);
    if (!blob || !blob.size) throw new Error(`${label || 'ファイル'}が空です`);
    let lastError = null;
    for (let attempt = 0; attempt < 2; attempt += 1) {
      try {
        await xhrUpload(
          'PUT',
          signedUrl,
          {
            'cache-control': 'max-age=3600',
            'content-type': contentType || 'application/octet-stream'
          },
          blob,
          180000,
          (loaded, total) => {
            const pct = total > 0 ? Math.max(0, Math.min(100, Math.round((loaded / total) * 100))) : 0;
            setStatus(`動画を保管庫へ送信しています… ${pct}%`);
          }
        );
        return true;
      } catch (err) {
        lastError = err;
      }
      if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, 700));
    }
    throw lastError || new Error(`${label || 'ファイル'}アップロードに失敗しました`);
  };

  const utf8Base64 = (value) => {
    const bytes = new TextEncoder().encode(String(value || ''));
    let binary = '';
    const step = 8192;
    for (let start = 0; start < bytes.length; start += step) {
      const slice = bytes.subarray(start, Math.min(bytes.length, start + step));
      binary += String.fromCharCode(...slice);
    }
    return btoa(binary);
  };

  const tusHeaders = () => {
    const headers = { 'Tus-Resumable': '1.0.0' };
    if (videoUploadToken) headers['x-signature'] = videoUploadToken;
    return headers;
  };

  const createTusUpload = async (blob, contentType) => {
    if (!videoTusEndpoint || !videoUploadToken || !videoUploadStoragePath || !videoUploadBucket) {
      throw new Error('再開可能アップロードの情報が不足しています');
    }
    const metadata = [
      `bucketName ${utf8Base64(videoUploadBucket)}`,
      `objectName ${utf8Base64(videoUploadStoragePath)}`,
      `contentType ${utf8Base64(contentType || 'video/webm')}`,
      `cacheControl ${utf8Base64('3600')}`
    ].join(',');
    const response = await xhrUpload(
      'POST',
      videoTusEndpoint,
      {
        ...tusHeaders(),
        'Upload-Length': String(blob.size),
        'Upload-Metadata': metadata
      },
      null,
      30000
    );
    let location = String(response.xhr.getResponseHeader('Location') || '').trim();
    if (!location) throw new Error('再開可能アップロードURLを取得できませんでした');
    try { location = new URL(location, videoTusEndpoint).toString(); } catch (_) {}
    return location;
  };

  const readTusOffset = async (uploadUrl) => {
    try {
      const response = await xhrUpload('HEAD', uploadUrl, tusHeaders(), null, 30000);
      const value = Number(response.xhr.getResponseHeader('Upload-Offset') || 0);
      return Number.isFinite(value) && value >= 0 ? value : 0;
    } catch (_) {
      return 0;
    }
  };

  const uploadVideoBlobResumable = async (blob, contentType) => {
    const chunkSize = 6 * 1024 * 1024;
    let uploadUrl = await createTusUpload(blob, contentType);
    let offset = 0;
    while (offset < blob.size) {
      const end = Math.min(blob.size, offset + chunkSize);
      const chunk = blob.slice(offset, end, contentType || blob.type || 'application/octet-stream');
      let sent = false;
      let lastError = null;
      for (let attempt = 0; attempt < 3 && !sent; attempt += 1) {
        try {
          const baseOffset = offset;
          const response = await xhrUpload(
            'PATCH',
            uploadUrl,
            {
              ...tusHeaders(),
              'Upload-Offset': String(offset),
              'Content-Type': 'application/offset+octet-stream'
            },
            chunk,
            120000,
            (loaded) => {
              const totalLoaded = Math.min(blob.size, baseOffset + loaded);
              const pct = Math.max(0, Math.min(100, Math.round((totalLoaded / blob.size) * 100)));
              setStatus(`動画を保管庫へ送信しています… ${pct}%`);
            }
          );
          const serverOffset = Number(response.xhr.getResponseHeader('Upload-Offset') || end);
          offset = Number.isFinite(serverOffset) && serverOffset > offset ? serverOffset : end;
          sent = true;
        } catch (err) {
          lastError = err;
          const resumedOffset = await readTusOffset(uploadUrl);
          if (resumedOffset > offset) {
            offset = resumedOffset;
            sent = true;
            break;
          }
          if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 900 * (attempt + 1)));
        }
      }
      if (!sent) throw lastError || new Error('再開可能アップロードに失敗しました');
    }
    setStatus('動画を保管庫へ送信しています… 100%');
    return true;
  };


  const buildCandidateSheet = async (frames) => {
    const source = Array.isArray(frames) ? frames.slice(0, 150) : [];
    if (!source.length) return null;
    const loaded = [];
    for (const frame of source) {
      const dataUrl = String(frame?.data_url || '');
      if (!dataUrl) continue;
      try {
        const image = await new Promise((resolve, reject) => {
          const node = new Image();
          node.onload = () => resolve(node);
          node.onerror = reject;
          node.src = dataUrl;
        });
        loaded.push({ frame, image });
      } catch (_) {}
    }
    if (!loaded.length) return null;
    const columns = Math.min(15, loaded.length);
    const rows = Math.ceil(loaded.length / columns);
    const tileWidth = Math.max(1, loaded[0].image.naturalWidth || loaded[0].image.width || 320);
    const tileHeight = Math.max(1, loaded[0].image.naturalHeight || loaded[0].image.height || 180);
    const sheet = document.createElement('canvas');
    sheet.width = tileWidth * columns;
    sheet.height = tileHeight * rows;
    const ctx = sheet.getContext('2d', { alpha: false });
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, sheet.width, sheet.height);
    const manifest = [];
    loaded.forEach((entry, index) => {
      const col = index % columns;
      const row = Math.floor(index / columns);
      ctx.drawImage(entry.image, col * tileWidth, row * tileHeight, tileWidth, tileHeight);
      manifest.push({
        frame_id: String(entry.frame?.frame_id || `F${String(index + 1).padStart(2, '0')}`),
        timestamp_ms: Math.max(0, Number(entry.frame?.timestamp_ms || 0)),
        tile_index: index
      });
    });
    const blob = await new Promise((resolve) => sheet.toBlob(resolve, 'image/jpeg', 0.80));
    if (!blob) return null;
    return { blob, manifest, columns, rows, tile_width: tileWidth, tile_height: tileHeight };
  };

  const uploadVideoBlobToSignedUrl = async (blob) => {
    if (!videoUploadSignedUrl || !videoUploadStoragePath) {
      throw new Error('動画のアップロード先がありません');
    }
    const contentType = String(blob.type || '').split(';', 1)[0] || 'video/webm';
    // v145: one transport path only. The browser uploads the untouched MediaRecorder
    // Blob to the server-minted signed URL. No candidate sheet, base64 video payload,
    // manual TUS protocol, transcode, resize, or re-encode is involved here.
    return await uploadRawBlobToSignedUrl(blob, videoUploadSignedUrl, contentType, '動画');
  };


  // Capture small candidate stills while recording. This avoids reopening/seeking
  // the finished video before upload and keeps the component payload small.
  const captureRecordingCandidateFrame = async () => {
    if (recordingCandidateBusy || !recordingStartedAt || !video.videoWidth || !video.videoHeight) return;
    if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
    if (recordingCandidateFrames.length >= 150) return;
    recordingCandidateBusy = true;
    try {
      const frameCanvas = document.createElement('canvas');
      const srcW = video.videoWidth || 960;
      const srcH = video.videoHeight || 540;
      const maxSide = 240;
      const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
      frameCanvas.width = Math.max(1, Math.round(srcW * scale));
      frameCanvas.height = Math.max(1, Math.round(srcH * scale));
      const ctx = frameCanvas.getContext('2d', { alpha: false });
      ctx.drawImage(video, 0, 0, frameCanvas.width, frameCanvas.height);
      const jpegBlob = await new Promise((resolve) => frameCanvas.toBlob(resolve, 'image/jpeg', 0.58));
      if (!jpegBlob || jpegBlob.size > 45 * 1024) return;
      const timestampMs = Math.max(0, Date.now() - recordingStartedAt);
      const dataUrl = await blobToDataUrl(jpegBlob);
      const index = recordingCandidateFrames.length + 1;
      recordingCandidateFrames.push({
        frame_id: `F${String(index).padStart(3, '0')}`,
        timestamp_ms: timestampMs,
        data_url: dataUrl
      });
    } catch (err) {
      console.warn('live candidate frame skipped', err);
    } finally {
      recordingCandidateBusy = false;
    }
  };

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

  const capturePosterDataUrl = async () => {
    if (!video.videoWidth || !video.videoHeight) throw new Error('video frame unavailable');
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
    return await blobToDataUrl(blob);
  };


  const captureVideoPosterDataUrl = async () => {
    if (!video.videoWidth || !video.videoHeight) throw new Error('video frame unavailable');
    const srcW = video.videoWidth;
    const srcH = video.videoHeight;
    const maxSide = 900;
    const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
    const width = Math.max(1, Math.round(srcW * scale));
    const height = Math.max(1, Math.round(srcH * scale));
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { alpha: false });
    ctx.drawImage(video, 0, 0, width, height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.72));
    if (!blob) throw new Error('video poster conversion failed');
    return await blobToDataUrl(blob);
  };


  const seekVideoFrame = (node, seconds) => new Promise((resolve, reject) => {
    let settled = false;
    const cleanup = () => {
      node.removeEventListener('seeked', onSeeked);
      node.removeEventListener('error', onError);
      clearTimeout(timer);
    };
    const finish = (fn, value) => {
      if (settled) return;
      settled = true;
      cleanup();
      fn(value);
    };
    const onSeeked = () => finish(resolve);
    const onError = () => finish(reject, new Error('video seek failed'));
    const timer = setTimeout(() => finish(reject, new Error('video seek timeout')), 3500);
    node.addEventListener('seeked', onSeeked, { once: true });
    node.addEventListener('error', onError, { once: true });
    try {
      node.currentTime = Math.max(0, seconds);
    } catch (err) {
      finish(reject, err);
    }
  });

  const extractVideoCandidateFrames = async (blob, durationMs) => {
    const objectUrl = URL.createObjectURL(blob);
    const probe = document.createElement('video');
    probe.preload = 'auto';
    probe.muted = true;
    probe.playsInline = true;
    probe.src = objectUrl;
    try {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('video metadata timeout')), 5000);
        const ready = () => {
          clearTimeout(timer);
          resolve();
        };
        const failed = () => {
          clearTimeout(timer);
          reject(new Error('video metadata failed'));
        };
        probe.addEventListener('loadedmetadata', ready, { once: true });
        probe.addEventListener('error', failed, { once: true });
      });

      const measuredDuration = Number.isFinite(probe.duration) && probe.duration > 0
        ? probe.duration
        : Math.max(0.2, Number(durationMs || 0) / 1000);
      const sampleCount = Math.max(1, Math.min(150, Math.ceil(measuredDuration * 10)));
      const frameCanvas = document.createElement('canvas');
      const srcW = probe.videoWidth || video.videoWidth || 1280;
      const srcH = probe.videoHeight || video.videoHeight || 720;
      const maxSide = 240;
      const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
      frameCanvas.width = Math.max(1, Math.round(srcW * scale));
      frameCanvas.height = Math.max(1, Math.round(srcH * scale));
      const ctx = frameCanvas.getContext('2d', { alpha: false });
      const frames = [];

      for (let i = 0; i < sampleCount; i += 1) {
        // Exact 0.1-second timeline positions: 0.0, 0.1, 0.2 ... up to 14.9s.
        const seconds = Math.min(Math.max(0, measuredDuration - 0.02), i / 10);
        try {
          await seekVideoFrame(probe, Math.min(Math.max(0, measuredDuration - 0.02), seconds));
          ctx.drawImage(probe, 0, 0, frameCanvas.width, frameCanvas.height);
          const jpegBlob = await new Promise((resolve) => frameCanvas.toBlob(resolve, 'image/jpeg', 0.60));
          if (!jpegBlob) continue;
          const dataUrl = await blobToDataUrl(jpegBlob);
          frames.push({
            frame_id: `F${String(i + 1).padStart(3, '0')}`,
            timestamp_ms: Math.max(0, Math.round(seconds * 1000)),
            data_url: dataUrl
          });
        } catch (err) {
          console.warn('candidate frame skipped', err);
        }
      }
      return frames;
    } finally {
      try { probe.pause(); } catch (_) {}
      probe.removeAttribute('src');
      try { probe.load(); } catch (_) {}
      URL.revokeObjectURL(objectUrl);
    }
  };

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
      const dataUrl = await capturePosterDataUrl();
      setStatus('位置情報を確認しています…');
      const location = await locationPromise;
      pendingMedia = {
        kind: 'photo',
        data_url: dataUrl,
        name: 'camera.jpg',
        source: 'camera',
        captured_at: capturedAt,
        location
      };
      showPhotoReview(dataUrl);
      setStatus('');
    } catch (err) {
      console.error(err);
      shootButton.disabled = false;
      const message = '撮影した画像を作れませんでした。もう一度お試しください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'CaptureError', message });
    }
  };

  const chooseRecorderMimeType = () => {
    const candidates = [
      'video/mp4;codecs=h264,aac',
      'video/mp4',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ];
    for (const type of candidates) {
      try {
        if (MediaRecorder.isTypeSupported(type)) return type;
      } catch (_) {}
    }
    return '';
  };

  const stopVideoRecording = () => {
    clearRecordingTimers();
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      try { mediaRecorder.stop(); } catch (_) {}
    }
  };

  const startVideoRecording = async () => {
    if (!stream || !video.videoWidth || !video.videoHeight) return;
    if (!stream.getAudioTracks().length) {
      const message = '動画用のマイクを利用できません。カメラとマイクの権限を確認してください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'MicrophoneUnavailable', message });
      return;
    }

    recordedChunks = [];
    recordingCandidateFrames = [];
    recordingCandidateBusy = false;
    recordingCancelled = false;
    recordingCapturedAt = new Date().toISOString();
    recordingLocationPromise = getLocationAtCapture();
    const mimeType = chooseRecorderMimeType();
    const captureTrack = stream.getVideoTracks && stream.getVideoTracks()[0];
    const captureSettings = (captureTrack && captureTrack.getSettings) ? captureTrack.getSettings() : {};
    const captureWidth = Math.max(0, Number(captureSettings?.width || video.videoWidth || 0));
    const captureHeight = Math.max(0, Number(captureSettings?.height || video.videoHeight || 0));
    const captureFrameRate = Math.max(0, Number(captureSettings?.frameRate || 0));
    const capturePixels = captureWidth * captureHeight;
    const requestedVideoBitrate = capturePixels >= 1700000
      ? 8000000
      : (capturePixels >= 800000 ? 5000000 : 3000000);
    try {
      const options = {
        videoBitsPerSecond: requestedVideoBitrate,
        audioBitsPerSecond: 128000
      };
      if (mimeType) options.mimeType = mimeType;
      try {
        mediaRecorder = new MediaRecorder(stream, options);
      } catch (_) {
        mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      }
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) recordedChunks.push(event.data);
      };
      mediaRecorder.onerror = (event) => {
        console.error(event);
        clearRecordingTimers();
        setRecordingUi(false);
        const message = '動画の録画中にエラーが発生しました。もう一度お試しください。';
        setStatus(message);
        setTriggerValue('camera_error', { name: 'VideoRecordError', message });
      };
      mediaRecorder.onstop = async () => {
        clearRecordingTimers();
        setRecordingUi(false);
        const recorder = mediaRecorder;
        mediaRecorder = null;
        if (recordingCancelled) {
          recordedChunks = [];
          recordingCandidateFrames = [];
          recordingCancelled = false;
          return;
        }
        try {
          const durationMs = Math.max(1, Date.now() - recordingStartedAt);
          const finalType = (recorder && recorder.mimeType) || mimeType || 'video/webm';
          const blob = new Blob(recordedChunks, { type: finalType });
          recordedChunks = [];
          if (!blob.size) throw new Error('recorded video is empty');

          // v139: preserve recording quality. No 0.1-second JPEG work runs while
          // MediaRecorder is active. The untouched original is uploaded first; only
          // after recording has ended do we decode lightweight AI thumbnails.
          if (menu) menu.hidden = true;
          if (activeActions) activeActions.hidden = true;
          if (video) video.hidden = true;
          setStatus('動画を自動保存する準備をしています…');

          let candidateFrames = [];
          recordingCandidateFrames = [];

          // Poster/location are useful metadata, but neither is allowed to block the
          // original video save. If poster capture fails, use the first lightweight
          // candidate still; the server can also create a neutral placeholder.
          let posterDataUrl = '';
          try {
            posterDataUrl = await captureVideoPosterDataUrl();
          } catch (posterErr) {
            console.warn('video poster skipped', posterErr);
          }
          if (!posterDataUrl && candidateFrames.length) {
            posterDataUrl = String(candidateFrames[0]?.data_url || '');
          }
          let location = { ok: false, error_code: 'UNAVAILABLE', error_message: '位置情報を取得できませんでした。' };
          try {
            location = await (recordingLocationPromise || getLocationAtCapture());
          } catch (locationErr) {
            console.warn('video location skipped', locationErr);
          }

          // Upload the original first. The trigger payload sent to Streamlit contains
          // only metadata and small JPEG stills, never the multi-megabyte video itself.
          setStatus('動画を保管庫へ送信しています…');
          await uploadVideoBlobToSignedUrl(blob);

          // v140: do not build any browser-side 0.1-second JPEG sheet. The saved
          // original video is now the single source of truth. The server extracts
          // native-resolution 0.1-second frames once, then creates separate small
          // AI copies. This removes duplicated work and avoids low-resolution paths.
          let candidateSheetPath = '';
          let candidateManifest = [];
          let candidateSheetColumns = 0;
          let candidateSheetRows = 0;

          const recordingId = (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function')
            ? globalThis.crypto.randomUUID()
            : `video_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
          const mediaToSave = {
            kind: 'video_uploaded',
            recording_id: recordingId,
            video_storage_path: videoUploadStoragePath,
            video_size_bytes: blob.size,
            poster_data_url: posterDataUrl,
            candidate_frames: [],
            candidate_sheet_path: candidateSheetPath,
            candidate_manifest: candidateManifest,
            candidate_sheet_columns: candidateSheetColumns,
            candidate_sheet_rows: candidateSheetRows,
            mime_type: finalType,
            duration_ms: durationMs,
            capture_width: captureWidth,
            capture_height: captureHeight,
            capture_frame_rate: captureFrameRate,
            video_bitrate_bps: Number((recorder && recorder.videoBitsPerSecond) || requestedVideoBitrate || 0),
            name: finalType.includes('mp4') ? 'camera.mp4' : 'camera.webm',
            source: 'video_camera',
            captured_at: recordingCapturedAt || new Date().toISOString(),
            location,
            auto_save: true,
            upload_complete: true
          };

          if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
          }
          setStatus('動画を保管庫へ送信しました。記録を登録しています…');
          setTriggerValue('video', mediaToSave);
        } catch (err) {
          console.error(err);
          const detail = (err && err.message) ? String(err.message).replace(/\s+/g, ' ').trim().slice(0, 240) : '';
          const message = detail
            ? `動画を保存できませんでした。${detail}`
            : '動画を保存できませんでした。もう一度お試しください。';
          setStatus(message);
          setTriggerValue('camera_error', { name: 'VideoPrepareError', message, detail });
        } finally {
          recordingStartedAt = 0;
          recordingLocationPromise = null;
        }
      };

      mediaRecorder.start(500);
      recordingStartedAt = Date.now();
      setRecordingUi(true);
      updateRecordingClock();
      recordingTimer = setInterval(updateRecordingClock, 250);
      // v139 quality-first recording: do not generate JPEG candidates while the
      // MediaRecorder encoder is running. Candidate extraction starts after stop.
      recordingMaxTimer = setTimeout(stopVideoRecording, VIDEO_MAX_SECONDS * 1000);
      setStatus('');
    } catch (err) {
      console.error(err);
      setRecordingUi(false);
      const message = 'この端末では動画録画を開始できませんでした。ブラウザを最新版にしてください。';
      setStatus(message);
      setTriggerValue('camera_error', { name: 'VideoStartError', message });
    }
  };

  const chooseGalleryPhoto = async () => {
    const file = galleryInput.files && galleryInput.files[0];
    if (!file) return;
    try {
      const dataUrl = await prepareImageFile(file);
      pendingMedia = {
        kind: 'photo',
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
      showPhotoReview(dataUrl);
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

  const findGoodMoments = async (event) => {
    // Hard gate: only a real click on the separately armed review button may
    // start frame extraction. Recording stop and review rendering never call it.
    if (!event || event.isTrusted !== true) return;
    if (!reviewFindMoments || event.currentTarget !== reviewFindMoments) return;
    if (reviewFindMoments.dataset.armedGeneration !== String(videoReviewGeneration)) return;
    if (!pendingMedia || pendingMedia.kind !== 'video' || !pendingVideoBlob) return;
    if (!review || review.hidden || reviewFindMoments.hidden) return;

    event.preventDefault();
    event.stopPropagation();
    reviewFindMoments.dataset.armedGeneration = '';
    if (reviewFindMoments) {
      reviewFindMoments.disabled = true;
      reviewFindMoments.textContent = '候補を準備しています…';
    }
    reviewSave.disabled = true;
    reviewRetry.disabled = true;
    setStatus('動画からいい瞬間の候補を準備しています…');

    try {
      const candidateFrames = await extractVideoCandidateFrames(
        pendingVideoBlob,
        pendingMedia.duration_ms
      );
      if (!Array.isArray(candidateFrames) || candidateFrames.length < 9) {
        throw new Error('not enough candidate frames');
      }
      const requestId = (globalThis.crypto && typeof globalThis.crypto.randomUUID === 'function')
        ? globalThis.crypto.randomUUID()
        : `selection_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
      const request = {
        ...pendingMedia,
        candidate_frames: candidateFrames,
        selection_requested: true,
        selection_request_id: requestId,
        selection_requested_at: new Date().toISOString()
      };
      setTriggerValue('video_selection', request);
    } catch (err) {
      console.error(err);
      const message = '良い瞬間を探す準備ができませんでした。もう一度お試しください。';
      setStatus(message);
      reviewSave.disabled = false;
      reviewRetry.disabled = false;
      if (reviewFindMoments) {
        reviewFindMoments.textContent = '✨ いい瞬間を探す';
      }
      setTriggerValue('camera_error', { name: 'VideoSelectionPrepareError', message });
    }
  };

  const savePendingMedia = () => {
    if (!pendingMedia) return;
    reviewSave.disabled = true;
    reviewRetry.disabled = true;
    const mediaToSave = pendingMedia;
    setStatus(mediaToSave.kind === 'video' ? '動画を保存しています…' : '写真を保存しています…');
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (mediaToSave.kind === 'video') {
      setTriggerValue('video', mediaToSave);
    } else {
      setTriggerValue('photo', mediaToSave);
    }
  };

  const retryPendingMedia = async () => {
    if (!pendingMedia) return;
    const source = pendingMedia.source;
    pendingMedia = null;
    pendingVideoBlob = null;
    reviewSave.disabled = false;
    reviewRetry.disabled = false;
    disarmGoodMomentsButton();
    setStatus('');
    hideReview();

    if ((source === 'camera' || source === 'video_camera') && stream && stream.getTracks().some((track) => track.readyState === 'live')) {
      cameraMode = source === 'video_camera' ? 'video' : 'photo';
      if (video.srcObject !== stream) video.srcObject = stream;
      await video.play();
      shootButton.disabled = false;
      showCameraActions();
      return;
    }
    showMenu();
  };

  const closeCamera = () => {
    stopStream();
    setStatus('');
  };

  const handleShoot = () => {
    if (cameraMode === 'video') {
      if (mediaRecorder && mediaRecorder.state === 'recording') stopVideoRecording();
      else startVideoRecording();
    } else {
      takePhoto();
    }
  };

  const switchCameraMode = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') return;
    startCamera(cameraMode === 'video' ? 'photo' : 'video');
  };

  const startPhotoCamera = () => startCamera('photo');
  const startVideoCamera = () => startCamera('video');

  startButton.addEventListener('click', startPhotoCamera);
  videoStartButton.addEventListener('click', startVideoCamera);
  modeSwitchButton.addEventListener('click', switchCameraMode);
  shootButton.addEventListener('click', handleShoot);
  stopButton.addEventListener('click', closeCamera);
  galleryInput.addEventListener('change', chooseGalleryPhoto);
  reviewSave.addEventListener('click', savePendingMedia);
  reviewRetry.addEventListener('click', retryPendingMedia);
  reviewFindMoments?.addEventListener('click', findGoodMoments);

  if (data?.auto_start_mode === 'video') {
    queueMicrotask(() => startCamera('video'));
  } else if (data?.auto_start) {
    queueMicrotask(() => startCamera('photo'));
  }

  return () => {
    startButton.removeEventListener('click', startPhotoCamera);
    videoStartButton.removeEventListener('click', startVideoCamera);
    modeSwitchButton.removeEventListener('click', switchCameraMode);
    shootButton.removeEventListener('click', handleShoot);
    stopButton.removeEventListener('click', closeCamera);
    galleryInput.removeEventListener('change', chooseGalleryPhoto);
    reviewSave.removeEventListener('click', savePendingMedia);
    reviewRetry.removeEventListener('click', retryPendingMedia);
    reviewFindMoments?.removeEventListener('click', findGoodMoments);
    clearGoodMomentsRevealTimer();
    stopStream();
    hideReview();
  };
}
"""

LIVE_CAMERA_COMPONENT_BUILD = "v143"

try:
    live_camera_component = st.components.v2.component(
        "tokyo_burari_live_camera_v145",
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
.diary-video-badge {
  position: absolute;
  left: 9px;
  bottom: 9px;
  z-index: 2;
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(17,24,39,.78);
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;
  pointer-events: none;
  box-shadow: 0 1px 5px rgba(0,0,0,.22);
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
  .diary-photo-delete { top: 2px; right: 2px; width: 23px; height: 23px; font-size: 17px; }
  .diary-video-badge { left: 7px; bottom: 7px; font-size: 9px; padding: 3px 6px; }
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

    if (photo.is_video) {
      const badge = document.createElement('div');
      badge.className = 'diary-video-badge';
      badge.textContent = '▶ 動画';
      button.appendChild(badge);
    }

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
  const validPages = new Set(['home', 'camera', 'videos', 'moments', 'diary', 'review', 'settings']);
  const marker = '__tokyo_burari_page__';
  const requestedPage = validPages.has(data?.page) ? data.page : 'home';
  const action = data?.action || 'sync';
  const navigationNode = String(data?.node || requestedPage);
  const interceptHierarchyBack = Boolean(data?.intercept_hierarchy_back) && requestedPage !== 'home';

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
    if (interceptHierarchyBack) {
      // The phone/browser Back control must mean "one folder level up", not
      // "whatever screen happened to be visited previously". Restore the app
      // entry immediately, then let Python apply the fixed parent mapping.
      window.history.pushState(
        { ...(window.history.state || {}), [marker]: requestedPage },
        '',
        urlFor(requestedPage)
      );
      const token = `${navigationNode}:${Date.now()}:${Math.random()}`;
      setTriggerValue('hierarchy_back', token);
      return;
    }
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
        'tokyo_burari_browser_history_v127',
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
  const cameraModeKey = 'tokyo_burari_last_camera_mode_v1';
  const accountKey = String(data?.account_key || '');
  const reviewSeenKey = accountKey ? `tokyo_burari_review_seen_v1:${accountKey}` : '';
  const reviewCheckKey = accountKey ? `tokyo_burari_review_check_v1:${accountKey}` : '';
  const instanceKey = String(data?.instance_key || 'default');
  const runtime = registry.get(instanceKey) || { lastState: '', lastError: '' };
  registry.set(instanceKey, runtime);

  try {
    const storeToken = String(data?.store_auth_token || '');
    if (storeToken) localStorage.setItem(authKey, storeToken);
    if (data?.clear_auth_token) localStorage.removeItem(authKey);

    if (reviewSeenKey && data?.mark_review_seen_month) {
      localStorage.setItem(reviewSeenKey, String(data.mark_review_seen_month));
    }
    if (reviewCheckKey && data?.store_review_check && typeof data.store_review_check === 'object') {
      localStorage.setItem(reviewCheckKey, JSON.stringify(data.store_review_check));
    }

    let reviewCheck = null;
    if (reviewCheckKey) {
      try {
        reviewCheck = JSON.parse(localStorage.getItem(reviewCheckKey) || 'null');
      } catch (_) {
        reviewCheck = null;
      }
    }

    const state = {
      auth_token: localStorage.getItem(authKey) || '',
      last_camera_open_at: Number(localStorage.getItem(cameraKey) || 0),
      last_camera_mode: localStorage.getItem(cameraModeKey) || '',
      review_seen_month: reviewSeenKey ? (localStorage.getItem(reviewSeenKey) || '') : '',
      review_check: reviewCheck,
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
        "tokyo_burari_browser_persistence_v126",
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

def read_browser_persistence(key, extra_data=None):
    if browser_persistence_component is None:
        return None
    data = {"instance_key": key}
    if isinstance(extra_data, dict):
        data.update(extra_data)
    result = browser_persistence_component(
        data=data,
        key=key,
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )
    state = getattr(result, "browser_state", None)
    return state if isinstance(state, dict) else None


def _browser_review_account_key():
    return f"{current_family_key()}|{current_member_key()}"


def read_browser_review_state():
    account_key = _browser_review_account_key()
    key_hash = hashlib.sha1(account_key.encode("utf-8")).hexdigest()[:12]
    return read_browser_persistence(
        f"browser_review_state_{key_hash}",
        {"account_key": account_key},
    )


def write_browser_review_seen(month_key):
    if browser_persistence_component is None or not month_key:
        return
    account_key = _browser_review_account_key()
    key_hash = hashlib.sha1(account_key.encode("utf-8")).hexdigest()[:12]
    browser_persistence_component(
        data={
            "instance_key": f"browser_review_seen_{key_hash}_{month_key}",
            "account_key": account_key,
            "mark_review_seen_month": str(month_key),
        },
        key=f"browser_review_seen_{key_hash}_{month_key}",
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )


def write_browser_review_check(check_payload):
    if browser_persistence_component is None or not isinstance(check_payload, dict):
        return
    account_key = _browser_review_account_key()
    current_month = str(check_payload.get("month") or "")
    key_hash = hashlib.sha1(account_key.encode("utf-8")).hexdigest()[:12]
    browser_persistence_component(
        data={
            "instance_key": f"browser_review_check_{key_hash}_{current_month}",
            "account_key": account_key,
            "store_review_check": check_payload,
        },
        key=f"browser_review_check_{key_hash}_{current_month}",
        on_browser_state_change=lambda: None,
        on_browser_error_change=lambda: None,
    )


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


def _coerce_component_data_url(value):
    """Normalize Streamlit component media values across browser/SDK variants."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        # Some component/runtime versions wrap a trigger value one level deeper.
        for key in ("data_url", "value", "url", "data"):
            candidate = value.get(key)
            if candidate is value:
                continue
            normalized = _coerce_component_data_url(candidate)
            if normalized:
                return normalized
    return ""


def _sniff_media_mime(raw):
    """Infer the media type from file signatures instead of trusting browser MIME labels."""
    if not raw:
        return ""
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return "image/gif"
    # ISO Base Media File Format: MP4/MOV/3GP variants carry an ftyp box near byte 4.
    if len(raw) >= 12 and raw[4:8] == b"ftyp":
        return "video/mp4"
    # WebM/Matroska EBML header. MediaRecorder commonly emits WebM on Chrome/Android.
    if raw.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"
    return ""


def _decode_browser_media_data_url(data_url, expected_kind=None):
    """Decode component media without assuming the browser's MIME label is reliable."""
    normalized = _coerce_component_data_url(data_url)
    if not normalized or not normalized.lower().startswith("data:"):
        raise ValueError("撮影データの形式が不正です。")
    try:
        header, encoded = normalized.split(",", 1)
    except ValueError as exc:
        raise ValueError("撮影データを読み込めません。") from exc
    if ";base64" not in header.lower():
        raise ValueError("撮影データの形式が不正です。")

    declared_mime = header[5:].split(";", 1)[0].strip().lower()
    # Browser/FileReader output is valid base64 but some engines insert whitespace.
    compact = "".join(encoded.split())
    try:
        raw = base64.b64decode(compact, validate=False)
    except Exception as exc:
        raise ValueError("撮影データを読み込めません。") from exc
    if not raw:
        raise ValueError("撮影データが空です。")

    sniffed_mime = _sniff_media_mime(raw)
    effective_mime = sniffed_mime or declared_mime
    if expected_kind == "image" and not effective_mime.startswith("image/"):
        raise ValueError("撮影画像の形式を判定できませんでした。")
    if expected_kind == "video" and not effective_mime.startswith("video/"):
        raise ValueError("撮影動画の形式を判定できませんでした。")
    return effective_mime, raw


def decode_camera_data_url(data_url):
    """Decode a trusted image data URL emitted by the live camera component."""
    _, raw = _decode_browser_media_data_url(data_url, "image")
    return raw


def decode_camera_video_data_url(data_url):
    """Decode a MediaRecorder data URL, tolerating generic browser MIME labels."""
    mime_type, raw = _decode_browser_media_data_url(data_url, "video")
    return mime_type, raw


def decode_video_candidate_frames(items, max_frames=24):
    """Decode browser-extracted video frames without resizing or recompression."""
    frames = []
    for index, item in enumerate(items or []):
        if len(frames) >= int(max_frames):
            break
        if not isinstance(item, dict):
            continue
        data_url = str(item.get("data_url") or "")
        if not data_url.startswith("data:image/"):
            continue
        try:
            raw = decode_camera_data_url(data_url)
            if not raw or len(raw) > 12 * 1024 * 1024:
                continue
            timestamp_ms = max(0, int(item.get("timestamp_ms") or 0))
            frame_id = str(item.get("frame_id") or f"F{index + 1:02d}").strip()[:16]
            frames.append(
                {
                    "frame_id": frame_id or f"F{index + 1:02d}",
                    "timestamp_ms": timestamp_ms,
                    "image_bytes": raw,
                    "ai_bytes": raw,
                    "output_source": "browser_frame_lossless_v141",
                }
            )
        except Exception:
            continue
    frames.sort(key=lambda x: (int(x.get("timestamp_ms") or 0), str(x.get("frame_id") or "")))
    return frames


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
                    st.session_state["_browser_last_camera_mode"] = str(browser_state.get("last_camera_mode") or "").strip().lower()
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
            st.session_state["_browser_last_camera_mode"] = ""
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
    mime = _sniff_media_mime(image_bytes)
    if not mime.startswith("image/"):
        mime = "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


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


def _image_extension_from_mime(mime_type, default=".jpg"):
    mime = str(mime_type or "").strip().lower()
    if mime == "image/png":
        return ".png"
    if mime == "image/webp":
        return ".webp"
    if mime == "image/gif":
        return ".gif"
    if mime in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    return str(default or ".jpg")


def _prepare_original_photo_upload(image_bytes, fallback_mime="image/jpeg"):
    raw = bytes(image_bytes or b"")
    if not raw:
        raise ValueError("写真データが空です。")
    mime = _sniff_media_mime(raw)
    if not mime.startswith("image/"):
        mime = str(fallback_mime or "image/jpeg").strip().lower() or "image/jpeg"
    ext = _image_extension_from_mime(mime)
    return raw, mime, ext


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


def photo_media_metadata(photo):
    reflection = (photo or {}).get("reflection_json") or {}
    return reflection if isinstance(reflection, dict) else {}


def photo_is_video(photo):
    reflection = photo_media_metadata(photo)
    return str(reflection.get("media_type") or "").strip().lower() == "video" and bool(
        str(reflection.get("video_storage_path") or "").strip()
    )


def diary_photos_only(photos):
    """Return still-photo rows only; original video rows never appear in diaries."""
    return [photo for photo in (photos or []) if isinstance(photo, dict) and not photo_is_video(photo)]


def photo_video_storage_path(photo):
    """Original recording path. This is never replaced by stabilization."""
    if not photo_is_video(photo):
        return ""
    return str(photo_media_metadata(photo).get("video_storage_path") or "").strip()


def photo_video_stabilization_meta(photo):
    metadata = photo_media_metadata(photo)
    value = metadata.get("video_stabilization") or {}
    return value if isinstance(value, dict) else {}


def photo_stabilized_video_storage_path(photo):
    """Return the ready stabilized proxy, if one exists."""
    meta = photo_video_stabilization_meta(photo)
    if str(meta.get("status") or "").strip().lower() != "ready":
        return ""
    return str(meta.get("storage_path") or "").strip()


def photo_video_playback_path(photo):
    """Prefer the stabilized proxy for playback while preserving the original."""
    return photo_stabilized_video_storage_path(photo) or photo_video_storage_path(photo)


def photo_video_ai_source_path(photo):
    """AI timing is based on the untouched original, matching the final still source."""
    return photo_video_storage_path(photo)


def video_is_stabilized(photo):
    return bool(photo_stabilized_video_storage_path(photo))


def video_stabilization_caption(photo):
    meta = photo_video_stabilization_meta(photo)
    status = str(meta.get("status") or "").strip().lower()
    if status == "ready" and photo_stabilized_video_storage_path(photo):
        return "手振れ補正：軽め（元動画も保存しています）"
    if status == "processing":
        return "手振れ補正版を自動作成中です"
    return ""


def video_display_url(photo, expires_in=1800):
    path = photo_video_playback_path(photo)
    if not path:
        return ""
    try:
        signed = signed_photo_url_map((path,), expires_in=int(expires_in))
        return str(signed.get(path) or "")
    except Exception:
        return ""


def photo_all_storage_paths(photo):
    paths = []
    poster = str((photo or {}).get("storage_path") or "").strip()
    if poster:
        paths.append(poster)
    video_path = photo_video_storage_path(photo)
    if video_path and video_path not in paths:
        paths.append(video_path)
    stabilized_path = photo_stabilized_video_storage_path(photo)
    if stabilized_path and stabilized_path not in paths:
        paths.append(stabilized_path)
    for item in video_ai_selection_items(photo):
        selection_path = str(item.get("storage_path") or "").strip()
        if selection_path and selection_path not in paths:
            paths.append(selection_path)
    selection_meta = photo_media_metadata(photo).get("ai_selection") or {}
    if isinstance(selection_meta, dict):
        bundle_path = str(selection_meta.get("candidate_bundle_path") or "").strip()
        if bundle_path and bundle_path not in paths:
            paths.append(bundle_path)
        sheet_path = str(selection_meta.get("candidate_sheet_path") or "").strip()
        if sheet_path and sheet_path not in paths:
            paths.append(sheet_path)
    return paths


def upload_photo(trip_id, image_bytes, location=None, captured_at=None, capture_source="camera", extra_reflection=None):
    active_snapshot = get_active_trip_fast(max_age_seconds=20) if st.session_state.get("active_trip_id") else None
    if not active_snapshot or str(active_snapshot.get("id") or "") != str(trip_id):
        if not get_trip(trip_id):
            raise ValueError("現在の個人アカウントのぶらり旅が見つかりません。")
    # Root quality rule (v141): user-facing stills are uploaded in their original
    # byte form. No resize and no JPEG recompression are applied here.
    original_bytes, content_type, extension = _prepare_original_photo_upload(image_bytes)

    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    path = f"{current_family_key()}/{current_member_key()}/{trip_id}/{stamp}_{uuid.uuid4().hex[:8]}{extension}"
    client = supabase_client()

    reflection = {
        "capture_source": str(capture_source or "camera"),
        "location": location if isinstance(location, dict) else {},
    }
    if isinstance(extra_reflection, dict):
        for key, value in extra_reflection.items():
            if key not in {"capture_source", "location", "media_type", "video_storage_path"}:
                reflection[str(key)] = value

    storage_saved = False
    try:
        client.storage.from_(PHOTO_BUCKET).upload(
            path=path,
            file=original_bytes,
            file_options={
                "content-type": content_type,
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


def video_storage_quota_bytes():
    return int(VIDEO_STORAGE_QUOTA_MB) * 1024 * 1024 if int(VIDEO_STORAGE_QUOTA_MB) > 0 else 0


def _coerce_storage_list_rows(response):
    if response is None:
        return []
    if isinstance(response, list):
        return [x for x in response if isinstance(x, dict)]
    if isinstance(response, dict):
        rows = response.get("data")
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, dict)]
        rows = response.get("items")
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, dict)]
    try:
        rows = getattr(response, "data", None)
    except Exception:
        rows = None
    if isinstance(rows, list):
        return [x for x in rows if isinstance(x, dict)]
    try:
        dumped = response.model_dump()
    except Exception:
        dumped = None
    if isinstance(dumped, dict):
        return _coerce_storage_list_rows(dumped)
    return []


def _storage_row_size(row):
    if not isinstance(row, dict):
        return 0
    metadata = row.get("metadata") or {}
    candidates = [row.get("size")]
    if isinstance(metadata, dict):
        candidates.extend([
            metadata.get("size"), metadata.get("contentLength"), metadata.get("content_length")
        ])
    for value in candidates:
        try:
            if value not in (None, ""):
                return max(0, int(value))
        except Exception:
            continue
    return 0


def _storage_row_mime(row):
    if not isinstance(row, dict):
        return ""
    metadata = row.get("metadata") or {}
    for value in (
        row.get("mimetype"), row.get("mime_type"),
        metadata.get("mimetype") if isinstance(metadata, dict) else None,
        metadata.get("contentType") if isinstance(metadata, dict) else None,
        metadata.get("content_type") if isinstance(metadata, dict) else None,
    ):
        if value:
            return str(value).strip().lower()
    return ""


def _storage_row_is_folder(row):
    if not isinstance(row, dict):
        return False
    # Supabase list() represents folders without an object id/metadata.
    object_id = row.get("id")
    metadata = row.get("metadata")
    if object_id in (None, "") and metadata in (None, {}, []):
        return True
    return False


def _storage_path_is_original_video(path, mime_type=""):
    value = str(path or "").strip().lower()
    mime = str(mime_type or "").strip().lower()
    if mime.startswith("video/"):
        return True
    ext = value.rsplit(".", 1)[-1] if "." in value else ""
    # Stabilized playback proxies are video objects too. Keep this historical
    # predicate broad enough that Storage audit/cleanup can account for both the
    # untouched original and the derived stabilized MP4.
    return ("_video." in value or "_stabilized_" in value) and ext in {"video", "webm", "mp4", "mov", "m4v"}


def _list_member_storage_objects(max_depth=4):
    """List actual Storage objects under only the current family/member prefix."""
    bucket = supabase_client().storage.from_(PHOTO_BUCKET)
    root = f"{current_family_key()}/{current_member_key()}".strip("/")
    results = []
    visited = set()

    def walk(folder, depth):
        folder = str(folder or "").strip("/")
        if folder in visited or depth > max_depth:
            return
        visited.add(folder)
        offset = 0
        page_size = 500
        while True:
            options = {
                "limit": page_size,
                "offset": offset,
                "sortBy": {"column": "name", "order": "asc"},
            }
            try:
                response = bucket.list(folder, options)
            except TypeError:
                response = bucket.list(path=folder, options=options)
            rows = _coerce_storage_list_rows(response)
            for row in rows:
                name = str(row.get("name") or "").strip("/")
                if not name or name in {".", "..", ".emptyFolderPlaceholder"}:
                    continue
                full_path = f"{folder}/{name}" if folder else name
                if _storage_row_is_folder(row):
                    walk(full_path, depth + 1)
                    continue
                results.append({
                    "path": full_path,
                    "name": name,
                    "size_bytes": _storage_row_size(row),
                    "mime_type": _storage_row_mime(row),
                    "updated_at": str(row.get("updated_at") or row.get("created_at") or ""),
                })
            if len(rows) < page_size:
                break
            offset += page_size

    walk(root, 0)
    return results


def _member_db_storage_references():
    client = supabase_client()
    refs = set()
    video_refs = set()
    offset = 0
    page_size = 1000
    while True:
        rows = (
            client.table(PHOTO_TABLE)
            .select("storage_path,reflection_json")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .range(offset, offset + page_size - 1)
            .execute()
        ).data or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            for path in photo_all_storage_paths(row):
                if path:
                    refs.add(str(path))
            video_path = photo_video_storage_path(row)
            if video_path:
                video_refs.add(str(video_path))
            stabilized_path = photo_stabilized_video_storage_path(row)
            if stabilized_path:
                video_refs.add(str(stabilized_path))
        if len(rows) < page_size:
            break
        offset += page_size
    return refs, video_refs


def member_storage_audit(force=False, max_age_seconds=45):
    """Compare actual Storage objects with DB references for the signed-in person."""
    cache_key = _account_cache_key("member_storage_audit_v111")
    if not force:
        cached = _session_cache_get(cache_key, max_age_seconds=max_age_seconds)
        if isinstance(cached, dict):
            return cached
    objects = _list_member_storage_objects()
    refs, video_refs = _member_db_storage_references()
    actual_paths = {str(x.get("path") or "") for x in objects if x.get("path")}
    video_objects = [
        x for x in objects
        if _storage_path_is_original_video(x.get("path"), x.get("mime_type"))
    ]
    orphan_videos = [x for x in video_objects if str(x.get("path") or "") not in video_refs]
    orphan_objects = [x for x in objects if str(x.get("path") or "") not in refs]
    report = {
        "scanned_at": now_jst().isoformat(),
        "root_prefix": f"{current_family_key()}/{current_member_key()}",
        "object_count": len(objects),
        "object_bytes": sum(max(0, int(x.get("size_bytes") or 0)) for x in objects),
        "video_count": len(video_objects),
        "video_bytes": sum(max(0, int(x.get("size_bytes") or 0)) for x in video_objects),
        "orphan_video_count": len(orphan_videos),
        "orphan_video_bytes": sum(max(0, int(x.get("size_bytes") or 0)) for x in orphan_videos),
        "orphan_videos": orphan_videos,
        "orphan_object_count": len(orphan_objects),
        "orphan_object_bytes": sum(max(0, int(x.get("size_bytes") or 0)) for x in orphan_objects),
        "missing_video_paths": sorted(video_refs - actual_paths),
    }
    return _session_cache_set(cache_key, report)


def _invalidate_video_storage_audit_cache():
    for suffix in ("member_storage_audit_v111", "video_storage_usage"):
        key = _account_cache_key(suffix)
        st.session_state.pop(key, None)


def remove_orphan_member_videos(paths):
    """Delete only unreferenced original-video objects under the current member prefix."""
    root = f"{current_family_key()}/{current_member_key()}/"
    safe_paths = []
    for path in paths or []:
        value = str(path or "").strip()
        if value.startswith(root) and _storage_path_is_original_video(value):
            safe_paths.append(value)
    safe_paths = list(dict.fromkeys(safe_paths))
    if not safe_paths:
        return 0
    bucket = supabase_client().storage.from_(PHOTO_BUCKET)
    for start in range(0, len(safe_paths), 50):
        bucket.remove(safe_paths[start:start + 50])
    _invalidate_video_storage_audit_cache()
    clear_camera_video_upload_reservation()
    return len(safe_paths)


def test_video_storage_upload_destination():
    """Mint a signed URL only; this does not create a Storage object or consume quota."""
    trip = ensure_today_trip()
    probe = f"{current_family_key()}/{current_member_key()}/{trip['id']}/{now_jst().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}_video.video"
    url = _create_signed_video_upload_url(probe)
    if not url:
        raise RuntimeError("署名付きアップロード先を取得できませんでした。")
    return True


def current_video_storage_usage_bytes():
    """Actual video bytes for the signed-in person, including stabilized proxies.

    Storage listing is preferred so orphan video objects also count toward the per-person
    quota. If listing is unavailable, DB metadata provides a conservative fallback.
    """
    cache_key = _account_cache_key("video_storage_usage")
    cached = _session_cache_get(cache_key, max_age_seconds=30)
    if cached is not None:
        try:
            return max(0, int(cached))
        except Exception:
            pass

    try:
        report = member_storage_audit(force=False, max_age_seconds=45)
        actual = max(0, int((report or {}).get("video_bytes") or 0))
        return _session_cache_set(cache_key, actual)
    except Exception:
        pass

    client = supabase_client()
    total = 0
    offset = 0
    page_size = 1000
    while True:
        rows = (
            client.table(PHOTO_TABLE)
            .select("reflection_json")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .range(offset, offset + page_size - 1)
            .execute()
        ).data or []
        for row in rows:
            reflection = row.get("reflection_json") or {}
            if not isinstance(reflection, dict):
                continue
            if str(reflection.get("media_type") or "").strip().lower() != "video":
                continue
            try:
                total += max(0, int(reflection.get("video_size_bytes") or 0))
            except Exception:
                pass
            try:
                stabilization = reflection.get("video_stabilization") or {}
                if isinstance(stabilization, dict) and str(stabilization.get("status") or "").lower() == "ready":
                    total += max(0, int(stabilization.get("size_bytes") or 0))
            except Exception:
                pass
        if len(rows) < page_size:
            break
        offset += page_size
    return _session_cache_set(cache_key, total)


def format_storage_size(num_bytes):
    value = max(0, int(num_bytes or 0))
    if value >= 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024 * 1024):.2f} GB"
    if value >= 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    if value >= 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value} B"


def ensure_video_storage_capacity(incoming_bytes):
    quota = video_storage_quota_bytes()
    if quota <= 0:
        return
    usage = current_video_storage_usage_bytes()
    incoming = max(0, int(incoming_bytes or 0))
    if usage + incoming > quota:
        remaining = max(0, quota - usage)
        raise ValueError(
            "この個人アカウントの動画保存容量が上限を超えます。"
            f" 現在 {format_storage_size(usage)} / 上限 {format_storage_size(quota)}、"
            f"残り {format_storage_size(remaining)} です。不要な動画を削除してから保存してください。"
        )


def video_recording_capacity_status():
    """Reserve enough room for one maximum 15-second recording before opening video mode."""
    quota = video_storage_quota_bytes()
    if quota <= 0:
        return {
            "allowed": True,
            "usage_bytes": 0,
            "quota_bytes": 0,
            "remaining_bytes": None,
            "required_bytes": VIDEO_MAX_BYTES,
            "message": f"動画は最大15秒です。高画質動画1本分として最大 {format_storage_size(VIDEO_MAX_BYTES)} を確保します。",
        }

    usage = current_video_storage_usage_bytes()
    remaining = max(0, quota - usage)
    allowed = remaining >= VIDEO_MAX_BYTES
    if allowed:
        message = (
            f"最大15秒の高画質動画を撮影できます。残り {format_storage_size(remaining)} / "
            f"上限 {format_storage_size(quota)}"
        )
    else:
        message = (
            "最大15秒の高画質動画1本分の空き容量がありません。"
            f" 残り {format_storage_size(remaining)} / 上限 {format_storage_size(quota)}。"
            f"撮影には少なくとも {format_storage_size(VIDEO_MAX_BYTES)} の空きが必要です。"
        )
    return {
        "allowed": allowed,
        "usage_bytes": usage,
        "quota_bytes": quota,
        "remaining_bytes": remaining,
        "required_bytes": VIDEO_MAX_BYTES,
        "message": message,
    }


def _extract_signed_upload_value(response, names):
    """Read signed-upload fields from storage-py dict/model response variants."""
    if response is None:
        return ""
    if isinstance(response, dict):
        for name in names:
            value = response.get(name)
            if value not in (None, ""):
                return str(value)
        nested = response.get("data")
        if nested is not response:
            value = _extract_signed_upload_value(nested, names)
            if value:
                return value
    for name in names:
        try:
            value = getattr(response, name, None)
        except Exception:
            value = None
        if value not in (None, ""):
            return str(value)
    try:
        model_data = response.model_dump()
    except Exception:
        model_data = None
    if isinstance(model_data, dict):
        return _extract_signed_upload_value(model_data, names)
    return ""


def _normalize_supabase_storage_signed_url(value):
    url = str(value or "").strip()
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/storage/v1/"):
        return SUPABASE_URL.rstrip("/") + url
    if url.startswith("/object/"):
        return SUPABASE_URL.rstrip("/") + "/storage/v1" + url
    if url.startswith("/"):
        return SUPABASE_URL.rstrip("/") + url
    return url


def _safe_error_text(value, limit=320):
    text = str(value or "").strip().replace("\n", " ")
    return text if len(text) <= limit else text[: max(0, limit - 3)] + "..."


def _supabase_secret_key_kind():
    """Describe the configured key without exposing any key material."""
    key = str(SUPABASE_SECRET_KEY or "").strip()
    if not key:
        return "未設定"
    if key.startswith("sb_secret_"):
        return "Secret key（sb_secret_…）"
    if key.startswith("sb_publishable_"):
        return "Publishable key（sb_publishable_…）"
    if key.count(".") == 2:
        try:
            payload = key.split(".", 2)[1]
            payload += "=" * (-len(payload) % 4)
            decoded = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
            role = str(decoded.get("role") or "").strip()
            if role == "service_role":
                return "Legacy service_role key"
            if role == "anon":
                return "Legacy anon key"
            return f"Legacy JWT key（role={role or '不明'}）"
        except Exception:
            return "JWT形式のキー"
    return "種類を判定できないキー"


def _supabase_tus_endpoint():
    """Return Supabase's resumable-upload endpoint, preferring the direct Storage host."""
    raw = str(SUPABASE_URL or "").strip().rstrip("/")
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
        host = str(parsed.hostname or "")
        if host.endswith(".supabase.co") and not host.endswith(".storage.supabase.co"):
            project_ref = host[: -len(".supabase.co")]
            if project_ref:
                return f"https://{project_ref}.storage.supabase.co/storage/v1/upload/resumable"
    except Exception:
        pass
    return raw + "/storage/v1/upload/resumable"


def _signed_upload_token_from_url(url):
    try:
        values = parse_qs(urlparse(str(url or "")).query)
        for key in ("token", "signature", "x-signature"):
            rows = values.get(key) or []
            if rows and str(rows[0] or "").strip():
                return str(rows[0]).strip()
    except Exception:
        pass
    return ""


def _create_signed_video_upload_target(path):
    """Create both a standard signed URL and its token for TUS resumable uploads."""
    errors = []
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL が設定されていません。")
    if not SUPABASE_SECRET_KEY:
        raise RuntimeError("SUPABASE_SECRET_KEY が設定されていません。")
    if str(SUPABASE_SECRET_KEY).startswith("sb_publishable_"):
        raise RuntimeError(
            "SUPABASE_SECRET_KEY に Publishable key が設定されています。動画保存には Secret key（sb_secret_…）または service_role key が必要です。"
        )

    encoded_path = quote(f"{PHOTO_BUCKET}/{path}", safe="/")
    endpoint = f"{SUPABASE_URL.rstrip('/')}/storage/v1/object/upload/sign/{encoded_path}"
    headers = {
        "apikey": SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
    }
    if not str(SUPABASE_SECRET_KEY or "").startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {SUPABASE_SECRET_KEY}"
    request = Request(endpoint, data=b"{}", method="POST", headers=headers)
    try:
        with urlopen(request, timeout=15) as http_response:
            raw = http_response.read().decode("utf-8", errors="replace")
        payload = json.loads(raw or "{}")
        signed_url = _normalize_supabase_storage_signed_url(
            _extract_signed_upload_value(payload, ("signed_url", "signedUrl", "signedURL", "url"))
        )
        token = _extract_signed_upload_value(payload, ("token", "signed_token", "signedToken", "signature"))
        token = str(token or _signed_upload_token_from_url(signed_url)).strip()
        if signed_url:
            return {
                "signed_url": signed_url,
                "token": token,
                "tus_endpoint": _supabase_tus_endpoint(),
            }
        errors.append("Storage REST API は応答しましたが署名URLが含まれていません。")
    except HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        errors.append(f"Storage REST API HTTP {getattr(exc, 'code', '')}: {_safe_error_text(detail or exc)}")
    except Exception as exc:
        errors.append(f"Storage REST API: {_safe_error_text(exc)}")

    try:
        bucket = supabase_client().storage.from_(PHOTO_BUCKET)
        if not hasattr(bucket, "create_signed_upload_url"):
            errors.append("現在の storage-py に create_signed_upload_url がありません。")
        else:
            response = bucket.create_signed_upload_url(path)
            signed_url = _normalize_supabase_storage_signed_url(
                _extract_signed_upload_value(response, ("signed_url", "signedUrl", "signedURL", "url"))
            )
            token = _extract_signed_upload_value(response, ("token", "signed_token", "signedToken", "signature"))
            token = str(token or _signed_upload_token_from_url(signed_url)).strip()
            if signed_url:
                return {
                    "signed_url": signed_url,
                    "token": token,
                    "tus_endpoint": _supabase_tus_endpoint(),
                }
            errors.append("storage-py は応答しましたが署名URLが含まれていません。")
    except Exception as exc:
        errors.append(f"storage-py: {_safe_error_text(exc)}")

    raise RuntimeError("動画アップロード先を作成できませんでした。" + " / ".join(errors[:3]))


def _create_signed_video_upload_url(path):
    """Compatibility wrapper for older call sites that only need the signed URL."""
    return str(_create_signed_video_upload_target(path).get("signed_url") or "")


def get_camera_video_upload_reservation(trip_id, capture_serial):
    """Return one stable signed upload destination for the current camera capture."""
    state_key = "_camera_video_upload_reservation_v116"
    current = st.session_state.get(state_key)
    family_key = current_family_key()
    member_key = current_member_key()
    serial = int(capture_serial or 0)
    if isinstance(current, dict):
        if (
            str(current.get("trip_id") or "") == str(trip_id)
            and str(current.get("family_key") or "") == str(family_key)
            and str(current.get("member_key") or "") == str(member_key)
            and int(current.get("capture_serial") if current.get("capture_serial") is not None else -1) == serial
            and str(current.get("storage_path") or "").strip()
            and str(current.get("signed_url") or "").strip()
            and str(current.get("upload_token") or "").strip()
            and str(current.get("tus_endpoint") or "").strip()
        ):
            return current

    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    token = uuid.uuid4().hex[:12]
    # The extension is intentionally generic because MediaRecorder may emit MP4 on
    # Safari and WebM on Chromium. Storage metadata carries the real MIME type.
    storage_path = f"{family_key}/{member_key}/{trip_id}/{stamp}_{token}_video.video"
    upload_target = _create_signed_video_upload_target(storage_path)
    signed_url = str(upload_target.get("signed_url") or "")
    upload_token = str(upload_target.get("token") or "")
    tus_endpoint = str(upload_target.get("tus_endpoint") or "")
    # v143: no browser candidate sheet is created. The stored original video is the
    # only source for Good Moments processing.
    candidate_sheet_path = ""
    candidate_sheet_signed_url = ""
    reservation = {
        "trip_id": str(trip_id),
        "family_key": str(family_key),
        "member_key": str(member_key),
        "capture_serial": serial,
        "storage_path": storage_path,
        "signed_url": signed_url,
        "upload_token": upload_token,
        "tus_endpoint": tus_endpoint,
        "candidate_sheet_path": candidate_sheet_path,
        "candidate_sheet_signed_url": candidate_sheet_signed_url,
        "created_at": now_jst().isoformat(),
    }
    st.session_state[state_key] = reservation
    return reservation


def clear_camera_video_upload_reservation():
    st.session_state.pop("_camera_video_upload_reservation_v116", None)


def _video_placeholder_poster_bytes():
    """Create a small neutral JPEG when the browser cannot provide a poster frame."""
    from PIL import Image
    out = io.BytesIO()
    Image.new("RGB", (960, 540), (38, 43, 49)).save(out, format="JPEG", quality=80, optimize=True)
    return out.getvalue()


def register_browser_uploaded_video(
    trip_id,
    video_storage_path,
    video_size_bytes,
    poster_bytes,
    mime_type="video/webm",
    duration_ms=0,
    location=None,
    captured_at=None,
    capture_source="video_camera",
    capture_width=0,
    capture_height=0,
    capture_frame_rate=0,
    video_bitrate_bps=0,
):
    """Register a video already uploaded by the browser to a signed Storage path."""
    active_snapshot = get_active_trip_fast(max_age_seconds=20) if st.session_state.get("active_trip_id") else None
    if not active_snapshot or str(active_snapshot.get("id") or "") != str(trip_id):
        if not get_trip(trip_id):
            raise ValueError("現在の個人アカウントのぶらり旅が見つかりません。")

    path = str(video_storage_path or "").strip()
    expected_prefix = f"{current_family_key()}/{current_member_key()}/{trip_id}/"
    if not path or not path.startswith(expected_prefix) or "_video." not in path:
        raise ValueError("動画の保存先を確認できませんでした。")

    size_value = max(0, int(video_size_bytes or 0))
    if size_value <= 0:
        raise ValueError("動画の容量を確認できませんでした。")
    if size_value > VIDEO_MAX_BYTES:
        raise ValueError("動画データが高画質15秒動画の保存上限を超えています。画質は下げません。保存上限またはSupabase Bucketのファイル上限を確認してください。")
    ensure_video_storage_capacity(size_value)

    try:
        poster = normalize_photo(poster_bytes) if poster_bytes else _video_placeholder_poster_bytes()
    except Exception:
        poster = _video_placeholder_poster_bytes()
    if not poster:
        poster = _video_placeholder_poster_bytes()

    clean_mime = str(mime_type or "video/webm").split(";", 1)[0].strip().lower()
    if clean_mime not in {"video/mp4", "video/webm"}:
        clean_mime = "video/webm"
    duration_value = min(VIDEO_PROCESSING_MAX_SECONDS * 1000, max(0, int(duration_ms or 0)))
    base = path.rsplit("_video.", 1)[0]
    poster_path = base + "_video.jpg"
    client = supabase_client()
    poster_uploaded = False
    reflection = {
        "capture_source": str(capture_source or "video_camera"),
        "location": location if isinstance(location, dict) else {},
        "media_type": "video",
        "video_storage_path": path,
        "video_mime_type": clean_mime,
        "video_duration_ms": duration_value,
        "video_size_bytes": size_value,
        "browser_direct_upload": True,
        "video_capture": {
            "width": max(0, int(capture_width or 0)),
            "height": max(0, int(capture_height or 0)),
            "frame_rate": max(0.0, float(capture_frame_rate or 0)),
            "video_bitrate_bps": max(0, int(video_bitrate_bps or 0)),
            "quality_pipeline": "v145_original_native_pipeline",
        },
        "video_stabilization": {
            "version": VIDEO_STABILIZATION_VERSION,
            "mode": "light",
            "status": "queued",
            "storage_path": "",
            "size_bytes": 0,
            "original_preserved": True,
            "last_error": "",
        },
    }
    try:
        client.storage.from_(PHOTO_BUCKET).upload(
            path=poster_path,
            file=poster,
            file_options={"content-type": (_sniff_media_mime(poster) or "image/jpeg"), "cache-control": "3600"},
        )
        poster_uploaded = True
        result = (
            client.table(PHOTO_TABLE)
            .insert(
                {
                    "trip_id": trip_id,
                    "family_key": current_family_key(),
                    "member_key": current_member_key(),
                    "storage_path": poster_path,
                    "captured_at": str(captured_at or now_jst().isoformat()),
                    "reflection_json": reflection,
                    "signals_json": {},
                }
            )
            .execute()
        )
        saved_row = (result.data or [None])[0]
        if not isinstance(saved_row, dict):
            saved_row = {}
        if not saved_row.get("id"):
            try:
                lookup = (
                    client.table(PHOTO_TABLE)
                    .select("id,trip_id,storage_path,captured_at,reflection_json,signals_json")
                    .eq("trip_id", trip_id)
                    .eq("family_key", current_family_key()).eq("member_key", current_member_key())
                    .eq("storage_path", poster_path)
                    .limit(1)
                    .execute()
                )
                rows = lookup.data or []
                if rows and isinstance(rows[0], dict):
                    saved_row = rows[0]
            except Exception:
                pass
        download_photo.clear()
        signed_photo_url_map.clear()
        _invalidate_fast_db_cache()
        if not saved_row:
            saved_row = {
                "trip_id": trip_id,
                "storage_path": poster_path,
                "captured_at": str(captured_at or now_jst().isoformat()),
                "reflection_json": reflection,
                "signals_json": {},
            }
        return saved_row
    except Exception:
        if poster_uploaded:
            try:
                client.storage.from_(PHOTO_BUCKET).remove([poster_path])
            except Exception:
                pass
        raise


def upload_video(
    trip_id,
    video_bytes,
    poster_bytes,
    mime_type="video/webm",
    duration_ms=0,
    location=None,
    captured_at=None,
    capture_source="video_camera",
):
    """Store a short video plus a JPEG poster in the existing photo record model.

    The JPEG remains the row's storage_path so all existing diary/monthly photo flows
    keep working. The original video path is stored in reflection_json.
    """
    active_snapshot = get_active_trip_fast(max_age_seconds=20) if st.session_state.get("active_trip_id") else None
    if not active_snapshot or str(active_snapshot.get("id") or "") != str(trip_id):
        if not get_trip(trip_id):
            raise ValueError("現在の個人アカウントのぶらり旅が見つかりません。")

    if not video_bytes:
        raise ValueError("動画データが空です。")
    # MediaRecorder.onstop may fire after the actual recording has already stopped.
    # The browser caps recording at 15 seconds, so do not reject a valid video based
    # on wall-clock delay between recorder.stop() and the onstop callback.
    duration_value = min(
        VIDEO_PROCESSING_MAX_SECONDS * 1000,
        max(0, int(duration_ms or 0)),
    )
    if len(video_bytes) > VIDEO_MAX_BYTES:
        raise ValueError("動画データが高画質15秒動画の保存上限を超えています。画質は下げません。保存上限またはSupabase Bucketのファイル上限を確認してください。")
    ensure_video_storage_capacity(len(video_bytes))
    poster = normalize_photo(poster_bytes)
    if not poster:
        raise ValueError("動画の代表画像を作れませんでした。")

    clean_mime = str(mime_type or "video/webm").split(";", 1)[0].strip().lower()
    if clean_mime == "video/mp4":
        extension = "mp4"
        clean_mime = "video/mp4"
    else:
        extension = "webm"
        clean_mime = "video/webm"

    stamp = now_jst().strftime("%Y%m%d_%H%M%S_%f")
    token = uuid.uuid4().hex[:8]
    base = f"{current_family_key()}/{current_member_key()}/{trip_id}/{stamp}_{token}"
    poster_path = base + "_video.jpg"
    video_path = base + f"_video.{extension}"
    client = supabase_client()
    uploaded_paths = []

    reflection = {
        "capture_source": str(capture_source or "video_camera"),
        "location": location if isinstance(location, dict) else {},
        "media_type": "video",
        "video_storage_path": video_path,
        "video_mime_type": clean_mime,
        "video_duration_ms": duration_value,
        "video_size_bytes": len(video_bytes),
        "video_stabilization": {
            "version": VIDEO_STABILIZATION_VERSION,
            "mode": "light",
            "status": "queued",
            "storage_path": "",
            "size_bytes": 0,
            "original_preserved": True,
            "last_error": "",
        },
    }

    try:
        client.storage.from_(PHOTO_BUCKET).upload(
            path=poster_path,
            file=poster,
            file_options={"content-type": (_sniff_media_mime(poster) or "image/jpeg"), "cache-control": "3600"},
        )
        uploaded_paths.append(poster_path)
        client.storage.from_(PHOTO_BUCKET).upload(
            path=video_path,
            file=video_bytes,
            file_options={"content-type": clean_mime, "cache-control": "3600"},
        )
        uploaded_paths.append(video_path)

        result = (
            client
            .table(PHOTO_TABLE)
            .insert(
                {
                    "trip_id": trip_id,
                    "family_key": current_family_key(),
                    "member_key": current_member_key(),
                    "storage_path": poster_path,
                    "captured_at": str(captured_at or now_jst().isoformat()),
                    "reflection_json": reflection,
                    "signals_json": {},
                }
            )
            .execute()
        )
        saved_row = (result.data or [None])[0]
        if not isinstance(saved_row, dict):
            saved_row = {}
        # Some PostgREST/Supabase configurations accept an INSERT but do not return
        # the inserted representation. Recover it by its unique storage path instead
        # of treating an empty response as a failed video save.
        if not saved_row.get("id"):
            try:
                lookup = (
                    client
                    .table(PHOTO_TABLE)
                    .select("id,trip_id,storage_path,captured_at,reflection_json,signals_json")
                    .eq("trip_id", trip_id)
                    .eq("family_key", current_family_key()).eq("member_key", current_member_key())
                    .eq("storage_path", poster_path)
                    .limit(1)
                    .execute()
                )
                rows = lookup.data or []
                if rows and isinstance(rows[0], dict):
                    saved_row = rows[0]
            except Exception:
                pass
        download_photo.clear()
        signed_photo_url_map.clear()
        _invalidate_fast_db_cache()
        if not saved_row:
            # The INSERT request completed without raising. Preserve the uploaded
            # files and let the next normal list refresh recover the DB row rather
            # than deleting a potentially successful save.
            saved_row = {
                "trip_id": trip_id,
                "storage_path": poster_path,
                "captured_at": str(captured_at or now_jst().isoformat()),
                "reflection_json": reflection,
                "signals_json": {},
            }
        return saved_row
    except Exception as exc:
        if uploaded_paths:
            try:
                client.storage.from_(PHOTO_BUCKET).remove(uploaded_paths)
            except Exception:
                pass
        raise RuntimeError(f"動画保存処理でエラーが発生しました: {exc}") from exc


def _video_selection_quality_label(value):
    labels = {
        "expression": "表情",
        "action": "躍動感",
        "beauty": "映え・写真美",
        "subject": "被写体の魅力",
        "story": "印象的な瞬間",
        "other": "総合",
    }
    return labels.get(str(value or "").strip().lower(), "総合")


def _image_dhash64(image_bytes):
    """Small perceptual hash used only to reject almost-identical selected frames."""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(image_bytes)) as img:
            pixels = list(img.convert("L").resize((9, 8)).getdata())
        value = 0
        bit = 0
        for row in range(8):
            start = row * 9
            for col in range(8):
                if pixels[start + col] > pixels[start + col + 1]:
                    value |= 1 << bit
                bit += 1
        return value
    except Exception:
        return None


def _hamming64(a, b):
    if a is None or b is None:
        return 64
    return (int(a) ^ int(b)).bit_count()


def _ask_json_with_images_client(client, prompt, image_items, name, schema, max_output_tokens=1500):
    """Vision JSON helper that can run from a background worker without Streamlit cache state."""
    content = [{"type": "input_text", "text": prompt}]
    for label, image_bytes in image_items or []:
        label = str(label or "").strip()
        if label:
            content.append({"type": "input_text", "text": label})
        if image_bytes:
            content.append({"type": "input_image", "image_url": image_data_url(image_bytes)})
    input_value = [{"role": "user", "content": content}]
    result = client.responses.create(
        **response_args(VISION_MODEL, input_value, name, schema, max_output_tokens)
    )
    return json.loads(result.output_text)


def _video_preference_prompt_text(preference_context):
    context = preference_context if isinstance(preference_context, dict) else {}
    liked = context.get("quality_counts") or {}
    rejected = context.get("rejected_quality_counts") or {}
    liked_count = sum(max(0, int(v or 0)) for v in liked.values()) if isinstance(liked, dict) else 0
    rejected_count = sum(max(0, int(v or 0)) for v in rejected.values()) if isinstance(rejected, dict) else 0
    if not liked_count and not rejected_count:
        return "まだ本人の選択履歴は少ないため、一般的な写真の良さを中心に選んでください。"

    label_map = {
        "expression": "表情",
        "action": "躍動感",
        "beauty": "映え・写真美",
        "subject": "被写体の魅力",
        "story": "印象的な瞬間",
        "other": "総合",
    }
    liked_parts = []
    for key, value in sorted(
        (liked.items() if isinstance(liked, dict) else []),
        key=lambda x: int(x[1] or 0),
        reverse=True,
    ):
        if int(value or 0) > 0:
            liked_parts.append(f"{label_map.get(str(key), str(key))}:{int(value)}")
    rejected_parts = []
    for key, value in sorted(
        (rejected.items() if isinstance(rejected, dict) else []),
        key=lambda x: int(x[1] or 0),
        reverse=True,
    ):
        if int(value or 0) > 0:
            rejected_parts.append(f"{label_map.get(str(key), str(key))}:{int(value)}")

    text = (
        "本人が過去に実際に選んだ写真の傾向は参考にしてください。"
        "ただし選定の土台は常に『一目で残したくなる映え』を優先し、過去の好みに寄せすぎないでください。"
    )
    if liked_parts:
        text += " 選ばれた傾向=" + "、".join(liked_parts[:5]) + "。"
    if rejected_parts:
        text += " 『取り直す』でまとめて却下された傾向=" + "、".join(rejected_parts[:5]) + "。"
    text += " ただし履歴に過剰適合せず、その動画固有の良い瞬間も残してください。"
    return text


def _video_frame_original_bytes(frame):
    """Load one native frame without resizing/re-encoding; disk-backed in v145."""
    if not isinstance(frame, dict):
        return b""
    raw = frame.get("image_bytes")
    if isinstance(raw, (bytes, bytearray)) and raw:
        return bytes(raw)
    path = str(frame.get("image_path") or "").strip()
    if path:
        try:
            return Path(path).read_bytes()
        except Exception:
            return b""
    return b""


def _cleanup_video_frame_temp(frame_items):
    paths = {
        str(frame.get("temp_dir") or "").strip()
        for frame in (frame_items or [])
        if isinstance(frame, dict) and str(frame.get("temp_dir") or "").strip()
    }
    for path in paths:
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass


def _video_photogenic_fallback_score(image_bytes):
    """Cheap visual-quality score used only if the AI response cannot be used."""
    try:
        from PIL import Image, ImageFilter, ImageStat
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb = img.convert("RGB")
            rgb.thumbnail((320, 320))
            gray = rgb.convert("L")
            gray_stat = ImageStat.Stat(gray)
            brightness = float(gray_stat.mean[0])
            contrast = float(gray_stat.stddev[0])
            edges = gray.filter(ImageFilter.FIND_EDGES)
            sharpness = float(ImageStat.Stat(edges).stddev[0])
            saturation = float(ImageStat.Stat(rgb.convert("HSV")).mean[1])

        exposure = max(0.0, 1.0 - abs(brightness - 132.0) / 132.0)
        sharp_term = min(1.0, sharpness / 42.0)
        contrast_term = min(1.0, contrast / 62.0)
        saturation_term = min(1.0, saturation / 105.0)
        return (0.42 * sharp_term) + (0.24 * contrast_term) + (0.20 * exposure) + (0.14 * saturation_term)
    except Exception:
        return 0.0


def choose_video_ai_frames(
    frame_items,
    preference_context=None,
    excluded_frame_ids=None,
    ai_client=None,
    progress_callback=None,
):
    """Pick up to nine stills after AI has inspected every 0.1-second candidate.

    v130 deliberately does not use sharpness/brightness or other non-AI scoring to
    cut the candidate pool before vision analysis. When there are many frames, they
    are split only to keep each API request stable. Every frame is shown to the
    vision model in a first-stage batch, and only the model's batch winners advance
    to the final cross-video comparison.
    """
    frames = list(frame_items or [])
    if not frames:
        raise ValueError("AIセレクション用の候補画像がありません。")

    excluded = {str(x) for x in (excluded_frame_ids or []) if str(x)}
    available = [frame for frame in frames if str(frame.get("frame_id") or "") not in excluded]
    # A reroll should avoid the previous set when enough candidates remain.
    if len(available) >= 3:
        frames = available

    quality_values = ["expression", "action", "beauty", "subject", "story", "other"]

    def selection_schema(max_items):
        return {
            "type": "object",
            "properties": {
                "selections": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": max(1, int(max_items)),
                    "items": {
                        "type": "object",
                        "properties": {
                            "rank": {"type": "integer", "minimum": 1, "maximum": max(1, int(max_items))},
                            "frame_id": {"type": "string"},
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "primary_quality": {"type": "string", "enum": quality_values},
                            "reason": {"type": "string"},
                        },
                        "required": ["rank", "frame_id", "score", "primary_quality", "reason"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["selections"],
            "additionalProperties": False,
        }

    context = preference_context if isinstance(preference_context, dict) else {}
    preference_text = _video_preference_prompt_text(preference_context)
    reference_items = []
    for idx, image_bytes in enumerate(context.get("reference_images") or [], start=1):
        if image_bytes:
            reference_items.append((f"過去に本人が選んだ好みの参考画像 {idx}", image_bytes))

    def call_selector(candidate_frames, prompt, name, max_items, max_output_tokens=1500):
        image_items = list(reference_items)
        image_items.extend(
            [
                (
                    f"候補 {frame['frame_id']} / {int(frame['timestamp_ms']) / 1000:.1f}秒",
                    _video_frame_original_bytes(frame),
                )
                for frame in candidate_frames
                if _video_frame_original_bytes(frame)
            ]
        )
        schema = selection_schema(min(max_items, max(1, len(candidate_frames))))
        if ai_client is None:
            return ask_json_with_images(
                prompt,
                image_items,
                name,
                schema,
                max_output_tokens=max_output_tokens,
            )
        return _ask_json_with_images_client(
            ai_client,
            prompt,
            image_items,
            name,
            schema,
            max_output_tokens=max_output_tokens,
        )

    # Stage 1: every 0.1-second frame is shown to AI. Batches are an API payload
    # boundary only. v132 runs up to three batches concurrently so 150-frame
    # analysis does not spend six request latencies back-to-back.
    coarse_records = []
    if len(frames) > VIDEO_AI_BATCH_SIZE:
        batch_specs = []
        for batch_index, batch_start in enumerate(range(0, len(frames), VIDEO_AI_BATCH_SIZE), start=1):
            batch = frames[batch_start:batch_start + VIDEO_AI_BATCH_SIZE]
            batch_keep = min(VIDEO_AI_BATCH_KEEP, len(batch))
            batch_prompt = (
                "15秒以内の動画を0.1秒間隔で切り出した連続フレームの一部です。"
                "このバッチ内の候補をすべて見比べ、人が写真として残したくなる強い瞬間を選んでください。\n"
                f"最大{batch_keep}枚を選びます。単なる時間分散ではなく、映え・表情・決定的瞬間・被写体の魅力を優先してください。"
                "似た連続フレームでは、一番良い0.1秒の1枚を優先してください。"
                "ピンぼけ、手ぶれ、目つぶり、大きな見切れ、強い白飛び/黒つぶれは避けてください。\n"
                "評価目安：映え・写真美30%、表情や決定的瞬間30%、被写体の魅力20%、動き・物語性10%、本人の過去の好み10%。\n"
                f"{preference_text}\n"
                "rank=1をこのバッチのBESTとし、scoreは0〜100で付けてください。"
            )
            batch_specs.append((batch_index, batch, batch_keep, batch_prompt))

        def run_first_stage_batch(spec):
            batch_index, batch, batch_keep, batch_prompt = spec
            def parse_result(result, candidate_batch):
                by_id = {str(frame.get("frame_id") or ""): frame for frame in candidate_batch}
                ranked = sorted(
                    [item for item in ((result or {}).get("selections") or []) if isinstance(item, dict)],
                    key=lambda item: int(item.get("rank") or 99),
                )
                records = []
                for item in ranked:
                    frame_id = str(item.get("frame_id") or "")
                    frame = by_id.get(frame_id)
                    if not frame:
                        continue
                    records.append({
                        "frame": frame,
                        "score": max(0, min(100, int(item.get("score") or 0))),
                        "primary_quality": str(item.get("primary_quality") or "other"),
                        "reason": str(item.get("reason") or "").strip()[:100],
                        "batch_rank": max(1, int(item.get("rank") or 99)),
                    })
                return records

            result = call_selector(
                batch,
                batch_prompt,
                f"video_moments_v145_coarse_{batch_index}",
                batch_keep,
                max_output_tokens=1100,
            )
            return parse_result(result, batch)

        if callable(progress_callback):
            try:
                progress_callback("ai_selection", 0, len(batch_specs), "AI一次選定を開始")
            except Exception:
                pass

        workers = max(1, min(int(VIDEO_AI_BATCH_WORKERS), len(batch_specs)))
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="burari-ai-batch") as batch_executor:
            futures = [batch_executor.submit(run_first_stage_batch, spec) for spec in batch_specs]
            for completed_index, future in enumerate(futures, start=1):
                coarse_records.extend(future.result())
                if callable(progress_callback):
                    try:
                        progress_callback(
                            "ai_selection",
                            completed_index,
                            len(batch_specs),
                            f"AI一次選定 {completed_index}/{len(batch_specs)}",
                        )
                    except Exception:
                        pass

        # De-duplicate only identical frame IDs emitted by the model; this is not a
        # visual quality filter. Every original frame has already been AI-reviewed.
        seen_ids = set()
        shortlist_records = []
        for record in coarse_records:
            frame_id = str(record["frame"].get("frame_id") or "")
            if not frame_id or frame_id in seen_ids:
                continue
            seen_ids.add(frame_id)
            shortlist_records.append(record)
        if not shortlist_records:
            raise ValueError("AIの一次選定結果を作成できませんでした。")
        final_frames = [record["frame"] for record in shortlist_records]
    else:
        shortlist_records = []
        final_frames = frames

    final_prompt = (
        "動画全体の最終フォトセレクターです。候補は0.1秒単位で比較されています。"
        "ここでは動画全体を横断して、最終的に残したい静止画を選んでください。\n"
        f"出力は最大{VIDEO_AI_MAX_SELECTIONS}枚です。十分に良い候補があれば基本は9枚を選んで3×3で比較できるようにしてください。"
        "ただし質の低い写真で9枚を埋める必要はありません。\n"
        "評価目安：映え・写真美30%、表情や決定的瞬間30%、被写体の魅力20%、動き・物語性10%、本人の過去の好み10%。"
        "特に、自然な笑顔、目線、躍動感、構図、光、色、背景との分離、ピント、被写体が魅力的に見える瞬間を重視してください。"
        "連続したほぼ同じ写真を複数選ばず、写真集として見たときにも変化がある組み合わせにしてください。\n"
        f"{preference_text}\n"
        "rank=1をAI BESTとし、最も残したい1枚を1位にしてください。reasonは日本語で短く具体的にしてください。"
    )

    # v145 keeps every API payload small while retaining the original-resolution
    # PNGs. The first stage has already shown every 0.1-second frame to AI. When
    # that produces more than 12 winners, run an AI-only semifinal tournament in
    # groups of at most 10 before the final comparison.
    if len(final_frames) > 12:
        semifinal_specs = []
        for semi_index, semi_start in enumerate(range(0, len(final_frames), 10), start=1):
            semi_frames = final_frames[semi_start:semi_start + 10]
            semi_keep = min(4, len(semi_frames))
            semifinal_specs.append((semi_index, semi_frames, semi_keep))

        def run_semifinal(spec):
            semi_index, semi_frames, semi_keep = spec
            semi_prompt = (
                "動画全体の最終候補を絞る準決勝です。すべて元動画から非縮小PNGで切り出した画像です。"
                f"この{len(semi_frames)}枚を比較し、写真として残したい順に最大{semi_keep}枚を選んでください。"
                "表情、決定的瞬間、構図、光、被写体の魅力を重視し、似た連続場面は最良の1枚を優先してください。"
            )
            return call_selector(
                semi_frames,
                semi_prompt,
                f"video_moments_v145_semifinal_{semi_index}",
                semi_keep,
                max_output_tokens=1000,
            )

        semi_records = []
        semi_workers = max(1, min(3, len(semifinal_specs)))
        with ThreadPoolExecutor(max_workers=semi_workers, thread_name_prefix="burari-ai-semi") as semi_executor:
            semi_futures = [semi_executor.submit(run_semifinal, spec) for spec in semifinal_specs]
            for spec, future in zip(semifinal_specs, semi_futures):
                _, semi_frames, _ = spec
                result = future.result()
                by_semi_id = {str(frame.get("frame_id") or ""): frame for frame in semi_frames}
                ranked_semi = sorted(
                    [item for item in ((result or {}).get("selections") or []) if isinstance(item, dict)],
                    key=lambda item: int(item.get("rank") or 99),
                )
                for item in ranked_semi:
                    frame = by_semi_id.get(str(item.get("frame_id") or ""))
                    if frame:
                        semi_records.append(frame)
        if len(semi_records) < min(VIDEO_AI_MAX_SELECTIONS, len(final_frames)):
            raise ValueError("AI準決勝の候補を十分に作成できませんでした。")
        final_frames = semi_records[:12]

    if callable(progress_callback):
        try:
            progress_callback("final_selection", 1, 1, "AI最終選定中")
        except Exception:
            pass
    try:
        final_result = call_selector(
            final_frames,
            final_prompt,
            "video_moments_v145_final",
            VIDEO_AI_MAX_SELECTIONS,
            max_output_tokens=1800,
        )
    except Exception:
        # One bounded retry of the same original-resolution final candidates.
        final_result = call_selector(
            final_frames,
            final_prompt,
            "video_moments_v145_final_retry",
            VIDEO_AI_MAX_SELECTIONS,
            max_output_tokens=1800,
        )

    by_id = {str(frame.get("frame_id") or ""): frame for frame in final_frames}
    raw = final_result.get("selections") if isinstance(final_result, dict) else []
    ranked = sorted(
        [item for item in (raw or []) if isinstance(item, dict)],
        key=lambda item: int(item.get("rank") or 99),
    )

    selected = []
    used_ids = set()
    used_hashes = []
    for item in ranked:
        frame_id = str(item.get("frame_id") or "")
        frame = by_id.get(frame_id)
        if not frame or frame_id in used_ids:
            continue
        frame_hash = _image_dhash64(_video_frame_original_bytes(frame))
        # Only remove near-identical duplicates after AI has already evaluated them.
        if any(_hamming64(frame_hash, existing) <= 1 for existing in used_hashes):
            continue
        selected.append(
            {
                "frame": frame,
                "score": max(0, min(100, int(item.get("score") or 0))),
                "primary_quality": str(item.get("primary_quality") or "other"),
                "reason": str(item.get("reason") or "").strip()[:100],
                "hash": frame_hash,
            }
        )
        used_ids.add(frame_id)
        used_hashes.append(frame_hash)
        if len(selected) >= VIDEO_AI_MAX_SELECTIONS:
            break

    if not selected:
        raise ValueError("AIセレクションを作成できませんでした。")
    return selected[:VIDEO_AI_MAX_SELECTIONS]

def _video_selection_base_path(photo):
    video_path = photo_video_storage_path(photo)
    if "_video." in video_path:
        return video_path.rsplit("_video.", 1)[0]
    if "." in video_path:
        return video_path.rsplit(".", 1)[0]
    return video_path


def _write_photo_reflection(photo_id, reflection):
    (
        supabase_client()
        .table(PHOTO_TABLE)
        .update({"reflection_json": reflection if isinstance(reflection, dict) else {}})
        .eq("id", photo_id)
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .execute()
    )
    signed_photo_url_map.clear()
    _invalidate_fast_db_cache()


def _write_photo_reflection_for_owner(photo_id, reflection, family_key, member_key, client=None):
    """Owner-explicit variant safe to call from a background worker."""
    db = client
    if db is None:
        from supabase import create_client as _create_client
        db = _create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    (
        db
        .table(PHOTO_TABLE)
        .update({"reflection_json": reflection if isinstance(reflection, dict) else {}})
        .eq("id", photo_id)
        .eq("family_key", str(family_key))
        .eq("member_key", str(member_key))
        .execute()
    )


def _storage_bytes(value):
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    content = getattr(value, "content", None)
    if isinstance(content, (bytes, bytearray)):
        return bytes(content)
    data = getattr(value, "data", None)
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    return b""


def _build_video_candidate_bundle(frame_items):
    frames = list(frame_items or [])[:VIDEO_AI_MAX_CANDIDATES]
    if not frames:
        raise ValueError("動画の候補フレームがありません。")
    manifest = []
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as zf:
        for index, frame in enumerate(frames, start=1):
            raw = _video_frame_original_bytes(frame)
            if not raw:
                continue
            frame_id = str(frame.get("frame_id") or f"F{index:02d}")[:24]
            extension = _image_extension_from_mime(_sniff_media_mime(raw))
            filename = f"{index:02d}_{frame_id}{extension}"
            zf.writestr(filename, raw)
            manifest.append(
                {
                    "filename": filename,
                    "frame_id": frame_id,
                    "timestamp_ms": max(0, int(frame.get("timestamp_ms") or 0)),
                }
            )
        zf.writestr(
            "manifest.json",
            json.dumps({"version": 1, "frames": manifest}, ensure_ascii=False).encode("utf-8"),
        )
    if not manifest:
        raise ValueError("動画の候補フレームを保存できませんでした。")
    return out.getvalue(), manifest


def _read_video_candidate_bundle(bundle_bytes):
    frames = []
    if not bundle_bytes:
        return frames
    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        for index, item in enumerate(manifest.get("frames") or [], start=1):
            if not isinstance(item, dict):
                continue
            filename = str(item.get("filename") or "")
            if not filename:
                continue
            raw = zf.read(filename)
            if not raw:
                continue
            frames.append(
                {
                    "frame_id": str(item.get("frame_id") or f"F{index:02d}")[:24],
                    "timestamp_ms": max(0, int(item.get("timestamp_ms") or 0)),
                    "image_bytes": raw,
                    "ai_bytes": raw,
                    "output_source": "original_video_native_0p1_lossless_v145",
                }
            )
    frames.sort(key=lambda x: (int(x.get("timestamp_ms") or 0), str(x.get("frame_id") or "")))
    return frames[:VIDEO_AI_MAX_CANDIDATES]


def _read_video_candidate_sheet(sheet_bytes, manifest, columns=4, rows=0):
    """Split a browser-created JPEG contact sheet back into candidate frames."""
    if not sheet_bytes:
        return []
    items = [x for x in (manifest or []) if isinstance(x, dict)][:VIDEO_AI_MAX_CANDIDATES]
    if not items:
        return []
    from PIL import Image
    image = Image.open(io.BytesIO(sheet_bytes)).convert("RGB")
    columns = max(1, min(int(columns or 4), len(items)))
    rows = max(1, int(rows or ((len(items) + columns - 1) // columns)))
    tile_w = max(1, image.width // columns)
    tile_h = max(1, image.height // rows)
    frames = []
    for index, item in enumerate(items):
        tile_index = max(0, int(item.get("tile_index") if item.get("tile_index") is not None else index))
        col = tile_index % columns
        row = tile_index // columns
        if row >= rows:
            continue
        crop = image.crop((col * tile_w, row * tile_h, min(image.width, (col + 1) * tile_w), min(image.height, (row + 1) * tile_h)))
        out = io.BytesIO()
        crop.save(out, format="JPEG", quality=88, optimize=True)
        raw = out.getvalue()
        if not raw:
            continue
        frames.append(
            {
                "frame_id": str(item.get("frame_id") or f"F{index + 1:02d}")[:24],
                "timestamp_ms": max(0, int(item.get("timestamp_ms") or 0)),
                "image_bytes": normalize_photo(raw, max_side=1280, quality=82),
                "ai_bytes": normalize_photo(raw, max_side=640, quality=72),
            }
        )
    frames.sort(key=lambda x: (int(x.get("timestamp_ms") or 0), str(x.get("frame_id") or "")))
    return frames[:VIDEO_AI_MAX_CANDIDATES]


def store_video_ai_candidate_sheet(photo, sheet_path, manifest, columns=4, rows=0):
    """Attach an already-uploaded candidate contact sheet to a saved video."""
    if not isinstance(photo, dict) or not photo.get("id") or not photo_is_video(photo):
        raise ValueError("候補保存対象の動画が見つかりません。")
    sheet_path = str(sheet_path or "").strip()
    manifest = [x for x in (manifest or []) if isinstance(x, dict)][:VIDEO_AI_MAX_CANDIDATES]
    if not sheet_path or not manifest:
        raise ValueError("動画の候補シートがありません。")
    reflection = dict(photo_media_metadata(photo))
    previous = reflection.get("ai_selection") or {}
    if not isinstance(previous, dict):
        previous = {}
    reflection["ai_selection"] = {
        **previous,
        "status": "processing",
        "queued_at": now_jst().isoformat(),
        "updated_at": now_jst().isoformat(),
        "candidate_count": len(manifest),
        "candidate_sheet_path": sheet_path,
        "candidate_manifest": manifest,
        "candidate_sheet_columns": max(1, int(columns or 4)),
        "candidate_sheet_rows": max(1, int(rows or ((len(manifest) + max(1, int(columns or 4)) - 1) // max(1, int(columns or 4))))),
        "candidate_sample_interval_ms": VIDEO_AI_SAMPLE_INTERVAL_MS,
        "candidate_sampling_version": "browser_0p1_v134",
        "stage": "ai_selection",
        "round": int(previous.get("round") or 0),
        "items": list(previous.get("items") or []),
        "history": list(previous.get("history") or []),
        "feedback_history": list(previous.get("feedback_history") or []),
        "last_error": "",
    }
    _write_photo_reflection(photo["id"], reflection)
    updated = dict(photo)
    updated["reflection_json"] = reflection
    return updated


def mark_video_ai_waiting_candidates(photo, message=""):
    if not isinstance(photo, dict) or not photo.get("id"):
        return photo
    reflection = dict(photo_media_metadata(photo))
    previous = reflection.get("ai_selection") or {}
    if not isinstance(previous, dict):
        previous = {}
    previous.update(
        {
            "status": "waiting_candidates",
            "updated_at": now_jst().isoformat(),
            "last_error": str(message or "")[:240],
            "items": list(previous.get("items") or []),
        }
    )
    reflection["ai_selection"] = previous
    _write_photo_reflection(photo["id"], reflection)
    updated = dict(photo)
    updated["reflection_json"] = reflection
    return updated


def _video_ai_has_candidate_source(selection_meta):
    if not isinstance(selection_meta, dict):
        return False
    return bool(
        str(selection_meta.get("candidate_sheet_path") or "").strip()
        or str(selection_meta.get("candidate_bundle_path") or "").strip()
    )


def _load_video_ai_candidate_frames(client, selection_meta):
    if not isinstance(selection_meta, dict):
        return []
    sheet_path = str(selection_meta.get("candidate_sheet_path") or "").strip()
    if sheet_path:
        raw = _storage_bytes(client.storage.from_(PHOTO_BUCKET).download(sheet_path))
        return _read_video_candidate_sheet(
            raw,
            selection_meta.get("candidate_manifest") or [],
            columns=selection_meta.get("candidate_sheet_columns") or 4,
            rows=selection_meta.get("candidate_sheet_rows") or 0,
        )
    bundle_path = str(selection_meta.get("candidate_bundle_path") or "").strip()
    if bundle_path:
        raw = _storage_bytes(client.storage.from_(PHOTO_BUCKET).download(bundle_path))
        return _read_video_candidate_bundle(raw)
    return []


def _ffmpeg_executable():
    """Return a usable ffmpeg executable without making network calls."""
    system_path = shutil.which("ffmpeg")
    if system_path:
        return system_path
    try:
        import imageio_ffmpeg
        candidate = str(imageio_ffmpeg.get_ffmpeg_exe() or "").strip()
        if candidate and os.path.exists(candidate):
            return candidate
    except Exception:
        pass
    return ""


def _video_stabilization_input_suffix(photo):
    metadata = photo_media_metadata(photo)
    mime = str(metadata.get("video_mime_type") or "").lower()
    if "mp4" in mime or "quicktime" in mime or "mov" in mime:
        return ".mp4"
    return ".webm"


def _ensure_video_stabilized_copy(client, photo, family_key, member_key, force=False):
    """Create a light stabilized playback/AI proxy while preserving the original.

    Stabilization is deliberately best-effort. The original recording remains the
    durable source of truth, and any ffmpeg/filter/quota failure is persisted as a
    non-fatal status so video saving and Good Moments can continue via the original
    or the browser-created 0.1-second candidate sheet.
    """
    if not isinstance(photo, dict) or not photo_is_video(photo):
        return photo

    original_path = photo_video_storage_path(photo)
    if not original_path:
        return photo

    reflection = dict(photo_media_metadata(photo))
    current_meta = reflection.get("video_stabilization") or {}
    if not isinstance(current_meta, dict):
        current_meta = {}
    current_status = str(current_meta.get("status") or "").strip().lower()
    current_version = str(current_meta.get("version") or "").strip()
    current_path = str(current_meta.get("storage_path") or "").strip()

    if not force and current_version == VIDEO_STABILIZATION_VERSION:
        if current_status == "ready" and current_path:
            return photo
        if current_status in {"unavailable", "error", "skipped_quota"}:
            return photo

    def persist(status, *, storage_path="", size_bytes=0, last_error="", extra=None):
        nonlocal reflection
        latest_meta = dict(current_meta)
        latest_meta.update(
            {
                "version": VIDEO_STABILIZATION_VERSION,
                "mode": "light",
                "status": str(status),
                "storage_path": str(storage_path or ""),
                "size_bytes": max(0, int(size_bytes or 0)),
                "updated_at": now_jst().isoformat(),
                "last_error": str(last_error or "")[:240],
                "original_preserved": True,
            }
        )
        if extra:
            latest_meta.update(dict(extra))
        reflection = dict(photo_media_metadata(photo))
        reflection["video_stabilization"] = latest_meta
        _write_photo_reflection_for_owner(
            photo.get("id"), reflection, family_key, member_key, client=client
        )
        updated = dict(photo)
        updated["reflection_json"] = reflection
        return updated

    ffmpeg = _ffmpeg_executable()
    if not ffmpeg:
        return persist(
            "unavailable",
            last_error="この実行環境では動画手振れ補正用のffmpegを利用できないため、元動画を使用します。",
            extra={"fallback_to_original": True},
        )

    try:
        original_raw = _storage_bytes(client.storage.from_(PHOTO_BUCKET).download(original_path))
    except Exception as exc:
        return persist(
            "error",
            last_error=f"手振れ補正用に元動画を読み込めませんでした: {exc}",
            extra={"fallback_to_original": True},
        )
    if not original_raw:
        return persist(
            "error",
            last_error="手振れ補正用に元動画を読み込めませんでした。",
            extra={"fallback_to_original": True},
        )

    try:
        persist(
            "processing",
            last_error="",
            extra={"started_at": now_jst().isoformat(), "fallback_to_original": True},
        )
    except Exception:
        pass

    with tempfile.TemporaryDirectory(prefix="burari-stabilize-") as tmpdir:
        input_path = os.path.join(tmpdir, "source" + _video_stabilization_input_suffix(photo))
        output_path = os.path.join(tmpdir, "stabilized.mp4")
        with open(input_path, "wb") as fh:
            fh.write(original_raw)

        # Mild translation/rotation compensation. A small search radius prevents
        # intentional pans and a child's movement from being over-corrected. Mirror
        # edge fill avoids the strong zoom/crop typical of aggressive stabilization.
        filter_value = (
            f"deshake=rx={int(VIDEO_STABILIZATION_RX)}:ry={int(VIDEO_STABILIZATION_RY)}:"
            "edge=mirror:blocksize=8:contrast=125:search=less"
        )
        command = [
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            input_path,
            "-vf",
            filter_value,
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-movflags",
            "+faststart",
            "-max_muxing_queue_size",
            "1024",
            "-y",
            output_path,
        ]
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=float(VIDEO_STABILIZATION_TIMEOUT_SECONDS),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return persist(
                "error",
                last_error="軽い手振れ補正が時間切れになったため、元動画を使用します。",
                extra={"fallback_to_original": True},
            )

        if completed.returncode != 0 or not os.path.exists(output_path):
            detail = completed.stderr.decode("utf-8", errors="ignore").strip().replace("\n", " ")
            if len(detail) > 180:
                detail = detail[:177] + "..."
            return persist(
                "error",
                last_error="軽い手振れ補正を作成できなかったため、元動画を使用します。" + (f" {detail}" if detail else ""),
                extra={"fallback_to_original": True},
            )

        stabilized_raw = Path(output_path).read_bytes()
        if not stabilized_raw:
            return persist(
                "error",
                last_error="手振れ補正版が空だったため、元動画を使用します。",
                extra={"fallback_to_original": True},
            )

    # A derived proxy must never make the account exceed an explicit video quota.
    try:
        ensure_video_storage_capacity(len(stabilized_raw))
    except Exception as exc:
        return persist(
            "skipped_quota",
            last_error=f"保存容量を優先して手振れ補正版の保存を省略しました: {exc}",
            extra={"fallback_to_original": True},
        )

    base = _video_selection_base_path(photo)
    stabilized_path = f"{base}_stabilized_v135_{uuid.uuid4().hex[:8]}.mp4"
    uploaded = False
    try:
        client.storage.from_(PHOTO_BUCKET).upload(
            path=stabilized_path,
            file=stabilized_raw,
            file_options={"content-type": "video/mp4", "cache-control": "3600"},
        )
        uploaded = True
        updated = persist(
            "ready",
            storage_path=stabilized_path,
            size_bytes=len(stabilized_raw),
            last_error="",
            extra={
                "generated_at": now_jst().isoformat(),
                "fallback_to_original": False,
                "filter": "deshake_light",
            },
        )
        if current_path and current_path != stabilized_path:
            try:
                client.storage.from_(PHOTO_BUCKET).remove([current_path])
            except Exception:
                pass
        try:
            signed_photo_url_map.clear()
        except Exception:
            pass
        try:
            _invalidate_video_storage_audit_cache()
        except Exception:
            pass
        return updated
    except Exception as exc:
        if uploaded:
            try:
                client.storage.from_(PHOTO_BUCKET).remove([stabilized_path])
            except Exception:
                pass
        return persist(
            "error",
            last_error=f"手振れ補正版を保存できなかったため、元動画を使用します: {exc}",
            extra={"fallback_to_original": True},
        )


def _video_ai_expected_candidate_count(photo):
    metadata = photo_media_metadata(photo)
    duration_ms = max(0, int(metadata.get("video_duration_ms") or 0))
    if duration_ms > 0:
        duration_seconds = min(float(VIDEO_MAX_SECONDS), max(0.1, duration_ms / 1000.0))
    else:
        duration_seconds = float(VIDEO_MAX_SECONDS)
    return max(
        1,
        min(
            VIDEO_AI_MAX_CANDIDATES,
            int(math.ceil((duration_seconds * 1000.0) / VIDEO_AI_SAMPLE_INTERVAL_MS)),
        ),
    )


def _background_extract_video_candidate_frames(client, photo):
    """Extract every 0.1-second candidate from the untouched original at native size.

    v141 is lossless with respect to still extraction: ffmpeg decodes the saved
    original video once and writes native-resolution PNG frames. Those exact bytes
    are reused for AI review, storage, display fallback, and diary saving.
    """
    video_path = photo_video_storage_path(photo)
    if not video_path:
        raise ValueError("元動画の保存先を確認できませんでした。")
    ffmpeg = _ffmpeg_executable()
    if not ffmpeg:
        raise RuntimeError(
            "元動画から高画質のいい瞬間を作るためのffmpegを利用できません。"
            "低画質候補には切り替えません。"
        )

    video_raw = _storage_bytes(client.storage.from_(PHOTO_BUCKET).download(video_path))
    if not video_raw:
        raise ValueError("保存済みの元動画を読み込めませんでした。")

    target_count = _video_ai_expected_candidate_count(photo)
    fps = 1000.0 / float(VIDEO_AI_SAMPLE_INTERVAL_MS)
    suffix = ".mp4" if str(video_path).lower().endswith(".mp4") else ".webm"
    tmpdir = tempfile.mkdtemp(prefix="burari-video-ai-v145-")
    try:
        input_path = os.path.join(tmpdir, "original" + suffix)
        output_pattern = os.path.join(tmpdir, "frame_%03d.png")
        with open(input_path, "wb") as fh:
            fh.write(video_raw)

        # Native dimensions, lossless PNG, one ffmpeg pass. Frames stay on disk so
        # 150 full-resolution PNGs do not have to remain in Python memory at once.
        command = [
            ffmpeg,
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            input_path,
            "-vf",
            f"fps={fps:.6f}:start_time=0:round=near",
            "-frames:v",
            str(target_count),
            output_pattern,
        ]
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("元動画から非圧縮相当の候補画像を作る処理が45秒でタイムアウトしました。") from exc

        files = sorted(Path(tmpdir).glob("frame_*.png"))[:target_count]
        if completed.returncode != 0 and not files:
            detail = completed.stderr.decode("utf-8", errors="ignore").strip().replace("\n", " ")
            if len(detail) > 180:
                detail = detail[:177] + "..."
            raise RuntimeError("元動画から候補画像を作成できませんでした。" + (f" {detail}" if detail else ""))
        if not files:
            raise ValueError("元動画から候補画像を1枚も作成できませんでした。")

        frames = []
        for index, frame_path in enumerate(files, start=1):
            if not frame_path.exists() or frame_path.stat().st_size <= 0:
                continue
            timestamp_ms = max(0, (index - 1) * VIDEO_AI_SAMPLE_INTERVAL_MS)
            frames.append(
                {
                    "frame_id": f"F{index:03d}",
                    "timestamp_ms": timestamp_ms,
                    "image_path": str(frame_path),
                    "temp_dir": tmpdir,
                    "output_source": "original_video_native_0p1_lossless_v145",
                }
            )
        if not frames:
            raise ValueError("元動画から有効な候補画像を作成できませんでした。")
        return frames[:VIDEO_AI_MAX_CANDIDATES]
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise

def _background_store_video_ai_candidate_bundle(client, photo, family_key, member_key, frame_items):
    """Background-safe candidate persistence for server-side video extraction."""
    bundle_bytes, manifest = _build_video_candidate_bundle(frame_items)
    base = _video_selection_base_path(photo)
    if not base:
        raise ValueError("動画の保存先を確認できませんでした。")
    bundle_path = f"{base}_candidates_auto_{uuid.uuid4().hex[:8]}.zip"
    client.storage.from_(PHOTO_BUCKET).upload(
        path=bundle_path,
        file=bundle_bytes,
        file_options={"content-type": "application/zip", "cache-control": "3600"},
    )

    reflection = dict(photo_media_metadata(photo))
    previous = reflection.get("ai_selection") or {}
    if not isinstance(previous, dict):
        previous = {}
    selection = dict(previous)
    selection.update(
        {
            "status": "processing",
            "queued_at": now_jst().isoformat(),
            "updated_at": now_jst().isoformat(),
            "candidate_count": len(manifest),
            "candidate_bundle_path": bundle_path,
            "candidate_sheet_path": "",
            "candidate_sample_interval_ms": VIDEO_AI_SAMPLE_INTERVAL_MS,
            "candidate_sampling_version": "v130",
            "round": int(previous.get("round") or 0),
            "items": list(previous.get("items") or []),
            "history": list(previous.get("history") or []),
            "feedback_history": list(previous.get("feedback_history") or []),
            "last_error": "",
        }
    )
    reflection["ai_selection"] = selection
    try:
        _write_photo_reflection_for_owner(
            photo.get("id"), reflection, family_key, member_key, client=client
        )
    except Exception:
        try:
            client.storage.from_(PHOTO_BUCKET).remove([bundle_path])
        except Exception:
            pass
        raise

    updated = dict(photo)
    updated["reflection_json"] = reflection
    return updated


def store_video_ai_candidate_bundle(photo, frame_items):
    """Persist candidates once so background selection and rerolls survive Streamlit reruns."""
    if not isinstance(photo, dict) or not photo.get("id") or not photo_is_video(photo):
        raise ValueError("候補保存対象の動画が見つかりません。")
    bundle_bytes, manifest = _build_video_candidate_bundle(frame_items)
    base = _video_selection_base_path(photo)
    if not base:
        raise ValueError("動画の保存先を確認できませんでした。")
    bundle_path = f"{base}_candidates_v105.zip"
    client = supabase_client()
    client.storage.from_(PHOTO_BUCKET).upload(
        path=bundle_path,
        file=bundle_bytes,
        file_options={"content-type": "application/zip", "cache-control": "3600"},
    )

    reflection = dict(photo_media_metadata(photo))
    reflection["ai_selection"] = {
        "status": "processing",
        "queued_at": now_jst().isoformat(),
        "candidate_count": len(manifest),
        "candidate_bundle_path": bundle_path,
        "round": 0,
        "items": [],
        "history": [],
        "feedback_history": [],
    }
    try:
        _write_photo_reflection(photo["id"], reflection)
    except Exception:
        try:
            client.storage.from_(PHOTO_BUCKET).remove([bundle_path])
        except Exception:
            pass
        raise
    updated = dict(photo)
    updated["reflection_json"] = reflection
    return updated


def _load_video_ai_preference_context_for_owner(client, family_key, member_key, max_rows=80):
    """Build lightweight per-person preferences from photos they actually chose."""
    rows = (
        client
        .table(PHOTO_TABLE)
        .select("id,captured_at,storage_path,reflection_json")
        .eq("family_key", str(family_key))
        .eq("member_key", str(member_key))
        .order("captured_at", desc=True)
        .limit(int(max_rows))
        .execute()
    ).data or []

    quality_counts = {}
    rejected_quality_counts = {}
    reference_paths = []
    for row in rows:
        reflection = row.get("reflection_json") or {}
        if not isinstance(reflection, dict):
            continue

        # Durable learning signal: a still explicitly sent to the diary remains
        # useful even if the source video is later deleted.
        if bool(reflection.get("human_selected_from_video")) or str(reflection.get("capture_source") or "") == "video_ai_selection":
            quality = str(reflection.get("source_selection_quality") or "other")
            quality_counts[quality] = int(quality_counts.get(quality, 0)) + 1
            durable_path = str(row.get("storage_path") or "").strip()
            if durable_path and durable_path not in reference_paths:
                reference_paths.append(durable_path)

        selection = reflection.get("ai_selection") or {}
        if not isinstance(selection, dict):
            continue

        for item in selection.get("items") or []:
            if not isinstance(item, dict) or not item.get("human_selected"):
                continue
            # When a chosen still was copied into the normal diary-photo collection,
            # the durable photo row above is the canonical learning signal.
            if item.get("saved_photo_id"):
                continue
            quality = str(item.get("primary_quality") or "other")
            quality_counts[quality] = int(quality_counts.get(quality, 0)) + 1
            path = str(item.get("storage_path") or "").strip()
            if path and path not in reference_paths:
                reference_paths.append(path)

        for history in selection.get("history") or []:
            if not isinstance(history, dict) or not history.get("reroll_rejected"):
                continue
            for quality in history.get("qualities") or []:
                quality = str(quality or "other")
                rejected_quality_counts[quality] = int(rejected_quality_counts.get(quality, 0)) + 1

    reference_images = []
    for path in reference_paths[:4]:
        try:
            raw = _storage_bytes(client.storage.from_(PHOTO_BUCKET).download(path))
            if raw:
                reference_images.append(raw)
        except Exception:
            continue

    return {
        "quality_counts": quality_counts,
        "rejected_quality_counts": rejected_quality_counts,
        "reference_images": reference_images,
    }


def _background_clients():
    from openai import OpenAI
    from supabase import create_client as _create_client
    return (
        _create_client(SUPABASE_URL, SUPABASE_SECRET_KEY),
        # Do not inherit a very long SDK/network timeout in a background worker.
        # If the provider is unavailable, the row is moved to error instead of
        # staying in "processing" for many minutes.
        OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=float(VIDEO_AI_REQUEST_TIMEOUT_SECONDS),
            max_retries=0,
        ),
    )


@st.cache_resource(show_spinner=False)
def _video_ai_executor():
    # Four slots leave room for recovery if a provider/network call from an old
    # Streamlit run is still unwinding. The registry still limits normal work to
    # one current job per video.
    return ThreadPoolExecutor(max_workers=4, thread_name_prefix="burari-video-ai")


@st.cache_resource(show_spinner=False)
def _video_ai_job_registry():
    return {"lock": threading.Lock(), "futures": {}}


def _background_store_video_ai_selection(
    client,
    photo,
    family_key,
    member_key,
    selections,
    round_number,
    previous_paths=None,
):
    """Persist only native-resolution frames extracted from the original video."""
    base = _video_selection_base_path(photo)
    if not base:
        raise ValueError("動画の保存先を確認できませんでした。")
    selected_items = list(selections or [])[:VIDEO_AI_MAX_SELECTIONS]
    if not selected_items:
        raise ValueError("AIセレクションを作成できませんでした。")

    # v140 never performs a second seek/re-extraction pass. The one 0.1-second
    # ffmpeg pass already produced native-resolution source frames. Refuse anything
    # that did not originate from that path rather than showing a blurry fallback.
    for selected in selected_items:
        frame = selected.get("frame") or {}
        if str(frame.get("output_source") or "") not in {"original_video_native_0p1_v140", "original_video_native_0p1_lossless_v141", "original_video_native_0p1_lossless_v145"}:
            raise ValueError("低解像度候補が混在しているため保存を中止しました。元動画から再処理します。")
        if not _video_frame_original_bytes(frame):
            raise ValueError("元動画由来の高画質画像を読み込めませんでした。")

    uploaded_paths = []
    items = []
    job_token = uuid.uuid4().hex[:8]
    try:
        for rank, selected in enumerate(selected_items, start=1):
            frame = selected.get("frame") or {}
            frame_id = str(frame.get("frame_id") or "").strip()
            image_bytes = _video_frame_original_bytes(frame)
            if not frame_id or not image_bytes:
                raise ValueError("元動画由来の高画質画像を読み込めませんでした。")
            extension = _image_extension_from_mime(_sniff_media_mime(image_bytes))
            path = f"{base}_ai_r{int(round_number):02d}_{job_token}_{rank:02d}{extension}"
            client.storage.from_(PHOTO_BUCKET).upload(
                path=path,
                file=image_bytes,
                file_options={"content-type": (_sniff_media_mime(image_bytes) or "image/jpeg"), "cache-control": "3600"},
            )
            uploaded_paths.append(path)
            items.append(
                {
                    "rank": rank,
                    "storage_path": path,
                    "frame_id": frame_id,
                    "timestamp_ms": max(0, int(frame.get("timestamp_ms") or 0)),
                    "output_source": "original_video_native_0p1_lossless_v145",
                    "score": int(selected.get("score") or 0),
                    "primary_quality": str(selected.get("primary_quality") or "other"),
                    "reason": str(selected.get("reason") or "").strip(),
                    "ai_best": rank == 1,
                    "saved_photo_id": None,
                    "human_selected": False,
                }
            )
        if len(items) != len(selected_items):
            raise ValueError("元動画由来の高画質画像を必要枚数保存できませんでした。")

        fresh = (
            client.table(PHOTO_TABLE)
            .select("*")
            .eq("id", photo.get("id"))
            .eq("family_key", str(family_key))
            .eq("member_key", str(member_key))
            .limit(1)
            .execute()
        )
        row = (fresh.data or [None])[0] or photo
        reflection = dict(photo_media_metadata(row))
        selection_meta = reflection.get("ai_selection") or {}
        if not isinstance(selection_meta, dict):
            selection_meta = {}
        selection_meta.update(
            {
                "status": "ready",
                "generated_at": now_jst().isoformat(),
                "updated_at": now_jst().isoformat(),
                "round": int(round_number),
                "items": items,
                "final_frame_mode": "original_native_0p1_single_pass_lossless_v145",
                "high_quality_count": len(items),
                "progress_message": "完了",
                "last_error": "",
            }
        )
        reflection["ai_selection"] = selection_meta
        _write_photo_reflection_for_owner(
            photo.get("id"), reflection, family_key, member_key, client=client
        )

        stale_paths = [str(x) for x in (previous_paths or []) if str(x)]
        if stale_paths:
            try:
                client.storage.from_(PHOTO_BUCKET).remove(stale_paths)
            except Exception:
                pass
        return True
    except Exception:
        if uploaded_paths:
            try:
                client.storage.from_(PHOTO_BUCKET).remove(uploaded_paths)
            except Exception:
                pass
        raise

def _video_ai_timestamp_age_seconds(selection_meta):
    if not isinstance(selection_meta, dict):
        return None
    raw = (
        selection_meta.get("started_at")
        or selection_meta.get("updated_at")
        or selection_meta.get("queued_at")
    )
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=JST)
        return max(0.0, (now_jst() - dt.astimezone(JST)).total_seconds())
    except Exception:
        return None


def video_ai_processing_is_stale(selection_meta):
    age = _video_ai_timestamp_age_seconds(selection_meta)
    return age is not None and age >= float(VIDEO_AI_STALE_SECONDS)


def _run_video_ai_background_job(photo_id, family_key, member_key):
    """Run one complete Good Moments job synchronously in the active Streamlit run."""
    client, ai_client = _background_clients()
    result = (
        client.table(PHOTO_TABLE)
        .select("*")
        .eq("id", str(photo_id))
        .eq("family_key", str(family_key))
        .eq("member_key", str(member_key))
        .limit(1)
        .execute()
    )
    photo = (result.data or [None])[0]
    if not photo or not photo_is_video(photo):
        return False

    reflection = dict(photo_media_metadata(photo))
    selection_meta = reflection.get("ai_selection") or {}
    if not isinstance(selection_meta, dict):
        selection_meta = {}

    selection_meta["status"] = "processing"
    selection_meta["stage"] = "candidate_preparation"
    selection_meta["started_at"] = now_jst().isoformat()
    selection_meta["updated_at"] = selection_meta["started_at"]
    selection_meta["attempt"] = max(0, int(selection_meta.get("attempt") or 0)) + 1
    selection_meta["pipeline_mode"] = "inline_native_lossless_v145"
    selection_meta["progress_message"] = "元動画から高画質候補を準備中"
    reflection["ai_selection"] = selection_meta
    try:
        _write_photo_reflection_for_owner(
            photo_id, reflection, family_key, member_key, client=client
        )
    except Exception:
        pass

    frames = []
    try:
        # v145 samples the untouched original in one native-resolution pass.
        # Legacy browser sheets/low-resolution bundles are ignored for final quality.
        frames = _background_extract_video_candidate_frames(client, photo)
        if not frames:
            raise ValueError("元動画から高画質候補フレームを読み込めませんでした。")

        selection_meta["status"] = "processing"
        selection_meta["stage"] = "ai_selection"
        selection_meta["candidate_count"] = len(frames)
        selection_meta["candidate_bundle_path"] = ""
        selection_meta["candidate_sheet_path"] = ""
        selection_meta["candidate_sample_interval_ms"] = VIDEO_AI_SAMPLE_INTERVAL_MS
        selection_meta["candidate_sampling_version"] = "original_native_0p1_lossless_v145"
        selection_meta["progress_message"] = "AI一次選定を開始"
        selection_meta["updated_at"] = now_jst().isoformat()
        reflection["ai_selection"] = selection_meta
        try:
            _write_photo_reflection_for_owner(
                photo_id, reflection, family_key, member_key, client=client
            )
        except Exception:
            pass

        preference = _load_video_ai_preference_context_for_owner(
            client, family_key, member_key
        )
        history = selection_meta.get("history") or []
        excluded_ids = []
        if isinstance(history, list):
            for history_item in history[-4:]:
                if not isinstance(history_item, dict) or not history_item.get("reroll_rejected"):
                    continue
                excluded_ids.extend(
                    [str(x) for x in (history_item.get("frame_ids") or []) if str(x)]
                )

        current_items = selection_meta.get("items") or []
        previous_paths = [
            str(item.get("storage_path") or "").strip()
            for item in current_items
            if isinstance(item, dict) and str(item.get("storage_path") or "").strip()
        ]
        round_number = max(1, int(selection_meta.get("round") or 0) + 1)

        def update_ai_progress(stage, completed=0, total=0, message=""):
            selection_meta["status"] = "processing"
            selection_meta["stage"] = str(stage or "ai_selection")
            selection_meta["progress_completed"] = max(0, int(completed or 0))
            selection_meta["progress_total"] = max(0, int(total or 0))
            selection_meta["progress_message"] = str(message or "")[:120]
            selection_meta["updated_at"] = now_jst().isoformat()
            reflection["ai_selection"] = selection_meta
            _write_photo_reflection_for_owner(
                photo_id, reflection, family_key, member_key, client=client
            )

        selections = choose_video_ai_frames(
            frames,
            preference_context=preference,
            excluded_frame_ids=excluded_ids,
            ai_client=ai_client,
            progress_callback=update_ai_progress,
        )
        _background_store_video_ai_selection(
            client,
            photo,
            family_key,
            member_key,
            selections,
            round_number,
            previous_paths=previous_paths,
        )
        return True
    except Exception as exc:
        try:
            fresh = (
                client.table(PHOTO_TABLE)
                .select("reflection_json")
                .eq("id", str(photo_id))
                .eq("family_key", str(family_key))
                .eq("member_key", str(member_key))
                .limit(1)
                .execute()
            )
            row = (fresh.data or [None])[0] or {}
            latest_reflection = row.get("reflection_json") or reflection
            if not isinstance(latest_reflection, dict):
                latest_reflection = dict(reflection)
            latest_selection = latest_reflection.get("ai_selection") or {}
            if not isinstance(latest_selection, dict):
                latest_selection = {}
            # If a reroll fails, keep the prior usable set. For a first pass, expose
            # a terminal error immediately rather than leaving a spinner for minutes.
            if latest_selection.get("items"):
                latest_selection["status"] = "ready"
            else:
                latest_selection["status"] = "error"
            latest_selection["last_error"] = str(exc)[:240]
            latest_selection["updated_at"] = now_jst().isoformat()
            latest_selection["stage"] = str(latest_selection.get("stage") or "pipeline")
            latest_selection["pipeline_mode"] = "inline_native_lossless_v145"
            latest_reflection["ai_selection"] = latest_selection
            _write_photo_reflection_for_owner(
                photo_id, latest_reflection, family_key, member_key, client=client
            )
        except Exception:
            pass
        return False
    finally:
        _cleanup_video_frame_temp(frames)

def launch_video_ai_background_job(photo):
    """Run the saved-video AI pipeline automatically in the normal Streamlit run.

    v134 intentionally does not detach the first-time selector into a long-lived
    ThreadPoolExecutor task. Streamlit workers can be rerun/recycled independently
    of those detached futures, which can leave a DB row in ``processing`` forever.
    Keeping the pipeline inside the active server execution is slower for that one
    request, but it is deterministic: no viewer button or other user action is
    required, and a later app execution can resume any unfinished row.

    The historical function name is retained so existing callers keep working.
    """
    if not isinstance(photo, dict) or not photo.get("id") or not photo_is_video(photo):
        return False

    photo_id = str(photo.get("id") or "").strip()
    family_key = str(photo.get("family_key") or current_family_key())
    member_key = str(photo.get("member_key") or current_member_key())
    if not photo_id:
        return False

    # Re-read the row so stale home-page cache data can never reprocess a video
    # that has already reached ready/reviewed.
    fresh = photo
    try:
        result = (
            supabase_client()
            .table(PHOTO_TABLE)
            .select("*")
            .eq("id", photo_id)
            .eq("family_key", family_key)
            .eq("member_key", member_key)
            .limit(1)
            .execute()
        )
        row = (result.data or [None])[0]
        if isinstance(row, dict) and row:
            fresh = row
    except Exception:
        pass

    selection = photo_media_metadata(fresh).get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    status = str(selection.get("status") or "").strip().lower()
    if status in {"ready", "reviewed"} and video_ai_selection_items(fresh):
        return False

    # Prevent accidental recursion during one Streamlit execution. This guard is
    # session-local; DB state remains the durable source of truth across reruns.
    active_key = "_video_ai_inline_active_v133"
    if str(st.session_state.get(active_key) or "") == photo_id:
        return False
    st.session_state[active_key] = photo_id

    attempted = False
    try:
        attempted = True
        # This function owns all exceptions and persists either ready or error.
        _run_video_ai_background_job(photo_id, family_key, member_key)

        # A provider/storage failure should normally already be recorded as error.
        # If the worker ever returns without a terminal state, convert that silent
        # stall into an explicit error instead of leaving ``processing`` forever.
        try:
            result = (
                supabase_client()
                .table(PHOTO_TABLE)
                .select("reflection_json")
                .eq("id", photo_id)
                .eq("family_key", family_key)
                .eq("member_key", member_key)
                .limit(1)
                .execute()
            )
            row = (result.data or [None])[0] or {}
            reflection = row.get("reflection_json") or {}
            if not isinstance(reflection, dict):
                reflection = {}
            latest = reflection.get("ai_selection") or {}
            if not isinstance(latest, dict):
                latest = {}
            latest_status = str(latest.get("status") or "").strip().lower()
            if latest_status not in {"ready", "reviewed", "error", "waiting_browser_candidates"}:
                latest["status"] = "error"
                latest["stage"] = str(latest.get("stage") or "pipeline")
                latest["last_error"] = "自動処理が終了状態を返さなかったため停止しました。"
                latest["updated_at"] = now_jst().isoformat()
                latest["pipeline_mode"] = "inline_native_lossless_v145"
                reflection["ai_selection"] = latest
                _write_photo_reflection_for_owner(
                    photo_id, reflection, family_key, member_key
                )
        except Exception:
            pass
    finally:
        if str(st.session_state.get(active_key) or "") == photo_id:
            st.session_state.pop(active_key, None)
        try:
            _home_video_counts_cached.clear()
        except Exception:
            pass

    return attempted


def resume_member_video_background_jobs(limit=24, min_interval_seconds=0):
    """Automatically process unfinished saved videos without any user action.

    v133 processes at most one unfinished video in each normal Streamlit execution.
    The main entry point immediately reruns after an attempt, so additional queued
    videos advance one by one. This is deliberately not tied to opening the viewer.
    """
    now_mono = time.monotonic()
    last_key = "_video_pipeline_resume_at_v133_inline"
    last = float(st.session_state.get(last_key) or 0.0)
    if min_interval_seconds and last and (now_mono - last) < float(min_interval_seconds):
        return 0
    st.session_state[last_key] = now_mono

    try:
        rows = (
            supabase_client()
            .table(PHOTO_TABLE)
            .select("*")
            .eq("family_key", current_family_key())
            .eq("member_key", current_member_key())
            .order("captured_at", desc=True)
            .limit(max(1, int(limit)))
            .execute()
        ).data or []
    except Exception:
        return 0

    for row in rows:
        if not photo_is_video(row):
            continue
        selection = photo_media_metadata(row).get("ai_selection") or {}
        if not isinstance(selection, dict):
            selection = {}
        status = str(selection.get("status") or "").strip().lower()
        has_items = bool(video_ai_selection_items(row))
        if status in {"ready", "reviewed"} and has_items:
            continue
        # v140 no longer depends on browser candidate recovery. Old waiting/error
        # states are automatically retried once using the saved original video.
        if status == "error":
            if has_items or selection.get("v145_auto_retry"):
                continue
            try:
                selection["v145_auto_retry"] = True
                selection["queued_at"] = now_jst().isoformat()
                selection["updated_at"] = selection["queued_at"]
                selection["pipeline_mode"] = "inline_native_lossless_v145"
                selection["status"] = "waiting_candidates"
                selection["stage"] = "candidate_preparation"
                selection["last_error"] = ""
                reflection = dict(photo_media_metadata(row))
                reflection["ai_selection"] = selection
                _write_photo_reflection_for_owner(
                    row.get("id"),
                    reflection,
                    row.get("family_key") or current_family_key(),
                    row.get("member_key") or current_member_key(),
                )
                row = dict(row)
                row["reflection_json"] = reflection
            except Exception:
                continue
        elif status == "waiting_browser_candidates":
            try:
                selection["status"] = "waiting_candidates"
                selection["stage"] = "candidate_preparation"
                selection["pipeline_mode"] = "inline_native_lossless_v145"
                selection["last_error"] = ""
                reflection = dict(photo_media_metadata(row))
                reflection["ai_selection"] = selection
                _write_photo_reflection_for_owner(
                    row.get("id"),
                    reflection,
                    row.get("family_key") or current_family_key(),
                    row.get("member_key") or current_member_key(),
                )
                row = dict(row)
                row["reflection_json"] = reflection
            except Exception:
                continue

        try:
            if launch_video_ai_background_job(row):
                return 1
        except Exception as exc:
            # Best-effort terminal error marker. No user button is needed to start
            # the job; this only makes a real failure visible rather than "stuck".
            try:
                reflection = dict(photo_media_metadata(row))
                selection = reflection.get("ai_selection") or {}
                if not isinstance(selection, dict):
                    selection = {}
                selection["status"] = "error"
                selection["last_error"] = str(exc)[:240]
                selection["updated_at"] = now_jst().isoformat()
                selection["pipeline_mode"] = "inline_native_lossless_v145"
                reflection["ai_selection"] = selection
                _write_photo_reflection_for_owner(
                    row.get("id"),
                    reflection,
                    row.get("family_key") or current_family_key(),
                    row.get("member_key") or current_member_key(),
                )
            except Exception:
                pass
            return 1
    return 0


def request_video_ai_reroll(photo, record_rejection=True):
    """Create another selection; optionally treat the current set as explicitly rejected."""
    if not isinstance(photo, dict) or not photo.get("id") or not photo_is_video(photo):
        raise ValueError("動画が見つかりません。")
    current = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("id", photo.get("id"))
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    fresh = (current.data or [None])[0] or photo
    reflection = dict(photo_media_metadata(fresh))
    selection = reflection.get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    if not (_video_ai_has_candidate_source(selection) or photo_video_storage_path(fresh)):
        raise ValueError("この動画は再選定できる元動画を保存していません。")

    items = [item for item in (selection.get("items") or []) if isinstance(item, dict)]
    history = list(selection.get("history") or [])
    history_entry = {
        "round": int(selection.get("round") or 0),
        "at": now_jst().isoformat(),
        "frame_ids": [str(item.get("frame_id") or "") for item in items],
        "qualities": [str(item.get("primary_quality") or "other") for item in items],
    }
    if record_rejection:
        history_entry["reroll_rejected"] = True
    else:
        # A confirmed video can be cut again simply to see another set. This is not
        # negative feedback about the previous photographs, so do not exclude them
        # from future preference learning or the new AI pass.
        history_entry["reroll_rejected"] = False
        history_entry["manual_recut"] = True
    history.append(history_entry)
    selection["history"] = history[-12:]
    selection["status"] = "processing"
    selection["queued_at"] = now_jst().isoformat()
    selection.pop("reviewed_at", None)
    selection.pop("review_result", None)
    reflection["ai_selection"] = selection
    _write_photo_reflection(photo.get("id"), reflection)

    updated = dict(fresh)
    updated["reflection_json"] = reflection
    launch_video_ai_background_job(updated)
    return updated


def record_video_ai_human_choices(video_photo, selected_ranks):
    """Persist explicit human picks so future AI selections can adapt per person."""
    ranks = {int(x) for x in (selected_ranks or []) if int(x) > 0}
    if not ranks:
        return video_photo
    current = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("id", video_photo.get("id"))
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    fresh = (current.data or [None])[0] or video_photo
    reflection = dict(photo_media_metadata(fresh))
    selection = reflection.get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    now_value = now_jst().isoformat()
    items = selection.get("items") or []
    # Keep the current selection state in sync even when a reviewed video is
    # opened again and the user changes which AI stills are selected. Previously
    # selected photos that were already copied into the diary are not deleted
    # automatically; this only updates the latest preference/selection state.
    for item in items:
        if not isinstance(item, dict):
            continue
        item_rank = int(item.get("rank") or 0)
        if item_rank in ranks:
            item["human_selected"] = True
            item["human_selected_at"] = now_value
        else:
            item["human_selected"] = False
            item.pop("human_selected_at", None)
    selection["items"] = items
    selection["review_result"] = "kept"
    feedback_history = list(selection.get("feedback_history") or [])
    feedback_history.append(
        {
            "at": now_value,
            "selected_ranks": sorted(ranks),
            "round": int(selection.get("round") or 0),
        }
    )
    selection["feedback_history"] = feedback_history[-20:]
    selection["reviewed_at"] = now_value
    selection["status"] = "reviewed"
    reflection["ai_selection"] = selection
    _write_photo_reflection(video_photo.get("id"), reflection)
    try:
        _home_video_counts_cached.clear()
    except Exception:
        pass

    # Once the user has accepted at least one still, the candidate ZIP is no
    # longer needed for reroll and can be removed to control storage cost.
    candidate_paths = [
        str(selection.get("candidate_bundle_path") or "").strip(),
        str(selection.get("candidate_sheet_path") or "").strip(),
    ]
    candidate_paths = [x for x in candidate_paths if x]
    if candidate_paths:
        try:
            supabase_client().storage.from_(PHOTO_BUCKET).remove(candidate_paths)
            selection["candidate_bundle_path"] = ""
            selection["candidate_sheet_path"] = ""
            reflection["ai_selection"] = selection
            _write_photo_reflection(video_photo.get("id"), reflection)
        except Exception:
            pass

    updated = dict(fresh)
    updated["reflection_json"] = reflection
    return updated


def record_video_ai_no_choice(video_photo):
    """Mark a video reviewed with no stills kept, and learn a weak negative signal."""
    if not isinstance(video_photo, dict) or not video_photo.get("id") or not photo_is_video(video_photo):
        raise ValueError("動画が見つかりません。")

    client = supabase_client()
    current = (
        client.table(PHOTO_TABLE)
        .select("*")
        .eq("id", video_photo.get("id"))
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    fresh = (current.data or [None])[0] or video_photo
    reflection = dict(photo_media_metadata(fresh))
    selection = reflection.get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}

    now_value = now_jst().isoformat()
    items = [item for item in (selection.get("items") or []) if isinstance(item, dict)]
    history = list(selection.get("history") or [])
    history.append(
        {
            "round": int(selection.get("round") or 0),
            "reroll_rejected": True,
            "final_rejected_all": True,
            "at": now_value,
            "frame_ids": [str(item.get("frame_id") or "") for item in items],
            "qualities": [str(item.get("primary_quality") or "other") for item in items],
        }
    )
    selection["history"] = history[-12:]

    feedback_history = list(selection.get("feedback_history") or [])
    feedback_history.append(
        {
            "at": now_value,
            "selected_ranks": [],
            "rejected_all": True,
            "round": int(selection.get("round") or 0),
        }
    )
    selection["feedback_history"] = feedback_history[-20:]
    selection["reviewed_at"] = now_value
    selection["review_result"] = "none_kept"
    selection["status"] = "reviewed"

    # No still was kept, so remove temporary AI-derived images and candidate data.
    cleanup_paths = []
    for item in items:
        path = str(item.get("storage_path") or "").strip()
        if path:
            cleanup_paths.append(path)
    for key in ("candidate_bundle_path", "candidate_sheet_path"):
        path = str(selection.get(key) or "").strip()
        if path:
            cleanup_paths.append(path)
    cleanup_paths = list(dict.fromkeys(cleanup_paths))
    if cleanup_paths:
        try:
            client.storage.from_(PHOTO_BUCKET).remove(cleanup_paths)
        except Exception:
            pass

    selection["items"] = []
    selection["candidate_bundle_path"] = ""
    selection["candidate_sheet_path"] = ""
    reflection["ai_selection"] = selection
    _write_photo_reflection(video_photo.get("id"), reflection)
    try:
        _home_video_counts_cached.clear()
    except Exception:
        pass

    updated = dict(fresh)
    updated["reflection_json"] = reflection
    return updated


def store_preselected_video_ai_selection(photo, selections, candidate_count=0):
    """Store already-selected timestamps using one native-resolution original pass."""
    if not isinstance(photo, dict) or not photo.get("id") or not photo_is_video(photo):
        raise ValueError("AIセレクション対象の動画が見つかりません。")
    selected_items = list(selections or [])[:9]
    if len(selected_items) < 9:
        raise ValueError("AIセレクションを9枚そろえられませんでした。")
    base = _video_selection_base_path(photo)
    if not base:
        raise ValueError("動画の保存先を確認できませんでした。")

    client = supabase_client()
    # Legacy/manual paths may carry small browser candidates. Rebuild the full
    # 0.1-second native-resolution set once from the original and remap by time.
    native_frames = _background_extract_video_candidate_frames(client, photo)
    if not native_frames:
        raise ValueError("元動画から高画質画像を作成できませんでした。")
    native_by_id = {str(frame.get("frame_id") or ""): frame for frame in native_frames}

    def native_for_selected(selected):
        source_frame = selected.get("frame") or {}
        frame_id = str(source_frame.get("frame_id") or "")
        if frame_id and frame_id in native_by_id:
            return native_by_id[frame_id]
        target_ms = max(0, int(source_frame.get("timestamp_ms") or 0))
        return min(
            native_frames,
            key=lambda frame: abs(int(frame.get("timestamp_ms") or 0) - target_ms),
        )

    uploaded_paths = []
    items = []
    try:
        for rank, selected in enumerate(selected_items, start=1):
            native = native_for_selected(selected)
            frame_id = str(native.get("frame_id") or "").strip()
            image_bytes = _video_frame_original_bytes(native)
            if str(native.get("output_source") or "") not in {"original_video_native_0p1_v140", "original_video_native_0p1_lossless_v141", "original_video_native_0p1_lossless_v145"}:
                raise ValueError("元動画由来ではない画像は保存しません。")
            if not frame_id or not image_bytes:
                raise ValueError("AIセレクション画像を元動画から読み込めませんでした。")
            extension = _image_extension_from_mime(_sniff_media_mime(image_bytes))
            path = f"{base}_ai_{rank:02d}{extension}"
            client.storage.from_(PHOTO_BUCKET).upload(
                path=path,
                file=image_bytes,
                file_options={"content-type": (_sniff_media_mime(image_bytes) or "image/jpeg"), "cache-control": "3600"},
            )
            uploaded_paths.append(path)
            items.append(
                {
                    "rank": rank,
                    "storage_path": path,
                    "frame_id": frame_id,
                    "timestamp_ms": max(0, int(native.get("timestamp_ms") or 0)),
                    "output_source": "original_video_native_0p1_lossless_v145",
                    "score": int(selected.get("score") or 0),
                    "primary_quality": str(selected.get("primary_quality") or "other"),
                    "reason": str(selected.get("reason") or "").strip(),
                    "ai_best": rank == 1,
                    "saved_photo_id": None,
                }
            )

        reflection = dict(photo_media_metadata(photo))
        reflection["ai_selection"] = {
            "status": "ready",
            "generated_at": now_jst().isoformat(),
            "candidate_count": max(0, int(candidate_count or len(native_frames))),
            "items": items,
            "final_frame_mode": "original_native_0p1_single_pass_lossless_v145",
            "high_quality_count": len(items),
        }
        _write_photo_reflection(photo["id"], reflection)
        updated = dict(photo)
        updated["reflection_json"] = reflection
        return updated
    except Exception:
        if uploaded_paths:
            try:
                client.storage.from_(PHOTO_BUCKET).remove(uploaded_paths)
            except Exception:
                pass
        raise

def store_video_ai_selection(photo, frame_items):
    """Run AI selection, store nine JPEG derivatives, and attach them to the video row."""
    selections = choose_video_ai_frames(frame_items)
    return store_preselected_video_ai_selection(
        photo,
        selections,
        candidate_count=len(frame_items or []),
    )

def mark_video_ai_selection_error(photo, message):
    if not isinstance(photo, dict) or not photo.get("id"):
        return
    reflection = dict(photo_media_metadata(photo))
    selection = reflection.get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    selection.update(
        {
            "status": "error",
            "generated_at": now_jst().isoformat(),
            "updated_at": now_jst().isoformat(),
            "message": str(message or "AIセレクションを作成できませんでした。")[:240],
            "last_error": str(message or "AIセレクションを作成できませんでした。")[:240],
            "items": list(selection.get("items") or []),
        }
    )
    reflection["ai_selection"] = selection
    try:
        _write_photo_reflection(photo["id"], reflection)
    except Exception:
        pass


def video_ai_selection_items(photo):
    selection = photo_media_metadata(photo).get("ai_selection") or {}
    if not isinstance(selection, dict):
        return []
    items = selection.get("items") or []
    if not isinstance(items, list):
        return []
    clean = [item for item in items if isinstance(item, dict) and str(item.get("storage_path") or "").strip()]
    return sorted(clean, key=lambda item: int(item.get("rank") or 99))[:9]


def _selection_capture_time(photo, timestamp_ms):
    raw = str((photo or {}).get("captured_at") or "").strip()
    if not raw:
        return now_jst().isoformat()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return (parsed + timedelta(milliseconds=max(0, int(timestamp_ms or 0)))).isoformat()
    except Exception:
        return raw


def save_video_ai_selection_as_photo(video_photo, selection_item):
    """Copy one AI derivative into the normal photo collection exactly once."""
    if not isinstance(video_photo, dict) or not isinstance(selection_item, dict):
        raise ValueError("保存する画像を確認できませんでした。")
    if selection_item.get("saved_photo_id"):
        return str(selection_item.get("saved_photo_id"))

    rank = int(selection_item.get("rank") or 0)
    source_path = str(selection_item.get("storage_path") or "").strip()
    if not source_path or rank <= 0:
        raise ValueError("保存する画像を確認できませんでした。")
    raw = download_photo(source_path)
    reflection = photo_media_metadata(video_photo)
    location = reflection.get("location") if isinstance(reflection.get("location"), dict) else {}
    saved = upload_photo(
        video_photo.get("trip_id"),
        raw,
        location=location,
        captured_at=_selection_capture_time(video_photo, selection_item.get("timestamp_ms")),
        capture_source="video_ai_selection",
        extra_reflection={
            "source_video_photo_id": str(video_photo.get("id") or ""),
            "source_selection_rank": rank,
            "source_selection_timestamp_ms": int(selection_item.get("timestamp_ms") or 0),
            "source_selection_quality": str(selection_item.get("primary_quality") or "other"),
            "source_selection_reason": str(selection_item.get("reason") or "").strip()[:120],
            "human_selected_from_video": True,
        },
    )
    saved_id = str((saved or {}).get("id") or "")
    if not saved_id:
        raise RuntimeError("写真として保存できませんでした。")

    current = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("reflection_json")
        .eq("id", video_photo.get("id"))
        .eq("family_key", current_family_key()).eq("member_key", current_member_key())
        .limit(1)
        .execute()
    )
    row = (current.data or [None])[0] or {}
    current_reflection = row.get("reflection_json") or {}
    if not isinstance(current_reflection, dict):
        current_reflection = {}
    selection = current_reflection.get("ai_selection") or {}
    if not isinstance(selection, dict):
        selection = {}
    items = selection.get("items") or []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and int(item.get("rank") or 0) == rank:
                item["saved_photo_id"] = saved_id
                break
    selection["items"] = items
    current_reflection["ai_selection"] = selection
    _write_photo_reflection(video_photo.get("id"), current_reflection)
    return saved_id


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
    storage_paths = []
    for photo in photos:
        storage_paths.extend(photo_all_storage_paths(photo))
    storage_paths = list(dict.fromkeys(path for path in storage_paths if path))

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

    storage_paths = photo_all_storage_paths(photo)
    if storage_paths:
        client.storage.from_(PHOTO_BUCKET).remove(storage_paths)

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


def delete_video_and_related_data(video_photo):
    """Delete one saved video plus its poster/AI working files and DB record."""
    if not isinstance(video_photo, dict) or not photo_is_video(video_photo):
        raise ValueError("削除する動画が見つかりませんでした。")
    photo_id = str(video_photo.get("id") or "").strip()
    trip_id = str(video_photo.get("trip_id") or "").strip()
    if not photo_id or not trip_id:
        raise ValueError("削除する動画の情報を確認できませんでした。")

    # Best effort: stop a queued/running selector from doing more work for a video
    # that the user has explicitly removed. Running provider calls may not cancel,
    # but later DB writes are owner/id guarded and will simply find no row.
    try:
        registry = _video_ai_job_registry()
        with registry["lock"]:
            future = registry["futures"].pop(photo_id, None)
            if future is not None:
                future.cancel()
    except Exception:
        pass

    result = delete_photo_and_related_data(trip_id, photo_id)

    # Clear video-specific counters/audits immediately so the UI and quota checks
    # reflect the newly freed Storage rather than waiting for cache expiry.
    try:
        _home_video_counts_cached.clear()
    except Exception:
        pass
    try:
        _invalidate_video_storage_audit_cache()
    except Exception:
        pass
    if st.session_state.get(f"_camera_recent_photo_{trip_id}") == photo_id:
        st.session_state.pop(f"_camera_recent_photo_{trip_id}", None)
    return result


def render_video_delete_controls(video_photo, key_prefix):
    """Show a two-step delete control directly below any displayed saved video."""
    if not isinstance(video_photo, dict) or not photo_is_video(video_photo):
        return
    photo_id = str(video_photo.get("id") or "").strip()
    if not photo_id:
        return
    safe_prefix = str(key_prefix or "video").replace(" ", "_")
    state_key = f"_video_delete_confirm_{safe_prefix}_{photo_id}"

    if not st.session_state.get(state_key):
        if st.button(
            "この動画を削除する",
            use_container_width=True,
            key=f"video_delete_begin_{safe_prefix}_{photo_id}",
        ):
            st.session_state[state_key] = True

    if st.session_state.get(state_key):
        st.warning(
            "この動画を削除します。元動画、代表画像、AIの候補・未保存の切り取り画像も削除されます。"
            "すでに日記へ送った写真は残ります。この操作は元に戻せません。"
        )
        delete_col, cancel_col = st.columns(2, gap="small")
        with delete_col:
            if st.button(
                "削除を実行",
                type="primary",
                use_container_width=True,
                key=f"video_delete_yes_{safe_prefix}_{photo_id}",
            ):
                try:
                    delete_video_and_related_data(video_photo)
                    st.session_state.pop(state_key, None)
                    st.session_state["_video_delete_notice"] = "動画を削除しました。"
                    st.rerun(scope="app")
                except Exception as exc:
                    st.error("動画を削除できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
        with cancel_col:
            if st.button(
                "キャンセル",
                use_container_width=True,
                key=f"video_delete_no_{safe_prefix}_{photo_id}",
            ):
                st.session_state.pop(state_key, None)
                st.rerun()


@st.dialog("この動画を削除しますか？")
def show_video_delete_dialog(video_photo):
    """Confirm deletion started from the × button on a video card."""
    if not isinstance(video_photo, dict) or not photo_is_video(video_photo):
        st.warning("この動画はすでに削除されているか、読み込めませんでした。")
        return

    photo_id = str(video_photo.get("id") or "").strip()
    if not photo_id:
        st.warning("削除する動画を確認できませんでした。")
        return

    st.markdown(f"**{html.escape(_moments_video_title(video_photo))}**")
    st.warning(
        "この動画を削除します。元動画、代表画像、AIの候補・未保存の切り取り画像も削除されます。"
        "すでに日記へ残した静止画は削除しません。この操作は元に戻せません。"
    )
    yes_col, no_col = st.columns(2, gap="small")
    with yes_col:
        if st.button(
            "削除する",
            type="primary",
            use_container_width=True,
            key=f"video_grid_delete_yes_{photo_id}",
        ):
            try:
                delete_video_and_related_data(video_photo)
                st.session_state["_video_delete_notice"] = "動画を削除しました。"
                st.rerun(scope="app")
            except Exception as exc:
                st.error("動画を削除できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
    with no_col:
        if st.button(
            "キャンセル",
            use_container_width=True,
            key=f"video_grid_delete_no_{photo_id}",
        ):
            st.rerun()


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


def previous_month_key(month_key=None):
    if month_key:
        year, month = [int(x) for x in str(month_key).split("-")]
        first = date(year, month, 1)
    else:
        today = now_jst().date()
        first = date(today.year, today.month, 1)
    return (first - timedelta(days=1)).strftime("%Y-%m")


def _month_has_photo_input(month_key):
    """True when the month has material worth reviewing: a diary or the child's saved words."""
    start, end = month_bounds(month_key)
    client = supabase_client()

    def photo_has_child_words(photo):
        reflection = (photo or {}).get("reflection_json") or {}
        if not isinstance(reflection, dict):
            return False
        if str(reflection.get("child_comment") or "").strip():
            return True
        conversation = reflection.get("conversation") or []
        return any(
            isinstance(turn, dict)
            and turn.get("role") == "child"
            and str(turn.get("text") or "").strip()
            for turn in conversation
        )

    try:
        rows = (
            client
            .table(TRIP_TABLE)
            .select(f"id,{DIARY_TABLE}(id),{PHOTO_TABLE}(id,reflection_json)")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .gte("trip_date", start)
            .lt("trip_date", end)
            .execute()
        ).data or []
        for row in rows:
            diaries = (row or {}).get(DIARY_TABLE) or []
            if isinstance(diaries, dict):
                diaries = [diaries]
            if diaries:
                return True
            photos = (row or {}).get(PHOTO_TABLE) or []
            if isinstance(photos, dict):
                photos = [photos]
            if any(photo_has_child_words(photo) for photo in photos):
                return True
        return False
    except Exception:
        trips = (
            client
            .table(TRIP_TABLE)
            .select("id")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .gte("trip_date", start)
            .lt("trip_date", end)
            .execute()
        ).data or []
        trip_ids = [str(row.get("id")) for row in trips if row.get("id")]
        if not trip_ids:
            return False
        diaries = (
            client
            .table(DIARY_TABLE)
            .select("id")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .in_("trip_id", trip_ids)
            .limit(1)
            .execute()
        ).data or []
        if diaries:
            return True
        photos = (
            client
            .table(PHOTO_TABLE)
            .select("id,reflection_json")
            .eq("family_key", current_family_key()).eq("member_key", current_member_key())
            .in_("trip_id", trip_ids)
            .execute()
        ).data or []
        return any(photo_has_child_words(photo) for photo in photos)


def home_review_attention_needed():
    """Nudge once each month when the immediately preceding month has photo input."""
    current_month = now_jst().strftime("%Y-%m")
    prior_month = previous_month_key(current_month)

    if st.session_state.get("_review_seen_month") == current_month:
        return False

    session_check = st.session_state.get("_home_review_attention_check")
    if isinstance(session_check, dict) and (
        str(session_check.get("month") or "") == current_month
        and str(session_check.get("previous_month") or "") == prior_month
    ):
        return bool(session_check.get("has_previous_content"))

    browser_state = read_browser_review_state()
    if isinstance(browser_state, dict):
        if str(browser_state.get("review_seen_month") or "") == current_month:
            st.session_state["_review_seen_month"] = current_month
            return False
        stored_check = browser_state.get("review_check")
        if isinstance(stored_check, dict) and (
            str(stored_check.get("month") or "") == current_month
            and str(stored_check.get("previous_month") or "") == prior_month
        ):
            st.session_state["_home_review_attention_check"] = dict(stored_check)
            return bool(stored_check.get("has_previous_content"))
    elif browser_persistence_component is not None:
        # Keep the first Home paint DB-free. localStorage returns immediately and
        # triggers a cheap rerun; the monthly DB check happens only after that.
        return False

    try:
        has_previous = _month_has_photo_input(prior_month)
    except Exception:
        has_previous = False

    check = {
        "month": current_month,
        "previous_month": prior_month,
        "has_previous_content": bool(has_previous),
    }
    st.session_state["_home_review_attention_check"] = check
    write_browser_review_check(check)
    return bool(has_previous)


def mark_current_month_review_seen():
    current_month = now_jst().strftime("%Y-%m")
    if st.session_state.get("_review_seen_month") == current_month:
        return
    st.session_state["_review_seen_month"] = current_month
    write_browser_review_seen(current_month)


def format_month_label(month_key):
    try:
        year, month = [int(x) for x in str(month_key).split("-")]
        return f"{year}年{month}月"
    except Exception:
        return str(month_key)


def get_month_bundle(month_key):
    start, end = month_bounds(month_key)
    client = supabase_client()
    try:
        rows = (
            client
            .table(TRIP_TABLE)
            .select(
                f"*,{DIARY_TABLE}(*),"
                f"{PHOTO_TABLE}(id,trip_id,storage_path,captured_at,reflection_json,signals_json)"
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
        .select("id,trip_id,storage_path,captured_at,reflection_json,signals_json")
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
# Monthly replay helpers
# ============================================================
def get_monthly_playback(review):
    if not isinstance(review, dict):
        return {}
    playback = review.get("_playback") or {}
    return dict(playback) if isinstance(playback, dict) else {}


def save_monthly_playback(month_key, review, playback):
    updated = dict(review or {})
    if isinstance(playback, dict) and playback:
        updated["_playback"] = dict(playback)
    else:
        updated.pop("_playback", None)
    save_monthly_review(month_key, updated)
    st.session_state[f"monthly_review_{month_key}"] = updated
    return updated


def _music_library_session_key():
    return f"_music_library_{current_family_key()}_{current_member_key()}"


def _normalize_music_library_item(item):
    item = item if isinstance(item, dict) else {}
    url = str(item.get("youtube_url") or "").strip()
    video_id = str(item.get("video_id") or "").strip() or parse_youtube_video_id(url)
    if not video_id:
        return None
    try:
        start_seconds = max(0, int(item.get("start_seconds") or 0))
    except Exception:
        start_seconds = 0
    try:
        end_seconds = int(item.get("end_seconds") or (start_seconds + 20))
    except Exception:
        end_seconds = start_seconds + 20
    if end_seconds <= start_seconds:
        end_seconds = start_seconds + 20
    return {
        "youtube_url": url or youtube_watch_url(video_id),
        "video_id": video_id,
        "title": str(item.get("title") or "").strip(),
        "author_name": str(item.get("author_name") or "").strip(),
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "reason": str(item.get("reason") or "").strip(),
        "confidence": str(item.get("confidence") or "").strip(),
        "saved_at": str(item.get("saved_at") or item.get("updated_at") or "").strip(),
    }


def get_saved_music_library(force=False):
    """Return the current member's saved YouTube music choices.

    The library lives in one sentinel row of the existing monthly-review table, so
    no new Supabase table or migration is required. It is still isolated by family/member.
    """
    cache_key = _music_library_session_key()
    if not force and isinstance(st.session_state.get(cache_key), list):
        return list(st.session_state.get(cache_key) or [])

    result = (
        supabase_client()
        .table(MONTHLY_TABLE)
        .select("id,review_json,updated_at")
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .eq("review_month", MUSIC_LIBRARY_REVIEW_DATE)
        .limit(1)
        .execute()
    )
    row = (result.data or [None])[0]
    review_json = (row or {}).get("review_json") or {}
    raw_items = review_json.get("items") if isinstance(review_json, dict) else []
    raw_items = raw_items if isinstance(raw_items, list) else []
    items = []
    seen = set()
    for raw in raw_items:
        item = _normalize_music_library_item(raw)
        if not item:
            continue
        key = item["video_id"]
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    st.session_state[cache_key] = items
    return list(items)


def _write_saved_music_library(items):
    normalized = []
    seen = set()
    for raw in list(items or [])[:50]:
        item = _normalize_music_library_item(raw)
        if not item or item["video_id"] in seen:
            continue
        seen.add(item["video_id"])
        normalized.append(item)

    client = supabase_client()
    existing = (
        client.table(MONTHLY_TABLE)
        .select("id")
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .eq("review_month", MUSIC_LIBRARY_REVIEW_DATE)
        .limit(1)
        .execute()
    )
    row = (existing.data or [None])[0]
    now_value = now_jst().isoformat()
    payload = {
        "family_key": current_family_key(),
        "member_key": current_member_key(),
        "review_month": MUSIC_LIBRARY_REVIEW_DATE,
        "review_json": {"_record_type": "music_library", "items": normalized},
        "updated_at": now_value,
    }
    if row:
        (
            client.table(MONTHLY_TABLE)
            .update(payload)
            .eq("id", row["id"])
            .eq("family_key", current_family_key())
            .eq("member_key", current_member_key())
            .execute()
        )
    else:
        payload["created_at"] = now_value
        client.table(MONTHLY_TABLE).insert(payload).execute()
    st.session_state[_music_library_session_key()] = normalized
    return normalized


def save_music_to_library(playback):
    item = _normalize_music_library_item(playback)
    if not item:
        raise ValueError("保存できるYouTube音楽が設定されていません。")
    meta = fetch_youtube_oembed(item.get("youtube_url"))
    if meta:
        item["title"] = str(meta.get("title") or item.get("title") or "").strip()
        item["author_name"] = str(meta.get("author_name") or item.get("author_name") or "").strip()
    if not item.get("title"):
        item["title"] = f"YouTube音楽 {item['video_id']}"
    item["saved_at"] = now_jst().isoformat()

    items = get_saved_music_library(force=True)
    items = [x for x in items if str(x.get("video_id") or "") != item["video_id"]]
    items.insert(0, item)
    _write_saved_music_library(items)
    return item


def music_library_label(item):
    item = item if isinstance(item, dict) else {}
    title = str(item.get("title") or item.get("video_id") or "保存した音楽").strip()
    author = str(item.get("author_name") or "").strip()
    start_seconds = int(item.get("start_seconds") or 0)
    end_seconds = int(item.get("end_seconds") or (start_seconds + 20))
    prefix = f"{title} / {author}" if author else title
    return f"{prefix}（{format_mmss(start_seconds)}〜{format_mmss(end_seconds)}）"


def apply_music_library_item(month_key, review, item):
    item = _normalize_music_library_item(item)
    if not item:
        raise ValueError("保存した音楽を読み込めませんでした。")
    state = _monthly_replay_state(month_key, review)
    st.session_state[state["url_key"]] = item["youtube_url"]
    st.session_state[state["start_key"]] = int(item["start_seconds"])
    st.session_state[state["end_key"]] = int(item["end_seconds"])
    st.session_state[state["reason_key"]] = str(item.get("reason") or "")
    st.session_state[state["confidence_key"]] = str(item.get("confidence") or "saved")
    st.session_state[state["title_key"]] = str(item.get("title") or "")
    playback = dict(item)
    playback["updated_at"] = now_jst().isoformat()
    playback["source"] = "saved_library"
    save_monthly_playback(month_key, review, playback)
    st.session_state[f"monthly_replay_applied_{month_key}"] = {
        "start_seconds": int(item["start_seconds"]),
        "end_seconds": int(item["end_seconds"]),
    }
    return playback


def format_mmss(total_seconds):
    try:
        total_seconds = max(0, int(total_seconds))
    except Exception:
        total_seconds = 0
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def parse_youtube_video_id(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if len(value) == 11 and all(ch.isalnum() or ch in {"-", "_"} for ch in value):
        return value
    try:
        parsed = urlparse(value)
    except Exception:
        return ""
    host = str(parsed.netloc or "").lower()
    path = str(parsed.path or "")
    query = parse_qs(parsed.query or "")
    video_id = ""
    if "youtu.be" in host:
        video_id = path.strip("/").split("/")[0]
    elif "youtube.com" in host or "youtube-nocookie.com" in host:
        if path == "/watch":
            video_id = (query.get("v") or [""])[0]
        elif path.startswith("/embed/"):
            video_id = path.split("/embed/", 1)[1].split("/")[0]
        elif path.startswith("/shorts/"):
            video_id = path.split("/shorts/", 1)[1].split("/")[0]
        elif path.startswith("/live/"):
            video_id = path.split("/live/", 1)[1].split("/")[0]
    video_id = "".join(ch for ch in str(video_id) if ch.isalnum() or ch in {"-", "_"})
    return video_id if 8 <= len(video_id) <= 15 else ""


def youtube_watch_url(video_id):
    video_id = str(video_id or "").strip()
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else ""


def youtube_embed_url(video_id, start_seconds=0, end_seconds=0, autoplay=False):
    video_id = str(video_id or "").strip()
    if not video_id:
        return ""
    params = {
        "start": max(0, int(start_seconds or 0)),
        "autoplay": 1 if autoplay else 0,
        "controls": 1,
        "rel": 0,
        "modestbranding": 1,
        "playsinline": 1,
    }
    end_seconds = int(end_seconds or 0)
    if end_seconds > params["start"]:
        params["end"] = end_seconds
    return f"https://www.youtube.com/embed/{video_id}?{urlencode(params)}"


def fetch_youtube_oembed(url):
    url = str(url or "").strip()
    if not url:
        return {}
    api_url = "https://www.youtube.com/oembed?" + urlencode({"url": url, "format": "json"})
    request = Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8", "ignore"))
        if isinstance(data, dict):
            return {
                "title": str(data.get("title") or "").strip(),
                "author_name": str(data.get("author_name") or "").strip(),
            }
    except Exception:
        return {}
    return {}


def guess_monthly_replay_window(youtube_url, month_key, review):
    meta = fetch_youtube_oembed(youtube_url)
    themes = []
    if isinstance(review, dict):
        for item in review.get("findings", []) or []:
            if isinstance(item, dict):
                theme = str(item.get("theme") or "").strip()
                if theme:
                    themes.append(theme)
    review_hint = " / ".join(themes[:3]) or str((review or {}).get("opening") or "").strip() or "特記事項なし"
    schema = {
        "type": "object",
        "properties": {
            "start_seconds": {"type": "integer"},
            "end_seconds": {"type": "integer"},
            "reason": {"type": "string"},
            "confidence": {"type": "string"},
        },
        "required": ["start_seconds", "end_seconds", "reason", "confidence"],
        "additionalProperties": False,
    }
    title = str(meta.get("title") or "").strip()
    author = str(meta.get("author_name") or "").strip()
    prompt = f"""
あなたは、月ごとの写真振り返りで使うYouTube音楽の『おすすめ区間』を提案します。
目的は、アプリ内で9:16の写真スライドを見返すときに、耳に残りやすい部分を短く使うことです。

入力:
- 対象期間: {month_key}
- YouTube URL: {youtube_url}
- 分かる場合のタイトル: {title or '不明'}
- 分かる場合の投稿者: {author or '不明'}
- その月の振り返り要点: {review_hint}

ルール:
- できるだけサビ・フック・いちばん印象に残りやすい部分を優先する。
- 曲や動画の正確な構成が分からない場合は、一般的なポップスの流れをもとに慎重に推測する。
- 使う長さは12〜25秒。理想は18〜22秒。
- start_seconds は0以上600以下。
- end_seconds は start_seconds より後にする。
- reason は日本語で60文字以内、簡潔に。
- confidence は low / medium / high のいずれか。
- 実在確認できないことを断定しない。推測であることを前提に、もっとも無難な候補を1つだけ返す。
""".strip()
    try:
        result = ask_json(prompt, "burari_monthly_replay_window", schema, 280)
    except Exception:
        result = {}
    start = max(0, min(600, int(result.get("start_seconds") or 48)))
    end = int(result.get("end_seconds") or (start + 20))
    if end <= start:
        end = start + 20
    end = max(start + 12, min(start + 25, end))
    end = min(620, end)
    reason = str(result.get("reason") or "一般的なサビ位置をもとに推測しました。").strip()
    confidence = str(result.get("confidence") or "low").strip().lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"
    return {
        "youtube_url": youtube_url,
        "video_id": parse_youtube_video_id(youtube_url),
        "title": title,
        "author_name": author,
        "start_seconds": start,
        "end_seconds": end,
        "reason": reason,
        "confidence": confidence,
        "updated_at": now_jst().isoformat(),
        "source": "ai_guess",
    }


def build_monthly_replay_photo_items(bundle, limit=18):
    trip_map = {str(t.get("id")): t for t in (bundle or {}).get("trips", []) if isinstance(t, dict) and t.get("id")}
    photos = [p for p in (bundle or {}).get("photos", []) if isinstance(p, dict)]
    photos.sort(key=lambda p: (
        str(trip_map.get(str(p.get("trip_id")), {}).get("trip_date") or ""),
        str(p.get("captured_at") or ""),
        str(p.get("id") or ""),
    ))
    if not photos:
        return []
    if len(photos) > limit:
        step = len(photos) / float(limit)
        picked = []
        seen = set()
        for idx in range(limit):
            item = photos[min(int(idx * step), len(photos) - 1)]
            key = str(item.get("id") or idx)
            if key not in seen:
                picked.append(item)
                seen.add(key)
        photos = picked or photos[:limit]
    signed_map = signed_photo_url_map([str(p.get("storage_path") or "") for p in photos], expires_in=1800)
    items = []
    for idx, photo in enumerate(photos, start=1):
        url = photo_display_url(photo, signed_map=signed_map, max_px=1080, quality=86)
        if not url:
            continue
        trip = trip_map.get(str(photo.get("trip_id")), {})
        label_bits = []
        trip_date = str(trip.get("trip_date") or "").strip()
        place = str(photo_location_label(photo) or trip.get("destination") or "").strip()
        if trip_date:
            label_bits.append(trip_date)
        if place:
            label_bits.append(place)
        caption = " / ".join(label_bits) or f"写真{idx}"
        items.append({"url": url, "caption": caption})
    return items


def monthly_playback_is_ready(playback):
    if not isinstance(playback, dict):
        return False
    video_id = str(playback.get("video_id") or "").strip() or parse_youtube_video_id(playback.get("youtube_url"))
    if not video_id:
        return False
    try:
        start_seconds = max(0, int(playback.get("start_seconds") or 0))
        end_seconds = int(playback.get("end_seconds") or 0)
    except Exception:
        return False
    return end_seconds > start_seconds


def render_monthly_replay_player(period_label, review, playback, photo_items):
    if not photo_items:
        return
    video_id = str((playback or {}).get("video_id") or "").strip() or parse_youtube_video_id((playback or {}).get("youtube_url"))
    if not video_id:
        return
    start_seconds = max(0, int((playback or {}).get("start_seconds") or 0))
    end_seconds = int((playback or {}).get("end_seconds") or (start_seconds + 20))
    if end_seconds <= start_seconds:
        end_seconds = start_seconds + 20
    duration_seconds = max(1, end_seconds - start_seconds)
    # Show every photo at least once when possible, but cap each photo at 2.5s so
    # a small set of photos naturally loops again while a longer music segment is playing.
    # Photo cycling is never used as the stop condition; only the music end time stops playback.
    display_ms = max(900, min(2500, int(max(1, duration_seconds) * 1000 / max(1, len(photo_items)))))
    period_label_escaped = html.escape(str(period_label or "期間の振り返り"))
    first_caption = html.escape(str(photo_items[0].get("caption") or "")) if photo_items else ""
    payload = json.dumps(photo_items, ensure_ascii=False)
    component_html = f"""
    <style>
      .burari-replay-wrap {{
        border: 1px solid rgba(128,128,128,.16);
        border-radius: 22px;
        padding: .12rem;
        margin: .24rem 0 .8rem;
        box-sizing: border-box;
        background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(246,249,252,.96));
      }}
      .burari-replay-phone {{
        width: min(480px, 100%);
        max-width: 480px;
        box-sizing: border-box;
        margin: 0 auto .8rem;
        padding: 6px;
        border-radius: 28px;
        background: #111827;
        box-shadow: 0 16px 32px rgba(17,24,39,.18);
      }}
      .burari-replay-stage {{
        position: relative;
        width: 100%;
        aspect-ratio: 9 / 16;
        overflow: hidden;
        border-radius: 22px;
        background: #0f172a;
      }}
      .burari-replay-stage img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }}
      .burari-replay-top {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        padding: 14px 14px 34px;
        color: #fff;
        background: linear-gradient(180deg, rgba(0,0,0,.65), rgba(0,0,0,0));
        text-shadow: 0 1px 3px rgba(0,0,0,.45);
      }}
      .burari-replay-kicker {{ font-size: 12px; opacity: .86; letter-spacing: .04em; }}
      .burari-replay-title {{ font-size: 20px; font-weight: 800; line-height: 1.25; margin-top: 4px; }}
      .burari-replay-bottom {{
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 34px 14px 14px;
        color: #fff;
        background: linear-gradient(180deg, rgba(0,0,0,0), rgba(0,0,0,.72));
        text-shadow: 0 1px 3px rgba(0,0,0,.45);
      }}
      .burari-replay-caption {{ font-size: 13px; line-height: 1.45; }}
      .burari-replay-progress {{ font-size: 12px; opacity: .86; margin-top: 4px; }}
      .burari-replay-controls {{ display: flex; gap: .42rem; margin-top: .72rem; }}
      .burari-replay-controls button {{
        flex: 1;
        min-width: 0;
        border: 0;
        border-radius: 999px;
        padding: .72rem .48rem;
        font-size: 13px;
        font-weight: 750;
        white-space: nowrap;
        cursor: pointer;
      }}
      #burariReplayStart {{ background: #2563eb; color: #fff; }}
      #burariReplayStop {{ background: #fee2e2; color: #991b1b; }}
      #burariReplayAgain {{ background: #e5edf8; color: #123; }}
      .burari-replay-meta {{ text-align: center; font-size: 13px; margin-bottom: .65rem; }}
      .burari-replay-player-wrap {{
        max-width: 356px;
        margin: .55rem auto 0;
        padding: 7px;
        border-radius: 16px;
        background: rgba(17,24,39,.06);
        border: 1px solid rgba(128,128,128,.16);
      }}
      .burari-replay-player-label {{
        text-align: center;
        font-size: 11px;
        opacity: .68;
        margin: 0 0 5px;
      }}
      #burariReplayPlayer {{
        display: block;
        width: 100%;
        height: 200px;
        border: 0;
        border-radius: 11px;
        background: #000;
        overflow: hidden;
      }}
      .burari-replay-note {{ max-width: 356px; margin: .42rem auto 0; font-size: 11px; opacity: .72; text-align: center; }}
      .burari-replay-status {{ text-align:center; font-size:12px; margin:.45rem 0 0; opacity:.78; }}
    </style>
    <div class="burari-replay-wrap">
      <div class="burari-replay-phone">
        <div class="burari-replay-stage">
          <img id="burariReplayImage" src="{html.escape(str(photo_items[0].get('url') or ''))}" alt="期間の振り返り写真" />
          <div class="burari-replay-top">
            <div class="burari-replay-kicker">まとめた期間の振り返り</div>
            <div class="burari-replay-title">{period_label_escaped}</div>
          </div>
          <div class="burari-replay-bottom">
            <div class="burari-replay-caption" id="burariReplayCaption">{first_caption}</div>
            <div class="burari-replay-progress" id="burariReplayProgress">1 / {len(photo_items)}</div>
          </div>
        </div>
        <div class="burari-replay-controls">
          <button id="burariReplayStart" type="button">▶ 再生</button>
          <button id="burariReplayStop" type="button">■ 中断</button>
          <button id="burariReplayAgain" type="button">↻ 最初から</button>
        </div>
      </div>
      <div class="burari-replay-meta">音楽区間：{format_mmss(start_seconds)}〜{format_mmss(end_seconds)} ／ 写真 {len(photo_items)}枚</div>
      <div class="burari-replay-player-wrap">
        <div class="burari-replay-player-label">YouTube 音楽</div>
        <div id="burariReplayPlayer"></div>
      </div>
      <div class="burari-replay-status" id="burariReplayStatus">再生すると {format_mmss(start_seconds)} から始まり、{format_mmss(end_seconds)} まで写真を繰り返します。</div>
      <div class="burari-replay-note">YouTubeの仕様上、再生中の公式プレーヤーは完全には隠さず、最小限の大きさで表示します。</div>
    </div>
    <script>
      const burariSlides = {payload};
      const burariVideoId = {json.dumps(video_id)};
      const burariStartSeconds = {start_seconds};
      const burariEndSeconds = {end_seconds};
      const burariDisplayMs = {display_ms};
      const burariDurationMs = {duration_seconds * 1000};
      let burariIndex = 0;
      let burariTimer = null;
      let burariMusicWatchTimer = null;
      let burariFallbackEndTimer = null;
      let burariPositionTimer = null;
      let burariPlayer = null;
      let burariPlayerReady = false;
      let burariPendingStart = false;
      let burariWaitingForRequestedPosition = false;
      let burariSlideLoopStarted = false;
      const burariImg = document.getElementById('burariReplayImage');
      const burariCaption = document.getElementById('burariReplayCaption');
      const burariProgress = document.getElementById('burariReplayProgress');
      const burariStatus = document.getElementById('burariReplayStatus');

      function burariShowSlide(index) {{
        if (!burariSlides.length) return;
        const safeIndex = ((index % burariSlides.length) + burariSlides.length) % burariSlides.length;
        const item = burariSlides[safeIndex] || {{}};
        if (item.url) burariImg.src = item.url;
        burariCaption.textContent = item.caption || '';
        burariProgress.textContent = `${{safeIndex + 1}} / ${{burariSlides.length}}`;
      }}

      function burariStopTimers() {{
        if (burariTimer) {{
          clearInterval(burariTimer);
          burariTimer = null;
        }}
        if (burariMusicWatchTimer) {{
          clearInterval(burariMusicWatchTimer);
          burariMusicWatchTimer = null;
        }}
        if (burariFallbackEndTimer) {{
          clearTimeout(burariFallbackEndTimer);
          burariFallbackEndTimer = null;
        }}
        if (burariPositionTimer) {{
          clearTimeout(burariPositionTimer);
          burariPositionTimer = null;
        }}
      }}

      function burariStopAtEnd() {{
        burariStopTimers();
        burariPendingStart = false;
        burariWaitingForRequestedPosition = false;
        burariSlideLoopStarted = false;
        try {{
          if (burariPlayer && typeof burariPlayer.pauseVideo === 'function') {{
            burariPlayer.pauseVideo();
          }}
        }} catch (_) {{}}
        if (burariStatus) burariStatus.textContent = `終了：${{burariEndSeconds}}秒で停止しました。`;
      }}

      function burariInterrupt() {{
        burariStopTimers();
        burariPendingStart = false;
        burariWaitingForRequestedPosition = false;
        burariSlideLoopStarted = false;
        try {{
          if (burariPlayer && typeof burariPlayer.pauseVideo === 'function') {{
            burariPlayer.pauseVideo();
          }}
        }} catch (_) {{}}
        if (burariStatus) burariStatus.textContent = '中断しました。▶ 再生で指定区間の最初から再生できます。';
      }}

      function burariStartSlideLoopOnce() {{
        // Photo motion must not depend on YouTube's position-confirmation event.
        // A newly changed video can take a moment to emit PLAYING/currentTime,
        // but the slideshow should still start reliably from the user's click.
        if (burariSlideLoopStarted) return;
        burariSlideLoopStarted = true;
        if (burariSlides.length > 1) {{
          burariTimer = setInterval(() => {{
            burariIndex = (burariIndex + 1) % burariSlides.length;
            burariShowSlide(burariIndex);
          }}, burariDisplayMs);
        }}
      }}

      function burariStartMusicEndWatch() {{
        // The photo list may loop any number of times. It must never decide when the
        // music stops. Watch YouTube's real playback position and stop only when the
        // requested end second is actually reached.
        if (burariMusicWatchTimer) {{
          clearInterval(burariMusicWatchTimer);
          burariMusicWatchTimer = null;
        }}
        if (burariFallbackEndTimer) {{
          clearTimeout(burariFallbackEndTimer);
          burariFallbackEndTimer = null;
        }}
        burariMusicWatchTimer = setInterval(() => {{
          try {{
            if (!burariPlayer || typeof burariPlayer.getCurrentTime !== 'function') return;
            const current = Number(burariPlayer.getCurrentTime());
            if (Number.isFinite(current) && current >= burariEndSeconds - 0.12) {{
              burariStopAtEnd();
            }}
          }} catch (_) {{}}
        }}, 180);

        // Very generous safety net for browsers that stop reporting currentTime.
        // It is intentionally much longer than the requested segment so buffering
        // cannot make the slideshow/music stop early.
        const fallbackMs = Math.max(15000, burariDurationMs * 3 + 10000);
        burariFallbackEndTimer = setTimeout(() => {{
          let current = -1;
          try {{ current = Number(burariPlayer && burariPlayer.getCurrentTime ? burariPlayer.getCurrentTime() : -1); }} catch (_) {{}}
          if (!Number.isFinite(current) || current >= burariEndSeconds - 0.5) {{
            burariStopAtEnd();
          }}
        }}, fallbackMs);
      }}

      function burariConfirmRequestedPosition(attempt = 0) {{
        if (!burariPlayer || !burariPlayerReady) return;
        let current = -1;
        try {{ current = Number(burariPlayer.getCurrentTime()); }} catch (_) {{}}
        const closeEnough = Number.isFinite(current) && Math.abs(current - burariStartSeconds) <= 2.0;
        if (closeEnough) {{
          burariWaitingForRequestedPosition = false;
          burariStartMusicEndWatch();
          if (burariStatus) burariStatus.textContent = `再生中：${{burariStartSeconds}}秒 → ${{burariEndSeconds}}秒`;
          return;
        }}
        if (attempt >= 8) {{
          try {{ burariPlayer.seekTo(burariStartSeconds, true); }} catch (_) {{}}
          burariWaitingForRequestedPosition = false;
          burariStartMusicEndWatch();
          if (burariStatus) burariStatus.textContent = `再生中：${{burariStartSeconds}}秒 → ${{burariEndSeconds}}秒`;
          return;
        }}
        try {{ burariPlayer.seekTo(burariStartSeconds, true); }} catch (_) {{}}
        burariPositionTimer = setTimeout(() => burariConfirmRequestedPosition(attempt + 1), 220);
      }}

      function burariActuallyStart() {{
        if (!burariPlayerReady || !burariPlayer) {{
          burariPendingStart = true;
          if (burariStatus) burariStatus.textContent = 'YouTubeプレーヤーを準備しています…';
          return;
        }}
        burariPendingStart = false;
        burariStopTimers();
        burariWaitingForRequestedPosition = true;
        burariSlideLoopStarted = false;
        burariIndex = 0;
        burariShowSlide(burariIndex);
        // Start the photo slideshow immediately and independently. This fixes the
        // changed-music case where YouTube plays but its PLAYING/currentTime event
        // arrives late or not at all inside the embedded iframe.
        burariStartSlideLoopOnce();
        if (burariStatus) burariStatus.textContent = `指定位置 ${{burariStartSeconds}}秒へ移動しています…`;
        // The slideshow is intentionally independent from YouTube readiness.
        // A separate currentTime watcher below controls the real end of playback.
        try {{
          burariPlayer.loadVideoById({{
            videoId: burariVideoId,
            startSeconds: burariStartSeconds,
            endSeconds: burariEndSeconds,
          }});
        }} catch (_) {{
          try {{
            burariPlayer.seekTo(burariStartSeconds, true);
            burariPlayer.playVideo();
          }} catch (_) {{}}
        }}
      }}

      window.onYouTubeIframeAPIReady = function() {{
        burariPlayer = new YT.Player('burariReplayPlayer', {{
          width: '100%',
          height: '200',
          playerVars: {{
            controls: 1,
            rel: 0,
            playsinline: 1,
            modestbranding: 1,
          }},
          events: {{
            onReady: function() {{
              burariPlayerReady = true;
              try {{
                burariPlayer.cueVideoById({{
                  videoId: burariVideoId,
                  startSeconds: burariStartSeconds,
                  endSeconds: burariEndSeconds,
                }});
              }} catch (_) {{}}
              if (burariPendingStart) burariActuallyStart();
            }},
            onStateChange: function(event) {{
              if (!window.YT) return;
              if (event.data === YT.PlayerState.PLAYING) {{
                if (burariWaitingForRequestedPosition) {{
                  burariConfirmRequestedPosition(0);
                }} else if (!burariMusicWatchTimer) {{
                  burariStartMusicEndWatch();
                }}
              }} else if (event.data === YT.PlayerState.ENDED) {{
                // ENDED is a YouTube-side end signal (requested segment or source video).
                // A completed photo cycle never reaches this branch and never stops music.
                burariStopAtEnd();
              }}
            }}
          }}
        }});
      }};

      const burariApiScript = document.createElement('script');
      burariApiScript.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(burariApiScript);

      document.getElementById('burariReplayStart').addEventListener('click', burariActuallyStart);
      document.getElementById('burariReplayStop').addEventListener('click', burariInterrupt);
      document.getElementById('burariReplayAgain').addEventListener('click', burariActuallyStart);
      burariShowSlide(0);
    </script>
    """
    st.components.v1.html(component_html, height=1180, scrolling=False)


def _monthly_replay_state(month_key, review):
    playback = get_monthly_playback(review)
    url_key = f"monthly_replay_url_{month_key}"
    start_key = f"monthly_replay_start_{month_key}"
    end_key = f"monthly_replay_end_{month_key}"
    reason_key = f"monthly_replay_reason_{month_key}"
    confidence_key = f"monthly_replay_confidence_{month_key}"
    title_key = f"monthly_replay_title_{month_key}"

    if url_key not in st.session_state:
        st.session_state[url_key] = str(playback.get("youtube_url") or "")
    if start_key not in st.session_state:
        raw_start = playback.get("start_seconds")
        st.session_state[start_key] = int(raw_start if raw_start is not None else 48)
    if end_key not in st.session_state:
        raw_end = playback.get("end_seconds")
        st.session_state[end_key] = int(raw_end if raw_end is not None else 68)
    if reason_key not in st.session_state:
        st.session_state[reason_key] = str(playback.get("reason") or "")
    if confidence_key not in st.session_state:
        st.session_state[confidence_key] = str(playback.get("confidence") or "")
    if title_key not in st.session_state:
        st.session_state[title_key] = str(playback.get("title") or "")

    return {
        "playback": playback,
        "url_key": url_key,
        "start_key": start_key,
        "end_key": end_key,
        "reason_key": reason_key,
        "confidence_key": confidence_key,
        "title_key": title_key,
    }


def render_monthly_music_settings(month_key, bundle, review, expanded=True):
    photo_items = build_monthly_replay_photo_items(bundle, limit=18)
    state = _monthly_replay_state(month_key, review)
    playback = state["playback"]
    url_key = state["url_key"]
    start_key = state["start_key"]
    end_key = state["end_key"]
    reason_key = state["reason_key"]
    confidence_key = state["confidence_key"]
    title_key = state["title_key"]

    with st.expander("YouTubeの音楽と再生設定", expanded=expanded):
        if photo_items:
            st.write(f"使う写真：**{len(photo_items)}枚**")
        else:
            st.warning("この期間には再生に使える写真がありません。音楽は設定できますが、写真ムービーは表示できません。")

        try:
            saved_music = get_saved_music_library()
        except Exception:
            saved_music = []
        if saved_music:
            st.markdown("**保存した音楽から選ぶ**")
            saved_choice_key = f"monthly_saved_music_choice_{month_key}"
            selected_index = st.selectbox(
                "保存した音楽",
                options=list(range(len(saved_music))),
                format_func=lambda idx: music_library_label(saved_music[idx]),
                key=saved_choice_key,
                label_visibility="collapsed",
            )
            if st.button(
                "この音楽を使う",
                type="primary",
                use_container_width=True,
                key=f"monthly_use_saved_music_{month_key}",
            ):
                try:
                    selected = saved_music[int(selected_index)]
                    apply_music_library_item(month_key, review, selected)
                    st.session_state[f"monthly_music_settings_open_{month_key}"] = False
                    st.success(f"『{selected.get('title') or '保存した音楽'}』を設定しました。")
                    st.rerun()
                except Exception as exc:
                    st.error("保存した音楽を設定できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))
            st.divider()

        st.text_input(
            "YouTube URL",
            key=url_key,
            placeholder="https://www.youtube.com/watch?v=...",
        )
        current_url = str(st.session_state.get(url_key) or "").strip()
        video_id = parse_youtube_video_id(current_url)
        if current_url and not video_id:
            st.warning("YouTube URLの形式を読み取れませんでした。通常の共有URLか埋め込みURLを入れてください。")
        elif video_id:
            st.caption(f"再生対象: {youtube_watch_url(video_id)}")

        if st.button("AIにおすすめ時間を推測", use_container_width=True, key=f"guess_monthly_replay_{month_key}"):
            if not video_id:
                st.error("先に有効なYouTube URLを入力してください。")
            else:
                try:
                    with st.spinner("AIがサビ候補を推測しています…"):
                        guessed = guess_monthly_replay_window(current_url, month_key, review)
                    st.session_state[start_key] = int(guessed.get("start_seconds") or 48)
                    st.session_state[end_key] = int(guessed.get("end_seconds") or 68)
                    st.session_state[reason_key] = str(guessed.get("reason") or "")
                    st.session_state[confidence_key] = str(guessed.get("confidence") or "")
                    st.session_state[title_key] = str(guessed.get("title") or "")
                    save_monthly_playback(month_key, review, guessed)
                    st.session_state[f"monthly_replay_applied_{month_key}"] = {
                        "start_seconds": int(st.session_state[start_key]),
                        "end_seconds": int(st.session_state[end_key]),
                    }
                    st.session_state[f"monthly_music_settings_open_{month_key}"] = False
                    st.success(f"おすすめ区間を {format_mmss(st.session_state[start_key])}〜{format_mmss(st.session_state[end_key])} に設定しました。")
                    st.rerun()
                except Exception as exc:
                    st.error("おすすめ時間を推測できませんでした。")
                    with st.expander("保護者向け詳細"):
                        st.code(str(exc))

        st.number_input("開始（秒）", min_value=0, step=1, key=start_key)
        st.number_input("終了（秒）", min_value=1, step=1, key=end_key)
        start_seconds = max(0, int(st.session_state.get(start_key) or 0))
        end_seconds = int(st.session_state.get(end_key) or (start_seconds + 20))
        if end_seconds <= start_seconds:
            st.warning("終了は開始より後にしてください。保存時に自動調整されます。")
        st.caption(f"入力中の区間: {format_mmss(start_seconds)}〜{format_mmss(max(end_seconds, start_seconds + 1))}")

        apply_cols = st.columns([1.4, 1])
        with apply_cols[0]:
            if st.button(
                "この時間を再生に反映",
                type="primary",
                use_container_width=True,
                key=f"apply_monthly_replay_time_{month_key}",
            ):
                if not video_id:
                    st.error("先に有効なYouTube URLを入力してください。")
                else:
                    start_seconds = max(0, int(st.session_state.get(start_key) or 0))
                    end_seconds = int(st.session_state.get(end_key) or (start_seconds + 20))
                    if end_seconds <= start_seconds:
                        end_seconds = start_seconds + 20
                        st.session_state[end_key] = end_seconds
                    meta = fetch_youtube_oembed(current_url)
                    applied_payload = {
                        "youtube_url": current_url,
                        "video_id": video_id,
                        "title": str(meta.get("title") or st.session_state.get(title_key) or "").strip(),
                        "author_name": str(meta.get("author_name") or "").strip(),
                        "start_seconds": start_seconds,
                        "end_seconds": end_seconds,
                        "reason": str(st.session_state.get(reason_key) or "").strip(),
                        "confidence": "manual",
                        "updated_at": now_jst().isoformat(),
                        "source": "manual",
                    }
                    save_monthly_playback(month_key, review, applied_payload)
                    st.session_state[f"monthly_replay_applied_{month_key}"] = {
                        "start_seconds": start_seconds,
                        "end_seconds": end_seconds,
                    }
                    st.session_state[confidence_key] = "manual"
                    st.session_state[f"monthly_music_settings_open_{month_key}"] = False
                    st.success(f"{format_mmss(start_seconds)}〜{format_mmss(end_seconds)} を再生に反映しました。")
                    st.rerun()
        with apply_cols[1]:
            if st.button("再生設定を消す", use_container_width=True, key=f"clear_monthly_replay_{month_key}"):
                st.session_state[url_key] = ""
                st.session_state[start_key] = 48
                st.session_state[end_key] = 68
                st.session_state[reason_key] = ""
                st.session_state[confidence_key] = ""
                st.session_state[title_key] = ""
                st.session_state.pop(f"monthly_replay_applied_{month_key}", None)
                st.session_state[f"monthly_music_settings_open_{month_key}"] = True
                save_monthly_playback(month_key, review, {})
                st.success("この期間の再生設定を消しました。")
                st.rerun()

        applied = st.session_state.get(f"monthly_replay_applied_{month_key}")
        if not isinstance(applied, dict):
            applied = {
                "start_seconds": int(playback.get("start_seconds") or start_seconds),
                "end_seconds": int(playback.get("end_seconds") or end_seconds),
            }
        st.caption(
            f"再生に反映中: {format_mmss(applied.get('start_seconds'))}〜{format_mmss(applied.get('end_seconds'))}"
        )
        if st.session_state.get(title_key):
            st.write(f"候補タイトル: **{st.session_state[title_key]}**")
        reason = str(st.session_state.get(reason_key) or "").strip()
        confidence = str(st.session_state.get(confidence_key) or "").strip()
        if reason:
            confidence_label = {"low": "低め", "medium": "中くらい", "high": "高め", "manual": "手動"}.get(confidence, confidence)
            st.caption(f"AIメモ: {reason}（確からしさ: {confidence_label or '不明'}）")
        st.caption("※ サビ候補はAIの推測です。曲によって外れることがあります。必要なら秒数を手で直してください。")


def render_monthly_time_settings(month_key, review):
    """Edit only the current music's playback window.

    The time editor intentionally uses dedicated widget keys. This prevents stale
    values from the full music-settings form from overriding the interval that is
    actually applied to the replay.
    """
    state = _monthly_replay_state(month_key, review)
    playback = get_monthly_playback(review) or state["playback"]
    current_url = str(st.session_state.get(state["url_key"]) or playback.get("youtube_url") or "").strip()
    video_id = str(playback.get("video_id") or "").strip() or parse_youtube_video_id(current_url)
    if not video_id:
        st.warning("先に音楽を設定してください。")
        return

    edit_start_key = f"monthly_time_edit_start_{month_key}"
    edit_end_key = f"monthly_time_edit_end_{month_key}"

    # If this view was restored without going through the open button, initialize
    # it from the interval currently used by the replay.
    applied = st.session_state.get(f"monthly_replay_applied_{month_key}")
    if isinstance(applied, dict):
        current_start = max(0, int(applied.get("start_seconds") if applied.get("start_seconds") is not None else 0))
        current_end = int(applied.get("end_seconds") if applied.get("end_seconds") is not None else current_start + 20)
    else:
        raw_start = playback.get("start_seconds")
        raw_end = playback.get("end_seconds")
        current_start = max(0, int(raw_start if raw_start is not None else st.session_state.get(state["start_key"], 0)))
        current_end = int(raw_end if raw_end is not None else st.session_state.get(state["end_key"], current_start + 20))
    if current_end <= current_start:
        current_end = current_start + 20

    if edit_start_key not in st.session_state:
        st.session_state[edit_start_key] = current_start
    if edit_end_key not in st.session_state:
        st.session_state[edit_end_key] = current_end

    with st.container(border=True):
        st.markdown("**音楽を再生する時間**")
        st.caption(f"現在の再生設定：{format_mmss(current_start)}〜{format_mmss(current_end)}")
        st.number_input("開始（秒）", min_value=0, step=1, key=edit_start_key)
        st.number_input("終了（秒）", min_value=1, step=1, key=edit_end_key)
        start_seconds = max(0, int(st.session_state.get(edit_start_key) or 0))
        end_seconds = int(st.session_state.get(edit_end_key) or (start_seconds + 20))
        if end_seconds <= start_seconds:
            st.warning("終了は開始より後にしてください。反映時は開始から20秒後に自動調整します。")
        display_end = end_seconds if end_seconds > start_seconds else start_seconds + 20
        st.caption(f"変更後：{format_mmss(start_seconds)}〜{format_mmss(display_end)}")
        if st.button(
            "この時間を再生に反映",
            type="primary",
            use_container_width=True,
            key=f"apply_monthly_time_only_{month_key}",
        ):
            if end_seconds <= start_seconds:
                end_seconds = start_seconds + 20

            updated = dict(playback or {})
            updated.update({
                "youtube_url": current_url,
                "video_id": video_id,
                "title": str(st.session_state.get(state["title_key"]) or playback.get("title") or "").strip(),
                "author_name": str(playback.get("author_name") or "").strip(),
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "reason": str(st.session_state.get(state["reason_key"]) or playback.get("reason") or "").strip(),
                "confidence": "manual",
                "updated_at": now_jst().isoformat(),
                "source": "manual_time",
            })
            save_monthly_playback(month_key, review, updated)

            # Keep every replay source in sync so the next rerun immediately uses
            # the newly entered interval.
            st.session_state[state["start_key"]] = start_seconds
            st.session_state[state["end_key"]] = end_seconds
            st.session_state[state["confidence_key"]] = "manual"
            st.session_state[f"monthly_replay_applied_{month_key}"] = {
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
            }
            st.session_state[f"monthly_time_settings_open_{month_key}"] = False
            st.success(f"{format_mmss(start_seconds)}〜{format_mmss(end_seconds)} に変更しました。")
            st.rerun()


def render_monthly_replay_section(month_key, period_label, bundle, review):
    photo_items = build_monthly_replay_photo_items(bundle, limit=18)
    if not photo_items:
        st.info("この期間には再生に使える写真がありません。")
        return False

    state = _monthly_replay_state(month_key, review)
    playback = state["playback"]
    current_url = str(st.session_state.get(state["url_key"]) or playback.get("youtube_url") or "").strip()
    video_id = parse_youtube_video_id(current_url)
    if not video_id:
        return False

    applied = st.session_state.get(f"monthly_replay_applied_{month_key}")
    if not isinstance(applied, dict):
        applied = {
            "start_seconds": int(playback.get("start_seconds") or st.session_state.get(state["start_key"]) or 0),
            "end_seconds": int(playback.get("end_seconds") or st.session_state.get(state["end_key"]) or 1),
        }
    applied_start = max(0, int(applied.get("start_seconds") or 0))
    applied_end = int(applied.get("end_seconds") or (applied_start + 20))
    if applied_end <= applied_start:
        applied_end = applied_start + 20

    effective_playback = {
        "youtube_url": current_url,
        "video_id": video_id,
        "start_seconds": applied_start,
        "end_seconds": applied_end,
        "reason": str(st.session_state.get(state["reason_key"]) or "").strip(),
        "confidence": str(st.session_state.get(state["confidence_key"]) or "").strip(),
        "title": str(st.session_state.get(state["title_key"]) or "").strip(),
    }
    render_monthly_replay_player(period_label, review, effective_playback, photo_items)
    return True


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
    """Summarize one trip from still photos plus the child's saved comments."""
    photos = diary_photos_only(photos)
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
def build_month_inner_evidence(bundle):
    """Build monthly evidence with the child's own saved words as the primary source.

    The generated diary is itself AI-organized text, so it should not be the main
    source when we are trying to reflect the child's inner interests back to them.
    """
    trip_map = {
        str(t.get("id")): t
        for t in (bundle or {}).get("trips", [])
        if isinstance(t, dict) and t.get("id")
    }
    comment_lines = []
    comment_count = 0
    comment_days = set()

    for photo in (bundle or {}).get("photos", []):
        if not isinstance(photo, dict):
            continue
        trip = trip_map.get(str(photo.get("trip_id")), {})
        reflection = photo.get("reflection_json") or {}
        conversation = reflection.get("conversation", []) if isinstance(reflection, dict) else []
        child_words = []
        for turn in conversation or []:
            if not isinstance(turn, dict) or turn.get("role") != "child":
                continue
            value = str(turn.get("text") or "").strip()
            if value:
                child_words.append(value)
        if not child_words:
            continue
        trip_date = str(trip.get("trip_date") or "").strip()
        where = str(photo_location_label(photo) or trip.get("destination") or "場所メモなし").strip()
        for value in child_words:
            comment_lines.append(f"[{trip_date or '日付不明'} / {where}] {value}")
            comment_count += 1
            if trip_date:
                comment_days.add(trip_date)

    if comment_lines:
        return {
            "text": "\n".join(comment_lines),
            "comment_count": comment_count,
            "day_count": len(comment_days),
            "source": "child_comments",
        }

    # Compatibility fallback for older periods that have a saved diary but no raw
    # per-photo conversation. Keep the prompt aware that this is weaker evidence.
    diary_lines = []
    diary_days = set()
    for diary in sorted(
        (bundle or {}).get("diaries", []),
        key=lambda x: str(trip_map.get(str((x or {}).get("trip_id")), {}).get("trip_date") or ""),
    ):
        if not isinstance(diary, dict):
            continue
        trip = trip_map.get(str(diary.get("trip_id")), {})
        trip_date = str(trip.get("trip_date") or "").strip()
        diary_text = str(diary.get("diary_text") or "").strip()
        if not diary_text:
            continue
        diary_lines.append(f"[{trip_date or '日付不明'}] {diary_text}")
        if trip_date:
            diary_days.add(trip_date)
    return {
        "text": "\n".join(diary_lines),
        "comment_count": 0,
        "day_count": len(diary_days),
        "source": "diary_fallback",
    }


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
    evidence_bundle = build_month_inner_evidence(bundle)
    evidence = str(evidence_bundle.get("text") or "").strip() or "本人の言葉はほとんどありません。"
    comment_count = int(evidence_bundle.get("comment_count") or 0)
    day_count = int(evidence_bundle.get("day_count") or 0)
    source = str(evidence_bundle.get("source") or "")
    source_note = (
        "以下は本人が写真について実際に残したコメントです。"
        if source == "child_comments"
        else "本人の生コメントが残っていないため、本人の発言をもとに作った保存日記を補助材料として使います。推測は特に弱くしてください。"
    )
    prompt = f"""
「東京ぶらり旅プロジェクト」の{month_key}の記録から、本人に返す短い『気づき』を作ります。
対象は5〜6歳の子どもです。

{source_note}
コメント数: {comment_count}件
記録日数: {day_count}日

記録:
{evidence}

目的:
本人が過去に言った言葉をそのまま並べることではありません。
複数の言葉に共通するものを一段だけ抽象化し、本人が
「ぼく、こういうところが気になっていたんだ」
「こういうときに心が動くんだ」
と自分で気づけるような、短く本質的なコメントにしてください。

ここでいう『内面』は心理診断ではありません。
記録から比較的自然に読み取れる、今の関心の向き・大事にしていそうなこと・心が動くポイント・迷いや違和感の向きだけを扱います。

厳守:
- 本人の発言を長く引用したり、発言の一覧を作ったりしない。
- 具体的な写真や出来事を順番に要約しない。
- まず共通する意味を探し、その意味を子どもにも分かる言葉で返す。
- 『観察力が高い』『優しい性格』『社会課題に関心が強い』『○○タイプ』など、能力評価・性格診断・ラベル付けをしない。
- 将来像や才能を予測しない。
- 記録にない感情を断定しない。
- 推測を含むときは『〜が気になっていたみたい』『〜を大事にしていたように見える』のように弱く言う。
- 1件しか根拠がないテーマを、その子全体の傾向のように一般化しない。
- 複数の日に同じ向きが出ているときだけ、期間全体の傾向として扱う。
- opening は本人向けの一言。25〜55文字程度、1文だけ。最も本質的な気づきを1つに絞る。
- findings は最大2件。theme は12文字程度まで。evidence は『根拠の引用』ではなく、その共通点を一段抽象化した説明を1文、35〜80文字程度で書く。
- findings の内容は opening の言い換えだけにしない。別の気づきが弱ければ1件だけでよい。
- ask_child は、その気づきを本人が自分で確かめられる短い問い。必要なときだけ1件まで。不要なら空文字。
- one_question も問いは1つまで。ask_child がある場合は原則空文字にする。
- repeated_notices と wishes は内部互換のため残すが、通常は空配列にする。
- parent_note は保護者向け。どの程度の記録量から推測したかと、断定を避けた理由を1〜2文で簡潔に書く。本人の発言を長く引用しない。
- 全体として簡潔にする。
""".strip()
    result = ask_json(prompt, "burari_monthly_review_insight_v2", schema, 1000)
    result["_insight_version"] = 2
    return result

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



VALID_APP_PAGES = {"home", "camera", "videos", "moments", "diary", "review", "settings"}


RECENT_CAMERA_AUTO_START_SECONDS = 60 * 60


def _remembered_recent_camera_mode():
    """Return the recently used camera mode while its one-hour window is valid."""
    last_open = st.session_state.get("_browser_last_camera_open_at")
    try:
        last_open_ms = float(last_open or 0)
    except Exception:
        last_open_ms = 0.0

    age_ms = time.time() * 1000.0 - last_open_ms
    if not (last_open_ms > 0 and 0 <= age_ms <= RECENT_CAMERA_AUTO_START_SECONDS * 1000):
        return ""

    mode = str(st.session_state.get("_browser_last_camera_mode") or "").strip().lower()
    # Old browser data has no mode. Preserve the previous behaviour by treating it
    # as a recent photo-camera session.
    return "video" if mode == "video" else "photo"


def _sync_recent_camera_state_from_browser(key="home_recent_camera_state_v126"):
    """Refresh the recent camera timestamp/mode from local browser storage."""
    try:
        state = read_browser_persistence(key)
    except Exception:
        state = None
    if not isinstance(state, dict):
        return False

    try:
        last_open_ms = float(state.get("last_camera_open_at") or 0)
    except Exception:
        last_open_ms = 0.0
    mode = str(state.get("last_camera_mode") or "").strip().lower()
    if mode not in {"photo", "video"}:
        mode = ""
    st.session_state["_browser_last_camera_open_at"] = last_open_ms
    st.session_state["_browser_last_camera_mode"] = mode
    return True


def restore_recent_camera_session():
    """Reopen a recently used photo/video camera in the same mode."""
    if st.session_state.get("_recent_camera_restore_checked", False):
        return
    st.session_state["_recent_camera_restore_checked"] = True

    mode = _remembered_recent_camera_mode()
    if not mode:
        return

    st.session_state["main_page"] = "camera"
    if mode == "video":
        st.session_state["_camera_auto_start_video"] = True
        st.session_state.pop("_camera_auto_start", None)
    else:
        st.session_state["_camera_auto_start"] = True
        st.session_state.pop("_camera_auto_start_video", None)
    st.session_state["_history_action"] = "replace"
    st.rerun()



def reset_diary_navigation_for_home_entry():
    """Return Diary to its neutral landing view when entered from Home.

    Keep persisted conversations/diaries intact; only discard transient drill-down
    state such as the previously opened photo or trip.
    """
    st.session_state.preferred_diary_trip_id = None
    st.session_state.pop("_pending_diary_open_trip_id", None)
    st.session_state["_diary_selector_serial"] = int(
        st.session_state.get("_diary_selector_serial") or 0
    ) + 1

    opened_trip_ids = set()
    for key in list(st.session_state.keys()):
        key_text = str(key)
        if key_text.startswith("diary_trip_selector_"):
            st.session_state.pop(key, None)
            continue
        for prefix in (
            "diary_talk_photo_",
            "diary_selected_photo_",
            "diary_existing_photo_view_",
            "diary_gallery_serial_",
        ):
            if key_text.startswith(prefix):
                trip_id = key_text[len(prefix):]
                if trip_id:
                    opened_trip_ids.add(trip_id)
                st.session_state.pop(key, None)
                break

    # A reflection_state is created when a photo is opened. Removing it for the
    # trips that were actually drilled into restores the diary/gallery landing
    # screen. Photo conversations themselves are stored in Supabase, so this does
    # not erase user content.
    for trip_id in opened_trip_ids:
        st.session_state.pop(f"reflection_state_{trip_id}", None)

def _active_diary_navigation_trip_id():
    """Return the diary trip currently open in the UI, if any."""
    pending_id = str(st.session_state.get("_pending_diary_open_trip_id") or "").strip()
    if pending_id:
        return pending_id

    serial = int(st.session_state.get("_diary_selector_serial") or 0)
    selected = st.session_state.get(f"diary_trip_selector_{serial}")
    if selected:
        return str(selected)

    preferred = st.session_state.get("preferred_diary_trip_id")
    if preferred:
        return str(preferred)

    # Fallback for an already-open photo after a widget-key migration.
    for key, value in list(st.session_state.items()):
        key_text = str(key)
        if key_text.startswith("diary_talk_photo_") and value:
            return key_text[len("diary_talk_photo_"):]
    return ""


def current_navigation_context():
    """Return the current hierarchy node and any relevant object id.

    This is deliberately a folder-style hierarchy, not a record of visit history.
    """
    page = str(st.session_state.get("main_page") or "home")
    if page == "diary":
        trip_id = _active_diary_navigation_trip_id()
        if trip_id and st.session_state.get(f"diary_talk_photo_{trip_id}"):
            return "diary_photo", trip_id
        if trip_id:
            return "diary_trip", trip_id
        return "diary", ""

    if page == "review":
        current_view = st.session_state.get("review_view_selector")
        period_label = "🗓 期間の振り返り"
        history_label = "📚 これまでの日記"
        if current_view == "🔍 今月の発見":
            current_view = period_label
        if current_view == history_label:
            detail_trip_id = str(st.session_state.get("history_detail_trip_id") or "")
            if detail_trip_id:
                return "review_history_detail", detail_trip_id
            return "review_history", ""
        if current_view == period_label:
            return "review_period", ""
        return "review", ""

    return page if page in VALID_APP_PAGES else "home", ""


def navigation_parent_node(node=None):
    """Return the fixed parent in the app hierarchy."""
    if node is None:
        node, _ = current_navigation_context()
    parents = {
        "diary_photo": "diary_trip",
        "diary_trip": "diary",
        "review_history_detail": "review_history",
        "review_history": "review",
        "review_period": "review",
        "camera": "home",
        "videos": "home",
        "moments": "home",
        "diary": "home",
        "review": "home",
        "settings": "home",
    }
    return parents.get(str(node), "")


def _return_diary_photo_to_gallery(trip_id):
    trip_id = str(trip_id or "")
    if not trip_id:
        return
    st.session_state.pop(f"diary_talk_photo_{trip_id}", None)
    st.session_state.pop(f"diary_selected_photo_{trip_id}", None)
    # Existing saved-diary photo views create a temporary reflection_state solely
    # for the individual-photo screen. Pending diaries keep their working state.
    if st.session_state.pop(f"diary_existing_photo_view_{trip_id}", False):
        st.session_state.pop(f"reflection_state_{trip_id}", None)


def navigate_to_parent():
    """Move one level up in the fixed app hierarchy, never by visit history."""
    node, object_id = current_navigation_context()
    if node == "home":
        return

    if node == "diary_photo":
        _return_diary_photo_to_gallery(object_id)
        st.session_state["_history_action"] = "replace"
        st.rerun()

    if node == "diary_trip":
        reset_diary_navigation_for_home_entry()
        st.session_state["_history_action"] = "replace"
        st.rerun()

    if node == "review_history_detail":
        st.session_state.pop("history_detail_trip_id", None)
        st.session_state["_history_action"] = "replace"
        st.rerun()

    if node in {"review_history", "review_period"}:
        st.session_state.pop("history_detail_trip_id", None)
        st.session_state.pop("review_view_selector", None)
        st.session_state["_history_action"] = "replace"
        st.rerun()

    # All first-level pages have Home as their parent.
    go_page("home", history_mode="replace")


def go_page(page_name, history_mode="push"):
    target = page_name if page_name in VALID_APP_PAGES else "home"
    current = st.session_state.get("main_page")
    if current != target:
        # Home -> Diary must always open the same neutral Diary landing page, not
        # the photo/trip the user happened to have open before returning Home.
        if target == "diary" and current == "home":
            reset_diary_navigation_for_home_entry()
        elif target == "diary":
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
    navigation_node, _ = current_navigation_context()
    result = browser_history_component(
        data={
            "page": page,
            "action": action,
            "node": navigation_node,
            "intercept_hierarchy_back": page != "home",
        },
        key="tokyo_burari_browser_history_instance_v127",
        on_page_change=lambda: None,
        on_hierarchy_back_change=lambda: None,
    )

    hierarchy_back = getattr(result, "hierarchy_back", None)
    if hierarchy_back:
        token = str(hierarchy_back)
        if token != str(st.session_state.get("_browser_hierarchy_back_token") or ""):
            st.session_state["_browser_hierarchy_back_token"] = token
            navigate_to_parent()

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


def render_home_button(label, page_name, key, ensure_trip=False, open_period_review=False):
    if st.button(label, key=key, use_container_width=True):
        if page_name == "camera":
            # The user's click is a valid browser gesture. Reopen the camera mode
            # used within the last hour; otherwise keep the usual photo auto-start.
            recent_mode = _remembered_recent_camera_mode()
            if recent_mode == "video":
                st.session_state["_camera_auto_start_video"] = True
                st.session_state.pop("_camera_auto_start", None)
            else:
                st.session_state["_camera_auto_start"] = True
                st.session_state.pop("_camera_auto_start_video", None)
        elif page_name == "review":
            # Always enter Review through the clear two-choice menu. The period-review
            # nudge on Home is still shown, but it no longer skips past this selector.
            st.session_state.pop("review_view_selector", None)
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


def inject_home_icon_css(review_attention=False):
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
        ".st-key-home_camera div.stButton > button::before,.st-key-home_diary div.stButton > button::before{width:50px;height:50px;}",
        ".st-key-home_review div.stButton > button::before,.st-key-home_settings div.stButton > button::before{width:42px;height:42px;}",
        "@media (max-width: 640px){.st-key-home_camera div.stButton > button::before,.st-key-home_diary div.stButton > button::before{width:36px;height:36px;}.st-key-home_review div.stButton > button::before,.st-key-home_settings div.stButton > button::before{width:30px;height:30px;}}",
        f'.home-title-accent{{color:color-mix(in srgb, {accent} 80%, rgba(31, 38, 48, .96) 20%);text-shadow:0 1px 0 rgba(255,255,255,.72);}}',
        f'.st-key-home_camera div.stButton > button,.st-key-home_diary div.stButton > button{{border-color:{accent} !important;background:linear-gradient(155deg,rgba({rgb2},.25),rgba({rgb1},.07)) !important;box-shadow:0 9px 22px rgba({rgb1},.10),0 0 0 2px rgba(255,255,255,.34) inset !important;}}',
        f'.st-key-home_camera div.stButton > button:hover,.st-key-home_diary div.stButton > button:hover{{border-color:{accent} !important;background:linear-gradient(155deg,rgba({rgb2},.34),rgba({rgb1},.11)) !important;box-shadow:0 11px 24px rgba({rgb1},.14),0 0 0 2px rgba(255,255,255,.40) inset !important;}}',
        f'.st-key-home_settings div.stButton > button{{border-color:rgba({rgb1},.46) !important;background:linear-gradient(155deg,rgba({rgb2},.18),rgba({rgb1},.035)) !important;box-shadow:0 8px 20px rgba({rgb1},.07),0 0 0 2px rgba(255,255,255,.30) inset !important;}}',
        f'.st-key-home_settings div.stButton > button:hover{{border-color:rgba({rgb1},.62) !important;background:linear-gradient(155deg,rgba({rgb2},.25),rgba({rgb1},.065)) !important;box-shadow:0 10px 22px rgba({rgb1},.10),0 0 0 2px rgba(255,255,255,.35) inset !important;}}',
    ]
    if review_attention:
        css_chunks.extend([
            '@keyframes burariReviewPulse{0%,100%{box-shadow:0 9px 22px rgba(226,133,24,.18),0 0 0 2px rgba(255,255,255,.34) inset,0 0 0 0 rgba(226,133,24,.18);}50%{box-shadow:0 11px 25px rgba(226,133,24,.26),0 0 0 2px rgba(255,255,255,.40) inset,0 0 0 7px rgba(226,133,24,0);}}',
            '.st-key-home_review div.stButton > button{position:relative !important;border:2.6px solid rgba(218,126,20,.96) !important;background:linear-gradient(155deg,rgba(255,241,202,.99),rgba(255,218,169,.97)) !important;animation:burariReviewPulse 2.6s ease-in-out infinite !important;}',
            '.st-key-home_review div.stButton > button::after{content:"";position:absolute;top:8px;right:10px;width:10px;height:10px;border-radius:999px;background:#E95C32;box-shadow:0 0 0 3px rgba(233,92,50,.16);}',
            '@media (prefers-reduced-motion: reduce){.st-key-home_review div.stButton > button{animation:none !important;}}',
        ])

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

def render_global_bottom_navigation(page_name):
    """Render hierarchy Back above the direct Home button on every non-Home page."""
    node, _ = current_navigation_context()
    if node == "home":
        return
    st.divider()
    with st.container(key=f"global_parent_nav_{page_name}_{node}"):
        if st.button(
            "← 1つ前に戻る",
            use_container_width=True,
            key=f"global_parent_back_{page_name}_{node}",
        ):
            navigate_to_parent()
    with st.container(key=f"global_home_nav_{page_name}_{node}"):
        if st.button(
            "トップページに戻る",
            use_container_width=True,
            key=f"global_bottom_home_{page_name}_{node}",
        ):
            go_page("home", history_mode="replace")


def page_top(title, caption=""):
    c1, c2 = st.columns([1, 5], vertical_alignment="center")
    with c1:
        if st.button("←", key=f"parent_back_{title}", help="1つ前の階層に戻る", use_container_width=True):
            navigate_to_parent()
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
                diary_photos_only([p for p in photos if isinstance(p, dict)]),
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
    result_rows = []
    for trip in pending_trips:
        stills = diary_photos_only(photo_map.get(str(trip.get("id")), []))
        if stills:
            result_rows.append({"trip": trip, "photos": stills})
    return result_rows


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
    """Create a diary from already-saved still-photo comments and persist it immediately."""
    trip = trip or {}
    photos = diary_photos_only(photos)
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
    photos = diary_photos_only(photos)
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


def render_saved_media_preview(photo, image_alt="ぶらり旅の写真", compact=True, delete_key_prefix="saved_media"):
    """Render a saved video when present, otherwise its normal still image."""
    if photo_is_video(photo):
        video_url = video_display_url(photo)
        if video_url:
            st.video(video_url)
            duration_ms = int(photo_media_metadata(photo).get("video_duration_ms") or 0)
            if duration_ms > 0:
                st.caption(f"🎥 動画 {max(1, round(duration_ms / 1000))}秒")
            stabilization_caption = video_stabilization_caption(photo)
            if stabilization_caption:
                st.caption(stabilization_caption)
            render_video_delete_controls(photo, f"{delete_key_prefix}_{photo.get('id')}")
            return True

    preview_src = photo_display_url(photo)
    if preview_src:
        max_width = "min(72vw,320px)" if compact else "min(90vw,520px)"
        max_height = "34dvh" if compact else "52dvh"
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:.25rem 0 .45rem;">
              <img src="{html.escape(preview_src, quote=True)}" alt="{html.escape(str(image_alt), quote=True)}" loading="lazy" decoding="async"
                   style="display:block;max-width:{max_width};max-height:{max_height};width:auto;height:auto;object-fit:contain;border-radius:14px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
        return True
    return False


@st.dialog("AIセレクション")
def show_video_ai_selection_dialog(storage_path, title, caption):
    path = str(storage_path or "").strip()
    if not path:
        st.warning("画像を表示できませんでした。")
        return
    try:
        signed = signed_photo_url_map((path,), expires_in=1800)
        url = str(signed.get(path) or "")
    except Exception:
        url = ""
    if url:
        st.image(url, use_container_width=True)
    else:
        try:
            st.image(download_photo(path), use_container_width=True)
        except Exception:
            st.warning("画像を表示できませんでした。")
            return
    if title:
        st.markdown(f"**{title}**")
    if caption:
        st.caption(caption)


@st.dialog("動画")
def show_video_library_dialog(video_photo, title, caption):
    video_url = video_display_url(video_photo, expires_in=1800)
    poster_path = str((video_photo or {}).get("storage_path") or "").strip()
    if video_url:
        st.video(video_url)
    elif poster_path:
        try:
            signed = signed_photo_url_map((poster_path,), expires_in=1800)
            poster_url = str(signed.get(poster_path) or "")
        except Exception:
            poster_url = ""
        if poster_url:
            st.image(poster_url, use_container_width=True)
        else:
            try:
                st.image(download_photo(poster_path), use_container_width=True)
            except Exception:
                st.warning("動画プレビューを表示できませんでした。")
    else:
        st.warning("動画プレビューを表示できませんでした。")

    if title:
        st.markdown(f"**{title}**")
    if caption:
        st.caption(caption)
    stabilization_caption = video_stabilization_caption(video_photo)
    if stabilization_caption:
        st.caption(stabilization_caption)
    render_video_delete_controls(video_photo, f"video_library_dialog_{video_photo.get('id')}")


def render_video_ai_selection(photo, key_prefix="video_selection", allow_save=True):
    """Render the nine AI-selected stills in a uniform 3x3 grid."""
    if not photo_is_video(photo):
        return
    selection_meta = photo_media_metadata(photo).get("ai_selection") or {}
    if not isinstance(selection_meta, dict):
        selection_meta = {}
    items = video_ai_selection_items(photo)
    if not items:
        status = str(selection_meta.get("status") or "")
        if status == "processing":
            st.caption("✨ AIがこの動画のいい瞬間を自動で作成しています。")
        elif status == "error":
            st.caption("AIセレクションを作成できませんでした。動画は保存されています。")
        return

    st.markdown("##### AIが選んだセレクション")
    st.caption(
        f"表情・躍動感・写真としての美しさ・被写体の魅力などを総合評価し、"
        f"似た場面が並びすぎないよう最大{VIDEO_AI_MAX_SELECTIONS}枚を選んでいます。"
    )
    paths = tuple(str(item.get("storage_path") or "").strip() for item in items)
    try:
        signed_map = signed_photo_url_map(paths, expires_in=1800)
    except Exception:
        signed_map = {}

    columns = st.columns(3, gap="small")
    for index, item in enumerate(items):
        rank = int(item.get("rank") or index + 1)
        path = str(item.get("storage_path") or "").strip()
        with columns[index % 3]:
            url = str(signed_map.get(path) or "")
            if not url:
                try:
                    url = image_data_url(download_photo(path))
                except Exception:
                    url = ""
            if url:
                image_html = (
                    f'<div style="width:100%;aspect-ratio:1/1;overflow:hidden;border-radius:12px;background:rgba(128,128,128,.08);">'
                    f'<img src="{html.escape(url, quote=True)}" alt="AIセレクション {rank}" loading="lazy" decoding="async" '
                    f'style="display:block;width:100%;height:100%;object-fit:cover;" /></div>'
                )
                st.markdown(image_html, unsafe_allow_html=True)
            else:
                st.caption("画像を表示できません")
            best_label = "★ AI BEST" if bool(item.get("ai_best")) or rank == 1 else f"SELECT {rank}"
            if rank == 1:
                st.markdown("**★ AI BEST**")
            quality = _video_selection_quality_label(item.get("primary_quality"))
            timestamp_ms = max(0, int(item.get("timestamp_ms") or 0))
            seconds = timestamp_ms / 1000
            reason = str(item.get("reason") or "").strip()
            caption = f"{seconds:.1f}秒・{quality}"
            if reason:
                caption += f"\n{reason}"
            st.caption(caption)
            if st.button(
                "大きく見る",
                use_container_width=True,
                key=f"{key_prefix}_view_{photo.get('id')}_{rank}",
            ):
                show_video_ai_selection_dialog(path, best_label, caption)
            if allow_save:
                saved = bool(item.get("saved_photo_id"))
                if st.button(
                    "保存済み" if saved else "保存する",
                    use_container_width=True,
                    disabled=saved,
                    key=f"{key_prefix}_save_{photo.get('id')}_{rank}",
                ):
                    try:
                        with st.spinner("写真として保存しています…"):
                            save_video_ai_selection_as_photo(photo, item)
                            record_video_ai_human_choices(photo, {rank})
                        previous_count = st.session_state.get("_home_today_photo_count")
                        try:
                            previous_count = int(previous_count) if previous_count is not None else 0
                        except Exception:
                            previous_count = 0
                        st.session_state["_home_today_photo_count"] = previous_count + 1
                        st.rerun()
                    except Exception as exc:
                        st.error("写真として保存できませんでした。")
                        with st.expander("保護者向け詳細"):
                            st.code(str(exc))


@st.dialog("AIセレクション")
def show_pending_video_ai_selection_dialog(image_bytes, title, caption):
    if not image_bytes:
        st.warning("画像を表示できませんでした。")
        return
    st.image(image_bytes, use_container_width=True)
    if title:
        st.markdown(f"**{title}**")
    if caption:
        st.caption(caption)


def render_pending_video_ai_review():
    """Review AI picks before the recorded video is persisted."""
    pending = st.session_state.get("_pending_video_ai_review")
    if not isinstance(pending, dict):
        return False
    selections = list(pending.get("selections") or [])[:9]
    if len(selections) < 9 or not pending.get("video_raw") or not pending.get("poster_raw"):
        st.session_state.pop("_pending_video_ai_review", None)
        return False

    st.markdown("### 撮影した動画")
    st.caption("AIセレクションを確認中です。まだこの動画は保存されていません。")
    st.video(pending["video_raw"], format=str(pending.get("mime_type") or "video/webm"))

    save_col, retry_col = st.columns([3, 1], gap="small")
    with save_col:
        save_video_clicked = st.button(
            "この動画を残す",
            type="primary",
            use_container_width=True,
            key="pending_ai_video_save",
        )
    with retry_col:
        retry_video_clicked = st.button(
            "撮り直す",
            use_container_width=True,
            key="pending_ai_video_retry",
        )

    if retry_video_clicked:
        st.session_state.pop("_pending_video_ai_review", None)
        st.session_state.pop("_pending_video_ai_review_digest", None)
        st.session_state.capture_serial += 1
        st.session_state["_camera_auto_start_video"] = True
        st.rerun()

    if save_video_clicked:
        try:
            trip = ensure_today_trip()
            capture_source = str(pending.get("source") or "video_camera")
            location = build_photo_location(
                pending.get("location"),
                trip,
                capture_source=capture_source,
            )
            with st.spinner("動画を残しています…"):
                saved_video = upload_video(
                    trip["id"],
                    pending["video_raw"],
                    pending["poster_raw"],
                    mime_type=pending.get("mime_type"),
                    duration_ms=pending.get("duration_ms"),
                    location=location,
                    captured_at=pending.get("captured_at"),
                    capture_source=capture_source,
                )

            ai_selection_ok = False
            if isinstance(saved_video, dict) and saved_video.get("id"):
                try:
                    with st.spinner("選んだ9枚を保存しています…"):
                        saved_video = store_preselected_video_ai_selection(
                            saved_video,
                            selections,
                            candidate_count=pending.get("candidate_count"),
                        )
                    ai_selection_ok = True
                except Exception as selection_exc:
                    mark_video_ai_selection_error(saved_video, selection_exc)

            if isinstance(saved_video, dict) and saved_video.get("id"):
                st.session_state[f"_camera_recent_photo_{trip['id']}"] = saved_video["id"]

            previous_count = st.session_state.get("_home_today_photo_count")
            try:
                previous_count = int(previous_count) if previous_count is not None else 0
            except Exception:
                previous_count = 0
            st.session_state["_home_today_photo_count"] = previous_count + 1
            place_label = str((location or {}).get("place_label") or trip.get("destination") or "").strip()
            if place_label:
                st.session_state["_home_today_place"] = place_label

            st.session_state.pop("_pending_video_ai_review", None)
            st.session_state.pop("_pending_video_ai_review_digest", None)
            st.session_state.capture_serial += 1
            st.session_state["_camera_notice"] = (
                "動画を保存し、AIセレクション9枚も保存しました。"
                if ai_selection_ok else
                "動画を保存しました。AIセレクションの保存には失敗しました。"
            )
            st.rerun()
        except Exception as exc:
            st.error("動画を保存できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    st.markdown("##### AIが選んだセレクション")
    st.caption("表情・躍動感・写真としての美しさ・被写体の魅力などを総合評価し、似た場面が並びすぎないよう9枚を選んでいます。")
    columns = st.columns(3, gap="small")
    for index, selected in enumerate(selections):
        rank = index + 1
        frame = selected.get("frame") or {}
        image_bytes = _video_frame_original_bytes(frame)
        timestamp_ms = max(0, int(frame.get("timestamp_ms") or 0))
        quality = _video_selection_quality_label(selected.get("primary_quality"))
        reason = str(selected.get("reason") or "").strip()
        caption = f"{timestamp_ms / 1000:.1f}秒・{quality}"
        if reason:
            caption += f"\n{reason}"
        best_label = "★ AI BEST" if rank == 1 else f"SELECT {rank}"
        with columns[index % 3]:
            if image_bytes:
                data_url = image_data_url(image_bytes)
                st.markdown(
                    '<div style="width:100%;aspect-ratio:1/1;overflow:hidden;border-radius:12px;background:rgba(128,128,128,.08);">'
                    f'<img src="{data_url}" alt="AIセレクション {rank}" style="display:block;width:100%;height:100%;object-fit:cover;" />'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("画像を表示できません")
            if rank == 1:
                st.markdown("**★ AI BEST**")
            st.caption(caption)
            if st.button(
                "大きく見る",
                use_container_width=True,
                key=f"pending_ai_video_view_{rank}",
            ):
                show_pending_video_ai_selection_dialog(image_bytes, best_label, caption)

    st.caption("動画を残すと、この9枚もAIセレクションとして保存され、各画像をあとから写真として保存できます。")
    return True


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
    """Three-across pending still-photo thumbnails."""
    subset = diary_photos_only(photos)
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
                "is_video": False,
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
    """Render history still photos lazily; original videos are intentionally omitted."""
    subset = diary_photos_only(photos)
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
        video_badge = (
            '<div style="position:absolute;left:6px;bottom:6px;padding:3px 7px;border-radius:999px;background:rgba(17,24,39,.78);color:#fff;font-size:10px;font-weight:800;">▶ 動画</div>'
            if photo_is_video(photo) else ""
        )
        cards.append(
            f'<div style="min-width:0;"><div style="position:relative;"><img src="{html.escape(src, quote=True)}" loading="lazy" decoding="async" fetchpriority="low" '
            f'style="display:block;width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:10px;" />{video_badge}</div>{location_html}</div>'
        )
    if cards:
        st.markdown(
            f'<div style="display:grid;grid-template-columns:repeat({column_count},minmax(0,1fr));gap:6px;width:100%;">'
            + "".join(cards) + "</div>",
            unsafe_allow_html=True,
        )

def render_diary_photo_gallery(trip_id, photos, state=None):
    """Show diary still photos in a three-column clickable grid."""
    photos = diary_photos_only(photos)
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
                "is_video": False,
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
@st.cache_data(ttl=3, max_entries=64, show_spinner=False)
def _home_video_counts_cached(family_key, member_key):
    """Return (saved videos, videos not yet accepted as diary stills)."""
    rows = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("id,reflection_json")
        .eq("family_key", str(family_key))
        .eq("member_key", str(member_key))
        .limit(1000)
        .execute()
    ).data or []

    saved_count = 0
    before_clip_count = 0
    processing_rows = []
    error_count = 0
    for row in rows:
        if not photo_is_video(row):
            continue
        saved_count += 1
        selection = photo_media_metadata(row).get("ai_selection") or {}
        if not isinstance(selection, dict):
            selection = {}
        # "瞬間切り取り前" is a processing count, not a review count. Once
        # AI has actually produced a usable selection (ready/reviewed), this
        # video is no longer waiting for cutting even if the user has not opened it.
        status = str(selection.get("status") or "").strip().lower()
        has_selection = bool(video_ai_selection_items(row))
        if not (status in {"ready", "reviewed"} and has_selection):
            before_clip_count += 1
        if status == "processing":
            job_row = dict(row)
            job_row["family_key"] = str(family_key)
            job_row["member_key"] = str(member_key)
            processing_rows.append(job_row)
        elif status == "error":
            error_count += 1
    return saved_count, before_clip_count, processing_rows, error_count


def home_video_counts():
    try:
        counts = _home_video_counts_cached(current_family_key(), current_member_key())
        st.session_state["_home_video_saved_count"] = int(counts[0])
        st.session_state["_home_video_before_clip_count"] = int(counts[1])
        st.session_state["_home_video_error_count"] = int(counts[3]) if len(counts) > 3 else 0
        # v133 processing is driven by the app-level automatic scheduler. Home
        # only reads status; opening or refreshing this page is never a trigger.
        return int(counts[0]), int(counts[1])
    except Exception:
        saved = st.session_state.get("_home_video_saved_count")
        before = st.session_state.get("_home_video_before_clip_count")
        if saved is None or before is None:
            return None
        try:
            return max(0, int(saved)), max(0, int(before))
        except Exception:
            return None


def _render_home_video_count_status():
    """Refresh video processing counts while the home page remains open."""
    video_counts = home_video_counts()
    if video_counts is not None:
        saved_video_count, before_clip_count = video_counts
        error_count = max(0, int(st.session_state.get("_home_video_error_count") or 0))
        suffix = f"　／　処理エラー {error_count}本" if error_count else ""
        st.caption(
            f"保存済み {saved_video_count}本　／　瞬間切り取り前 {before_clip_count}本{suffix}"
        )
    else:
        st.caption("保存済み本数を確認できませんでした。")


if hasattr(st, "fragment"):
    render_home_video_count_status = st.fragment(run_every="5s")(_render_home_video_count_status)
else:
    render_home_video_count_status = _render_home_video_count_status


def page_home():
    # Keep the recent photo/video camera mode fresh using browser-local storage only.
    _sync_recent_camera_state_from_browser()
    review_attention = home_review_attention_needed()
    inject_home_icon_css(review_attention=review_attention)
    fast_family_name = str(st.session_state.get("_current_family_name") or current_family_key())
    fast_member_name = str(st.session_state.get("_current_member_name") or current_member_key())
    st.markdown(
        f'<div class="home-account">{html.escape(fast_family_name)} ／ 個人：{html.escape(fast_member_name)}（{html.escape(current_member_key())}）</div>',
        unsafe_allow_html=True,
    )
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
        status_main = f"今日の記録 {count_value}件" if count_value else "今日はまだ記録なし"
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
            render_home_button("写真・動画を撮る", "camera", "home_camera")
        with primary_right:
            render_home_button("日記にする・見る", "diary", "home_diary")

    with st.container(key="home_good_moments"):
        if st.button(
            "✨ いい瞬間を見る",
            key="home_good_moments_button",
            use_container_width=True,
        ):
            go_page("moments")

    with st.container(key="home_video_vault"):
        if st.button(
            "🎞️ 動画保管庫",
            key="home_video_vault_button",
            use_container_width=True,
        ):
            go_page("videos")
        render_home_video_count_status()

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

    st.markdown('<div class="home-section-label" style="margin-top:.60rem;">たまに使う</div>', unsafe_allow_html=True)
    with st.container(key="home_secondary"):
        secondary_left, secondary_right = st.columns([1.2, 1])
        with secondary_left:
            review_label = "振り返り（先月あり）" if review_attention else "振り返り（たまに）"
            render_home_button(review_label, "review", "home_review", open_period_review=review_attention)
        with secondary_right:
            render_home_button("設定", "settings", "home_settings")

    st.markdown(
        '<div class="home-footer-note">写真・動画は0件でも大丈夫。気になったときだけ使います。</div>',
        unsafe_allow_html=True,
    )



_MOMENTS_RECOVERY_HTML = """
<div id="moments-recovery" style="font-size:14px;color:#6b7280;padding:.35rem 0;">元動画からAI候補を準備しています…</div>
"""

_MOMENTS_RECOVERY_JS = r"""
export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const status = parentElement.querySelector('#moments-recovery');
  let cancelled = false;
  const setStatus = (text) => { if (status) status.textContent = text || ''; };
  const blobToDataUrl = (blob) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
  const seek = (video, seconds) => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('seek timeout')), 5000);
    const done = () => { clearTimeout(timer); resolve(); };
    const fail = () => { clearTimeout(timer); reject(new Error('seek failed')); };
    video.addEventListener('seeked', done, { once: true });
    video.addEventListener('error', fail, { once: true });
    try { video.currentTime = seconds; } catch (err) { clearTimeout(timer); reject(err); }
  });
  const upload = async (blob, url) => {
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'content-type': 'image/jpeg', 'cache-control': 'max-age=3600' },
      body: await blob.arrayBuffer()
    });
    if (!response.ok) {
      let detail = '';
      try { detail = await response.text(); } catch (_) {}
      throw new Error(`候補画像の保存に失敗しました (${response.status}) ${String(detail || '').slice(0, 160)}`);
    }
  };
  const run = async () => {
    if (!data?.enabled || !data?.video_url || !data?.sheet_signed_url || !data?.sheet_path) return;
    try {
      setStatus('元動画を読み込み、AI候補を準備しています…');
      const response = await fetch(String(data.video_url));
      if (!response.ok) throw new Error(`元動画を読み込めません (${response.status})`);
      const videoBlob = await response.blob();
      const objectUrl = URL.createObjectURL(videoBlob);
      const probe = document.createElement('video');
      probe.preload = 'auto';
      probe.muted = true;
      probe.playsInline = true;
      probe.src = objectUrl;
      try {
        await new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('動画情報の読込がタイムアウトしました')), 7000);
          probe.addEventListener('loadedmetadata', () => { clearTimeout(timer); resolve(); }, { once: true });
          probe.addEventListener('error', () => { clearTimeout(timer); reject(new Error('動画情報を読み込めません')); }, { once: true });
        });
        const duration = Number.isFinite(probe.duration) && probe.duration > 0 ? probe.duration : 1;
        const count = Math.max(1, Math.min(150, Math.ceil(duration * 10)));
        const srcW = probe.videoWidth || 1280;
        const srcH = probe.videoHeight || 720;
        const maxSide = 240;
        const scale = Math.min(1, maxSide / Math.max(srcW, srcH));
        const tileW = Math.max(1, Math.round(srcW * scale));
        const tileH = Math.max(1, Math.round(srcH * scale));
        const columns = Math.min(15, count);
        const rows = Math.ceil(count / columns);
        const sheet = document.createElement('canvas');
        sheet.width = tileW * columns;
        sheet.height = tileH * rows;
        const ctx = sheet.getContext('2d', { alpha: false });
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, sheet.width, sheet.height);
        const manifest = [];
        let actual = 0;
        for (let i = 0; i < count; i += 1) {
          if (cancelled) return;
          const seconds = Math.min(Math.max(0, duration - 0.03), i / 10);
          try {
            await seek(probe, seconds);
            const col = actual % columns;
            const row = Math.floor(actual / columns);
            ctx.drawImage(probe, col * tileW, row * tileH, tileW, tileH);
            manifest.push({ frame_id: `F${String(actual + 1).padStart(3, '0')}`, timestamp_ms: Math.round(seconds * 1000), tile_index: actual });
            actual += 1;
          } catch (_) {}
        }
        if (!actual) throw new Error('元動画から候補画像を作れませんでした');
        // Repack to the actual row count if a few seeks failed.
        const actualRows = Math.ceil(actual / columns);
        const finalCanvas = document.createElement('canvas');
        finalCanvas.width = sheet.width;
        finalCanvas.height = tileH * actualRows;
        finalCanvas.getContext('2d', { alpha: false }).drawImage(sheet, 0, 0);
        const sheetBlob = await new Promise((resolve) => finalCanvas.toBlob(resolve, 'image/jpeg', 0.82));
        if (!sheetBlob) throw new Error('候補シートを作れませんでした');
        setStatus('候補画像を保管庫へ保存しています…');
        await upload(sheetBlob, String(data.sheet_signed_url));
        if (cancelled) return;
        setStatus('AI選定を開始します…');
        setTriggerValue('candidate_sheet', {
          path: String(data.sheet_path),
          manifest,
          columns,
          rows: actualRows,
          recovery_id: String(data.recovery_id || '')
        });
      } finally {
        try { probe.pause(); } catch (_) {}
        probe.removeAttribute('src');
        try { probe.load(); } catch (_) {}
        URL.revokeObjectURL(objectUrl);
      }
    } catch (err) {
      const message = String(err?.message || err || '候補画像を準備できませんでした').slice(0, 240);
      setStatus(message);
      setTriggerValue('recovery_error', { message });
    }
  };
  queueMicrotask(run);
  return () => { cancelled = true; };
}
"""

try:
    moments_recovery_component = st.components.v2.component(
        "tokyo_burari_moments_recovery_v134",
        html=_MOMENTS_RECOVERY_HTML,
        js=_MOMENTS_RECOVERY_JS,
    )
except Exception:
    moments_recovery_component = None


def _candidate_sheet_recovery_reservation(photo):
    video_id = str((photo or {}).get("id") or "").strip()
    if not video_id:
        raise ValueError("動画IDを確認できません。")
    key = f"_moments_recovery_reservation_v134_{video_id}"
    current = st.session_state.get(key)
    if isinstance(current, dict) and current.get("path") and current.get("signed_url"):
        return current
    base = _video_selection_base_path(photo)
    if not base:
        raise ValueError("動画の保存先を確認できません。")
    path = f"{base}_candidates_recovery_{uuid.uuid4().hex[:8]}.jpg"
    reservation = {
        "path": path,
        "signed_url": _create_signed_video_upload_url(path),
        "recovery_id": uuid.uuid4().hex,
    }
    st.session_state[key] = reservation
    return reservation


def _render_moments_candidate_recovery(photo, index):
    if moments_recovery_component is None:
        st.warning("この動画の候補画像がありません。元動画からの再生成機能を読み込めませんでした。")
        return False
    video_url = video_display_url(photo, expires_in=1800)
    if not video_url:
        st.warning("元動画を読み込めないため、AI候補を再生成できません。")
        return False
    try:
        reservation = _candidate_sheet_recovery_reservation(photo)
    except Exception as exc:
        st.warning("AI候補の再生成先を準備できませんでした。")
        with st.expander("詳細"):
            st.code(str(exc))
        return False
    result = moments_recovery_component(
        data={
            "enabled": True,
            "video_url": video_url,
            "sheet_signed_url": reservation.get("signed_url"),
            "sheet_path": reservation.get("path"),
            "recovery_id": reservation.get("recovery_id"),
        },
        key=f"moments_recovery_v134_{photo.get('id')}_{reservation.get('recovery_id')}",
        on_candidate_sheet_change=lambda: None,
        on_recovery_error_change=lambda: None,
    )
    payload = getattr(result, "candidate_sheet", None)
    if isinstance(payload, dict) and str(payload.get("path") or "") == str(reservation.get("path") or ""):
        try:
            updated = store_video_ai_candidate_sheet(
                photo,
                payload.get("path"),
                payload.get("manifest") or [],
                columns=payload.get("columns") or 4,
                rows=payload.get("rows") or 0,
            )
            st.session_state.pop(f"_moments_recovery_reservation_v134_{photo.get('id')}", None)
            launch_video_ai_background_job(updated)
            try:
                _home_video_counts_cached.clear()
            except Exception:
                pass
            st.rerun()
        except Exception as exc:
            st.error("元動画からAI候補を登録できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))
    error_payload = getattr(result, "recovery_error", None)
    if isinstance(error_payload, dict) and error_payload.get("message"):
        st.warning("元動画からの候補作成に失敗しました。")
        with st.expander("詳細"):
            st.code(str(error_payload.get("message")))
    return True


def auto_recover_one_video_candidate_sheet():
    """Automatically recover one video that needs browser-side frame extraction.

    This renders the recovery component without requiring a viewer button. The
    component fetches the already-saved original video, samples it every 0.1s,
    uploads one contact sheet, and triggers the normal AI pipeline.
    """
    if moments_recovery_component is None:
        return False
    try:
        rows = (
            supabase_client()
            .table(PHOTO_TABLE)
            .select("*")
            .eq("family_key", current_family_key())
            .eq("member_key", current_member_key())
            .order("captured_at", desc=True)
            .limit(24)
            .execute()
        ).data or []
    except Exception:
        return False

    for row in rows:
        if not photo_is_video(row):
            continue
        selection = photo_media_metadata(row).get("ai_selection") or {}
        if not isinstance(selection, dict):
            selection = {}
        status = str(selection.get("status") or "").strip().lower()
        if status != "waiting_browser_candidates":
            continue
        st.caption("保存済み動画から、いい瞬間の候補を自動復旧しています…")
        _render_moments_candidate_recovery(row, -134)
        return True
    return False


def list_member_videos_for_moments(limit=300):
    rows = (
        supabase_client()
        .table(PHOTO_TABLE)
        .select("*")
        .eq("family_key", current_family_key())
        .eq("member_key", current_member_key())
        .order("captured_at", desc=True)
        .limit(max(1, int(limit)))
        .execute()
    ).data or []
    # The query is already newest-first. page_moments groups by review status
    # without disturbing that order inside each group.
    return [row for row in rows if photo_is_video(row)]


def _moments_video_title(photo):
    captured = str(photo.get("captured_at") or "").strip()
    label = captured
    try:
        parsed = datetime.fromisoformat(captured.replace("Z", "+00:00"))
        label = parsed.astimezone(ZoneInfo(APP_TIMEZONE)).strftime("%Y/%m/%d %H:%M")
    except Exception:
        pass
    place = photo_location_label(photo)
    return f"{label}　{place}" if place else label



_MOMENTS_SELECT_HTML = """
<div id="moments-select-grid" class="moments-select-grid"></div>
"""

_MOMENTS_SELECT_CSS = """
.moments-select-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  box-sizing: border-box;
  margin: 4px 0 8px;
}
.moments-select-card,
.moments-select-empty {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border-radius: 13px;
}
.moments-select-card {
  appearance: none;
  -webkit-appearance: none;
  position: relative;
  margin: 0;
  padding: 4px;
  border: 3px solid rgba(174, 182, 194, .72);
  background: rgba(174, 182, 194, .07);
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  overflow: hidden;
  color: var(--st-text-color);
  text-align: left;
}
.moments-select-card.selected {
  border-color: #F59E0B;
  background: rgba(245, 158, 11, .16);
  box-shadow: 0 0 0 2px rgba(245, 158, 11, .12);
}
.moments-select-card:active { transform: scale(.985); }
.moments-select-card:disabled {
  cursor: default;
  opacity: 1;
}
.moments-select-image-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  border-radius: 9px;
  background: rgba(128,128,128,.08);
}
.moments-select-image-wrap img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.moments-select-rank,
.moments-select-picked {
  position: absolute;
  z-index: 2;
  border-radius: 999px;
  color: #fff;
  font-weight: 800;
  line-height: 1.15;
  box-shadow: 0 1px 4px rgba(0,0,0,.22);
}
.moments-select-rank {
  left: 5px;
  top: 5px;
  padding: 3px 6px;
  background: rgba(17,24,39,.72);
  font-size: 9px;
}
.moments-select-picked {
  right: 5px;
  bottom: 5px;
  padding: 4px 7px;
  background: #F59E0B;
  font-size: 9px;
}
.moments-select-meta {
  margin-top: 5px;
  font-size: 10px;
  line-height: 1.2;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.moments-select-reason {
  margin-top: 2px;
  min-height: 2.3em;
  font-size: 9px;
  line-height: 1.18;
  opacity: .75;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.moments-select-empty {
  aspect-ratio: 1 / 1;
  border: 1px dashed rgba(128,128,128,.18);
  background: rgba(128,128,128,.035);
}
@media (max-width: 640px) {
  .moments-select-grid { gap: 6px; }
  .moments-select-card { padding: 3px; border-radius: 11px; }
  .moments-select-image-wrap { border-radius: 7px; }
  .moments-select-meta { font-size: 9px; }
  .moments-select-reason { font-size: 8px; }
  .moments-select-rank, .moments-select-picked { font-size: 8px; }
}
"""

_MOMENTS_SELECT_JS = r"""
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const grid = parentElement.querySelector('#moments-select-grid');
  if (!grid) return;

  grid.replaceChildren();
  const photos = Array.isArray(data?.photos) ? data.photos.slice(0, 9) : [];
  const disabled = Boolean(data?.disabled);
  const selected = new Set(
    (Array.isArray(data?.selected_ranks) ? data.selected_ranks : [])
      .map((value) => Number(value))
      .filter((value) => Number.isFinite(value) && value > 0)
  );

  const emitSelection = () => {
    setTriggerValue('selected_ranks', Array.from(selected).sort((a, b) => a - b));
  };

  for (let index = 0; index < 9; index += 1) {
    const photo = photos[index];
    if (!photo) {
      const empty = document.createElement('div');
      empty.className = 'moments-select-empty';
      grid.appendChild(empty);
      continue;
    }

    const rank = Number(photo.rank || (index + 1));
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'moments-select-card';
    button.disabled = disabled;
    button.setAttribute('aria-label', `写真${rank}を${selected.has(rank) ? '選択解除' : '選択'}`);

    const imageWrap = document.createElement('div');
    imageWrap.className = 'moments-select-image-wrap';

    if (photo.src) {
      const img = document.createElement('img');
      img.src = String(photo.src);
      img.alt = `いい瞬間 ${rank}`;
      img.loading = 'lazy';
      img.decoding = 'async';
      img.fetchPriority = 'low';
      imageWrap.appendChild(img);
    }

    const rankBadge = document.createElement('div');
    rankBadge.className = 'moments-select-rank';
    rankBadge.textContent = photo.ai_best ? '★ AI BEST' : `#${rank}`;
    imageWrap.appendChild(rankBadge);

    const pickedBadge = document.createElement('div');
    pickedBadge.className = 'moments-select-picked';
    pickedBadge.textContent = '選択中';
    imageWrap.appendChild(pickedBadge);

    const meta = document.createElement('div');
    meta.className = 'moments-select-meta';
    meta.textContent = String(photo.meta || '');

    const reason = document.createElement('div');
    reason.className = 'moments-select-reason';
    reason.textContent = String(photo.reason || '');

    const syncVisual = () => {
      const active = selected.has(rank);
      button.classList.toggle('selected', active);
      pickedBadge.style.display = active ? 'block' : 'none';
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
      button.setAttribute('aria-label', `写真${rank}を${active ? '選択解除' : '選択'}`);
    };

    syncVisual();
    button.appendChild(imageWrap);
    button.appendChild(meta);
    button.appendChild(reason);

    if (!disabled) {
      button.addEventListener('click', () => {
        if (selected.has(rank)) selected.delete(rank);
        else selected.add(rank);
        syncVisual();
        emitSelection();
      });
    }

    grid.appendChild(button);
  }
}
"""

moments_select_component = None
_moments_select_component_initialized = False


def _get_moments_select_component():
    global moments_select_component, _moments_select_component_initialized
    if _moments_select_component_initialized:
        return moments_select_component
    _moments_select_component_initialized = True
    try:
        moments_select_component = st.components.v2.component(
            "tokyo_burari_moments_select_v124",
            html=_MOMENTS_SELECT_HTML,
            css=_MOMENTS_SELECT_CSS,
            js=_MOMENTS_SELECT_JS,
        )
    except Exception:
        moments_select_component = None
    return moments_select_component


def _render_moments_picker(photo, index):
    selection_meta = photo_media_metadata(photo).get("ai_selection") or {}
    if not isinstance(selection_meta, dict):
        selection_meta = {}
    status = str(selection_meta.get("status") or "").strip().lower()
    title = _moments_video_title(photo)
    video_id = str(photo.get("id") or "")
    round_number = int(selection_meta.get("round") or 0)

    def render_reviewed_recut_button():
        can_recut = bool(_video_ai_has_candidate_source(selection_meta) or photo_video_storage_path(photo))
        if not can_recut:
            return
        st.markdown("---")
        if st.button(
            "🔄 いい瞬間をもう一度作る",
            use_container_width=True,
            key=f"moments_reviewed_recut_{video_id}_{round_number}",
            help=(
                "元動画から0.1秒間隔で再評価して、新しい『いい瞬間』候補を作ります。"
                "すでに日記へ残した写真は削除しません。"
            ),
        ):
            try:
                with st.spinner("元動画から、いい瞬間をもう一度作っています…"):
                    request_video_ai_reroll(photo, record_rejection=False)
                st.session_state.pop(f"_moments_tap_selected_{video_id}_{round_number}", None)
                st.session_state.pop(f"_moments_tap_serial_{video_id}_{round_number}", None)
                st.session_state["_moments_notice"] = (
                    "元動画から新しい『いい瞬間』の再作成を開始しました。"
                    "すでに日記へ残した写真はそのまま残ります。"
                )
                st.rerun()
            except Exception as exc:
                st.error("いい瞬間をもう一度作成できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    st.markdown(f"#### {html.escape(title)}")
    capture_meta = photo_media_metadata(photo).get("video_capture") or {}
    if isinstance(capture_meta, dict):
        width = max(0, int(capture_meta.get("width") or 0))
        height = max(0, int(capture_meta.get("height") or 0))
        fps = max(0.0, float(capture_meta.get("frame_rate") or 0))
        bitrate = max(0, int(capture_meta.get("video_bitrate_bps") or 0))
        details = []
        if width and height:
            details.append(f"{width}×{height}")
        if fps:
            details.append(f"{fps:.0f}fps")
        if bitrate:
            details.append(f"約{bitrate / 1_000_000:.1f}Mbps")
        if details:
            st.caption("元動画品質：" + " / ".join(details))
    high_quality_count = max(0, int(selection_meta.get("high_quality_count") or 0))
    if status in {"ready", "reviewed"} and high_quality_count:
        st.caption(f"切り抜き：元動画の元解像度フレーム {high_quality_count}枚")
    video_expander_label = "動画を見る（軽い手振れ補正）" if video_is_stabilized(photo) else "元の動画を見る"
    with st.expander(video_expander_label):
        video_url = video_display_url(photo)
        if video_url:
            st.video(video_url)
            stabilization_caption = video_stabilization_caption(photo)
            if stabilization_caption:
                st.caption(stabilization_caption)
            render_video_delete_controls(photo, f"moments_source_{video_id}_{index}")
        else:
            st.caption("動画を読み込めませんでした。")
            render_video_delete_controls(photo, f"moments_source_missing_{video_id}_{index}")

    # v116: this page is a viewer only. It never starts candidate extraction or
    # initial AI selection. Those jobs start automatically after video storage and
    # are also resumed by app-level maintenance after a Streamlit restart.
    if status == "processing":
        stage = str(selection_meta.get("stage") or "").strip().lower()
        if stage == "candidate_preparation":
            st.info("保存済み動画を0.1秒間隔で切り出し、AI候補を準備しています。")
        else:
            st.info("現在いい瞬間の切り取り中です。")
            progress_message = str(selection_meta.get("progress_message") or "").strip()
            if progress_message:
                st.caption(progress_message)
        if video_ai_processing_is_stale(selection_meta):
            st.caption("処理が長引いています。アプリ側で自動再開の対象になります。")
        if st.button(
            "状態を更新",
            use_container_width=True,
            key=f"moments_refresh_{video_id}_{index}",
        ):
            st.rerun()
        return

    if status in {"", "waiting_candidates", "waiting_browser_candidates"}:
        st.info("現在いい瞬間の切り取り中です。")
        if st.button(
            "状態を更新",
            use_container_width=True,
            key=f"moments_refresh_waiting_{video_id}_{index}",
        ):
            st.rerun()
        return

    if status == "error":
        st.warning("この動画の自動切り取りを完了できませんでした。元動画は保存されています。")
        detail = str(selection_meta.get("last_error") or selection_meta.get("message") or "").strip()
        if detail:
            with st.expander("詳細"):
                st.code(detail)
        st.caption("「いい瞬間を見る」は閲覧専用です。ここから初回の切り取り処理は開始しません。")
        return

    items = video_ai_selection_items(photo)
    if status == "reviewed" and str(selection_meta.get("review_result") or "") == "none_kept":
        st.success("この動画では、写真を1枚も残さない選択をしています。")
        render_reviewed_recut_button()
        return
    if not items:
        st.info("いい瞬間の自動処理結果を待っています。")
        if st.button(
            "状態を更新",
            use_container_width=True,
            key=f"moments_refresh_empty_{video_id}_{index}",
        ):
            st.rerun()
        return

    st.caption(
        f"AIが映えを重視して最大{VIDEO_AI_MAX_SELECTIONS}枚を選んでいます。3×3で比較し、気に入った写真を複数選べます。"
        "選んだ結果は、次回以降のAIセレクションにも軽く反映されます。"
    )
    if status == "reviewed":
        st.info(
            "確認済みの動画も、写真をタップして再度選択できます。"
            "すでに日記へ残した写真は自動削除せず、新しく選んだ写真を追加で残せます。"
        )
        render_reviewed_recut_button()

    paths = tuple(str(item.get("storage_path") or "").strip() for item in items)
    try:
        signed_map = signed_photo_url_map(paths, expires_in=1800)
    except Exception:
        signed_map = {}

    grid_items = list(items)[:VIDEO_AI_MAX_SELECTIONS]
    valid_ranks = {
        int(item.get("rank") or idx + 1)
        for idx, item in enumerate(grid_items)
        if isinstance(item, dict)
    }
    selection_state_key = f"_moments_tap_selected_{video_id}_{round_number}"
    component_serial_key = f"_moments_tap_serial_{video_id}_{round_number}"
    if selection_state_key not in st.session_state:
        st.session_state[selection_state_key] = sorted(
            int(item.get("rank") or idx + 1)
            for idx, item in enumerate(grid_items)
            if isinstance(item, dict) and bool(item.get("human_selected"))
        )

    selected_ranks = sorted(
        rank for rank in (st.session_state.get(selection_state_key) or [])
        if int(rank) in valid_ranks
    )
    cards = []
    for item_index, item in enumerate(grid_items):
        rank = int(item.get("rank") or item_index + 1)
        path = str(item.get("storage_path") or "").strip()
        url = str(signed_map.get(path) or "")
        if not url:
            try:
                url = image_data_url(download_photo(path))
            except Exception:
                url = ""
        quality = _video_selection_quality_label(item.get("primary_quality"))
        seconds = max(0, int(item.get("timestamp_ms") or 0)) / 1000
        cards.append(
            {
                "rank": rank,
                "src": url,
                "ai_best": bool(item.get("ai_best")) or rank == 1,
                "meta": f"{seconds:.1f}秒・{quality}",
                "reason": str(item.get("reason") or "").strip(),
            }
        )

    picker_component = _get_moments_select_component()
    if picker_component is not None:
        serial = int(st.session_state.get(component_serial_key) or 0)
        result = picker_component(
            data={
                "photos": cards,
                "selected_ranks": selected_ranks,
                "disabled": False,
            },
            key=f"moments_tap_picker_{video_id}_{round_number}_{serial}",
            on_selected_ranks_change=lambda: None,
        )
        result_selected = getattr(result, "selected_ranks", None)
        if isinstance(result_selected, (list, tuple)):
            normalized = sorted(
                {
                    int(value)
                    for value in result_selected
                    if str(value).strip().lstrip("-").isdigit() and int(value) in valid_ranks
                }
            )
            if normalized != selected_ranks:
                st.session_state[selection_state_key] = normalized
                st.session_state[component_serial_key] = serial + 1
                st.rerun()
        selected_ranks = sorted(
            rank for rank in (st.session_state.get(selection_state_key) or [])
            if int(rank) in valid_ranks
        )
    else:
        # Fallback for older Streamlit runtimes: keep the 3×3 layout and offer a
        # compact select/unselect button immediately below each photo.
        for row_start in range(0, VIDEO_AI_MAX_SELECTIONS, 3):
            row_columns = st.columns(3, gap="small")
            for column_offset in range(3):
                item_index = row_start + column_offset
                with row_columns[column_offset]:
                    if item_index >= len(cards):
                        st.write("")
                        continue
                    card = cards[item_index]
                    rank = int(card["rank"])
                    border = "#F59E0B" if rank in selected_ranks else "rgba(174,182,194,.72)"
                    if card.get("src"):
                        st.markdown(
                            f'<div style="padding:3px;border:3px solid {border};border-radius:12px;">'
                            f'<img src="{html.escape(str(card["src"]), quote=True)}" '
                            'style="display:block;width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;" />'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                    if st.button(
                        "選択解除" if rank in selected_ranks else "選択",
                        use_container_width=True,
                        disabled=False,
                        key=f"moments_fallback_pick_{video_id}_{round_number}_{rank}",
                    ):
                        current = set(selected_ranks)
                        if rank in current:
                            current.remove(rank)
                        else:
                            current.add(rank)
                        st.session_state[selection_state_key] = sorted(current)
                        st.rerun()

    st.caption("写真をタップすると選択できます。選択中の写真はオレンジ色の枠で表示されます。")
    selected_rank_set = set(selected_ranks)
    send_clicked = st.button(
        f"選択した写真を残す（{len(selected_rank_set)}枚）",
        type="primary",
        use_container_width=True,
        disabled=not selected_rank_set,
        key=f"moments_send_{video_id}_{round_number}",
    )
    if send_clicked:
        newly_saved = 0
        try:
            with st.spinner("選択した写真を残しています…"):
                for item in items:
                    rank = int(item.get("rank") or 0)
                    if rank not in selected_rank_set:
                        continue
                    if not item.get("saved_photo_id"):
                        save_video_ai_selection_as_photo(photo, item)
                        newly_saved += 1
                record_video_ai_human_choices(photo, selected_rank_set)

            if newly_saved:
                previous_count = st.session_state.get("_home_today_photo_count")
                try:
                    previous_count = int(previous_count) if previous_count is not None else 0
                except Exception:
                    previous_count = 0
                st.session_state["_home_today_photo_count"] = previous_count + newly_saved
            st.session_state["_moments_notice"] = (
                f"選択した{len(selected_rank_set)}枚を確認しました。新しく選んだ写真は日記に残しました。"
                "今回選んだ傾向は、今後のAIセレクションにも反映します。"
            )
            st.rerun()
        except Exception as exc:
            st.error("選択した写真を残せませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    if status != "reviewed":
        if st.button(
            "どれも残さない",
            use_container_width=True,
            key=f"moments_keep_none_{video_id}_{round_number}",
            help="今回の候補写真は1枚も日記に残さず、この動画の確認を完了します。元動画は動画保管庫に残ります。",
        ):
            try:
                with st.spinner("今回の候補を残さない設定にしています…"):
                    record_video_ai_no_choice(photo)
                st.session_state.pop(selection_state_key, None)
                st.session_state.pop(component_serial_key, None)
                st.session_state["_moments_notice"] = (
                    "この動画からは写真を残しませんでした。元動画は動画保管庫に残っています。"
                )
                st.rerun()
            except Exception as exc:
                st.error("どれも残さない設定を保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    can_reroll = bool(_video_ai_has_candidate_source(selection_meta) or photo_video_storage_path(photo))
    if can_reroll and status != "reviewed":
        st.markdown("---")
        if st.button(
            "🔄 再作成",
            use_container_width=True,
            disabled=bool(selected_rank_set),
            help="現在の候補に気に入る写真がない場合、同じ動画から映えを重視して別の候補を再作成します。",
            key=f"moments_reroll_{video_id}_{round_number}",
        ):
            try:
                request_video_ai_reroll(photo)
                st.session_state.pop(selection_state_key, None)
                st.session_state.pop(component_serial_key, None)
                st.session_state["_moments_notice"] = (
                    "前回の候補は好みではなかったという情報を残し、映えを重視して別の候補を再作成しています。"
                )
                st.rerun()
            except Exception as exc:
                st.error("いい瞬間を再作成できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    if status == "reviewed":
        st.success("この動画は確認済みです。写真をタップすれば、いつでも再度選択できます。")


def _render_video_storage_repair_panel(db_video_count):
    with st.expander("Storageの整理・修復", expanded=(int(db_video_count or 0) == 0)):
        st.caption(
            "動画保管庫はDB登録済み動画だけを表示します。ここではSupabase Storageの実体を直接確認し、"
            "DBに登録されていない孤立動画を安全に整理できます。"
        )
        st.caption(f"Supabaseキー：{_supabase_secret_key_kind()} ／ Bucket：{PHOTO_BUCKET}")

        check_col, test_col = st.columns(2)
        with check_col:
            if st.button("Storage実体を確認", use_container_width=True, key="video_storage_audit_run"):
                try:
                    with st.spinner("Storageの実ファイルを確認しています…"):
                        report = member_storage_audit(force=True)
                    st.session_state["_video_storage_audit_visible"] = report
                    _invalidate_video_storage_audit_cache()
                    # Keep the just-generated report visible even though the normal cache was cleared.
                    st.session_state["_video_storage_audit_visible"] = report
                except Exception as exc:
                    st.session_state.pop("_video_storage_audit_visible", None)
                    st.error("Storage実体を確認できませんでした。")
                    st.code(_safe_error_text(exc, 600))
        with test_col:
            if st.button("動画保存先をテスト", use_container_width=True, key="video_storage_sign_test"):
                try:
                    with st.spinner("署名付きアップロード先を確認しています…"):
                        test_video_storage_upload_destination()
                    clear_camera_video_upload_reservation()
                    st.success("動画保存先を正常に作成できます。テストではファイルを作成していません。")
                except Exception as exc:
                    st.error("動画保存先を作成できません。")
                    st.code(_safe_error_text(exc, 700))

        report = st.session_state.get("_video_storage_audit_visible")
        if not isinstance(report, dict):
            return

        actual_video_count = int(report.get("video_count") or 0)
        actual_video_bytes = int(report.get("video_bytes") or 0)
        orphan_count = int(report.get("orphan_video_count") or 0)
        orphan_bytes = int(report.get("orphan_video_bytes") or 0)
        st.markdown(
            f"**Storage実体：動画 {actual_video_count}本 / {format_storage_size(actual_video_bytes)}**  "
            f"  \n**うちDB未登録：{orphan_count}本 / {format_storage_size(orphan_bytes)}**"
        )

        missing = list(report.get("missing_video_paths") or [])
        if missing:
            st.warning(f"DBには記録があるのにStorageに見つからない動画が {len(missing)} 本あります。")

        orphan_videos = list(report.get("orphan_videos") or [])
        if not orphan_videos:
            st.success("この個人アカウントには、Storageにだけ残った孤立動画はありません。")
            return

        st.warning(
            "孤立動画が見つかりました。過去の保存失敗で動画本体だけStorageに残った可能性があります。"
            "下の削除はDBに参照がない元動画だけを対象にします。"
        )
        for item in orphan_videos[:30]:
            path = str(item.get("path") or "")
            st.caption(f"• {path}  ({format_storage_size(item.get('size_bytes') or 0)})")
        if len(orphan_videos) > 30:
            st.caption(f"ほか {len(orphan_videos) - 30}件")

        confirm_key = "_confirm_remove_orphan_videos"
        if st.session_state.get(confirm_key):
            st.error(f"DB未登録の孤立動画 {orphan_count}本をSupabase Storageから削除します。")
            delete_col, cancel_col = st.columns(2)
            with delete_col:
                if st.button("孤立動画を削除する", type="primary", use_container_width=True, key="remove_orphan_videos_execute"):
                    try:
                        paths = [str(x.get("path") or "") for x in orphan_videos]
                        removed = remove_orphan_member_videos(paths)
                        st.session_state.pop(confirm_key, None)
                        st.session_state.pop("_video_storage_audit_visible", None)
                        st.session_state["_video_storage_repair_notice"] = f"孤立動画を{removed}本削除しました。"
                        st.rerun()
                    except Exception as exc:
                        st.error("孤立動画を削除できませんでした。")
                        st.code(_safe_error_text(exc, 700))
            with cancel_col:
                if st.button("キャンセル", use_container_width=True, key="remove_orphan_videos_cancel"):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
        else:
            if st.button("孤立動画を削除", use_container_width=True, key="remove_orphan_videos_prepare"):
                st.session_state[confirm_key] = True
                st.rerun()


_VIDEO_LIBRARY_GRID_HTML = """
<div id="video-library-grid" class="video-library-grid"></div>
"""

_VIDEO_LIBRARY_GRID_CSS = """
.video-library-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  box-sizing: border-box;
  margin: 5px 0 10px;
}
.video-library-card,
.video-library-empty {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border-radius: 12px;
}
.video-library-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(174,182,194,.45);
  background: rgba(174,182,194,.055);
}
.video-library-open {
  appearance: none;
  -webkit-appearance: none;
  width: 100%;
  display: block;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--st-text-color);
  text-align: left;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
.video-library-open:active { transform: scale(.99); }
.video-library-image-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  background: rgba(128,128,128,.08);
}
.video-library-image-wrap img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.video-library-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  opacity: .62;
}
.video-library-play {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,.52);
  color: white;
  font-size: 16px;
  line-height: 1;
  box-shadow: 0 2px 8px rgba(0,0,0,.2);
  pointer-events: none;
}
.video-library-delete {
  appearance: none;
  -webkit-appearance: none;
  position: absolute;
  z-index: 5;
  top: 5px;
  right: 5px;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(17,24,39,.82);
  color: white;
  font-size: 21px;
  font-weight: 700;
  line-height: 26px;
  text-align: center;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  box-shadow: 0 2px 7px rgba(0,0,0,.24);
}
.video-library-delete:active { transform: scale(.92); }
.video-library-info {
  padding: 6px 7px 7px;
  min-height: 57px;
  box-sizing: border-box;
}
.video-library-title {
  font-size: 10px;
  line-height: 1.25;
  font-weight: 750;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.video-library-meta {
  margin-top: 3px;
  font-size: 9px;
  line-height: 1.2;
  opacity: .78;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.video-library-status {
  margin-top: 3px;
  font-size: 8.5px;
  line-height: 1.2;
  opacity: .78;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.video-library-empty {
  aspect-ratio: 1 / 1;
  border: 1px dashed rgba(128,128,128,.16);
  background: rgba(128,128,128,.025);
}
@media (max-width: 640px) {
  .video-library-grid { gap: 6px; }
  .video-library-card { border-radius: 10px; }
  .video-library-delete {
    top: 4px;
    right: 4px;
    width: 25px;
    height: 25px;
    font-size: 19px;
    line-height: 23px;
  }
  .video-library-play { width: 30px; height: 30px; font-size: 14px; }
  .video-library-info { padding: 5px 5px 6px; min-height: 52px; }
  .video-library-title { font-size: 9px; }
  .video-library-meta { font-size: 8px; }
  .video-library-status { font-size: 7.5px; }
}
"""

_VIDEO_LIBRARY_GRID_JS = r"""
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const grid = parentElement.querySelector('#video-library-grid');
  if (!grid) return;

  grid.replaceChildren();
  const videos = Array.isArray(data?.videos) ? data.videos.slice(0, 9) : [];

  for (let index = 0; index < 9; index += 1) {
    const video = videos[index];
    if (!video) {
      const empty = document.createElement('div');
      empty.className = 'video-library-empty';
      grid.appendChild(empty);
      continue;
    }

    const id = String(video.id || '');
    const card = document.createElement('div');
    card.className = 'video-library-card';

    const openButton = document.createElement('button');
    openButton.type = 'button';
    openButton.className = 'video-library-open';
    openButton.setAttribute('aria-label', `${String(video.title || '動画')}を見る`);

    const imageWrap = document.createElement('div');
    imageWrap.className = 'video-library-image-wrap';
    if (video.src) {
      const img = document.createElement('img');
      img.src = String(video.src);
      img.alt = '動画サムネイル';
      img.loading = 'lazy';
      img.decoding = 'async';
      img.fetchPriority = 'low';
      imageWrap.appendChild(img);
    } else {
      const placeholder = document.createElement('div');
      placeholder.className = 'video-library-placeholder';
      placeholder.textContent = '動画';
      imageWrap.appendChild(placeholder);
    }

    const play = document.createElement('div');
    play.className = 'video-library-play';
    play.textContent = '▶';
    imageWrap.appendChild(play);

    const info = document.createElement('div');
    info.className = 'video-library-info';

    const title = document.createElement('div');
    title.className = 'video-library-title';
    title.textContent = String(video.title || '');
    info.appendChild(title);

    const meta = document.createElement('div');
    meta.className = 'video-library-meta';
    meta.textContent = String(video.meta || '');
    info.appendChild(meta);

    const status = document.createElement('div');
    status.className = 'video-library-status';
    status.textContent = String(video.status || '');
    info.appendChild(status);

    openButton.appendChild(imageWrap);
    openButton.appendChild(info);
    openButton.addEventListener('click', () => {
      if (id) setTriggerValue('open_video_id', id);
    });

    const deleteButton = document.createElement('button');
    deleteButton.type = 'button';
    deleteButton.className = 'video-library-delete';
    deleteButton.textContent = '×';
    deleteButton.setAttribute('aria-label', `${String(video.title || '動画')}を削除`);
    deleteButton.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (id) setTriggerValue('delete_video_id', id);
    });

    card.appendChild(openButton);
    card.appendChild(deleteButton);
    grid.appendChild(card);
  }
}
"""

video_library_grid_component = None
_video_library_grid_component_initialized = False


def _get_video_library_grid_component():
    global video_library_grid_component, _video_library_grid_component_initialized
    if _video_library_grid_component_initialized:
        return video_library_grid_component
    _video_library_grid_component_initialized = True
    try:
        video_library_grid_component = st.components.v2.component(
            "tokyo_burari_video_library_grid_v128",
            html=_VIDEO_LIBRARY_GRID_HTML,
            css=_VIDEO_LIBRARY_GRID_CSS,
            js=_VIDEO_LIBRARY_GRID_JS,
        )
    except Exception:
        video_library_grid_component = None
    return video_library_grid_component


def page_videos():
    delete_notice = st.session_state.pop("_video_delete_notice", None)
    if delete_notice:
        st.success(delete_notice)

    page_top(
        "🎞️ 動画保管庫",
        "保存された元動画を3×3で確認できます。動画を押すと再生、右上の×で削除できます。",
    )

    try:
        videos = list_member_videos_for_moments(limit=500)
    except Exception as exc:
        st.error("動画保管庫を読み込めませんでした。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        return

    quota = video_storage_quota_bytes()
    try:
        usage = current_video_storage_usage_bytes()
    except Exception:
        usage = sum(
            max(0, int(photo_media_metadata(v).get("video_size_bytes") or 0))
            for v in videos
        )
    if quota > 0:
        st.caption(
            f"DB登録済み動画：{len(videos)}本 ／ 動画Storage実使用量 {format_storage_size(usage)} / "
            f"上限 {format_storage_size(quota)} ／ 残り {format_storage_size(max(0, quota - usage))}"
        )
    else:
        st.caption(f"DB登録済み動画：{len(videos)}本 ／ 動画Storage実使用量 {format_storage_size(usage)} ／ 総容量上限は未設定")

    repair_notice = st.session_state.pop("_video_storage_repair_notice", None)
    if repair_notice:
        st.success(repair_notice)
    _render_video_storage_repair_panel(len(videos))

    if not videos:
        st.info("DBに登録された動画はありません。上の「Storage実体を確認」で、未登録の動画が残っていないか確認できます。")
        return

    # Nine videos per page keeps the vault as an exact 3×3 grid on both desktop
    # and mobile. The custom component never collapses the three columns.
    per_page = 9
    page_count = max(1, (len(videos) + per_page - 1) // per_page)
    page_key = "_video_library_grid_page"
    try:
        current_page = int(st.session_state.get(page_key) or 0)
    except Exception:
        current_page = 0
    current_page = max(0, min(current_page, page_count - 1))
    st.session_state[page_key] = current_page

    start_index = current_page * per_page
    visible_videos = videos[start_index:start_index + per_page]
    cards = []
    for local_index, video_row in enumerate(visible_videos):
        metadata = photo_media_metadata(video_row)
        size_value = max(0, int(metadata.get("video_size_bytes") or 0))
        duration_ms = max(0, int(metadata.get("video_duration_ms") or 0))
        detail_parts = []
        if duration_ms:
            detail_parts.append(f"{max(1, round(duration_ms / 1000))}秒")
        if size_value:
            detail_parts.append(format_storage_size(size_value))

        selection = metadata.get("ai_selection") or {}
        status_label = ""
        if isinstance(selection, dict):
            status = str(selection.get("status") or "").lower()
            if status == "processing":
                stage = str(selection.get("stage") or "").strip().lower()
                status_label = "✨ 0.1秒間隔で候補を準備中" if stage == "candidate_preparation" else "✨ いい瞬間を自動選定中"
            elif status in {"", "waiting_candidates"}:
                status_label = "✨ 自動処理を開始待ち"
            elif status == "ready":
                status_label = "✨ いい瞬間を確認できます"
            elif status == "reviewed":
                status_label = "✓ いい瞬間を確認済み"
            elif status == "error":
                status_label = "AI選定は未完了"

        poster_path = str(video_row.get("storage_path") or "").strip()
        preview_url = photo_display_url(video_row)
        if not preview_url and poster_path:
            try:
                preview_url = thumbnail_photo_data_url(poster_path, max_px=520, quality=82)
            except Exception:
                preview_url = ""

        cards.append(
            {
                "id": str(video_row.get("id") or ""),
                "src": preview_url,
                "title": _moments_video_title(video_row),
                "meta": " ／ ".join(detail_parts),
                "status": status_label,
            }
        )

    grid_component = _get_video_library_grid_component()
    handled_action = False
    if grid_component is not None:
        serial_key = "_video_library_grid_serial"
        serial = int(st.session_state.get(serial_key) or 0)
        result = grid_component(
            data={"videos": cards},
            key=f"video_library_grid_{current_page}_{serial}",
            on_open_video_id_change=lambda: None,
            on_delete_video_id_change=lambda: None,
        )
        open_video_id = str(getattr(result, "open_video_id", None) or "").strip()
        delete_video_id = str(getattr(result, "delete_video_id", None) or "").strip()

        if delete_video_id:
            target = next((row for row in visible_videos if str(row.get("id") or "") == delete_video_id), None)
            if target:
                st.session_state[serial_key] = serial + 1
                show_video_delete_dialog(target)
                handled_action = True
        elif open_video_id:
            target = next((row for row in visible_videos if str(row.get("id") or "") == open_video_id), None)
            if target:
                metadata = photo_media_metadata(target)
                detail_parts = []
                duration_ms = max(0, int(metadata.get("video_duration_ms") or 0))
                size_value = max(0, int(metadata.get("video_size_bytes") or 0))
                if duration_ms:
                    detail_parts.append(f"{max(1, round(duration_ms / 1000))}秒")
                if size_value:
                    detail_parts.append(format_storage_size(size_value))
                st.session_state[serial_key] = serial + 1
                show_video_library_dialog(target, _moments_video_title(target), " ／ ".join(detail_parts))
                handled_action = True
    else:
        # Fallback for older Streamlit runtimes. Keep three columns and place an ×
        # control at the upper-right area of each card.
        for row_start in range(0, per_page, 3):
            row_columns = st.columns(3, gap="small")
            for offset in range(3):
                item_index = row_start + offset
                with row_columns[offset]:
                    if item_index >= len(visible_videos):
                        st.write("")
                        continue
                    video_row = visible_videos[item_index]
                    card = cards[item_index]
                    _, delete_col = st.columns([5, 1], gap="small")
                    with delete_col:
                        if st.button(
                            "×",
                            key=f"video_fallback_delete_{current_page}_{item_index}_{video_row.get('id')}",
                            help="この動画を削除",
                        ):
                            show_video_delete_dialog(video_row)
                    if card.get("src"):
                        st.image(card["src"], use_container_width=True)
                    st.caption(card.get("title") or "")
                    if st.button(
                        "見る",
                        use_container_width=True,
                        key=f"video_fallback_open_{current_page}_{item_index}_{video_row.get('id')}",
                    ):
                        show_video_library_dialog(video_row, card.get("title") or "", card.get("meta") or "")

    if page_count > 1 and not handled_action:
        st.caption(f"{current_page + 1} / {page_count}ページ　（1ページ9本）")
        prev_col, next_col = st.columns(2, gap="small")
        with prev_col:
            if st.button(
                "← 前の9本",
                use_container_width=True,
                disabled=current_page <= 0,
                key=f"video_grid_prev_{current_page}",
            ):
                st.session_state[page_key] = max(0, current_page - 1)
                st.rerun()
        with next_col:
            if st.button(
                "次の9本 →",
                use_container_width=True,
                disabled=current_page >= page_count - 1,
                key=f"video_grid_next_{current_page}",
            ):
                st.session_state[page_key] = min(page_count - 1, current_page + 1)
                st.rerun()


def page_moments():
    delete_notice = st.session_state.pop("_video_delete_notice", None)
    if delete_notice:
        st.success(delete_notice)

    page_top(
        "✨ いい瞬間",
        "動画ごとにAIが選んだ瞬間を確認し、気に入った写真だけ日記へ送れます。",
    )
    notice = st.session_state.pop("_moments_notice", None)
    if notice:
        st.success(notice)

    try:
        videos = list_member_videos_for_moments(limit=300)
    except Exception as exc:
        st.error("動画の一覧を読み込めませんでした。")
        with st.expander("保護者向け詳細"):
            st.code(str(exc))
        return

    if not videos:
        st.info("まだ動画がありません。動画を撮影すると、自動保存後にAIがいい瞬間を探します。")
        return

    pending = []
    ready = []
    reviewed = []
    for video in videos:
        selection = photo_media_metadata(video).get("ai_selection") or {}
        if not isinstance(selection, dict):
            selection = {}
        status = str(selection.get("status") or "").lower()
        if status == "reviewed":
            reviewed.append(video)
        elif status == "ready" and video_ai_selection_items(video):
            ready.append(video)
        else:
            pending.append(video)

    display_videos = pending + ready
    if display_videos:
        for idx, video in enumerate(display_videos):
            if idx:
                st.divider()
            _render_moments_picker(video, idx)
    else:
        st.info("未確認のAIセレクションはありません。")

    if reviewed:
        st.divider()
        with st.expander(f"確認済みの動画（{len(reviewed)}本）— 再選択できます"):
            for idx, video in enumerate(reviewed[:30]):
                if idx:
                    st.divider()
                _render_moments_picker(video, 1000 + idx)



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
    is_video = photo_is_video(photo)
    st.markdown("#### 今撮った動画" if is_video else "#### 今撮った写真")
    if not render_saved_media_preview(photo, image_alt="今撮った動画の代表画像" if is_video else "今撮った写真", delete_key_prefix="recent_camera"):
        st.warning("撮影した記録のプレビューを表示できませんでした。コメントは続けられます。")
    if is_video:
        st.caption("✨ いい瞬間は自動で作成します。トップページの「いい瞬間を見る」から確認できます。")

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
        st.caption("この動画について、まず自由に1回話してね。" if is_video else "この写真について、まず自由に1回話してね。")
        mic_label = "今撮った動画について話してね" if is_video else "今撮った写真について話してね"
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
                f"東京ぶらり旅で今撮った{'動画' if is_video else '写真'}について、子どもが自由に説明しています。場所は{location_label or '不明'}です。",
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
    if st.button("←", key="camera_back_parent", help="1つ前の階層に戻る"):
        navigate_to_parent()

    notice = st.session_state.pop("_camera_notice", None)
    if notice:
        st.success(notice)

    if live_camera_component is None:
        st.error("ライブカメラ機能に必要なStreamlitのバージョンが古いです。requirements.txtを更新してください。")
        return

    # Video mode is gated before recording begins. Capacity and Storage-upload
    # preparation are deliberately reported as separate states: a failure to mint
    # an upload destination must never be mislabeled as "capacity shortage".
    video_unavailable_reason = ""
    try:
        video_capacity = video_recording_capacity_status()
    except Exception as exc:
        video_capacity = {
            "allowed": False,
            "message": "動画の保存容量を確認できないため、動画撮影を一時停止しています。",
        }
        video_unavailable_reason = "capacity_check"
        with st.expander("動画容量チェックの詳細"):
            st.code(str(exc))

    if not bool(video_capacity.get("allowed")):
        if not video_unavailable_reason:
            video_unavailable_reason = "quota"
        st.warning(str(video_capacity.get("message") or "動画の保存容量が不足しています。"))

    auto_start = bool(st.session_state.pop("_camera_auto_start", False))
    auto_start_video = bool(st.session_state.pop("_camera_auto_start_video", False))
    active_snapshot = st.session_state.get("_active_trip_snapshot")
    if not isinstance(active_snapshot, dict) or active_snapshot.get("trip_date") != today_iso() or active_snapshot.get("status") != "active":
        active_snapshot = None

    # v107: reserve a short-lived signed Storage upload destination before video
    # recording. The browser can then PUT the Blob straight to Supabase and only
    # return compact metadata to Streamlit.
    video_reservation = {}
    video_allowed = bool(video_capacity.get("allowed"))
    video_capacity_message = str(video_capacity.get("message") or "")
    camera_trip = active_snapshot
    if video_allowed:
        try:
            camera_trip = camera_trip or ensure_today_trip()
            video_reservation = get_camera_video_upload_reservation(
                camera_trip["id"],
                st.session_state.capture_serial,
            )
        except Exception as exc:
            video_allowed = False
            video_unavailable_reason = "storage_setup"
            video_capacity_message = "保存容量ではなく、動画のアップロード先を準備できないため撮影を開始できません。"
            st.error(video_capacity_message)
            st.caption(f"Supabaseキー：{_supabase_secret_key_kind()} / Bucket：{PHOTO_BUCKET}")
            with st.expander("動画保存先の準備エラー", expanded=True):
                st.code(_safe_error_text(exc, 900))

    camera_trip_key = str((camera_trip or {}).get("id") or "pending")
    result = live_camera_component(
        data={
            "auto_start": auto_start,
            "auto_start_mode": "video" if auto_start_video else ("photo" if auto_start else ""),
            "video_allowed": video_allowed,
            "video_capacity_message": video_capacity_message,
            "video_unavailable_reason": video_unavailable_reason,
            "video_upload_signed_url": str(video_reservation.get("signed_url") or ""),
            "video_upload_storage_path": str(video_reservation.get("storage_path") or ""),
            "video_upload_token": str(video_reservation.get("upload_token") or ""),
            "video_tus_endpoint": str(video_reservation.get("tus_endpoint") or ""),
            "video_upload_bucket": PHOTO_BUCKET,
            "video_candidate_sheet_signed_url": str(video_reservation.get("candidate_sheet_signed_url") or ""),
            "video_candidate_sheet_storage_path": str(video_reservation.get("candidate_sheet_path") or ""),
        },
        key=f"live_camera_v145_{camera_trip_key}_{st.session_state.capture_serial}",
        on_photo_change=lambda: None,
        on_video_change=lambda: None,
        on_camera_error_change=lambda: None,
    )

    payload = getattr(result, "photo", None)
    video_payload = getattr(result, "video", None)
    camera_error = getattr(result, "camera_error", None)
    # A component cycle is either a video event or a photo event. Never feed a stale
    # video/preview value into the still-photo data-URL decoder after video handling.
    video_event_present = isinstance(video_payload, dict) and bool(video_payload)

    if camera_error:
        message = camera_error.get("message") if isinstance(camera_error, dict) else str(camera_error)
        if message:
            st.warning(message)
        if isinstance(camera_error, dict):
            detail = str(camera_error.get("detail") or "").strip()
            if detail and detail not in str(message or ""):
                with st.expander("動画保存エラーの詳細", expanded=True):
                    st.code(detail)

    if (
        isinstance(video_payload, dict)
        and video_payload.get("upload_complete")
        and video_payload.get("video_storage_path")
    ):
        save_stage = "アップロード済み動画の確認"
        video_saved = False
        uploaded_video_path = str(video_payload.get("video_storage_path") or "").strip()
        try:
            reservation = st.session_state.get("_camera_video_upload_reservation_v116")
            if not isinstance(reservation, dict):
                raise ValueError("動画の保存予約を確認できませんでした。")
            reserved_video_path = str(reservation.get("storage_path") or "").strip()
            if uploaded_video_path != reserved_video_path:
                # A Streamlit rerun can recreate the reservation object while the browser
                # is finishing a direct upload. The uploaded path itself was originally
                # minted by this server, so accept it when it is still inside the current
                # signed-in member and trip prefix. This also makes registration resilient
                # to a stale reservation without weakening cross-member isolation.
                safe_prefix = (
                    f"{current_family_key()}/{current_member_key()}/"
                    f"{str(reservation.get('trip_id') or '')}/"
                )
                if not (
                    uploaded_video_path.startswith(safe_prefix)
                    and _storage_path_is_original_video(
                        uploaded_video_path,
                        video_payload.get("mime_type"),
                    )
                ):
                    raise ValueError("動画の保存先が撮影前の予約と一致しません。")

            save_stage = "代表画像の読み込み"
            poster_raw = b""
            try:
                poster_raw = decode_camera_data_url(video_payload.get("poster_data_url"))
            except Exception:
                # The original video is already safely in Storage. If the compact
                # poster value was dropped by the component runtime, reuse the first
                # valid AI still rather than failing the whole video registration.
                for frame_item in video_payload.get("candidate_frames") or []:
                    if not isinstance(frame_item, dict):
                        continue
                    try:
                        poster_raw = decode_camera_data_url(frame_item.get("data_url"))
                    except Exception:
                        poster_raw = b""
                    if poster_raw:
                        break
                # A missing poster must not invalidate an already-uploaded original.
                # register_browser_uploaded_video() creates a neutral placeholder.

            video_size = max(0, int(video_payload.get("video_size_bytes") or 0))
            recording_id = str(video_payload.get("recording_id") or "").strip()
            digest_source = f"{uploaded_video_path}|{video_size}|{recording_id}"
            digest = hashlib.sha1(digest_source.encode("utf-8")).hexdigest()
            digest_key = "saved_camera_video_digest_current"
            if st.session_state.get(digest_key) != digest:
                save_stage = "動画記録の登録"
                trip = ensure_today_trip()
                if str(trip.get("id") or "") != str(reservation.get("trip_id") or ""):
                    raise ValueError("動画の保存先と現在のぶらり旅が一致しません。")
                capture_source = str(video_payload.get("source") or "video_camera")
                location = build_photo_location(
                    video_payload.get("location"),
                    trip,
                    capture_source=capture_source,
                )

                with st.spinner("動画を保管庫に登録しています…"):
                    saved_video = register_browser_uploaded_video(
                        trip["id"],
                        uploaded_video_path,
                        video_size,
                        poster_raw,
                        mime_type=video_payload.get("mime_type"),
                        duration_ms=video_payload.get("duration_ms"),
                        location=location,
                        captured_at=video_payload.get("captured_at"),
                        capture_source=capture_source,
                        capture_width=video_payload.get("capture_width"),
                        capture_height=video_payload.get("capture_height"),
                        capture_frame_rate=video_payload.get("capture_frame_rate"),
                        video_bitrate_bps=video_payload.get("video_bitrate_bps"),
                    )

                video_saved = True
                st.session_state[digest_key] = digest
                if isinstance(saved_video, dict) and saved_video.get("id"):
                    st.session_state[f"_camera_recent_photo_{trip['id']}"] = saved_video["id"]
                try:
                    _home_video_counts_cached.clear()
                except Exception:
                    pass

                # v142: the saved original video is the only source of truth. Never
                # attach or consume a browser JPEG candidate sheet for new recordings.
                ai_status = "queued"
                if isinstance(saved_video, dict) and saved_video.get("id"):
                    try:
                        saved_video = mark_video_ai_waiting_candidates(
                            saved_video,
                            "元動画から非縮小・非劣化の0.1秒フレームを自動生成します。",
                        )
                    except Exception:
                        pass

                # v145: registration ends immediately after the original is durable.
                # The next automatic Streamlit execution processes queued Good Moments
                # synchronously. No user button is required and no detached thread is used.
                ai_status = "queued"

                previous_count = st.session_state.get("_home_today_photo_count")
                try:
                    previous_count = int(previous_count) if previous_count is not None else 0
                except Exception:
                    previous_count = 0
                st.session_state["_home_today_photo_count"] = previous_count + 1
                place_label = str((location or {}).get("place_label") or trip.get("destination") or "").strip()
                if place_label:
                    st.session_state["_home_today_place"] = place_label

                clear_camera_video_upload_reservation()
                st.session_state["_browser_last_camera_open_at"] = time.time() * 1000.0
                st.session_state["_browser_last_camera_mode"] = "video"
                st.session_state.capture_serial += 1
                if ai_status in {"queued", "queued_recovery"}:
                    notice = "動画を保管庫に保存しました。いい瞬間は自動で作成します。"
                else:
                    notice = "動画を保管庫に保存しました。いい瞬間を自動で作成しました。"
                st.session_state["_camera_notice"] = notice
                st.rerun()
        except Exception as exc:
            if video_saved:
                st.warning("動画本体は保管庫に保存済みです。保存後の処理だけ完了できませんでした。")
            else:
                detail = str(exc).strip().replace("\n", " ")
                if len(detail) > 220:
                    detail = detail[:217] + "..."
                st.error(f"動画を保存できませんでした。処理段階：{save_stage}" + (f" ／ {detail}" if detail else ""))
                # The original video has already reached Storage. Keep it intact even if
                # DB registration fails; quality-first recovery is safer than deleting
                # the source recording. A new reservation is minted for the next capture.
                try:
                    clear_camera_video_upload_reservation()
                except Exception:
                    pass
            with st.expander("保護者向け詳細"):
                st.code(f"処理段階: {save_stage}\n{exc}")

    if (not video_event_present) and isinstance(payload, dict) and payload.get("data_url"):
        try:
            raw = decode_camera_data_url(payload["data_url"])
            digest = hashlib.sha1(raw).hexdigest()
            digest_key = "saved_camera_digest_current"
            if st.session_state.get(digest_key) != digest:
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

                previous_count = st.session_state.get("_home_today_photo_count")
                try:
                    previous_count = int(previous_count) if previous_count is not None else 0
                except Exception:
                    previous_count = 0
                st.session_state["_home_today_photo_count"] = previous_count + 1
                place_label = str((location or {}).get("place_label") or trip.get("destination") or "").strip()
                if place_label:
                    st.session_state["_home_today_place"] = place_label

                st.session_state["_browser_last_camera_open_at"] = time.time() * 1000.0
                st.session_state["_browser_last_camera_mode"] = "photo"
                st.session_state.capture_serial += 1
                st.session_state["_camera_notice"] = "写真を保存しました。"
                st.rerun()
        except Exception as exc:
            st.error("写真を保存できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))

    trip = st.session_state.get("_active_trip_snapshot")
    if isinstance(trip, dict) and trip.get("id"):
        render_recent_camera_photo_comment(trip)


# ============================================================
# Page: Diary conversation
# ============================================================
def page_diary():
    page_top(
        "📖 日記",
        "まだ日記になっていない写真を一覧で確認できます。元動画は動画保管庫で管理し、日記には静止画だけを残します。",
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
        st.caption("撮影済みで、まだ日記として保存されていない写真です。動画そのものは日記には表示しません。")
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
        # Do not fetch any saved-diary photos until a specific trip is selected.
        # Original video rows stay in the video vault and are excluded from the diary.
        photos = diary_photos_only(list_trip_photos(trip_id))
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

    if photo_is_video(photo):
        st.info("元動画は日記には表示しません。動画保管庫から確認できます。")
        return
    if not render_saved_media_preview(photo, image_alt="日記の写真", delete_key_prefix="diary_media"):
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
        photos = diary_photos_only(list_trip_photos(trip_id))
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


def render_monthly_ai_comments(review):
    review = review if isinstance(review, dict) else {}
    st.markdown("#### AIからの気づき")
    opening = str(review.get("opening") or "").strip()
    if opening:
        st.markdown(
            f'<div class="monthly-card"><div class="big-text">{html.escape(opening)}</div></div>',
            unsafe_allow_html=True,
        )

    first_question = ""
    for finding in list(review.get("findings", []) or [])[:2]:
        if not isinstance(finding, dict):
            continue
        theme = str(finding.get("theme") or "").strip()
        insight = str(finding.get("evidence") or "").strip()
        if theme:
            st.markdown(f"**{theme}**")
        if insight:
            st.write(insight)
        if not first_question:
            first_question = str(finding.get("ask_child") or "").strip()

    question = first_question or str(review.get("one_question") or "").strip()
    if question:
        st.info(f"ちょっと考えてみる：{question}")

    with st.expander("保護者向けメモ"):
        st.write(review.get("parent_note", ""))
        st.caption(
            "本人が残したコメントの共通点を一段抽象化した振り返りです。"
            "性格診断・能力評価・将来予測ではありません。"
        )


# ============================================================
# Page: Monthly review
# ============================================================
def page_monthly(embedded=False):
    if not embedded:
        page_top("🗓 期間の振り返り")
    deleted_notice = st.session_state.pop("_monthly_video_deleted_notice", None)
    if deleted_notice:
        st.success(deleted_notice)
    st.caption("保存した日記と本人の言葉を、まとまった期間ごとにつないで振り返ります。")

    recent = list_recent_diaries(limit=120)
    pending_rows = list_pending_photo_trips(limit=80)
    month_keys = []
    for row in recent:
        trip_date = str(row.get("trip", {}).get("trip_date") or "")
        if len(trip_date) >= 7:
            key = trip_date[:7]
            if key not in month_keys:
                month_keys.append(key)
    for row in pending_rows:
        trip_date = str((row.get("trip") or {}).get("trip_date") or "")
        if len(trip_date) >= 7:
            key = trip_date[:7]
            if key not in month_keys:
                month_keys.append(key)
    month_keys = sorted(month_keys, reverse=True)
    if not month_keys:
        month_keys = [now_jst().strftime("%Y-%m")]

    month_key = st.selectbox(
        "振り返る期間",
        month_keys,
        format_func=format_month_label,
        key="monthly_selector",
    )
    period_label = format_month_label(month_key)
    st.markdown(f"### {period_label}の振り返り")
    bundle = get_month_bundle(month_key)
    completed_count = len(bundle["diaries"])
    commented_photo_count = sum(
        1
        for photo in bundle.get("photos", [])
        if _conversation_has_child_words(_stored_photo_conversation(photo))
    )
    st.write(f"この期間の日記：**{completed_count}回**　／　本人の言葉がある写真：**{commented_photo_count}枚**")
    if completed_count == 0 and commented_photo_count == 0:
        st.info("この期間には、まだ振り返りに使える本人の言葉がありません。")
        return

    saved = get_saved_monthly_review(month_key)
    session_key = f"monthly_review_{month_key}"
    if session_key not in st.session_state and saved:
        st.session_state[session_key] = saved.get("review_json") or {}
    review = st.session_state.get(session_key)

    # First-time creation still needs AI to assemble the review before music/video can be paired with it.
    if not review:
        if st.button("AIとこの期間を振り返る", type="primary", use_container_width=True):
            try:
                with st.spinner("この期間の言葉をつないでいます…"):
                    review = make_monthly_review(month_key, bundle)
                    save_monthly_review(month_key, review)
                st.session_state[session_key] = review
                st.session_state.pop(f"monthly_audio_{month_key}", None)
                st.session_state.pop(f"monthly_audio_pending_{month_key}", None)
                st.rerun()
            except Exception as exc:
                st.error("期間の振り返りを作れませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        return

    # Period reviews are text-only unless the user starts the YouTube replay.
    st.session_state.pop(f"monthly_audio_{month_key}", None)
    st.session_state.pop(f"monthly_audio_pending_{month_key}", None)

    playback = get_monthly_playback(review)
    music_ready = monthly_playback_is_ready(playback)
    settings_open_key = f"monthly_music_settings_open_{month_key}"
    comments_open_key = f"monthly_ai_comments_open_{month_key}"

    if not music_ready:
        # Older saved reviews may still contain quote-like summaries. Since the AI
        # comment is visible in the no-music state, upgrade it once to the insight format.
        if int(review.get("_insight_version") or 0) < 2:
            try:
                with st.spinner("本人の言葉から、短い気づきを作り直しています…"):
                    refreshed = make_monthly_review(month_key, bundle)
                    previous_playback = get_monthly_playback(review)
                    if previous_playback:
                        refreshed["_playback"] = previous_playback
                    save_monthly_review(month_key, refreshed)
                st.session_state[session_key] = refreshed
                st.rerun()
            except Exception:
                pass
        # With no music configured, make the next action obvious at the top.
        if st.button(
            "🎵 音楽をセットする",
            type="primary",
            use_container_width=True,
            key=f"monthly_music_setup_top_{month_key}",
        ):
            st.session_state[settings_open_key] = True

        if st.session_state.get(settings_open_key):
            render_monthly_music_settings(month_key, bundle, review, expanded=True)

        # Until a movie exists, keep the normal AI review visible.
        render_monthly_ai_comments(review)
        if st.button(
            "この期間をもう一度まとめる",
            use_container_width=True,
            key=f"monthly_regenerate_without_music_{month_key}",
        ):
            try:
                previous_playback = get_monthly_playback(review)
                with st.spinner("この期間の言葉をつないでいます…"):
                    refreshed = make_monthly_review(month_key, bundle)
                    if previous_playback:
                        refreshed["_playback"] = previous_playback
                    save_monthly_review(month_key, refreshed)
                st.session_state[session_key] = refreshed
                st.rerun()
            except Exception as exc:
                st.error("期間の振り返りを作れませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        return

    # Once music is configured, the movie becomes the main content.
    st.markdown("#### 振り返りムービー")
    rendered = render_monthly_replay_section(month_key, period_label, bundle, review)
    if not rendered:
        st.warning("振り返りムービーを表示できませんでした。音楽または写真の設定を確認してください。")

    time_settings_open_key = f"monthly_time_settings_open_{month_key}"
    if st.button(
        "⏱ 音楽を再生する時間を変更する",
        use_container_width=True,
        key=f"monthly_change_music_time_{month_key}",
    ):
        opening_time_settings = not bool(st.session_state.get(time_settings_open_key))
        st.session_state[time_settings_open_key] = opening_time_settings
        if opening_time_settings:
            st.session_state[settings_open_key] = False

            # Every time the editor is opened, preload the interval that is actually
            # being used by the current replay rather than any older form value.
            current_playback = get_monthly_playback(review) or {}
            applied = st.session_state.get(f"monthly_replay_applied_{month_key}")
            if isinstance(applied, dict):
                raw_start = applied.get("start_seconds")
                raw_end = applied.get("end_seconds")
            else:
                raw_start = current_playback.get("start_seconds")
                raw_end = current_playback.get("end_seconds")
            current_start = max(0, int(raw_start if raw_start is not None else 0))
            current_end = int(raw_end if raw_end is not None else current_start + 20)
            if current_end <= current_start:
                current_end = current_start + 20
            st.session_state[f"monthly_time_edit_start_{month_key}"] = current_start
            st.session_state[f"monthly_time_edit_end_{month_key}"] = current_end

    if st.session_state.get(time_settings_open_key):
        render_monthly_time_settings(month_key, review)

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button(
            "🎵 音楽を変更する",
            use_container_width=True,
            key=f"monthly_change_music_{month_key}",
        ):
            st.session_state[settings_open_key] = not bool(st.session_state.get(settings_open_key))
            if st.session_state[settings_open_key]:
                st.session_state[time_settings_open_key] = False

        if st.button(
            "☆ この音楽を保存する",
            use_container_width=True,
            key=f"monthly_save_current_music_{month_key}",
        ):
            try:
                state = _monthly_replay_state(month_key, review)
                current_playback = dict(get_monthly_playback(review) or {})
                current_url = str(st.session_state.get(state["url_key"]) or current_playback.get("youtube_url") or "").strip()
                video_id = parse_youtube_video_id(current_url)
                applied = st.session_state.get(f"monthly_replay_applied_{month_key}")
                if not isinstance(applied, dict):
                    applied = {
                        "start_seconds": int(current_playback.get("start_seconds") or st.session_state.get(state["start_key"]) or 0),
                        "end_seconds": int(current_playback.get("end_seconds") or st.session_state.get(state["end_key"]) or 1),
                    }
                current_playback.update({
                    "youtube_url": current_url,
                    "video_id": video_id,
                    "title": str(st.session_state.get(state["title_key"]) or current_playback.get("title") or "").strip(),
                    "start_seconds": max(0, int(applied.get("start_seconds") or 0)),
                    "end_seconds": int(applied.get("end_seconds") or 1),
                    "reason": str(st.session_state.get(state["reason_key"]) or current_playback.get("reason") or "").strip(),
                    "confidence": str(st.session_state.get(state["confidence_key"]) or current_playback.get("confidence") or "").strip(),
                })
                saved_item = save_music_to_library(current_playback)
                st.success(f"『{saved_item.get('title') or 'この音楽'}』を保存しました。")
            except Exception as exc:
                st.error("この音楽を保存できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    with action_cols[1]:
        comments_open = bool(st.session_state.get(comments_open_key))
        comments_label = "AIのコメントを閉じる" if comments_open else "✨ AIのコメントを見る"
        with st.container(key="monthly_ai_comments_action"):
            if st.button(
                comments_label,
                use_container_width=True,
                key=f"monthly_toggle_ai_comments_{month_key}",
            ):
                st.session_state[comments_open_key] = not comments_open
                st.rerun()

    if st.session_state.get(settings_open_key):
        render_monthly_music_settings(month_key, bundle, review, expanded=True)

    if st.session_state.get(comments_open_key):
        # Upgrade legacy saved summaries only when the user asks to see AI comments.
        if int(review.get("_insight_version") or 0) < 2:
            try:
                with st.spinner("本人の言葉から、短い気づきを作り直しています…"):
                    refreshed = make_monthly_review(month_key, bundle)
                    previous_playback = get_monthly_playback(review)
                    if previous_playback:
                        refreshed["_playback"] = previous_playback
                    save_monthly_review(month_key, refreshed)
                st.session_state[session_key] = refreshed
                st.rerun()
            except Exception as exc:
                st.error("AIの気づきを更新できませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))
        render_monthly_ai_comments(review)
        if st.button(
            "この期間をもう一度まとめる",
            use_container_width=True,
            key=f"monthly_regenerate_with_music_{month_key}",
        ):
            try:
                previous_playback = get_monthly_playback(review)
                with st.spinner("この期間の言葉をつないでいます…"):
                    refreshed = make_monthly_review(month_key, bundle)
                    if previous_playback:
                        refreshed["_playback"] = previous_playback
                    save_monthly_review(month_key, refreshed)
                st.session_state[session_key] = refreshed
                st.rerun()
            except Exception as exc:
                st.error("期間の振り返りを作れませんでした。")
                with st.expander("保護者向け詳細"):
                    st.code(str(exc))

    # The replay is generated from this period's photos plus the attached music
    # settings; there is no separate video file. Deleting the replay therefore
    # removes only this period's music/replay association. Diaries, photos, AI
    # comments, and the member's saved music library are kept.
    delete_video_confirm_key = f"monthly_delete_video_confirm_{month_key}"
    st.divider()
    with st.container(key="monthly_delete_video_area"):
        if st.session_state.get(delete_video_confirm_key):
            st.warning("この期間の振り返り動画を削除します。写真・日記・AIコメント・保存済み音楽は削除されません。")
            delete_col, cancel_col = st.columns([1.25, 1])
            with delete_col:
                with st.container(key="monthly_delete_video_confirm_action"):
                    if st.button(
                        "削除する",
                        use_container_width=True,
                        key=f"monthly_delete_video_confirm_button_{month_key}",
                    ):
                        try:
                            state = _monthly_replay_state(month_key, review)
                            save_monthly_playback(month_key, review, {})
                            for state_key in (
                                state["url_key"],
                                state["start_key"],
                                state["end_key"],
                                state["reason_key"],
                                state["confidence_key"],
                                state["title_key"],
                                f"monthly_replay_applied_{month_key}",
                                f"monthly_music_settings_open_{month_key}",
                                f"monthly_time_settings_open_{month_key}",
                                delete_video_confirm_key,
                            ):
                                st.session_state.pop(state_key, None)
                            st.session_state["_monthly_video_deleted_notice"] = "この期間の振り返り動画を削除しました。"
                            st.rerun()
                        except Exception as exc:
                            st.error("振り返り動画を削除できませんでした。")
                            with st.expander("保護者向け詳細"):
                                st.code(str(exc))
            with cancel_col:
                if st.button(
                    "キャンセル",
                    use_container_width=True,
                    key=f"monthly_delete_video_cancel_{month_key}",
                ):
                    st.session_state.pop(delete_video_confirm_key, None)
                    st.rerun()
        else:
            with st.container(key="monthly_delete_video_action"):
                if st.button(
                    "🗑 この振り返り動画を削除する",
                    use_container_width=True,
                    key=f"monthly_delete_video_{month_key}",
                ):
                    st.session_state[delete_video_confirm_key] = True
                    st.rerun()


# ============================================================
# Page: Review / Settings
# ============================================================
def page_review():
    period_label = "🗓 期間の振り返り"
    history_label = "📚 これまでの日記"
    current_view = st.session_state.get("review_view_selector")
    if current_view == "🔍 今月の発見":
        current_view = period_label
        st.session_state["review_view_selector"] = current_view
    if current_view not in {period_label, history_label}:
        current_view = None

    page_top(
        "🔍 振り返り",
        "見たい振り返りを選んでください。期間のまとめと、1日ごとの日記を分けて見られます。",
    )
    st.markdown(
        """
        <style>
          .st-key-review_period_choice,
          .st-key-review_history_choice {
            border: 1px solid rgba(128,128,128,.18);
            border-radius: 18px;
            padding: .58rem .68rem .48rem;
            margin: .18rem 0 .62rem;
            background: rgba(255,255,255,.72);
          }
          .st-key-review_period_choice div.stButton > button,
          .st-key-review_history_choice div.stButton > button {
            min-height: 3.2rem;
            font-size: 1.05rem;
            font-weight: 800;
            border-radius: 14px;
          }
          .st-key-review_period_choice [data-testid="stCaptionContainer"],
          .st-key-review_history_choice [data-testid="stCaptionContainer"] {
            margin-top: -.18rem;
            padding: 0 .18rem .06rem;
          }
          .st-key-review_back_menu_bottom {
            margin-top: .34rem;
            margin-bottom: .10rem;
          }
          .st-key-review_back_menu_bottom div.stButton > button {
            min-height: 3.05rem;
            border: 1.9px solid rgba(218,126,20,.90) !important;
            border-radius: 14px !important;
            background: linear-gradient(155deg, rgba(255,241,202,.99), rgba(255,218,169,.97)) !important;
            color: #633a05 !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 18px rgba(218,126,20,.14), 0 0 0 2px rgba(255,255,255,.34) inset !important;
          }
          .st-key-review_back_menu_bottom div.stButton > button:hover {
            background: linear-gradient(155deg, rgba(255,235,187,1), rgba(255,207,142,.99)) !important;
            border-color: rgba(197,105,10,.98) !important;
          }
          .st-key-monthly_delete_video_action {
            margin-top: .24rem;
            margin-bottom: .12rem;
          }
          .st-key-monthly_delete_video_action div.stButton > button,
          .st-key-monthly_delete_video_confirm_action div.stButton > button {
            min-height: 3.0rem;
            border: 1.8px solid rgba(199,62,62,.82) !important;
            border-radius: 14px !important;
            background: linear-gradient(155deg, rgba(255,238,238,.99), rgba(255,218,218,.97)) !important;
            color: #8b1f1f !important;
            font-weight: 800 !important;
            box-shadow: 0 7px 16px rgba(180,54,54,.10), 0 0 0 2px rgba(255,255,255,.30) inset !important;
          }
          .st-key-monthly_delete_video_action div.stButton > button:hover,
          .st-key-monthly_delete_video_confirm_action div.stButton > button:hover {
            background: linear-gradient(155deg, rgba(255,226,226,1), rgba(255,202,202,.99)) !important;
            border-color: rgba(177,43,43,.96) !important;
          }
          .st-key-monthly_ai_comments_action div.stButton > button {
            min-height: 3.0rem;
            border: 1.9px solid rgba(91,91,214,.82) !important;
            border-radius: 14px !important;
            background: linear-gradient(155deg, rgba(235,238,255,.99), rgba(215,224,255,.98)) !important;
            color: #303785 !important;
            font-weight: 850 !important;
            box-shadow: 0 8px 20px rgba(83,91,205,.16), 0 0 0 2px rgba(255,255,255,.38) inset !important;
          }
          .st-key-monthly_ai_comments_action div.stButton > button:hover {
            background: linear-gradient(155deg, rgba(225,230,255,1), rgba(198,211,255,.99)) !important;
            border-color: rgba(73,73,191,.96) !important;
            transform: translateY(-1px);
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 見たい振り返り")
    with st.container(key="review_period_choice"):
        if st.button(
            period_label,
            type="primary" if current_view == period_label else "secondary",
            use_container_width=True,
            key="review_choose_period",
        ):
            st.session_state["review_view_selector"] = period_label
            st.rerun()
        st.caption("写真と音楽の振り返りムービーや、AIからの短い気づきを見る")

    with st.container(key="review_history_choice"):
        if st.button(
            history_label,
            type="primary" if current_view == history_label else "secondary",
            use_container_width=True,
            key="review_choose_history",
        ):
            st.session_state["review_view_selector"] = history_label
            st.rerun()
        st.caption("これまで作った日記を、1日ごとに読み返す")

    if current_view == period_label:
        mark_current_month_review_seen()
        st.divider()
        page_monthly(embedded=True)
    elif current_view == history_label:
        st.divider()
        page_history(embedded=True)
    else:
        st.caption("上のどちらかを押すと内容が表示されます。")

    # Keep a clear two-step exit at the very bottom of either review detail:
    # first return to the review chooser, then the shared Home button below it.
    if current_view in {period_label, history_label}:
        with st.container(key="review_back_menu_bottom"):
            if st.button(
                "↩ 振り返り（たまに）に戻る",
                use_container_width=True,
                key="review_back_to_menu_bottom",
            ):
                st.session_state.pop("review_view_selector", None)
                st.rerun()



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
    st.markdown("#### 動画の保存容量")
    quota_bytes = video_storage_quota_bytes()
    st.caption(f"現在の設定値：VIDEO_STORAGE_QUOTA_MB = {VIDEO_STORAGE_QUOTA_MB}")
    if quota_bytes > 0:
        try:
            usage_bytes = current_video_storage_usage_bytes()
            remaining_bytes = max(0, quota_bytes - usage_bytes)
            st.write(
                f"この個人アカウント：**{format_storage_size(usage_bytes)} / {format_storage_size(quota_bytes)}**"
            )
            st.caption(
                f"残り：{format_storage_size(remaining_bytes)}。動画撮影を始める前に、"
                f"15秒の高画質録画1本分として {format_storage_size(VIDEO_MAX_BYTES)} の空きがあるか確認します。"
                "AIセレクションの静止画・候補ZIPはこの動画容量には含めません。"
                "軽い手振れ補正版を作成できた場合、その補正版は動画容量に含まれます。"
            )
            if remaining_bytes < VIDEO_MAX_BYTES:
                st.warning("15秒録画と保存処理用バッファの空きがないため、現在は動画撮影を開始できません。")
            st.progress(min(1.0, usage_bytes / quota_bytes) if quota_bytes else 0.0)
        except Exception as exc:
            st.caption("動画容量を確認できませんでした。")
            with st.expander("保護者向け詳細"):
                st.code(str(exc))
    else:
        st.caption(
            "1人あたりの動画総容量はまだ未設定です。Streamlit Secrets の "
            "VIDEO_STORAGE_QUOTA_MB に上限MBを設定すると自動で制限します。"
        )

    st.divider()
    st.markdown("#### カメラについて")
    st.write(
        "『カメラで撮る』画面では、ブラウザのライブカメラを直接開いて撮影します。"
        "初回だけ、このサイトへのカメラ使用を『許可』してください。"
    )
    st.caption(
        "動画は最大15秒です。録画を止めると確認画面を挟まず元動画を保管庫へ自動保存します。"
        "『いい瞬間』は保存済みの元動画を0.1秒間隔で元解像度のまま1回だけ切り出し、AI用には別の軽量コピーを使います。"
        "利用者が見る最大9枚は元動画由来の高画質フレームのみで、低解像度候補へは切り替えません。"
        "初回はカメラとは別に位置情報の許可も求められます。位置情報がオフ・拒否・取得不能の場合は、"
        "ホームの地名表示（未登録なら『地名：登録なし（自動取得）』）を押して入力した内容を写真の場所として使います。"
    )

    st.divider()
    st.markdown("#### プロジェクトの考え方")
    st.caption("写真の枚数や『便利・不便を見つけること』を課題にはしません。本人が気になったものを残し、あとから本人の言葉で振り返ります。")
    st.caption(f"アプリビルド：{APP_BUILD}")

# ============================================================
# Main UI
# ============================================================
verify_setup()
require_family_pin()
init_state()
# v133: unfinished videos are processed automatically in the normal Streamlit
# execution, not in a detached long-lived thread. No viewer/button action is
# required. Process one saved video, then rerun so another queued video can follow.
with st.spinner("保存済み動画の『いい瞬間』を自動処理しています…"):
    _video_auto_processed_v140 = resume_member_video_background_jobs()
if _video_auto_processed_v140:
    try:
        _home_video_counts_cached.clear()
    except Exception:
        pass
    st.rerun()
# v140 does not use browser-side low-resolution candidate recovery. If native
# extraction from the saved original is unavailable, the job ends as an explicit
# error instead of silently substituting blurry frames.
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
elif page == "videos":
    page_videos()
elif page == "moments":
    page_moments()
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

# Every non-Home page gets the same hierarchy Back button followed by a direct
# Home button. This is based on the app's fixed folder structure, not visit order.
if page in {"camera", "videos", "moments", "diary", "review", "settings"}:
    render_global_bottom_navigation(page)
