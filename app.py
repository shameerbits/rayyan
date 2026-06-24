import streamlit as st
import random
import datetime
import json
import re
import importlib
from PIL import Image
import os
import shutil

import dashboard_page


DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "app_state.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
STATE_SCHEMA_VERSION = 1
LOAD_ERROR_SESSION_KEY = "_persistence_load_error"
MAX_BACKUP_FILES = 25
PERSISTED_STATE_KEYS = [
    "xp",
    "streak",
    "last_active_date",
    "last_inactivity_penalty_for_date",
    "history",
    "last_blessing_claim",
    "recent_praise",
    "memorized",
    "revised_dates",
    "nav_section",
    "milestone_claims",
    "milestone_catalog",
    "milestone_version",
    "assigned_surahs",
    "selected_surah",
    "hifdh_selected_surah",
    "murajah_selected_surah",
]

XP_PER_AYAH_LEARNED = 5
XP_PER_AYAH_REVISED = 2
INACTIVITY_DAYS_THRESHOLD = 3
INACTIVITY_XP_PENALTY = 10


def build_persisted_state_payload():
    payload = {"schema_version": STATE_SCHEMA_VERSION}
    for key in PERSISTED_STATE_KEYS:
        if key in st.session_state:
            payload[key] = st.session_state[key]
    return payload


def prune_old_backups():
    if not os.path.isdir(BACKUP_DIR):
        return
    backup_entries = []
    for name in os.listdir(BACKUP_DIR):
        file_path = os.path.join(BACKUP_DIR, name)
        if not os.path.isfile(file_path):
            continue
        try:
            modified_time = os.path.getmtime(file_path)
        except OSError:
            continue
        backup_entries.append((modified_time, file_path))

    if len(backup_entries) <= MAX_BACKUP_FILES:
        return

    backup_entries.sort(key=lambda item: item[0], reverse=True)
    for _, stale_file in backup_entries[MAX_BACKUP_FILES:]:
        try:
            os.remove(stale_file)
        except OSError:
            continue


def save_app_state():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)

        if os.path.exists(STATE_FILE):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            backup_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_file = os.path.join(BACKUP_DIR, f"app_state_{backup_stamp}.json")
            shutil.copy2(STATE_FILE, backup_file)
            prune_old_backups()

        payload = build_persisted_state_payload()
        temp_file = f"{STATE_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.replace(temp_file, STATE_FILE)
    except Exception:
        # Persistence issues should not block the learning flow.
        pass


def load_app_state():
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return
        for key in PERSISTED_STATE_KEYS:
            if key in payload:
                st.session_state[key] = payload[key]
        st.session_state.pop(LOAD_ERROR_SESSION_KEY, None)
    except json.JSONDecodeError:
        st.session_state[LOAD_ERROR_SESSION_KEY] = (
            "Saved progress file is malformed JSON. App started with defaults for this session. "
            "Please fix or remove data/app_state.json."
        )
    except Exception:
        # Corrupt or incompatible state should fall back to defaults.
        return


_native_rerun = st.rerun


def rerun_with_persist(*args, **kwargs):
    save_app_state()
    return _native_rerun(*args, **kwargs)


st.rerun = rerun_with_persist

# Set page config
st.set_page_config(
    page_title="Rayyan's Quran Tracker 🌟",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

if LOAD_ERROR_SESSION_KEY in st.session_state:
    st.warning(st.session_state[LOAD_ERROR_SESSION_KEY])

NAV_ITEMS = [
    "🏠 Dashboard",
    "📖 Memorization & Revision",
    "🏆 Achievements & Rewards",
]

# ===== iPad V2 Layout =====
st.markdown("""
<style>
:root{
    --space-16:16px;
    --space-24:24px;
    --space-32:32px;
}
.block-container{
    max-width:1100px;
    margin:auto;
    padding-top:var(--space-16);
    padding-bottom:3rem;
}
html, body, [class*="css"]{
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",sans-serif;
}

h2 {
    margin-top: 0;
    margin-bottom: var(--space-16);
}

h3 {
    margin-top: 0;
    margin-bottom: var(--space-16);
}

[data-testid="stSidebar"]{
    width:280px !important;
}
.stButton button{
    min-height:52px;
    border-radius:16px;
}
@media (min-width:1400px){
    .block-container{max-width:1400px;}
}
</style>
""", unsafe_allow_html=True)
# ===== End iPad V2 Layout =====

# Soft green, gold, and white custom styles
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #f0fdf4;
    }

    /* Headers styling */
    h1, h2, h3 {
        color: #14532d !important;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
    }

    /* Cards and container divs */
    .custom-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: var(--space-24);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        border: 2px solid #bbf7d0;
        margin-bottom: var(--space-24);
    }

    .page-hero-title {
        text-align: center;
        margin: 0 0 var(--space-16) 0;
    }

    .page-hero-subtitle {
        text-align: center;
        color: #166534;
        font-size: 1.06rem;
        margin: 0 0 var(--space-24) 0;
    }

    .gold-border {
        border-color: #fef08a !important;
        background-color: #fffbeb !important;
    }

    /* Custom buttons */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Sidebar styling override */
    [data-testid="stSidebar"] {
        background-color: #dcfce7;
        border-right: 2px solid #bbf7d0;
    }

    /* Compact metric values for selected sidebar stat cards */
    .compact-metric [data-testid="stMetricValue"],
    .compact-metric [data-testid="stMetricValue"] > div,
    .compact-metric [data-testid="stMetricValue"] p {
        font-size: clamp(0.86rem, 1.35vw, 1.2rem) !important;
        line-height: 1.2 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        word-break: break-word !important;
    }

    /* Custom badges */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .badge-gold {
        background-color: #fef08a;
        color: #854d0e;
    }
    .badge-green {
        background-color: #dcfce7;
        color: #166534;
    }

    /* Progress bar custom color styling */
    .stProgress > div > div > div > div {
        background-color: #22c55e;
    }

    /* Ayah selection checkboxes: render as fixed-size selectable squares with centered numbers */
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"],
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] {
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
        width: 100%;
        min-height: 48px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label {
        margin: 0 !important;
        width: 44px;
        height: 44px;
        border-radius: 8px;
        border: 1px solid #cbd5e1;
        background: #f8fafc;
        display: inline-grid !important;
        place-items: center;
        cursor: pointer;
        padding: 0 !important;
        transition: border-color 0.18s ease, background-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label > div:first-child,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label > div:first-child {
        display: none !important;
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label p,
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label span,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label p,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label span {
        margin: 0 !important;
        font-size: 0.88rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        color: #1f2937 !important;
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label:hover,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label:hover {
        border-color: #16a34a;
        box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.14);
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label:has(input:checked),
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label:has(input:checked) {
        border-color: #15803d;
        background: #dcfce7;
        box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.2);
    }
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label:has(input:checked) p,
    div[class*="st-key-hifdh_"] div[data-testid="stCheckbox"] label:has(input:checked) span,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label:has(input:checked) p,
    div[class*="st-key-murajah_"] div[data-testid="stCheckbox"] label:has(input:checked) span {
        color: #166534 !important;
    }

    /* Modern Surah cards */
    .surah-card {
        background: linear-gradient(160deg, #ffffff 0%, #f7fff9 100%);
        border: 2px solid #dcfce7;
        border-radius: 18px;
        padding: 14px;
        margin-bottom: 10px;
        min-height: 250px;
        box-shadow: 0 10px 20px rgba(20, 83, 45, 0.10);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }

    .surah-card:hover {
        transform: translateY(-4px);
        border-color: #86efac;
        box-shadow: 0 16px 28px rgba(20, 83, 45, 0.14);
    }

    .surah-card-title {
        margin: 0 0 8px 0;
        color: #14532d;
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.3;
    }

    .surah-status-badge {
        display: inline-block;
        margin-bottom: 8px;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.02em;
    }

    .status-complete {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #22c55e;
    }

    .status-inprogress {
        background-color: #dbeafe;
        color: #1d4ed8;
        border: 1px solid #60a5fa;
    }

    .status-revision {
        background-color: #ffedd5;
        color: #c2410c;
        border: 1px solid #fb923c;
    }

    .status-notstarted {
        background-color: #f3f4f6;
        color: #4b5563;
        border: 1px solid #d1d5db;
    }

    .surah-meta-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #166534;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 4px;
    }

    .surah-progress-track {
        height: 9px;
        width: 100%;
        background-color: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
    }

    .surah-progress-fill-mem {
        height: 100%;
        background: linear-gradient(90deg, #34d399, #22c55e);
    }

    .surah-progress-fill-rev {
        height: 100%;
        background: linear-gradient(90deg, #93c5fd, #3b82f6);
    }

    .surah-footer {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px dashed #bbf7d0;
        color: #14532d;
        font-size: 0.78rem;
        font-weight: 700;
    }

    div[class*="st-key-shared_tile_"] div[data-testid="stButton"] > button {
        border-radius: 12px;
        min-height: 40px;
        font-weight: 700;
    }

    /* Continue learning section */
    .continue-learning-card {
        background: linear-gradient(140deg, #ffffff 0%, #effcf5 52%, #fffbeb 100%);
        border: 2px solid #bbf7d0;
        border-radius: 20px;
        padding: 18px;
        margin: 6px 0 18px 0;
        box-shadow: 0 12px 22px rgba(21, 128, 61, 0.10);
    }

    .continue-title {
        margin: 0 0 3px 0;
        color: #14532d;
        font-size: 1.1rem;
        font-weight: 800;
    }

    .continue-subtitle {
        margin: 0 0 12px 0;
        color: #166534;
        font-size: 0.88rem;
        font-weight: 600;
    }

    .continue-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
    }

    .continue-item {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 12px;
        padding: 10px;
        min-height: 72px;
    }

    .continue-label {
        color: #166534;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 3px;
    }

    .continue-value {
        color: #14532d;
        font-size: 0.95rem;
        font-weight: 800;
        line-height: 1.3;
    }

    /* Journey to Jannah road scene */
    .journey-wrapper {
        border: 2px solid #cfe6ff;
        border-radius: 24px;
        margin-bottom: 22px;
        overflow: hidden;
        background: linear-gradient(180deg, #dff4ff 0%, #eef9ff 46%, #f7ffe9 100%);
        box-shadow: 0 18px 34px rgba(18, 61, 102, 0.16);
    }

    .jannah-sky {
        position: relative;
        min-height: 360px;
        padding: 10px 12px 18px 12px;
        overflow: hidden;
        background:
            radial-gradient(circle at 16% 14%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 36%),
            radial-gradient(circle at 82% 18%, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0) 30%),
            linear-gradient(180deg, #b8e6ff 0%, #d8efff 40%, #f2f9ff 100%);
    }

    .jannah-star {
        position: absolute;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 0 8px rgba(255, 255, 255, 0.75);
        animation: twinkle 3.2s ease-in-out infinite;
        z-index: 2;
    }

    .star-1 { top: 12%; left: 12%; }
    .star-2 { top: 9%; left: 31%; animation-delay: 0.8s; }
    .star-3 { top: 13%; left: 58%; animation-delay: 1.5s; }
    .star-4 { top: 10%; left: 75%; animation-delay: 2.1s; }
    .star-5 { top: 17%; left: 89%; animation-delay: 0.3s; }

    .jannah-cloud {
        position: absolute;
        background: rgba(255, 255, 255, 0.94);
        border-radius: 999px;
        filter: drop-shadow(0 6px 8px rgba(44, 97, 152, 0.08));
        z-index: 3;
        animation: cloud-drift linear infinite;
    }

    .jannah-cloud::before,
    .jannah-cloud::after {
        content: "";
        position: absolute;
        background: rgba(255, 255, 255, 0.94);
        border-radius: 999px;
    }

    .jannah-cloud.c1 {
        width: 90px;
        height: 28px;
        top: 15%;
        left: -110px;
        animation-duration: 30s;
    }

    .jannah-cloud.c1::before {
        width: 30px;
        height: 30px;
        top: -14px;
        left: 13px;
    }

    .jannah-cloud.c1::after {
        width: 36px;
        height: 36px;
        top: -18px;
        left: 44px;
    }

    .jannah-cloud.c2 {
        width: 120px;
        height: 34px;
        top: 24%;
        left: -160px;
        animation-duration: 42s;
        animation-delay: -12s;
    }

    .jannah-cloud.c2::before {
        width: 40px;
        height: 40px;
        top: -15px;
        left: 20px;
    }

    .jannah-cloud.c2::after {
        width: 45px;
        height: 45px;
        top: -22px;
        left: 62px;
    }

    .jannah-cloud.c3 {
        width: 75px;
        height: 24px;
        top: 10%;
        left: -90px;
        animation-duration: 26s;
        animation-delay: -6s;
    }

    .jannah-cloud.c3::before {
        width: 28px;
        height: 28px;
        top: -11px;
        left: 9px;
    }

    .jannah-cloud.c3::after {
        width: 32px;
        height: 32px;
        top: -16px;
        left: 36px;
    }

    .jannah-mountain {
        position: absolute;
        bottom: 24%;
        width: 42%;
        height: 36%;
        background: linear-gradient(165deg, #8cb4d9 0%, #6d94bf 100%);
        clip-path: polygon(0 100%, 50% 0, 100% 100%);
        opacity: 0.8;
        z-index: 1;
    }

    .jannah-mountain.m1 { left: -4%; }
    .jannah-mountain.m2 { left: 24%; opacity: 0.65; }
    .jannah-mountain.m3 { right: -6%; width: 46%; opacity: 0.78; }

    .jannah-masjid {
        position: absolute;
        right: 10%;
        bottom: 27%;
        width: 95px;
        height: 55px;
        background: linear-gradient(180deg, #4d698b 0%, #3e5672 100%);
        border-radius: 8px 8px 0 0;
        opacity: 0.58;
        z-index: 4;
    }

    .jannah-masjid::before {
        content: "";
        position: absolute;
        top: -26px;
        left: 26px;
        width: 42px;
        height: 30px;
        border-radius: 50% 50% 0 0;
        background: #3f5875;
    }

    .jannah-masjid::after {
        content: "";
        position: absolute;
        right: -9px;
        top: -40px;
        width: 10px;
        height: 68px;
        background: #3c5370;
        border-radius: 3px;
    }

    .jannah-tree {
        position: absolute;
        bottom: 28%;
        width: 12px;
        height: 38px;
        background: #4c6944;
        border-radius: 4px;
        z-index: 5;
    }

    .jannah-tree::before {
        content: "";
        position: absolute;
        left: -14px;
        top: -24px;
        width: 40px;
        height: 28px;
        border-radius: 60% 60% 50% 50%;
        background: #5b8754;
    }

    .jannah-tree.t1 { left: 13%; }
    .jannah-tree.t2 { left: 31%; }
    .jannah-tree.t3 { left: 67%; }
    .jannah-tree.t4 { left: 84%; }

    .jannah-road-path {
        position: absolute;
        left: 5%;
        right: 5%;
        bottom: 10%;
        height: 34%;
        border-radius: 220px 220px 30px 30px;
        background:
            radial-gradient(circle at 16% 56%, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0) 28%),
            linear-gradient(175deg, #efce93 0%, #d7b078 58%, #bf945d 100%);
        border: 2px solid rgba(142, 103, 58, 0.46);
        z-index: 6;
    }

    .jannah-road-path::before {
        content: "";
        position: absolute;
        left: 8%;
        right: 8%;
        top: 50%;
        height: 3px;
        background: repeating-linear-gradient(
            90deg,
            rgba(255, 248, 228, 0.85) 0,
            rgba(255, 248, 228, 0.85) 14px,
            rgba(255, 248, 228, 0) 14px,
            rgba(255, 248, 228, 0) 24px
        );
        transform: translateY(-50%);
    }

    .road-milestone {
        position: absolute;
        transform: translate(-50%, -50%);
        z-index: 8;
        text-align: center;
        min-width: 72px;
        max-width: 114px;
        padding: 6px 7px;
        border-radius: 12px;
        border: 2px solid #bfd7f8;
        background: rgba(255, 255, 255, 0.92);
        box-shadow: 0 8px 14px rgba(32, 76, 121, 0.15);
    }

    .road-milestone::after {
        content: "";
        position: absolute;
        left: 50%;
        bottom: -10px;
        width: 2px;
        height: 10px;
        background: #7095bc;
        transform: translateX(-50%);
    }

    .road-milestone-title {
        margin: 0;
        color: #173861;
        font-size: 0.66rem;
        font-weight: 800;
        line-height: 1.15;
    }

    .road-milestone-meta {
        margin: 3px 0 0 0;
        color: #295885;
        font-size: 0.62rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .road-milestone.state-claimed {
        border-color: #7cc8ff;
        background: linear-gradient(170deg, #ecf8ff 0%, #def0ff 100%);
    }

    .road-milestone.state-ready {
        border-color: #ffc979;
        background: linear-gradient(170deg, #fff6df 0%, #ffecc8 100%);
        animation: milestone-pulse 2.1s ease-in-out infinite;
    }

    .road-milestone.state-progress {
        border-color: #cad6e6;
        background: rgba(255, 255, 255, 0.88);
    }

    .road-start,
    .road-finish {
        position: absolute;
        z-index: 9;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.69rem;
        font-weight: 800;
        line-height: 1;
        box-shadow: 0 8px 14px rgba(31, 71, 112, 0.16);
    }

    .road-start {
        left: 5%;
        bottom: 29%;
        background: linear-gradient(180deg, #ecf9ff 0%, #dff3ff 100%);
        border: 1px solid #95d2ff;
        color: #1b5f8c;
    }

    .road-finish {
        right: 5%;
        bottom: 29%;
        background: linear-gradient(180deg, #fff7e1 0%, #ffecc3 100%);
        border: 1px solid #ffd58b;
        color: #7f5722;
    }

    .journey-character {
        position: absolute;
        left: var(--target-x, 12%);
        bottom: 20%;
        transform: translateX(-50%);
        z-index: 10;
        text-align: center;
        animation: character-arrive 2.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    }

    .character-icon {
        display: block;
        font-size: 1.85rem;
        line-height: 1;
        filter: drop-shadow(0 6px 8px rgba(17, 61, 104, 0.28));
    }

    .character-label {
        display: inline-block;
        margin-top: 3px;
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid #b8d8ff;
        color: #1a4a78;
        font-size: 0.62rem;
        font-weight: 800;
    }

    .journey-character.motion-run .character-icon {
        animation: run-bounce 0.45s ease-in-out infinite;
    }

    .journey-character.motion-cycle .character-icon {
        animation: cycle-wobble 0.85s linear infinite;
    }

    .journey-character.motion-camel .character-icon {
        animation: camel-sway 1.1s ease-in-out infinite;
    }

    .journey-legend {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
        margin-top: 10px;
    }

    .journey-legend-item {
        border-radius: 12px;
        border: 1px solid #cfe0f5;
        background: rgba(255, 255, 255, 0.9);
        padding: 7px 8px;
        color: #2a5a87;
        font-size: 0.72rem;
        font-weight: 700;
        text-align: center;
    }

    @keyframes cloud-drift {
        0% { transform: translateX(0); }
        100% { transform: translateX(calc(100vw + 220px)); }
    }

    @keyframes twinkle {
        0%, 100% { opacity: 0.5; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.35); }
    }

    @keyframes character-arrive {
        0% { left: 4%; transform: translateX(-50%) scale(0.9); }
        70% { transform: translateX(-50%) scale(1.04); }
        100% { left: var(--target-x, 12%); transform: translateX(-50%) scale(1); }
    }

    @keyframes run-bounce {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-3px); }
    }

    @keyframes cycle-wobble {
        0%, 100% { transform: rotate(-1.6deg); }
        50% { transform: rotate(1.6deg); }
    }

    @keyframes camel-sway {
        0%, 100% { transform: translateY(0) rotate(-1deg); }
        50% { transform: translateY(-2px) rotate(1deg); }
    }

    @keyframes milestone-pulse {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.04); }
    }

    /* Hero + statistics reusable dashboard styles */
    .hero-dashboard {
        background: linear-gradient(135deg, #dff7e9 0%, #ffffff 52%, #fff8e2 100%);
        border: 2px solid #bbf7d0;
        border-radius: 22px;
        padding: 14px;
        margin-bottom: 8px;
        box-shadow: 0 14px 28px rgba(20, 83, 45, 0.10);
    }

    .hero-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-bottom: 8px;
    }

    .hero-title {
        margin: 0;
        color: #14532d;
        font-size: 1.34rem;
        font-weight: 800;
        letter-spacing: 0.01em;
    }

    .hero-subtitle {
        margin: 4px 0 0 0;
        color: #166534;
        font-size: 0.84rem;
        font-weight: 600;
    }

    .hero-chip {
        background: #ffffff;
        border: 2px solid #fde68a;
        border-radius: 999px;
        padding: 6px 11px;
        color: #92400e;
        font-weight: 800;
        font-size: 0.76rem;
        white-space: nowrap;
        box-shadow: 0 5px 12px rgba(146, 64, 14, 0.12);
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 7px;
    }

    .metric-card {
        background: #ffffff;
        border: 2px solid #dcfce7;
        border-radius: 15px;
        padding: 8px 6px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(15, 118, 110, 0.08);
    }

    .metric-label {
        color: #166534;
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
    }

    .metric-value {
        color: #14532d;
        font-size: 1.02rem;
        font-weight: 800;
        line-height: 1.2;
    }

    /* Achievement and gamification styles */
    .achievement-header {
        margin: 0 0 6px 0;
        color: #14532d;
        font-size: 1.02rem;
        font-weight: 800;
    }

    .achievement-subtitle {
        margin: 0 0 8px 0;
        color: #166534;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .achievement-card {
        background: #ffffff;
        border: 2px solid #dcfce7;
        border-radius: 14px;
        padding: 9px;
        min-height: 108px;
        box-shadow: 0 7px 15px rgba(22, 101, 52, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .achievement-card.locked {
        border-style: dashed;
        border-color: #d1d5db;
        background: #f9fafb;
        opacity: 0.85;
    }

    .achievement-title {
        color: #14532d;
        font-size: 0.84rem;
        font-weight: 800;
        line-height: 1.25;
        margin-bottom: 2px;
    }

    .achievement-meta {
        color: #166534;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .dashboard-mini-card {
        background: #ffffff;
        border: 2px solid #dcfce7;
        border-radius: 12px;
        padding: 10px;
        min-height: 118px;
        box-shadow: 0 6px 14px rgba(22, 101, 52, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 6px;
    }

    .dashboard-mini-card.ready {
        border-color: #facc15;
        background: #fffbeb;
    }

    .dashboard-mini-card.claimed {
        border-color: #22c55e;
        background: #f0fdf4;
    }

    .dashboard-mini-card.upcoming {
        border-color: #86efac;
        background: #f7fff8;
    }

    .dashboard-mini-badge {
        color: #854d0e;
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin: 0 0 4px 0;
    }

    .dashboard-mini-title {
        color: #14532d;
        font-size: 0.82rem;
        font-weight: 800;
        line-height: 1.25;
        margin: 0 0 4px 0;
        overflow-wrap: anywhere;
    }

    .dashboard-mini-meta {
        color: #166534;
        font-size: 0.72rem;
        font-weight: 700;
        line-height: 1.25;
        margin: 0;
        overflow-wrap: anywhere;
    }

    .milestone-grid-card {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 12px;
        padding: 10px;
        min-height: 150px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        overflow: hidden;
    }

    .milestone-grid-card.is-ready {
        border: 2px solid #facc15;
        background: #fffbeb;
    }

    .milestone-grid-card.is-claimed {
        border: 2px solid #22c55e;
        background: #f0fdf4;
    }

    .milestone-card-title {
        color: #14532d;
        font-size: clamp(0.72rem, 0.66rem + 0.18vw, 0.86rem);
        font-weight: 800;
        line-height: 1.2;
        margin: 0 0 4px 0;
        overflow-wrap: anywhere;
        word-break: break-word;
        white-space: normal;
        text-wrap: balance;
    }

    .milestone-card-row {
        color: #166534;
        font-size: clamp(0.64rem, 0.6rem + 0.15vw, 0.72rem);
        font-weight: 700;
        line-height: 1.2;
        margin: 2px 0;
        overflow-wrap: anywhere;
        word-break: break-word;
        white-space: normal;
    }

    .fit-text-small {
        font-size: 0.66rem !important;
    }

    .fit-text-xsmall {
        font-size: 0.61rem !important;
    }

    .level-chip {
        display: inline-block;
        margin-left: 8px;
        border-radius: 999px;
        padding: 5px 10px;
        border: 1px solid #fde68a;
        background-color: #fffbeb;
        color: #92400e;
        font-size: 0.76rem;
        font-weight: 800;
    }

    .overall-progress-shell {
        background: linear-gradient(160deg, #ffffff 0%, #f3fff6 58%, #fff9e8 100%);
        border: 2px solid #bbf7d0;
        border-radius: 18px;
        padding: 16px;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .overall-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }

    .overall-card {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 12px;
        padding: 10px;
        min-height: 86px;
    }

    .overall-label {
        color: #166534;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .overall-value {
        color: #14532d;
        font-size: 1.08rem;
        font-weight: 800;
        margin-top: 4px;
    }

    .recent-achievement-item {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-left: 5px solid #22c55e;
        border-radius: 10px;
        padding: 8px;
        margin-bottom: 0;
        color: #14532d;
        font-weight: 700;
        font-size: 0.8rem;
    }

    .recent-achievements-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
    }

    .reward-map-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
        gap: 8px;
    }

    .reward-map-card {
        border-radius: 12px;
        padding: 10px 8px;
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-align: center;
    }

    .reward-map-card.unlocked {
        border: 2px solid #22c55e;
        background-color: #dcfce7;
    }

    .reward-map-card.locked {
        border: 2px dashed #9ca3af;
        background-color: #f3f4f6;
    }

    .reward-map-level {
        color: #1f2937;
        font-weight: 800;
        font-size: 0.78rem;
        line-height: 1.2;
    }

    .reward-map-xp {
        font-size: 0.74rem;
        color: #4b5563;
        margin-top: 3px;
    }

    .reward-map-text {
        font-size: 0.74rem;
        color: #14532d;
        font-weight: 700;
        line-height: 1.2;
        margin-top: 6px;
        overflow-wrap: anywhere;
    }

    .top-nav-caption {
        color: #166534;
        font-size: 0.78rem;
        font-weight: 800;
        margin: 0 0 6px 2px;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }

    .top-nav-row {
        margin-bottom: 6px;
    }

    .top-nav-row:last-child {
        margin-bottom: 0;
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button {
        min-height: 48px;
        border-radius: 14px;
        font-size: 0.84rem;
        font-weight: 800;
        line-height: 1.2;
        white-space: normal;
        overflow-wrap: anywhere;
        border: 2px solid #bbf7d0;
        background: linear-gradient(160deg, #ffffff 0%, #f0fdf4 100%);
        color: #14532d;
        box-shadow: 0 6px 14px rgba(22, 101, 52, 0.10);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 18px rgba(22, 101, 52, 0.14);
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button[kind="primary"] {
        border-color: #22c55e;
        background: linear-gradient(160deg, #dcfce7 0%, #bbf7d0 100%);
        color: #14532d;
    }

    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        min-height: 48px;
        border-radius: 14px;
    }

    div[class*="st-key-mem_tile_"] div[data-testid="stButton"] > button,
    div[class*="st-key-rev_tile_"] div[data-testid="stButton"] > button {
        min-height: 48px;
    }

    @media (max-width: 1200px) {
        .metric-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }

    @media (max-width: 1024px) {
        .block-container {
            padding-top: var(--space-16);
            padding-bottom: var(--space-24);
        }

        .page-hero-title {
            margin-bottom: 12px;
        }

        .page-hero-subtitle {
            font-size: 1rem;
            margin-bottom: var(--space-16);
        }

        .hero-dashboard,
        .continue-learning-card,
        .overall-progress-shell,
        .journey-wrapper,
        .custom-card {
            padding: var(--space-16);
        }

        .metric-label {
            font-size: 0.86rem;
        }

        .metric-value {
            font-size: 1.12rem;
        }

        .surah-card {
            padding: var(--space-16);
            margin-bottom: var(--space-16);
        }

    }

    @media (max-width: 900px) {
        .hero-dashboard {
            padding: 16px;
            border-radius: 18px;
        }

        .hero-topbar {
            flex-direction: column;
            align-items: flex-start;
        }

        .hero-title {
            font-size: 1.12rem;
        }

        .hero-chip {
            font-size: 0.72rem;
            padding: 5px 10px;
        }

        .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 7px;
        }

        .metric-card {
            padding: 8px 6px;
        }

        .metric-value {
            font-size: 0.98rem;
        }

        .recent-achievements-grid {
            grid-template-columns: 1fr;
        }

        .stat-card {
            min-height: 80px;
            padding: 12px 10px;
        }

        .stat-value {
            font-size: 1.15rem;
        }

        .overall-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .continue-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
        }

        .continue-item {
            min-height: 66px;
        }

        .surah-card {
            min-height: 238px;
            padding: 12px;
        }

        .surah-card-title {
            font-size: 0.95rem;
        }
    }

    @media (max-width: 640px) {
        .overall-grid {
            grid-template-columns: 1fr;
        }

        .continue-grid {
            grid-template-columns: 1fr;
        }

        .surah-card {
            min-height: auto;
        }

        div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button {
            min-height: 44px;
            font-size: 0.76rem;
            padding: 8px;
        }
    }

    @media (min-width: 900px) and (max-width: 1366px) and (min-height: 700px) {
        .block-container {
            padding-top: 10px;
            padding-bottom: 10px;
        }

        .hero-dashboard {
            padding: 12px;
        }

        .achievement-card {
            min-height: 78px;
            padding: 8px;
        }
    }

    /* Kid-friendly colorful theme overrides */
    .stApp {
        background:
            radial-gradient(circle at 8% 10%, rgba(255, 216, 152, 0.38), transparent 30%),
            radial-gradient(circle at 90% 18%, rgba(151, 220, 255, 0.34), transparent 26%),
            radial-gradient(circle at 25% 92%, rgba(120, 186, 255, 0.24), transparent 35%),
            linear-gradient(170deg, #fff9f2 0%, #f5fbff 42%, #f7f9ff 100%);
    }

    h1, h2, h3 {
        color: #173861 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8f8ff 0%, #f4fff6 48%, #fff6ec 100%);
        border-right: 2px solid #b8deff;
    }

    .custom-card,
    .hero-dashboard,
    .continue-learning-card,
    .overall-progress-shell,
    .journey-wrapper {
        background: linear-gradient(165deg, #ffffff 0%, #f9fbff 58%, #fffdf6 100%);
        border: 2px solid #cfe6ff;
        box-shadow: 0 14px 30px rgba(23, 56, 97, 0.10);
    }

    .hero-title,
    .continue-title,
    .achievement-header,
    .dashboard-mini-title,
    .milestone-card-title,
    .surah-card-title,
    .overall-value,
    .metric-value {
        color: #1a3f6b;
    }

    .hero-subtitle,
    .continue-subtitle,
    .achievement-subtitle,
    .milestone-card-row,
    .overall-label,
    .metric-label,
    .dashboard-mini-meta,
    .reward-map-text,
    .top-nav-caption,
    .surah-meta-row {
        color: #345f8d;
    }

    .hero-chip,
    .level-chip,
    .badge-gold {
        border: 1px solid #ffd27d;
        background: linear-gradient(180deg, #fff6d9 0%, #ffe9b8 100%);
        color: #88541f;
        box-shadow: 0 6px 14px rgba(255, 174, 68, 0.22);
    }

    .badge-green {
        background: linear-gradient(180deg, #e9f8ff 0%, #d8efff 100%);
        color: #1f5683;
    }

    .metric-card,
    .achievement-card,
    .dashboard-mini-card,
    .overall-card,
    .milestone-grid-card,
    .continue-item,
    .journey-node,
    .reward-map-card {
        border-radius: 14px;
        border: 2px solid #dbeafe;
        background: linear-gradient(160deg, #ffffff 0%, #f9fcff 100%);
    }

    .dashboard-mini-card.ready,
    .milestone-grid-card.is-ready {
        border-color: #ffd27d;
        background: linear-gradient(170deg, #fff8e8 0%, #fff0cf 100%);
    }

    .dashboard-mini-card.claimed,
    .milestone-grid-card.is-claimed,
    .reward-map-card.unlocked,
    .journey-node-complete,
    .journey-finish-complete {
        border-color: #8fd1ff;
        background: linear-gradient(170deg, #ecf8ff 0%, #ddf1ff 100%);
        color: #1f5b8e;
    }

    .dashboard-mini-card.upcoming {
        border-color: #8ec5ff;
        background: linear-gradient(170deg, #eef6ff 0%, #deefff 100%);
    }

    .achievement-card.locked,
    .reward-map-card.locked {
        border-style: dashed;
        border-color: #cfcfd6;
        background: #f6f7fb;
    }

    .recent-achievement-item {
        border-left: 5px solid #ff9f7e;
        color: #1a3f6b;
        background: linear-gradient(180deg, #ffffff 0%, #fff7f2 100%);
    }

    .journey-start {
        background: linear-gradient(180deg, #edfaff 0%, #e1f5ff 100%);
        border: 1px solid #9fd9ff;
        color: #18608c;
    }

    .journey-finish {
        background: linear-gradient(180deg, #fff8e2 0%, #ffefc5 100%);
        border: 1px solid #ffd27d;
        color: #8a591c;
    }

    .journey-line {
        color: #ff9a6f;
    }

    .surah-card {
        background: linear-gradient(170deg, #ffffff 0%, #f3f8ff 64%, #fff8f1 100%);
        border: 2px solid #cfe6ff;
        box-shadow: 0 12px 24px rgba(23, 56, 97, 0.12);
    }

    .surah-card:hover {
        border-color: #86cbff;
        box-shadow: 0 16px 28px rgba(36, 74, 117, 0.16);
    }

    .surah-progress-fill-mem {
        background: linear-gradient(90deg, #ff9e84, #ffbf63);
    }

    .surah-progress-fill-rev {
        background: linear-gradient(90deg, #69c7ff, #5b8cff);
    }

    .surah-footer {
        border-top: 1px dashed #cfe3ff;
        color: #2b5f91;
    }

    .status-complete {
        background-color: #e9f8ff;
        color: #185f8f;
        border-color: #8fd1ff;
    }

    .status-inprogress {
        background-color: #fff2d8;
        color: #7c551f;
        border-color: #ffc779;
    }

    .status-revision {
        background-color: #e8f4ff;
        color: #255a89;
        border-color: #8fc6ff;
    }

    .status-notstarted {
        background-color: #eff1f6;
        color: #5c6480;
        border-color: #cfd5e5;
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button {
        border: 2px solid #c7dcff;
        background: linear-gradient(160deg, #ffffff 0%, #eff7ff 100%);
        color: #1a4777;
        box-shadow: 0 7px 16px rgba(44, 97, 152, 0.12);
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button:hover {
        border-color: #8ec8ff;
        box-shadow: 0 10px 22px rgba(105, 173, 238, 0.22);
    }

    div[class*="st-key-nav_tab_"] div[data-testid="stButton"] > button[kind="primary"] {
        border-color: #7ebfff;
        background: linear-gradient(160deg, #e9f5ff 0%, #d7ecff 100%);
        color: #235887;
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(160deg, #ffffff 0%, #eff7ff 100%);
        border: 2px solid #c8ddff;
        color: #1f4d7e;
        font-weight: 700;
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        border-color: #8ec8ff;
        background: linear-gradient(160deg, #edf7ff 0%, #deefff 100%);
        color: #235887;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #6fc8ff, #5a8cff, #9c76ff);
    }

    @keyframes floatGlow {
        0% { box-shadow: 0 10px 20px rgba(39, 89, 142, 0.10); }
        50% { box-shadow: 0 14px 26px rgba(255, 164, 122, 0.15); }
        100% { box-shadow: 0 10px 20px rgba(39, 89, 142, 0.10); }
    }

    .hero-dashboard,
    .continue-learning-card {
        animation: floatGlow 3.8s ease-in-out infinite;
    }

    /* Journey to Jannah Road dashboard scene */
    .jannah-journey-shell {
        background: linear-gradient(165deg, #ffffff 0%, #f6fbff 48%, #fff9ef 100%);
        border: 2px solid #cfe6ff;
        border-radius: 22px;
        padding: 14px;
        margin-top: 10px;
        box-shadow: 0 16px 30px rgba(23, 56, 97, 0.12);
    }

    .jannah-journey-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 8px;
        flex-wrap: wrap;
    }

    .jannah-journey-title {
        margin: 0;
        color: #173861;
        font-size: 1.12rem;
        font-weight: 800;
    }

    .jannah-journey-subtitle {
        margin: 2px 0 0 0;
        color: #355f8c;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .jannah-journey-chip {
        border-radius: 999px;
        border: 1px solid #ffd27d;
        background: linear-gradient(180deg, #fff8e5 0%, #ffefca 100%);
        color: #84551d;
        font-size: 0.74rem;
        font-weight: 800;
        padding: 5px 10px;
        white-space: nowrap;
    }

    .jannah-journey-scene {
        position: relative;
        height: 430px;
        border-radius: 18px;
        overflow: hidden;
        border: 2px solid #bfdfff;
        background:
            radial-gradient(circle at 18% 8%, rgba(255, 255, 255, 0.85), transparent 28%),
            radial-gradient(circle at 78% 14%, rgba(255, 240, 212, 0.7), transparent 34%),
            linear-gradient(180deg, #cbe9ff 0%, #e7f4ff 46%, #f4f8f0 46.2%, #dbeac7 100%);
    }

    .journey-cloud {
        position: absolute;
        font-size: 2rem;
        filter: drop-shadow(0 3px 3px rgba(0, 0, 0, 0.1));
        opacity: 0.75;
        pointer-events: none;
    }

    .journey-cloud.c1 { top: 16px; left: -60px; animation: cloudDriftA 24s linear infinite; }
    .journey-cloud.c2 { top: 40px; left: -120px; animation: cloudDriftB 30s linear infinite; font-size: 2.3rem; }
    .journey-cloud.c3 { top: 74px; left: -90px; animation: cloudDriftA 36s linear infinite; font-size: 1.8rem; }

    .journey-star {
        position: absolute;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #fff6cf;
        box-shadow: 0 0 9px rgba(255, 250, 200, 0.75);
        animation: starTwinkle 2.4s ease-in-out infinite;
        pointer-events: none;
    }

    .journey-star.s1 { top: 30px; left: 18%; animation-delay: 0s; }
    .journey-star.s2 { top: 64px; left: 32%; animation-delay: 0.8s; }
    .journey-star.s3 { top: 24px; left: 56%; animation-delay: 0.4s; }
    .journey-star.s4 { top: 50px; left: 73%; animation-delay: 1.1s; }
    .journey-star.s5 { top: 20px; left: 88%; animation-delay: 1.6s; }

    .journey-mountain {
        position: absolute;
        bottom: 168px;
        width: 0;
        height: 0;
        border-left: 86px solid transparent;
        border-right: 86px solid transparent;
        border-bottom: 132px solid #8da5bf;
        opacity: 0.6;
        pointer-events: none;
    }

    .journey-mountain.m1 { left: 8%; border-bottom-color: #94abc4; }
    .journey-mountain.m2 { left: 26%; border-left-width: 102px; border-right-width: 102px; border-bottom-width: 150px; border-bottom-color: #7f9ab8; }
    .journey-mountain.m3 { left: 51%; border-bottom-color: #93a8be; }
    .journey-mountain.m4 { left: 72%; border-left-width: 112px; border-right-width: 112px; border-bottom-width: 160px; border-bottom-color: #8199b5; }

    .journey-tree,
    .journey-masjid {
        position: absolute;
        bottom: 126px;
        font-size: 1.25rem;
        filter: drop-shadow(0 4px 2px rgba(0, 0, 0, 0.2));
        pointer-events: none;
    }

    .journey-tree.t1 { left: 12%; }
    .journey-tree.t2 { left: 44%; font-size: 1.4rem; }
    .journey-tree.t3 { left: 85%; }
    .journey-masjid.ms1 { left: 33%; font-size: 1.4rem; opacity: 0.82; }
    .journey-masjid.ms2 { left: 66%; font-size: 1.3rem; opacity: 0.85; }

    .journey-road-band {
        position: absolute;
        left: 4%;
        right: 4%;
        height: 96px;
        border-radius: 999px;
        background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(0, 0, 0, 0.08)),
            linear-gradient(90deg, #93715d 0%, #a8846c 36%, #b18e74 100%);
        border: 2px solid rgba(98, 65, 44, 0.35);
        box-shadow: inset 0 8px 18px rgba(0, 0, 0, 0.18);
    }

    .journey-road-band.upper {
        bottom: 136px;
    }

    .journey-road-band.lower {
        bottom: 26px;
    }

    .journey-road-band::before {
        content: "";
        position: absolute;
        top: 50%;
        left: 5%;
        right: 5%;
        height: 3px;
        transform: translateY(-50%);
        background: repeating-linear-gradient(
            90deg,
            #fff2c3 0 18px,
            transparent 18px 32px
        );
        opacity: 0.9;
    }

    .road-milestone {
        position: absolute;
        transform: translate(-50%, -50%);
        min-width: 150px;
        max-width: 184px;
        text-align: center;
        z-index: 6;
        pointer-events: none;
    }

    .road-dot {
        width: 13px;
        height: 13px;
        border-radius: 50%;
        margin: 0 auto 4px auto;
        border: 2px solid #ffffff;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.18);
    }

    .road-milestone-label {
        border-radius: 10px;
        padding: 5px 7px;
        font-size: 0.6rem;
        font-weight: 700;
        line-height: 1.2;
        background: rgba(255, 255, 255, 0.92);
        color: #1d3f65;
        border: 1px solid #b9d8ff;
        text-align: left;
    }

    .road-milestone-line {
        margin: 2px 0;
        display: block;
        line-height: 1.22;
    }

    .road-milestone-line.line-title {
        font-weight: 800;
        color: #143a60;
    }

    .road-milestone-line.line-reward,
    .road-milestone-line.line-condition {
        font-weight: 700;
        color: #1f4f79;
    }

    .road-milestone.claimed .road-dot {
        background: #34d399;
    }

    .road-milestone.ready .road-dot {
        background: #fbbf24;
    }

    .road-milestone.inprogress .road-dot {
        background: #60a5fa;
    }

    .journey-character {
        position: absolute;
        top: 52%;
        left: 6%;
        transform: translate(-50%, -50%) scaleX(-1);
        font-size: 1.9rem;
        z-index: 8;
        filter: drop-shadow(0 5px 3px rgba(0, 0, 0, 0.22));
        animation: characterMoveIn 2.2s ease-out forwards, characterBounce 0.55s ease-in-out 2.2s infinite alternate;
        pointer-events: none;
    }

    .journey-character-shadow {
        position: absolute;
        top: 58%;
        left: 6%;
        width: 20px;
        height: 7px;
        border-radius: 50%;
        background: rgba(0, 0, 0, 0.24);
        transform: translate(-50%, -50%);
        z-index: 7;
        animation: characterMoveIn 2.2s ease-out forwards, shadowPulse 0.55s ease-in-out 2.2s infinite alternate;
        pointer-events: none;
    }

    .journey-legend {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
        margin-top: 10px;
    }

    .journey-legend-item {
        border-radius: 10px;
        border: 1px solid #d8e8ff;
        background: #ffffff;
        padding: 6px 8px;
        color: #2d5f8d;
        font-size: 0.74rem;
        font-weight: 700;
        text-align: center;
    }

    @keyframes cloudDriftA {
        0% { transform: translateX(0); }
        100% { transform: translateX(125vw); }
    }

    @keyframes cloudDriftB {
        0% { transform: translateX(0); }
        100% { transform: translateX(135vw); }
    }

    @keyframes starTwinkle {
        0%, 100% { opacity: 0.45; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.4); }
    }

    @keyframes characterMoveIn {
        0% {
            left: 6%;
            opacity: 0.2;
        }
        100% {
            left: var(--character-target, 20%);
            opacity: 1;
        }
    }

    @keyframes characterBounce {
        0% { transform: translate(-50%, -50%) scaleX(-1) translateY(0px); }
        100% { transform: translate(-50%, -50%) scaleX(-1) translateY(-4px); }
    }

    @keyframes shadowPulse {
        0% { transform: translate(-50%, -50%) scale(1); opacity: 0.22; }
        100% { transform: translate(-50%, -50%) scale(0.82); opacity: 0.14; }
    }

    @media (max-width: 900px) {
        .jannah-journey-scene {
            height: 520px;
        }

        .journey-legend {
            grid-template-columns: 1fr;
        }

        .road-milestone {
            min-width: 124px;
            max-width: 150px;
        }

        .road-milestone-label {
            font-size: 0.56rem;
        }

        .journey-road-band.upper {
            bottom: 210px;
        }

        .journey-road-band.lower {
            bottom: 56px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Full Quran Surah list (1-114)
SURAH_LIST = [
    "1. Al-Fatihah (The Opening) - 7 Ayahs",
    "2. Al-Baqarah (The Cow) - 286 Ayahs",
    "3. Aal-E-Imran (Family of Imran) - 200 Ayahs",
    "4. An-Nisa (The Women) - 176 Ayahs",
    "5. Al-Ma'idah (The Table Spread) - 120 Ayahs",
    "6. Al-An'am (The Cattle) - 165 Ayahs",
    "7. Al-A'raf (The Heights) - 206 Ayahs",
    "8. Al-Anfal (The Spoils of War) - 75 Ayahs",
    "9. At-Tawbah (The Repentance) - 129 Ayahs",
    "10. Yunus (Jonah) - 109 Ayahs",
    "11. Hud (Hud) - 123 Ayahs",
    "12. Yusuf (Joseph) - 111 Ayahs",
    "13. Ar-Ra'd (The Thunder) - 43 Ayahs",
    "14. Ibrahim (Abraham) - 52 Ayahs",
    "15. Al-Hijr (The Rocky Tract) - 99 Ayahs",
    "16. An-Nahl (The Bee) - 128 Ayahs",
    "17. Al-Isra (The Night Journey) - 111 Ayahs",
    "18. Al-Kahf (The Cave) - 110 Ayahs",
    "19. Maryam (Mary) - 98 Ayahs",
    "20. Ta-Ha (Ta-Ha) - 135 Ayahs",
    "21. Al-Anbiya (The Prophets) - 112 Ayahs",
    "22. Al-Hajj (The Pilgrimage) - 78 Ayahs",
    "23. Al-Mu'minun (The Believers) - 118 Ayahs",
    "24. An-Nur (The Light) - 64 Ayahs",
    "25. Al-Furqan (The Criterion) - 77 Ayahs",
    "26. Ash-Shu'ara (The Poets) - 227 Ayahs",
    "27. An-Naml (The Ant) - 93 Ayahs",
    "28. Al-Qasas (The Stories) - 88 Ayahs",
    "29. Al-Ankabut (The Spider) - 69 Ayahs",
    "30. Ar-Rum (The Romans) - 60 Ayahs",
    "31. Luqman (Luqman) - 34 Ayahs",
    "32. As-Sajdah (The Prostration) - 30 Ayahs",
    "33. Al-Ahzab (The Confederates) - 73 Ayahs",
    "34. Saba (Sheba) - 54 Ayahs",
    "35. Fatir (Originator) - 45 Ayahs",
    "36. Ya-Sin (Ya-Sin) - 83 Ayahs",
    "37. As-Saffat (Those Who Set the Ranks) - 182 Ayahs",
    "38. Sad (Sad) - 88 Ayahs",
    "39. Az-Zumar (The Groups) - 75 Ayahs",
    "40. Ghafir (The Forgiver) - 85 Ayahs",
    "41. Fussilat (Explained in Detail) - 54 Ayahs",
    "42. Ash-Shuraa (The Consultation) - 53 Ayahs",
    "43. Az-Zukhruf (The Gold Adornments) - 89 Ayahs",
    "44. Ad-Dukhan (The Smoke) - 59 Ayahs",
    "45. Al-Jathiyah (The Crouching) - 37 Ayahs",
    "46. Al-Ahqaf (The Wind-Curved Sandhills) - 35 Ayahs",
    "47. Muhammad (Muhammad) - 38 Ayahs",
    "48. Al-Fath (The Victory) - 29 Ayahs",
    "49. Al-Hujurat (The Rooms) - 18 Ayahs",
    "50. Qaf (Qaf) - 45 Ayahs",
    "51. Adh-Dhariyat (The Winnowing Winds) - 60 Ayahs",
    "52. At-Tur (The Mount) - 49 Ayahs",
    "53. An-Najm (The Star) - 62 Ayahs",
    "54. Al-Qamar (The Moon) - 55 Ayahs",
    "55. Ar-Rahman (The Most Merciful) - 78 Ayahs",
    "56. Al-Waqi'ah (The Inevitable) - 96 Ayahs",
    "57. Al-Hadid (The Iron) - 29 Ayahs",
    "58. Al-Mujadila (The Pleading Woman) - 22 Ayahs",
    "59. Al-Hashr (The Exile) - 24 Ayahs",
    "60. Al-Mumtahanah (She That Is to Be Examined) - 13 Ayahs",
    "61. As-Saff (The Ranks) - 14 Ayahs",
    "62. Al-Jumu'ah (The Congregation) - 11 Ayahs",
    "63. Al-Munafiqun (The Hypocrites) - 11 Ayahs",
    "64. At-Taghabun (Mutual Disillusion) - 18 Ayahs",
    "65. At-Talaq (The Divorce) - 12 Ayahs",
    "66. At-Tahrim (The Prohibition) - 12 Ayahs",
    "67. Al-Mulk (The Sovereignty) - 30 Ayahs",
    "68. Al-Qalam (The Pen) - 52 Ayahs",
    "69. Al-Haqqah (The Reality) - 52 Ayahs",
    "70. Al-Ma'arij (The Ascending Stairways) - 44 Ayahs",
    "71. Nuh (Noah) - 28 Ayahs",
    "72. Al-Jinn (The Jinn) - 28 Ayahs",
    "73. Al-Muzzammil (The Enshrouded One) - 20 Ayahs",
    "74. Al-Muddaththir (The Cloaked One) - 56 Ayahs",
    "75. Al-Qiyamah (The Resurrection) - 40 Ayahs",
    "76. Al-Insan (The Human) - 31 Ayahs",
    "77. Al-Mursalat (The Emissaries) - 50 Ayahs",
    "78. An-Naba (The Tidings) - 40 Ayahs",
    "79. An-Naziat (Those Who Drag Forth) - 46 Ayahs",
    "80. Abasa (He Frowned) - 42 Ayahs",
    "81. At-Takwir (The Overthrowing) - 29 Ayahs",
    "82. Al-Infitar (The Cleaving) - 19 Ayahs",
    "83. Al-Mutaffifin (Defrauding) - 36 Ayahs",
    "84. Al-Inshiqaq (The Sundering) - 25 Ayahs",
    "85. Al-Buruj (The Mansions of the Stars) - 22 Ayahs",
    "86. At-Tariq (The Morning Star) - 17 Ayahs",
    "87. Al-A'la (The Most High) - 19 Ayahs",
    "88. Al-Ghashiyah (The Overwhelming) - 26 Ayahs",
    "89. Al-Fajr (The Dawn) - 30 Ayahs",
    "90. Al-Balad (The City) - 20 Ayahs",
    "91. Ash-Shams (The Sun) - 15 Ayahs",
    "92. Al-Layl (The Night) - 21 Ayahs",
    "93. Ad-Duha (The Morning Hours) - 11 Ayahs",
    "94. Ash-Sharh / Al-Inshirah (The Solace) - 8 Ayahs",
    "95. At-Tin (The Fig) - 8 Ayahs",
    "96. Al-Alaq (The Clot) - 19 Ayahs",
    "97. Al-Qadr (The Power) - 5 Ayahs",
    "98. Al-Bayyinah (The Clear Proof) - 8 Ayahs",
    "99. Az-Zalzalah (The Earthquake) - 8 Ayahs",
    "100. Al-Adiyat (The Courser) - 11 Ayahs",
    "101. Al-Qari'ah (The Calamity) - 11 Ayahs",
    "102. At-Takathur (The Rivalry in World Increase) - 8 Ayahs",
    "103. Al-Asr (The Declining Day) - 3 Ayahs",
    "104. Al-Humazah (The Traducer) - 9 Ayahs",
    "105. Al-Fil (The Elephant) - 5 Ayahs",
    "106. Quraish (Quraish) - 4 Ayahs",
    "107. Al-Ma'un (The Small Kindnesses) - 7 Ayahs",
    "108. Al-Kauthar (The Abundance) - 3 Ayahs",
    "109. Al-Kafirun (The Disbelievers) - 6 Ayahs",
    "110. An-Nasr (The Help) - 3 Ayahs",
    "111. Al-Masad (The Palm Fiber) - 5 Ayahs",
    "112. Al-Ikhlas (The Sincerity) - 4 Ayahs",
    "113. Al-Falaq (The Daybreak) - 5 Ayahs",
    "114. An-Nas (Mankind) - 6 Ayahs",
]

# Default assigned list: 37 Surahs (78-114)
DEFAULT_ASSIGNED_SURAHS = [
    surah
    for surah in SURAH_LIST
    if 78 <= int(surah.split(".", 1)[0]) <= 114
]

# Level Reward Definition
LEVEL_REWARDS = {
    2: "🍦 Ice Cream Treat!",
    3: "🧸 15 Mins Extra Playtime!",
    4: "🚲 Trip to the Park!",
    5: "🍫 Choose a Favorite Candy!",
    6: "🎯 Random Fun Surprise Reward!"
}

AYAHS_PER_LEVEL = 104
MAX_LEVEL = 60

LEVEL_TITLES = {
    1: "Beginner",
    2: "First Steps",
    3: "Ayah Explorer",
    4: "Young Learner",
    5: "Quran Seeker",
    6: "Dedicated Student",
    7: "Knowledge Builder",
    8: "Memorization Scout",
    9: "Quran Traveler",
    10: "Path Walker",
    11: "Consistent Learner",
    12: "Ayah Collector",
    13: "Focused Student",
    14: "Quran Adventurer",
    15: "Rising Reciter",
    16: "Steady Memorizer",
    17: "Quran Companion",
    18: "Strong Learner",
    19: "Dedicated Reciter",
    20: "Faith Builder",
    21: "Ayah Guardian",
    22: "Quran Keeper",
    23: "Wisdom Seeker",
    24: "Memorization Champion",
    25: "Quran Achiever",
    26: "Noble Learner",
    27: "Quran Ambassador",
    28: "Knowledge Guardian",
    29: "Faithful Reciter",
    30: "Quran Pathfinder",
    31: "Skilled Memorizer",
    32: "Ayah Master",
    33: "Quran Mentor",
    34: "Trusted Learner",
    35: "Light Bearer",
    36: "Keeper of Verses",
    37: "Student of Excellence",
    38: "Guardian of Knowledge",
    39: "Quran Luminary",
    40: "Advanced Memorizer",
    41: "Respected Reciter",
    42: "Trusted Guardian",
    43: "Quran Scholar",
    44: "Wisdom Carrier",
    45: "Noble Protector",
    46: "Elite Memorizer",
    47: "Beacon of Learning",
    48: "Quran Steward",
    49: "Keeper of Light",
    50: "Distinguished Reciter",
    51: "Master of Ayahs",
    52: "Quran Leader",
    53: "Guardian of Revelation",
    54: "Pillar of Knowledge",
    55: "Servant of the Quran",
    56: "Crowned Memorizer",
    57: "Champion of the Quran",
    58: "Custodian of Revelation",
    59: "Nearing Hafiz",
    60: "Hafiz",
}

MILESTONE_GOAL_TYPES = {
    "surahs_completed": "Surahs Completed",
    "ayahs_memorized": "Ayahs Memorized",
    "streak_days": "Streak Days",
    "xp_total": "Total XP",
    "level_reached": "Level Reached",
    "juz_completion_pct": "Juz Completion %",
}


def build_default_milestone_catalog():
    now = datetime.date.today().isoformat()
    default_items = [
        {
            "id": "milestone_first_surah",
            "title": "🏅 First Surah Completed",
            "goal_type": "surahs_completed",
            "target_value": 1,
            "reward_label": "🍦 Ice Cream Treat",
            "reward_xp": 20,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "milestone_streak_7",
            "title": "🔥 7 Day Streak",
            "goal_type": "streak_days",
            "target_value": 7,
            "reward_label": "⭐ 35 XP Blessing Bonus",
            "reward_xp": 35,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "milestone_surah_5",
            "title": "📖 5 Surahs Completed",
            "goal_type": "surahs_completed",
            "target_value": 5,
            "reward_label": "🧸 15 mins extra playtime",
            "reward_xp": 50,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "milestone_xp_500",
            "title": "⭐ 500 XP Earned",
            "goal_type": "xp_total",
            "target_value": 500,
            "reward_label": "🚲 Trip to the Park",
            "reward_xp": 70,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "milestone_juz_amma_master",
            "title": "🏆 Juz Amma Master",
            "goal_type": "surahs_completed",
            "target_value": len(SURAH_LIST),
            "reward_label": "👑 Family Celebration Reward",
            "reward_xp": 120,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    ]

    for lvl in range(2, 11):
        reward_desc = LEVEL_REWARDS.get(lvl, LEVEL_REWARDS[6])
        default_items.append(
            {
                "id": f"milestone_level_{lvl}",
                "title": f"🎯 Reach Level {lvl}",
                "goal_type": "level_reached",
                "target_value": lvl,
                "reward_label": reward_desc,
                "reward_xp": 0,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )

    return default_items


def make_unique_milestone_id(title, existing_ids):
    cleaned = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not cleaned:
        cleaned = "custom_milestone"
    base_id = f"milestone_{cleaned}"
    candidate = base_id
    counter = 2
    while candidate in existing_ids:
        candidate = f"{base_id}_{counter}"
        counter += 1
    return candidate


def get_goal_progress(goal_type, current_level, surahs_completed, juz_completion_pct, total_ayahs_memorized):
    if goal_type == "surahs_completed":
        return int(surahs_completed)
    if goal_type == "ayahs_memorized":
        return int(total_ayahs_memorized)
    if goal_type == "streak_days":
        return int(st.session_state.streak)
    if goal_type == "xp_total":
        return int(st.session_state.xp)
    if goal_type == "level_reached":
        return int(current_level)
    if goal_type == "juz_completion_pct":
        return int(round(juz_completion_pct))
    return 0


def get_goal_text(goal_type, target_value):
    if goal_type == "surahs_completed":
        return f"Surah Target: {target_value}"
    if goal_type == "ayahs_memorized":
        return f"Ayah Target: {target_value}"
    if goal_type == "streak_days":
        return f"Streak Days: {target_value}"
    if goal_type == "xp_total":
        return f"Points Target: {target_value}"
    if goal_type == "level_reached":
        return f"Level Target: {target_value}"
    if goal_type == "juz_completion_pct":
        return f"Juz Completion Target: {target_value}%"
    return f"Reach target {target_value}"


def get_elapsed_learning_days(today):
    history_dates = []
    for event in st.session_state.history:
        raw_date = str(event.get("date", ""))
        try:
            history_dates.append(datetime.date.fromisoformat(raw_date))
        except Exception:
            continue

    if not history_dates:
        return 1

    first_day = min(history_dates)
    elapsed_days = (today - first_day).days + 1
    return max(1, elapsed_days)


def get_recent_activity_bonus(today):
    history_dates = []
    for event in st.session_state.history:
        raw_date = str(event.get("date", ""))
        try:
            history_dates.append(datetime.date.fromisoformat(raw_date))
        except Exception:
            continue

    if not history_dates:
        return 0.0

    days_since_latest = max(0, (today - max(history_dates)).days)
    return max(0.0, 1.0 - (days_since_latest / 14.0))


def estimate_goal_pace_per_day(
    goal_type,
    elapsed_days,
    current_level,
    surahs_completed,
    juz_completion_pct,
    total_ayahs_memorized,
):
    elapsed_days = max(1, int(elapsed_days))

    # Conservative floors keep ETA finite in low/no-history scenarios.
    floors = {
        "xp_total": 5.0,
        "surahs_completed": 0.05,
        "ayahs_memorized": 1.0,
        "streak_days": 0.25,
        "level_reached": 0.03,
        "juz_completion_pct": 0.5,
    }

    if goal_type == "xp_total":
        pace = float(st.session_state.xp) / float(elapsed_days)
    elif goal_type == "surahs_completed":
        pace = float(surahs_completed) / float(elapsed_days)
    elif goal_type == "ayahs_memorized":
        pace = float(total_ayahs_memorized) / float(elapsed_days)
    elif goal_type == "streak_days":
        pace = 1.0 if st.session_state.streak > 0 else 0.0
    elif goal_type == "level_reached":
        pace = float(max(0, current_level - 1)) / float(elapsed_days)
    elif goal_type == "juz_completion_pct":
        pace = float(juz_completion_pct) / float(elapsed_days)
    else:
        pace = 0.0

    return max(floors.get(goal_type, 0.1), pace)


def apply_eta_based_milestone_ranking(
    items,
    current_level,
    surahs_completed,
    juz_completion_pct,
    total_ayahs_memorized,
):
    today = datetime.date.today()
    elapsed_days = get_elapsed_learning_days(today)
    activity_bonus = get_recent_activity_bonus(today)
    max_reward_xp = max((int(item.get("reward_xp", 0)) for item in items), default=0)
    reward_denom = max(1, max_reward_xp)

    for item in items:
        goal_type = str(item.get("goal_type", "xp_total"))
        target = max(1, int(item.get("target", 1)))
        progress = max(0, int(item.get("progress", 0)))
        remaining = max(0, target - progress)

        pace_per_day = estimate_goal_pace_per_day(
            goal_type,
            elapsed_days,
            current_level,
            surahs_completed,
            juz_completion_pct,
            total_ayahs_memorized,
        )
        eta_days = 0.0 if remaining <= 0 else (float(remaining) / float(max(0.0001, pace_per_day)))

        completion_ratio = min(1.0, float(progress) / float(max(1, target)))

        # Quick-win bias: short ETA milestones should dominate ranking.
        closeness = 1.0 / ((1.0 + eta_days) ** 1.35)
        short_horizon_bonus = 0.0
        if eta_days <= 7:
            short_horizon_bonus = 0.15
        elif eta_days <= 21:
            short_horizon_bonus = 0.08
        elif eta_days <= 45:
            short_horizon_bonus = 0.03

        long_horizon_penalty = 0.0
        if eta_days > 60:
            long_horizon_penalty = min(0.25, (eta_days - 60.0) / 600.0)

        reward_bonus = float(int(item.get("reward_xp", 0))) / float(reward_denom)
        rank_score = (
            (0.88 * closeness)
            + (0.08 * completion_ratio)
            + (0.03 * reward_bonus)
            + (0.01 * activity_bonus)
            + short_horizon_bonus
            - long_horizon_penalty
        )
        rank_score = max(0.0, min(1.0, rank_score))

        item["remaining"] = remaining
        item["pace_per_day"] = pace_per_day
        item["eta_days"] = eta_days
        item["completion_ratio"] = completion_ratio
        item["rank_score"] = rank_score

    return items


def get_fit_text_class(text):
    text_len = len(str(text or ""))
    if text_len >= 85:
        return " fit-text-xsmall"
    if text_len >= 55:
        return " fit-text-small"
    return ""


def normalize_milestone_catalog(raw_catalog):
    now = datetime.date.today().isoformat()
    normalized = []
    existing_ids = set()
    for record in raw_catalog or []:
        if not isinstance(record, dict):
            continue
        raw_title = str(record.get("title", "")).strip()
        if not raw_title:
            continue

        raw_goal_type = str(record.get("goal_type", "xp_total"))
        goal_type = raw_goal_type if raw_goal_type in MILESTONE_GOAL_TYPES else "xp_total"

        try:
            target_value = int(record.get("target_value", 1))
        except Exception:
            target_value = 1
        target_value = max(1, target_value)

        try:
            reward_xp = int(record.get("reward_xp", 0))
        except Exception:
            reward_xp = 0
        reward_xp = max(0, reward_xp)

        raw_id = str(record.get("id", "")).strip()
        milestone_id = raw_id if raw_id else make_unique_milestone_id(raw_title, existing_ids)
        if milestone_id in existing_ids:
            milestone_id = make_unique_milestone_id(raw_title, existing_ids)
        existing_ids.add(milestone_id)

        normalized.append(
            {
                "id": milestone_id,
                "title": raw_title,
                "goal_type": goal_type,
                "target_value": target_value,
                "reward_label": str(record.get("reward_label", "🎁 Custom Reward")).strip() or "🎁 Custom Reward",
                "reward_xp": reward_xp,
                "is_active": bool(record.get("is_active", True)),
                "created_at": str(record.get("created_at", now)),
                "updated_at": str(record.get("updated_at", now)),
            }
        )
    return normalized


def normalize_assigned_surahs(raw_assigned):
    if not isinstance(raw_assigned, list):
        return DEFAULT_ASSIGNED_SURAHS.copy()
    valid = [s for s in raw_assigned if s in SURAH_LIST]
    if not valid:
        return DEFAULT_ASSIGNED_SURAHS.copy()
    seen = set()
    ordered = []
    for surah in valid:
        if surah not in seen:
            ordered.append(surah)
            seen.add(surah)
    return ordered


def get_assigned_surahs():
    assigned = st.session_state.get("assigned_surahs", DEFAULT_ASSIGNED_SURAHS.copy())
    return normalize_assigned_surahs(assigned)


def get_total_memorized_ayahs():
    return sum(len(st.session_state.memorized.get(surah, [])) for surah in SURAH_LIST)


def get_level_from_memorized_ayahs(total_memorized_ayahs):
    return min(MAX_LEVEL, (int(total_memorized_ayahs) // AYAHS_PER_LEVEL) + 1)


def get_level_progress_stats(total_memorized_ayahs):
    current_level = get_level_from_memorized_ayahs(total_memorized_ayahs)
    if current_level >= MAX_LEVEL:
        return current_level, 100.0, 0

    progress_percent = ((int(total_memorized_ayahs) % AYAHS_PER_LEVEL) / AYAHS_PER_LEVEL) * 100
    ayahs_remaining = AYAHS_PER_LEVEL - (int(total_memorized_ayahs) % AYAHS_PER_LEVEL)
    return current_level, progress_percent, ayahs_remaining


def get_level_title(level):
    safe_level = max(1, min(MAX_LEVEL, int(level)))
    return LEVEL_TITLES.get(safe_level, "Hafiz")

def get_ayah_count(surah_name):
    try:
        parts = surah_name.split(" - ")
        if len(parts) > 1:
            count_str = parts[-1].replace("Ayahs", "").replace("Ayah", "").strip()
            return int(count_str)
    except Exception:
        pass
    return 7  # default backup


def get_surah_short_name(surah_name):
    no_number = surah_name.split(".", 1)[-1].strip()
    return no_number.split("(")[0].strip()


def get_mem_status(mem_count, total_count):
    if mem_count == 0:
        return "None", "⬜"
    if mem_count == total_count:
        return "Full", "🟩"
    return "Partial", "🟧"


def get_revision_status_for_surah(surah_name, today, apply_cycle_reset=True):
    memorized_list = st.session_state.memorized.get(surah_name, [])
    rev_dates = st.session_state.revised_dates.get(surah_name, {})
    recently_revised = []
    eligible_ayahs = []

    for ayah in memorized_list:
        last_rev_str = rev_dates.get(str(ayah))
        if last_rev_str:
            last_rev_date = datetime.date.fromisoformat(last_rev_str)
            days_since = (today - last_rev_date).days
            if days_since < 7:
                recently_revised.append(ayah)
                continue
        eligible_ayahs.append(ayah)

    cycle_completed = False

    return memorized_list, rev_dates, eligible_ayahs, recently_revised, cycle_completed


# Load persisted state once per browser session before defaults are applied.
if "_state_loaded" not in st.session_state:
    load_app_state()
    st.session_state["_state_loaded"] = True


# Initialize Session States
if 'xp' not in st.session_state:
    st.session_state.xp = 0
if 'streak' not in st.session_state:
    st.session_state.streak = 0
if 'last_active_date' not in st.session_state:
    st.session_state.last_active_date = None
if 'last_inactivity_penalty_for_date' not in st.session_state:
    st.session_state.last_inactivity_penalty_for_date = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_blessing_claim' not in st.session_state:
    st.session_state.last_blessing_claim = None
if 'recent_praise' not in st.session_state:
    st.session_state.recent_praise = ""
if 'memorized' not in st.session_state:
    st.session_state.memorized = {} # surah_name -> list of ints
if 'revised_dates' not in st.session_state:
    st.session_state.revised_dates = {} # surah_name -> dict(str(ayah) -> iso_date_str)
if 'nav_section' not in st.session_state:
    st.session_state.nav_section = NAV_ITEMS[0]
if 'milestone_claims' not in st.session_state:
    st.session_state.milestone_claims = {}
if 'milestone_catalog' not in st.session_state:
    st.session_state.milestone_catalog = build_default_milestone_catalog()
if 'milestone_version' not in st.session_state:
    st.session_state.milestone_version = 1
if 'assigned_surahs' not in st.session_state:
    st.session_state.assigned_surahs = DEFAULT_ASSIGNED_SURAHS.copy()
if 'last_level_checkpoint' not in st.session_state:
    st.session_state.last_level_checkpoint = get_level_from_memorized_ayahs(get_total_memorized_ayahs())

st.session_state.milestone_catalog = normalize_milestone_catalog(st.session_state.milestone_catalog)
st.session_state.assigned_surahs = normalize_assigned_surahs(st.session_state.assigned_surahs)

# Fun encouragements
HIFDH_PRAISES = [
    "MashaAllah! You memorized another Ayah! Keep shining, Rayyan! 🌟",
    "Wow! Rayyan is a superstar! High five! 🖐️",
    "Fantastic job! The angels are smiling! 👼",
    "You did it! Keep building your crown of light! 👑",
    "SubhanAllah! Beautiful reading, Rayyan! Keep going! 🚀"
]

MURAJAH_PRAISES = [
    "Super Murajah Master! Revision makes your memorization as strong as a mountain! 🏔️",
    "Amazing revision, Rayyan! You are keeping the Quran glowing in your heart! ❤️",
    "Revision hero! That's double-strength power! 💪🌟",
    "MashAllah! Revision is the secret of champions! You did an awesome job! 🏆",
    "Praise be to Allah! You revised beautifully today! 🌈"
]


def apply_inactivity_penalty_if_needed(today):
    last_active_str = st.session_state.get("last_active_date")
    if not last_active_str:
        return

    try:
        last_active_date = datetime.date.fromisoformat(last_active_str)
    except ValueError:
        return

    days_without_learning = (today - last_active_date).days
    if days_without_learning < INACTIVITY_DAYS_THRESHOLD:
        return

    # Apply once per inactivity window (anchored on last active learning date).
    if st.session_state.get("last_inactivity_penalty_for_date") == last_active_str:
        return

    st.session_state.xp = max(0, st.session_state.xp - INACTIVITY_XP_PENALTY)
    st.session_state.last_inactivity_penalty_for_date = last_active_str
    st.session_state.history.insert(0, {
        "date": today.strftime("%Y-%m-%d"),
        "activity": "Inactivity Penalty",
        "surah": "-",
        "details": f"No learning for {INACTIVITY_DAYS_THRESHOLD} days",
        "points": -INACTIVITY_XP_PENALTY,
    })

# Helper function to add XP and update streak
def add_xp(points, activity_type, surah_name, details=""):
    st.session_state.xp += points

    # Update streak logic
    today = datetime.date.today().isoformat()
    if st.session_state.last_active_date != today:
        if st.session_state.last_active_date == (datetime.date.today() - datetime.timedelta(days=1)).isoformat():
            st.session_state.streak += 1
        elif st.session_state.last_active_date is None or st.session_state.streak == 0:
            st.session_state.streak = 1
        st.session_state.last_active_date = today

    # Log history
    st.session_state.history.insert(0, {
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "activity": activity_type,
        "surah": surah_name,
        "details": details,
        "points": points
    })

    # Trigger ayah-based level celebration.
    new_level = get_level_from_memorized_ayahs(get_total_memorized_ayahs())
    previous_level = int(st.session_state.get("last_level_checkpoint", new_level))
    if new_level > previous_level:
        st.session_state.confetti_trigger = True
        st.session_state.level_up_context = {
            "level": new_level,
            "title": get_level_title(new_level),
        }
    st.session_state.last_level_checkpoint = new_level

    if new_level > previous_level:
        return True
    return False


def ensure_selection_state():
    assigned_surahs = get_assigned_surahs()
    default_surah = assigned_surahs[0] if assigned_surahs else SURAH_LIST[0]
    if "selected_surah" not in st.session_state:
        st.session_state["selected_surah"] = default_surah
    elif st.session_state["selected_surah"] not in assigned_surahs:
        st.session_state["selected_surah"] = default_surah
    if "hifdh_selected_surah" not in st.session_state:
        st.session_state["hifdh_selected_surah"] = default_surah
    elif st.session_state["hifdh_selected_surah"] not in assigned_surahs:
        st.session_state["hifdh_selected_surah"] = default_surah
    if "murajah_selected_surah" not in st.session_state:
        st.session_state["murajah_selected_surah"] = default_surah
    elif st.session_state["murajah_selected_surah"] not in assigned_surahs:
        st.session_state["murajah_selected_surah"] = default_surah


def reset_application_data(preserve_parental_config=False):
    preserved_assigned_surahs = normalize_assigned_surahs(
        st.session_state.get("assigned_surahs", SURAH_LIST.copy())
    )
    preserved_milestone_catalog = normalize_milestone_catalog(
        st.session_state.get("milestone_catalog", build_default_milestone_catalog())
    )
    preserved_milestone_version = max(1, int(st.session_state.get("milestone_version", 1)))

    st.session_state.xp = 0
    st.session_state.streak = 0
    st.session_state.last_active_date = None
    st.session_state.last_inactivity_penalty_for_date = None
    st.session_state.history = []
    st.session_state.last_blessing_claim = None
    st.session_state.recent_praise = ""
    st.session_state.memorized = {}
    st.session_state.revised_dates = {}
    st.session_state.milestone_claims = {}
    st.session_state.last_level_checkpoint = get_level_from_memorized_ayahs(0)
    st.session_state.confetti_trigger = False
    st.session_state.pop("level_up_context", None)

    if preserve_parental_config:
        st.session_state.assigned_surahs = preserved_assigned_surahs
        st.session_state.milestone_catalog = preserved_milestone_catalog
        st.session_state.milestone_version = preserved_milestone_version
    else:
        st.session_state.assigned_surahs = SURAH_LIST.copy()
        st.session_state.milestone_catalog = build_default_milestone_catalog()
        st.session_state.milestone_version = 1

    ensure_selection_state()


def get_summary_metrics():
    total_ayahs_memorized = get_total_memorized_ayahs()
    current_level = get_level_from_memorized_ayahs(total_ayahs_memorized)
    level_title = get_level_title(current_level)
    surahs_completed = sum(
        1 for s in SURAH_LIST if len(st.session_state.memorized.get(s, [])) >= get_ayah_count(s)
    )
    juz_completion_pct = (surahs_completed / len(SURAH_LIST)) * 100
    return current_level, level_title, surahs_completed, juz_completion_pct, total_ayahs_memorized


def render_sidebar_profile(
    current_level,
    level_title,
    total_ayahs_memorized,
):
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>👦 Rayyan's Profile</h2>", unsafe_allow_html=True)

        avatar_path = "rayyan_avatar.png"
        if os.path.exists(avatar_path):
            image = Image.open(avatar_path)
            st.image(image, width="stretch", caption="Rayyan the Quran Champion!")
        else:
            st.markdown("<div style='text-align: center; font-size: 80px;'>🤖</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="game-level-badge" style="margin: 6px 0 10px 0;">
                <p class="game-level-icon">🏅</p>
                <p class="game-level-number">Level {current_level}</p>
                <p class="game-level-name">{level_title}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("💡 **Tip**: Memorize at least 1 Ayah or revise every day to keep your streak burning! 🔥")

        st.markdown("---")
        st.markdown("### 🧭 More")
        if st.button(
            "📜 Journal",
            key="sidebar_journal",
            width="stretch",
            type="primary" if st.session_state.nav_section == "📜 Journal" else "secondary",
        ):
            st.session_state.nav_section = "📜 Journal"
            st.rerun()

        if st.button(
            "⚙️ Parents",
            key="sidebar_parents",
            width="stretch",
            type="primary" if st.session_state.nav_section == "⚙️ Parents" else "secondary",
        ):
            st.session_state.nav_section = "⚙️ Parents"
            st.rerun()


def render_top_navigation():
    row_size = 4
    for row_start in range(0, len(NAV_ITEMS), row_size):
        row_items = NAV_ITEMS[row_start:row_start + row_size]
        st.markdown("<div class='top-nav-row'>", unsafe_allow_html=True)
        nav_cols = st.columns(len(row_items), gap="small")
        for idx, page_label in enumerate(row_items):
            is_active = st.session_state.nav_section == page_label
            with nav_cols[idx]:
                if st.button(
                    page_label,
                    key=f"nav_tab_{row_start + idx}",
                    width="stretch",
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.nav_section = page_label
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.nav_section


def render_level_celebration():
    if st.session_state.get("confetti_trigger", False):
        st.balloons()
        st.toast("🎉 Level up achieved!", icon="🏆")
        st.session_state.confetti_trigger = False
        level_context = st.session_state.pop("level_up_context", None)
        if level_context:
            new_level = int(level_context.get("level", get_level_from_memorized_ayahs(get_total_memorized_ayahs())))
            new_title = str(level_context.get("title", get_level_title(new_level)))
        else:
            new_level = get_level_from_memorized_ayahs(get_total_memorized_ayahs())
            new_title = get_level_title(new_level)

        reward = LEVEL_REWARDS.get(new_level, LEVEL_REWARDS[6] if new_level > 5 else "A special surprise!")
        st.success(f"🎉 LEVEL UP! You reached **Level {new_level} - {new_title}**! You unlocked your reward: **{reward}** 🎁")


def get_milestone_items(current_level, surahs_completed, juz_completion_pct, total_ayahs_memorized):
    items = []
    for config in st.session_state.milestone_catalog:
        target_value = max(1, int(config.get("target_value", 1)))
        goal_type = config.get("goal_type", "xp_total")
        progress = get_goal_progress(goal_type, current_level, surahs_completed, juz_completion_pct, total_ayahs_memorized)
        completed = progress >= target_value
        claimed = config["id"] in st.session_state.milestone_claims
        if claimed:
            state = "claimed"
        elif completed:
            state = "ready_to_claim"
        else:
            state = "in_progress"

        items.append(
            {
                "id": config["id"],
                "title": config["title"],
                "goal": get_goal_text(goal_type, target_value),
                "goal_type": goal_type,
                "goal_type_label": MILESTONE_GOAL_TYPES.get(goal_type, "Goal"),
                "reward": config.get("reward_label", "🎁 Reward"),
                "reward_xp": int(config.get("reward_xp", 0)),
                "progress": progress,
                "target": target_value,
                "completed": completed,
                "claimed": claimed,
                "state": state,
                "is_active": bool(config.get("is_active", True)),
            }
        )

    return apply_eta_based_milestone_ranking(
        items,
        current_level,
        surahs_completed,
        juz_completion_pct,
        total_ayahs_memorized,
    )


def build_recent_achievements(current_level):
    recent_achievements = []
    completed_surahs = [s for s in SURAH_LIST if len(st.session_state.memorized.get(s, [])) >= get_ayah_count(s)]
    if completed_surahs:
        recent_achievements.append(f"🎉 Completed {get_surah_short_name(completed_surahs[-1])}")
    if st.session_state.streak >= 7:
        recent_achievements.append(f"🔥 Reached {st.session_state.streak} Day Streak")
    recent_achievements.append(f"⭐ Reached Level {current_level} - {get_level_title(current_level)}")

    for item in st.session_state.history[:5]:
        if item["surah"] != "N/A":
            recent_achievements.append(
                f"📘 {item['activity']} logged in {get_surah_short_name(item['surah'])} (+{item['points']} XP)"
            )
        else:
            recent_achievements.append(f"✨ {item['activity']} (+{item['points']} XP)")
    return recent_achievements[:5]


def build_achievement_gallery_data(current_level, surahs_completed, juz_completion_pct, total_ayahs_memorized):
    milestone_items = get_milestone_items(current_level, surahs_completed, juz_completion_pct, total_ayahs_memorized)
    item_by_id = {item["id"]: item for item in milestone_items}

    def _goal_instruction(goal_type, target):
        if goal_type == "xp_total":
            return f"Complete {target} Points"
        if goal_type == "surahs_completed":
            unit = "Surah" if target == 1 else "Surahs"
            return f"Complete {target} {unit}"
        if goal_type == "ayahs_memorized":
            unit = "Ayah" if target == 1 else "Ayahs"
            return f"Complete {target} {unit}"
        if goal_type == "streak_days":
            unit = "Day" if target == 1 else "Days"
            return f"Complete {target} {unit} Streak"
        if goal_type == "level_reached":
            required_ayahs = max(0, (target - 1) * AYAHS_PER_LEVEL)
            return f"Reach Level {target} ({required_ayahs} memorized ayahs)"
        if goal_type == "juz_completion_pct":
            return f"Reach {target}% Juz Completion"
        return f"Reach target {target}"

    def _remaining_instruction(goal_type, remaining):
        if goal_type == "xp_total":
            return f"{remaining} more Points"
        if goal_type == "surahs_completed":
            unit = "Surah" if remaining == 1 else "Surahs"
            return f"{remaining} more {unit}"
        if goal_type == "ayahs_memorized":
            unit = "Ayah" if remaining == 1 else "Ayahs"
            return f"{remaining} more {unit}"
        if goal_type == "streak_days":
            unit = "Day" if remaining == 1 else "Days"
            return f"{remaining} more {unit}"
        if goal_type == "level_reached":
            unit = "Level" if remaining == 1 else "Levels"
            return f"{remaining} more {unit}"
        if goal_type == "juz_completion_pct":
            return f"{remaining}% more"
        return f"{remaining} remaining"

    ready_to_claim_items = [
        item for item in milestone_items
        if item.get("is_active", True) and item["state"] == "ready_to_claim"
    ]
    ready_to_claim_items.sort(key=lambda item: item["title"])

    claimed_events = []
    for milestone_id, claim_date in st.session_state.milestone_claims.items():
        milestone = item_by_id.get(milestone_id)
        if not milestone:
            continue
        try:
            claim_dt = datetime.date.fromisoformat(str(claim_date))
        except Exception:
            claim_dt = datetime.date.min
        claimed_events.append((claim_dt, milestone, str(claim_date)))

    claimed_events.sort(key=lambda x: x[0], reverse=True)

    achievement_cards = []

    for item in ready_to_claim_items:
        achievement_cards.append(
            {
                "state": "ready",
                "id": item["id"],
                "title": item["title"],
                "meta": f"Reward: {item['reward']}",
            }
        )

    for _, milestone, claim_date in claimed_events[:2]:
        achievement_cards.append(
            {
                "state": "claimed",
                "id": milestone["id"],
                "title": milestone["title"],
                "meta": f"Claimed on {claim_date}",
            }
        )

    achievement_cards = achievement_cards[:6]

    upcoming_candidates = [
        item for item in milestone_items if item.get("is_active", True) and item["state"] == "in_progress"
    ]

    def _priority(item):
        return (
            -item.get("rank_score", 0.0),
            item.get("eta_days", float("inf")),
            item["title"],
        )

    upcoming_candidates.sort(key=_priority)
    next_5 = []
    for item in upcoming_candidates[:5]:
        remaining = max(0, int(item["target"]) - int(item["progress"]))
        next_5.append(
            {
                **item,
                "remaining": remaining,
                "goal_instruction": _goal_instruction(item["goal_type"], int(item["target"])),
                "remaining_instruction": _remaining_instruction(item["goal_type"], remaining),
            }
        )
    return achievement_cards, next_5


def render_surah_browser(today, key_prefix, description_text):
    st.markdown(description_text)
    surah_xp_totals = {}
    for entry in st.session_state.history:
        if entry["surah"] != "N/A":
            surah_xp_totals[entry["surah"]] = surah_xp_totals.get(entry["surah"], 0) + entry["points"]

    tile_cols = st.columns(3)
    for idx, surah in enumerate(SURAH_LIST):
        total = get_ayah_count(surah)
        mem_list = st.session_state.memorized.get(surah, [])
        mem_count = len(mem_list)
        mem_label, mem_icon = get_mem_status(mem_count, total)

        _, _, eligible_preview, locked_preview, _ = get_revision_status_for_surah(surah, today, apply_cycle_reset=False)
        locked_count = len(locked_preview)
        ready_count = len(eligible_preview)

        if mem_count == 0:
            rev_label = "None"
            rev_icon = "⬜"
        elif ready_count == 0 and locked_count > 0:
            rev_label = "Locked"
            rev_icon = "🟡"
        else:
            rev_label = "Ready"
            rev_icon = "🟢"

        completion_pct = (mem_count / total) * 100 if total else 0

        if mem_count == 0:
            status_text = "⚪ Not Started"
            status_class = "status-notstarted"
        elif mem_count >= total and ready_count == 0 and locked_count > 0:
            status_text = "🟢 Complete"
            status_class = "status-complete"
        elif ready_count > 0:
            status_text = "🟠 Revision Needed"
            status_class = "status-revision"
        else:
            status_text = "🔵 In Progress"
            status_class = "status-inprogress"

        surah_xp = surah_xp_totals.get(surah, 0)
        is_selected = st.session_state["selected_surah"] == surah

        with tile_cols[idx % 3]:
            surah_short = get_surah_short_name(surah)
            st.markdown(
                f"""<div class="surah-card"><h4 class="surah-card-title">📖 {surah_short}</h4><span class="surah-status-badge {status_class}">{status_text}</span><div class="surah-meta-row"><span>Memorization Progress</span><span>{mem_count}/{total} ({mem_icon} {mem_label})</span></div><div class="surah-progress-track"><div class="surah-progress-fill-mem" style="width: {completion_pct:.1f}%;"></div></div><div class="surah-meta-row"><span>Revision Progress</span><span>{ready_count}/{mem_count if mem_count else 0} ({rev_icon} {rev_label})</span></div><div class="surah-progress-track"><div class="surah-progress-fill-rev" style="width: {(ready_count / mem_count * 100) if mem_count else 0:.1f}%;"></div></div><div class="surah-meta-row"><span>Completion</span><span>{completion_pct:.1f}%</span></div><div class="surah-footer">⭐ XP from this Surah: {surah_xp if surah_xp else 'No XP logged yet'}</div></div>""",
                unsafe_allow_html=True,
            )

            if st.button(
                "Continue with this Surah",
                key=f"{key_prefix}_tile_{idx}",
                width="stretch",
                type="primary" if is_selected else "secondary",
            ):
                st.session_state["selected_surah"] = surah
                st.session_state["hifdh_selected_surah"] = surah
                st.session_state["murajah_selected_surah"] = surah
                st.rerun()

    return st.session_state["selected_surah"]


def render_memorization_revision_page(today):
    st.markdown("## 📖 Memorization & 🔁 Revision")
    if st.session_state.recent_praise:
        st.info(st.session_state.recent_praise)

    assigned_surahs = get_assigned_surahs()
    if not assigned_surahs:
        st.warning("No Surahs are assigned by parent yet. Please ask parent to assign at least one Surah in Parents > Manage Quran.")
        return

    sorted_assigned_surahs = sorted(
        assigned_surahs,
        key=lambda surah: int(str(surah).split(".", 1)[0]),
        reverse=False,
    )

    if st.session_state.get("selected_surah") not in sorted_assigned_surahs:
        st.session_state["selected_surah"] = sorted_assigned_surahs[0]

    surah_choice = st.selectbox(
        "📖 Select a Surah",
        options=sorted_assigned_surahs,
        key="selected_surah",
    )
    st.session_state["hifdh_selected_surah"] = surah_choice
    st.session_state["murajah_selected_surah"] = surah_choice

    surah_short_name = surah_choice.split("(")[0].strip()
    total_hifdh_ayahs = get_ayah_count(surah_choice)
    memorized_count = len(st.session_state.memorized.get(surah_choice, []))
    _, _, eligible_preview, locked_preview, _ = get_revision_status_for_surah(
        surah_choice,
        today,
        apply_cycle_reset=False,
    )

    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("📖 Memorized", f"{memorized_count}/{total_hifdh_ayahs}")
    with summary_cols[1]:
        st.metric("🟢 Ready for Revision", len(eligible_preview))
    with summary_cols[2]:
        st.metric("🟡 Locked", len(locked_preview))

    memorized_list_rev, rev_dates, eligible_ayahs, _, cycle_completed = get_revision_status_for_surah(
        surah_choice,
        today,
        apply_cycle_reset=True,
    )

    mem_col, rev_col = st.columns(2, gap="large")

    with mem_col:
        st.markdown(
            """
            <div class="custom-card">
                <h3>🌱 Log New Memorization (Hifdh)</h3>
                <p style="color: #166534;">Ayah-by-Ayah progress. Every single Ayah counts!</p>
                <p style="font-weight: bold; color: #22c55e;">⭐ +5 XP per Ayah</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        memorized_list = st.session_state.memorized.get(surah_choice, [])
        st.markdown(f"##### 📖 Progress Map for: *{surah_short_name}* (🟢 Memorized | ⚪ Not Memorized)")
        for i in range(1, total_hifdh_ayahs + 1):
            col_idx = (i - 1) % 10
            if col_idx == 0:
                s_row = st.columns(10)
            is_mem = i in memorized_list
            emoji = "🟢" if is_mem else "⚪"
            tooltip = "Memorized" if is_mem else "Not Memorized"
            with s_row[col_idx]:
                st.markdown(
                    f"<div style='text-align: center; font-size: 1.1rem;' title='{tooltip}'>{emoji}<br/><span style='font-size: 0.7rem; color: #666;'>{i}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<br/>", unsafe_allow_html=True)
        remaining_ayahs = [i for i in range(1, total_hifdh_ayahs + 1) if i not in memorized_list]

        with st.form(f"hifdh_form_{surah_choice}", clear_on_submit=False):
            selected_ayahs = []
            if not remaining_ayahs:
                st.success("🏆 SubhanAllah! Rayyan has memorized all Ayahs of this Surah! Revision is now available. 🏔️")
                submit_hifdh = st.form_submit_button("Submit Memorization! 🚀", disabled=True)
            else:
                st.write("Select the Ayah numbers you memorized today:")
                cols_per_row = 10
                for idx, i in enumerate(remaining_ayahs):
                    col_idx = idx % cols_per_row
                    if col_idx == 0:
                        row_cols = st.columns(cols_per_row)
                    with row_cols[col_idx]:
                        if st.checkbox(f"{i}", key=f"hifdh_{surah_choice}_{i}"):
                            selected_ayahs.append(i)
                submit_hifdh = st.form_submit_button("Submit Memorization! 🚀")

            if submit_hifdh:
                if not selected_ayahs:
                    st.error("Please select at least one Ayah! 📖")
                else:
                    pts = len(selected_ayahs) * XP_PER_AYAH_LEARNED
                    selected_ayahs.sort()

                    prev_memorized_count = len(st.session_state.memorized.get(surah_choice, []))
                    current_memorized = set(st.session_state.memorized.get(surah_choice, []))
                    current_memorized.update(selected_ayahs)
                    st.session_state.memorized[surah_choice] = sorted(list(current_memorized))
                    st.session_state["hifdh_selected_surah"] = surah_choice

                    ayah_ranges = f"Ayah(s): {', '.join(map(str, selected_ayahs))}"
                    add_xp(pts, "Memorization", surah_choice, ayah_ranges)
                    st.session_state.recent_praise = random.choice(HIFDH_PRAISES) + f" (Log: {ayah_ranges} memorized!)"
                    st.toast(f"✨ Great job! +{pts} XP from memorization.", icon="📖")
                    if prev_memorized_count < total_hifdh_ayahs <= len(current_memorized):
                        st.balloons()
                        st.toast(f"🏅 Achievement unlocked: Completed {surah_short_name}", icon="🎉")
                    st.rerun()

    with rev_col:
        st.markdown(
            """
            <div class="custom-card" style="border-color: #fde047; background-color: #fefce8;">
                <h3>🏔️ Log Revision (Murajah)</h3>
                <p style="color: #854d0e;">Keep your memorization strong. Revision gets extra rewards!</p>
                <p style="font-weight: bold; color: #ca8a04;">⭐ +2 XP per Revised Ayah</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(f"##### 🏔️ Revision Map for: *{surah_short_name}* (🟢 Ready | 🟡 Locked | ⚪ Not Memorized)")
        for i in range(1, total_hifdh_ayahs + 1):
            col_idx = (i - 1) % 10
            if col_idx == 0:
                s_row_rev = st.columns(10)

            if i not in memorized_list_rev:
                emoji = "⚪"
                tooltip = "Not Memorized"
            elif i in eligible_ayahs:
                emoji = "🟢"
                tooltip = "Ready to Revise"
            else:
                emoji = "🟡"
                tooltip = f"Revised on {rev_dates.get(str(i))} (Lock is active)"

            with s_row_rev[col_idx]:
                st.markdown(
                    f"<div style='text-align: center; font-size: 1.1rem;' title='{tooltip}'>{emoji}<br/><span style='font-size: 0.7rem; color: #666;'>{i}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<br/>", unsafe_allow_html=True)

        st.markdown("### 📊 Revision Summary")
        summary_cols = st.columns(3)
        with summary_cols[0]:
            st.metric("🟢 Ready Ayahs", len(eligible_ayahs))
        with summary_cols[1]:
            st.metric("🟡 Locked Ayahs", len([a for a in memorized_list_rev if a not in eligible_ayahs]))
        with summary_cols[2]:
            revised_entries = sum(len(v) for v in st.session_state.revised_dates.values())
            st.metric("✅ Completed Revisions", revised_entries)

        with st.form(f"murajah_form_{surah_choice}", clear_on_submit=False):
            selected_revised = []
            if not memorized_list_rev:
                st.warning("⚠️ Rayyan has not memorized any Ayahs in this Surah yet! Memorize first to unlock revision! 🌱")
                submit_murajah = st.form_submit_button("Submit Revision! 🏆", disabled=True)
            else:
                if cycle_completed:
                    st.info("🎉 Full Revision Cycle Completed! All memorized Ayahs are unlocked for revision!")
                st.write("Select the Ayah numbers you revised today:")
                cols_per_row = 10
                for idx, ayah_num in enumerate(eligible_ayahs):
                    col_idx = idx % cols_per_row
                    if col_idx == 0:
                        row_cols = st.columns(cols_per_row)
                    with row_cols[col_idx]:
                        if st.checkbox(f"{ayah_num}", key=f"murajah_{surah_choice}_{ayah_num}"):
                            selected_revised.append(ayah_num)
                submit_murajah = st.form_submit_button("Submit Revision! 🏆")

            if submit_murajah and memorized_list_rev:
                if not selected_revised:
                    st.error("Please select at least one Ayah! 📖")
                else:
                    rev_count = len(selected_revised)
                    pts = rev_count * XP_PER_AYAH_REVISED
                    selected_revised.sort()

                    if surah_choice not in st.session_state.revised_dates:
                        st.session_state.revised_dates[surah_choice] = {}
                    today_str = today.isoformat()
                    for ayah in selected_revised:
                        st.session_state.revised_dates[surah_choice][str(ayah)] = today_str
                    st.session_state["murajah_selected_surah"] = surah_choice

                    ayah_ranges = f"Ayah(s): {', '.join(map(str, selected_revised))}"
                    add_xp(pts, "Revision", surah_choice, ayah_ranges)
                    st.session_state.recent_praise = random.choice(MURAJAH_PRAISES) + f" (Log: {ayah_ranges} revised!)"
                    st.toast(f"🏔️ Strong revision! +{pts} XP earned.", icon="⭐")
                    st.rerun()


def render_achievements_rewards_page(current_level, level_title, surahs_completed, juz_completion_pct, total_ayahs_memorized):
    st.markdown(f"## 🏆 Milestones - Level {current_level} ({level_title})")
    st.caption("Achievements and rewards are now merged into one journey. Complete milestones, then claim rewards.")

    milestone_items = get_milestone_items(
        current_level,
        surahs_completed,
        juz_completion_pct,
        total_ayahs_memorized,
    )
    ready_items = [item for item in milestone_items if item["is_active"] and item["state"] == "ready_to_claim"]
    active_items = [item for item in milestone_items if item["is_active"] and item["state"] == "in_progress"]
    claimed_items = [item for item in milestone_items if item["state"] == "claimed"]

    next_item = None
    if active_items:
        next_item = max(
            active_items,
            key=lambda item: (
                item.get("rank_score", 0.0),
                (item["progress"] / item["target"]) if item["target"] else 0,
            ),
        )

    hero_cols = st.columns(4)
    with hero_cols[0]:
        st.metric("✅ Claimed", len(claimed_items))
    with hero_cols[1]:
        st.metric("🎁 Ready To Claim", len(ready_items))
    with hero_cols[2]:
        st.metric("⏳ In Progress", len(active_items))
    with hero_cols[3]:
        completion_pct = (len(claimed_items) / len(milestone_items)) * 100 if milestone_items else 0
        st.metric("📈 Journey Complete", f"{completion_pct:.0f}%")

    if next_item:
        progress_ratio = min(1.0, (next_item["progress"] / next_item["target"])) if next_item["target"] else 0.0
        st.markdown(
            f"""
            <div class="custom-card gold-border" style="padding: 12px; margin-top: 8px;">
                <p style="margin: 0; font-size: 0.85rem; color: #854d0e; font-weight: bold;">NEXT BEST MILESTONE 🎯</p>
                <p style="margin: 4px 0 0 0; color: #14532d; font-weight: bold;">{next_item['title']}</p>
                <p style="margin: 2px 0 0 0; color: #166534; font-size: 0.85rem;">{next_item['progress']} / {next_item['target']} • Reward: {next_item['reward']}</p>
                <p style="margin: 2px 0 0 0; color: #6b7280; font-size: 0.78rem;">ETA: ~{next_item.get('eta_days', 0.0):.1f} day(s)</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(progress_ratio)

    tab_active, tab_ready, tab_claimed = st.tabs(["⏳ Active", "🎁 Ready to Claim", "✅ Claimed"])

    def render_milestone_card(item, card_type):
        extra_class = ""
        if card_type == "ready":
            extra_class = " is-ready"
        elif card_type == "claimed":
            extra_class = " is-claimed"

        title_fit_class = get_fit_text_class(item["title"])
        goal_fit_class = get_fit_text_class(item["goal"])
        reward_fit_class = get_fit_text_class(item["reward"])

        st.markdown(
            f"""
            <div class="milestone-grid-card{extra_class}">
                <div>
                    <p class="milestone-card-title{title_fit_class}">{item['title']}</p>
                    <p class="milestone-card-row{goal_fit_class}">Goal: {item['goal_type_label']} = {item['target']}</p>
                    <p class="milestone-card-row{reward_fit_class}">Reward: {item['reward']}</p>
                </div>
                <div>
                    <p class="milestone-card-row">Progress: {item['progress']} / {item['target']}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def render_milestone_grid(items, card_type):
        if not items:
            return
        cards_per_row = min(4, len(items))
        for row_start in range(0, len(items), cards_per_row):
            row_items = items[row_start:row_start + cards_per_row]
            cols = st.columns(cards_per_row, gap="small")
            for idx, item in enumerate(row_items):
                with cols[idx]:
                    render_milestone_card(item, card_type)
                    if card_type == "ready":
                        if st.button("Claim Reward", key=f"claim_{item['id']}", width="stretch", type="primary"):
                            st.session_state.milestone_claims[item["id"]] = datetime.date.today().isoformat()
                            if item["reward_xp"] > 0:
                                add_xp(item["reward_xp"], "Milestone Reward", "N/A", item["title"])
                                st.toast(f"Reward claimed: +{item['reward_xp']} XP", icon="🎁")
                            else:
                                st.toast(f"Reward claimed: {item['reward']}", icon="🎁")
                            st.rerun()

    with tab_active:
        if not active_items:
            st.success("All milestones are complete. Check Ready to Claim for rewards.")
        render_milestone_grid(active_items, "active")

    with tab_ready:
        if not ready_items:
            st.info("No rewards ready yet. Keep going on active milestones.")
        render_milestone_grid(ready_items, "ready")

    with tab_claimed:
        if not claimed_items:
            st.info("No claimed milestones yet. Claim one from the Ready to Claim tab.")
        normalized_claimed_items = []
        for item in claimed_items:
            claimed_on = st.session_state.milestone_claims.get(item["id"], "-")
            archived_note = " • Archived" if not item.get("is_active", True) else ""
            normalized_claimed_items.append(
                {
                    **item,
                    "progress": item["target"],
                    "goal": f"Claimed on: {claimed_on}{archived_note}",
                }
            )
        render_milestone_grid(normalized_claimed_items, "claimed")

    st.markdown("### ✨ Daily Blessing Bonus")
    st.write("Ask parents for permission, then click to check your daily blessing bonus!")
    if st.button("✨ Claim Daily Blessing Bonus! ✨"):
        today_str = datetime.date.today().isoformat()
        if st.session_state.last_blessing_claim == today_str:
            st.warning("You already claimed your Blessing Bonus today! Come back tomorrow for another surprise! 🌟")
        else:
            bonus_pts = random.randint(5, 15)
            st.session_state.last_blessing_claim = today_str
            add_xp(bonus_pts, "Blessing Bonus", "N/A", "Daily random bonus")
            st.toast(f"🎁 Blessing bonus claimed: +{bonus_pts} XP", icon="✨")
            st.success(f"🌟 Alhumdulillah! You got a Random Blessing Bonus of **+{bonus_pts} XP**! Keep working hard! 🎁")
            st.rerun()


def render_journal_page():
    st.markdown("## 📜 Journal")
    if not st.session_state.history:
        st.info("No activities logged yet. Start memorizing or revising to earn points! 🚀")
        return

    st.markdown("### 📈 Last 30 Days: Ayahs Memorized vs Ayahs Revised")
    trend_rows = dashboard_page.build_last_30_day_trend_rows(datetime.date.today())
    chart_values = []
    max_count = 0
    for row in trend_rows:
        max_count = max(max_count, row["Ayahs Memorized"], row["Ayahs Revised"])
        chart_values.append(
            {
                "Date": row["date_iso"],
                "Metric": "Ayahs Memorized",
                "Count": row["Ayahs Memorized"],
            }
        )
        chart_values.append(
            {
                "Date": row["date_iso"],
                "Metric": "Ayahs Revised",
                "Count": row["Ayahs Revised"],
            }
        )

    today_key = datetime.date.today().isoformat()
    today_row = next((row for row in trend_rows if row["date_iso"] == today_key), None)
    if today_row:
        st.caption(
            f"Today ({today_key}): Ayahs Memorized {today_row['Ayahs Memorized']} • Ayahs Revised {today_row['Ayahs Revised']}"
        )

    st.vega_lite_chart(
        chart_values,
        {
            "mark": {"type": "line", "point": {"filled": True, "size": 90}},
            "encoding": {
                "x": {
                    "field": "Date",
                    "type": "ordinal",
                    "title": "Day",
                    "axis": {"labelAngle": -45},
                },
                "y": {
                    "field": "Count",
                    "type": "quantitative",
                    "title": "Count",
                    "scale": {"domain": [0, max(1, max_count)]},
                },
                "color": {"field": "Metric", "type": "nominal", "title": "Series"},
                "tooltip": [
                    {"field": "Date", "type": "nominal", "title": "Date"},
                    {"field": "Metric", "type": "nominal", "title": "Metric"},
                    {"field": "Count", "type": "quantitative", "title": "Count"},
                ],
            },
            "height": 320,
        },
        width="stretch",
    )

    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        date_filter = st.selectbox("Filter", ["Today", "Last 7 Days", "Last 30 Days", "All Time"])
    with search_col:
        search_term = st.text_input("Search Surah or Activity")

    cutoff_date = None
    if date_filter == "Today":
        cutoff_date = datetime.date.today()
    elif date_filter == "Last 7 Days":
        cutoff_date = datetime.date.today() - datetime.timedelta(days=7)
    elif date_filter == "Last 30 Days":
        cutoff_date = datetime.date.today() - datetime.timedelta(days=30)

    filtered = []
    for entry in st.session_state.history:
        entry_date = datetime.date.fromisoformat(entry["date"])
        if cutoff_date and entry_date < cutoff_date:
            continue

        if search_term:
            search_l = search_term.lower()
            if search_l not in entry["activity"].lower() and search_l not in entry["surah"].lower():
                continue

        filtered.append(entry)

    if not filtered:
        st.warning("No journal entries match your filters.")
        return

    table_rows = []
    for entry in filtered:
        table_rows.append(
            {
                "Date": entry["date"],
                "Activity": entry["activity"],
                "Surah": entry["surah"],
                "Details": entry["details"],
                "XP": entry["points"],
            }
        )

    st.dataframe(table_rows, width="stretch", hide_index=True)


def render_parents_page(total_ayahs_memorized):
    st.markdown("## ⚙️ Parents")
    st.markdown("### 📊 Statistics")
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("✨ Total XP", st.session_state.xp)
    with stat_cols[1]:
        st.metric("📖 Total Ayahs Memorized", total_ayahs_memorized)
    with stat_cols[2]:
        revised_entries = sum(len(v) for v in st.session_state.revised_dates.values())
        st.metric("🔁 Total Revisions", revised_entries)
    with stat_cols[3]:
        st.metric("🔥 Streak", st.session_state.streak)

    st.markdown("### 📚 Manage Quran")
    st.caption("Select Surahs to assign. Only assigned Surahs will be shown on the Memorization & Revision page.")

    quran_col1, quran_col2 = st.columns([1, 1])
    with quran_col1:
        if st.button("Assign All Surahs", width="stretch"):
            st.session_state.assigned_surahs = SURAH_LIST.copy()
            ensure_selection_state()
            st.success("All Surahs assigned.")
            st.rerun()
    with quran_col2:
        if st.button("Keep Only Last 10 Surahs", width="stretch"):
            st.session_state.assigned_surahs = SURAH_LIST[-10:]
            ensure_selection_state()
            st.success("Assigned last 10 Surahs.")
            st.rerun()

    assigned_default = get_assigned_surahs()
    with st.form("manage_quran_assignment_form"):
        selected_surahs = st.multiselect(
            "Assigned Surahs",
            options=SURAH_LIST,
            default=assigned_default,
            help="Parents can choose one or many Surahs for current study plan.",
        )
        apply_assignments = st.form_submit_button("Save Assigned Surahs")

        if apply_assignments:
            if not selected_surahs:
                st.error("Please select at least one Surah.")
            else:
                st.session_state.assigned_surahs = normalize_assigned_surahs(selected_surahs)
                ensure_selection_state()
                st.success(f"Assigned {len(st.session_state.assigned_surahs)} Surahs for study.")
                st.rerun()

    st.info(f"Currently assigned: {len(get_assigned_surahs())} / {len(SURAH_LIST)} Surahs")

    st.markdown("### 🏆 Manage Milestones")
    st.caption("Parents can add, update, archive, or remove milestones that combine achievements and rewards.")

    manager_tabs = st.tabs(["📋 View", "➕ Add", "✏️ Update", "🗑️ Remove", "📦 Import/Export"])

    with manager_tabs[0]:
        filter_mode = st.selectbox(
            "Filter milestones",
            ["All", "Active", "Inactive", "Claimed", "Unclaimed"],
            key="milestone_view_filter",
        )

        table_rows = []
        for milestone in st.session_state.milestone_catalog:
            is_claimed = milestone["id"] in st.session_state.milestone_claims
            row = {
                "Title": milestone["title"],
                "ID": milestone["id"],
                "Goal Type": MILESTONE_GOAL_TYPES.get(milestone["goal_type"], milestone["goal_type"]),
                "Target": milestone["target_value"],
                "Reward": milestone["reward_label"],
                "Reward XP": milestone["reward_xp"],
                "Status": "Active" if milestone.get("is_active", True) else "Inactive",
                "Claimed": "Yes" if is_claimed else "No",
                "Last Updated": milestone.get("updated_at", "-"),
            }
            if filter_mode == "Active" and row["Status"] != "Active":
                continue
            if filter_mode == "Inactive" and row["Status"] != "Inactive":
                continue
            if filter_mode == "Claimed" and row["Claimed"] != "Yes":
                continue
            if filter_mode == "Unclaimed" and row["Claimed"] != "No":
                continue
            table_rows.append(row)

        if table_rows:
            st.dataframe(table_rows, width="stretch", hide_index=True)
        else:
            st.info("No milestones match the selected filter.")

    with manager_tabs[1]:
        with st.form("add_milestone_form", clear_on_submit=True):
            st.markdown("#### Add New Milestone")
            new_title = st.text_input("Title")
            new_goal_type = st.selectbox("Goal Type", list(MILESTONE_GOAL_TYPES.keys()), format_func=lambda x: MILESTONE_GOAL_TYPES[x])
            new_target = st.number_input("Target Value", min_value=1, value=1, step=1)
            new_reward = st.text_input("Reward Label", value="🎁 Custom Reward")
            new_reward_xp = st.number_input("Reward XP", min_value=0, value=0, step=1)
            new_active = st.checkbox("Active", value=True)
            submit_add = st.form_submit_button("Add Milestone")

            if submit_add:
                title_clean = new_title.strip()
                reward_clean = new_reward.strip() or "🎁 Custom Reward"
                if not title_clean:
                    st.error("Title is required.")
                else:
                    existing_titles = {m["title"].strip().lower() for m in st.session_state.milestone_catalog}
                    if title_clean.lower() in existing_titles:
                        st.error("A milestone with this title already exists.")
                    else:
                        existing_ids = {m["id"] for m in st.session_state.milestone_catalog}
                        new_id = make_unique_milestone_id(title_clean, existing_ids)
                        today_str = datetime.date.today().isoformat()
                        st.session_state.milestone_catalog.append(
                            {
                                "id": new_id,
                                "title": title_clean,
                                "goal_type": new_goal_type,
                                "target_value": int(new_target),
                                "reward_label": reward_clean,
                                "reward_xp": int(new_reward_xp),
                                "is_active": bool(new_active),
                                "created_at": today_str,
                                "updated_at": today_str,
                            }
                        )
                        st.success("Milestone added successfully.")
                        st.rerun()

    with manager_tabs[2]:
        if not st.session_state.milestone_catalog:
            st.info("No milestones available to update.")
        else:
            edit_options = {f"{m['title']} ({m['id']})": m["id"] for m in st.session_state.milestone_catalog}
            selected_label = st.selectbox("Select milestone", list(edit_options.keys()), key="milestone_update_select")
            selected_id = edit_options[selected_label]
            selected_index = next((idx for idx, m in enumerate(st.session_state.milestone_catalog) if m["id"] == selected_id), -1)
            selected_milestone = st.session_state.milestone_catalog[selected_index]

            st.markdown("#### Update Milestone")
            updated_title = st.text_input("Title", value=selected_milestone["title"], key=f"edit_title_{selected_id}")
            updated_goal_type = st.selectbox(
                "Goal Type",
                list(MILESTONE_GOAL_TYPES.keys()),
                index=list(MILESTONE_GOAL_TYPES.keys()).index(selected_milestone["goal_type"]),
                format_func=lambda x: MILESTONE_GOAL_TYPES[x],
                key=f"edit_goal_type_{selected_id}",
            )
            updated_target = st.number_input(
                "Target Value",
                min_value=1,
                value=int(selected_milestone["target_value"]),
                step=1,
                key=f"edit_target_{selected_id}",
            )
            updated_reward = st.text_input(
                "Reward Label",
                value=selected_milestone["reward_label"],
                key=f"edit_reward_{selected_id}",
            )
            updated_reward_xp = st.number_input(
                "Reward XP",
                min_value=0,
                value=int(selected_milestone["reward_xp"]),
                step=1,
                key=f"edit_reward_xp_{selected_id}",
            )
            updated_active = st.checkbox(
                "Active",
                value=bool(selected_milestone.get("is_active", True)),
                key=f"edit_active_{selected_id}",
            )

            already_claimed = selected_id in st.session_state.milestone_claims
            rule_change = (
                updated_goal_type != selected_milestone["goal_type"]
                or int(updated_target) != int(selected_milestone["target_value"])
            )

            if already_claimed and rule_change:
                st.warning("This milestone was already claimed. Changing goal rule can affect future tracking.")
            confirm_rule_change = True
            if already_claimed and rule_change:
                confirm_rule_change = st.checkbox("I confirm I want to change goal type/target for this claimed milestone.")

            if st.button("Save Milestone Updates", width="stretch", type="primary"):
                title_clean = updated_title.strip()
                reward_clean = updated_reward.strip() or "🎁 Custom Reward"
                if not title_clean:
                    st.error("Title is required.")
                elif not confirm_rule_change:
                    st.error("Please confirm the rule change for this claimed milestone.")
                else:
                    duplicate_title = any(
                        m["id"] != selected_id and m["title"].strip().lower() == title_clean.lower()
                        for m in st.session_state.milestone_catalog
                    )
                    if duplicate_title:
                        st.error("Another milestone already uses this title.")
                    else:
                        updated_record = {
                            **selected_milestone,
                            "title": title_clean,
                            "goal_type": updated_goal_type,
                            "target_value": int(updated_target),
                            "reward_label": reward_clean,
                            "reward_xp": int(updated_reward_xp),
                            "is_active": bool(updated_active),
                            "updated_at": datetime.date.today().isoformat(),
                        }
                        st.session_state.milestone_catalog[selected_index] = updated_record
                        st.success("Milestone updated successfully.")
                        st.rerun()

    with manager_tabs[3]:
        if not st.session_state.milestone_catalog:
            st.info("No milestones available to remove.")
        else:
            remove_options = {f"{m['title']} ({m['id']})": m["id"] for m in st.session_state.milestone_catalog}
            remove_label = st.selectbox("Select milestone", list(remove_options.keys()), key="milestone_remove_select")
            remove_id = remove_options[remove_label]
            remove_index = next((idx for idx, m in enumerate(st.session_state.milestone_catalog) if m["id"] == remove_id), -1)
            remove_record = st.session_state.milestone_catalog[remove_index]
            remove_mode = st.radio(
                "Removal mode",
                ["Soft remove (archive/inactive)", "Hard delete (permanent)"],
                key="milestone_remove_mode",
            )

            if remove_id in st.session_state.milestone_claims:
                st.warning("This milestone has been claimed before.")

            confirm_remove = st.checkbox("I confirm this remove action.", key="milestone_remove_confirm")
            if st.button("Apply Remove", width="stretch", disabled=not confirm_remove):
                if remove_mode == "Soft remove (archive/inactive)":
                    remove_record["is_active"] = False
                    remove_record["updated_at"] = datetime.date.today().isoformat()
                    st.session_state.milestone_catalog[remove_index] = remove_record
                    st.success("Milestone archived successfully.")
                else:
                    st.session_state.milestone_catalog = [
                        m for m in st.session_state.milestone_catalog if m["id"] != remove_id
                    ]
                    if remove_id in st.session_state.milestone_claims:
                        del st.session_state.milestone_claims[remove_id]
                    st.success("Milestone deleted permanently.")
                st.rerun()

    with manager_tabs[4]:
        st.markdown("#### Export Milestone Settings")
        milestone_payload = {
            "milestone_version": st.session_state.milestone_version,
            "milestone_catalog": st.session_state.milestone_catalog,
            "milestone_claims": st.session_state.milestone_claims,
        }
        st.download_button(
            label="Download Milestone Settings JSON",
            data=json.dumps(milestone_payload, indent=2),
            file_name="rayyan_milestones.json",
            mime="application/json",
        )

        st.markdown("#### Import Milestone Settings")
        import_mode = st.radio("Import mode", ["Replace", "Merge by ID"], horizontal=True)
        import_claims = st.checkbox("Import claim history", value=True)
        uploaded_file = st.file_uploader("Upload milestone JSON", type=["json"], key="milestone_import_file")
        if st.button("Apply Import", width="stretch", type="primary"):
            if not uploaded_file:
                st.error("Please upload a JSON file first.")
            else:
                try:
                    payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
                    imported_catalog_raw = payload.get("milestone_catalog") if isinstance(payload, dict) else None
                    if imported_catalog_raw is None and isinstance(payload, list):
                        imported_catalog_raw = payload
                    imported_catalog = normalize_milestone_catalog(imported_catalog_raw)

                    if not imported_catalog:
                        st.error("No valid milestones found in file.")
                    else:
                        if import_mode == "Replace":
                            st.session_state.milestone_catalog = imported_catalog
                        else:
                            existing_map = {m["id"]: m for m in st.session_state.milestone_catalog}
                            for incoming in imported_catalog:
                                existing_map[incoming["id"]] = incoming
                            st.session_state.milestone_catalog = list(existing_map.values())

                        if import_claims and isinstance(payload, dict) and isinstance(payload.get("milestone_claims"), dict):
                            valid_ids = {m["id"] for m in st.session_state.milestone_catalog}
                            st.session_state.milestone_claims = {
                                k: v for k, v in payload["milestone_claims"].items() if k in valid_ids
                            }

                        if isinstance(payload, dict) and isinstance(payload.get("milestone_version"), int):
                            st.session_state.milestone_version = payload["milestone_version"]

                        st.success("Milestone settings imported successfully.")
                        st.rerun()
                except Exception as ex:
                    st.error(f"Import failed: {ex}")

    st.markdown("### 🛠️ Administration")
    export_payload = {
        "xp": st.session_state.xp,
        "streak": st.session_state.streak,
        "last_active_date": st.session_state.last_active_date,
        "last_inactivity_penalty_for_date": st.session_state.last_inactivity_penalty_for_date,
        "history": st.session_state.history,
        "last_blessing_claim": st.session_state.last_blessing_claim,
        "recent_praise": st.session_state.recent_praise,
        "memorized": st.session_state.memorized,
        "revised_dates": st.session_state.revised_dates,
        "assigned_surahs": st.session_state.assigned_surahs,
        "milestone_version": st.session_state.milestone_version,
        "milestone_catalog": st.session_state.milestone_catalog,
        "milestone_claims": st.session_state.milestone_claims,
    }

    st.download_button(
        label="Export Progress",
        data=json.dumps(export_payload, indent=2),
        file_name="rayyan_quran_tracker_export.json",
        mime="application/json",
    )

    st.markdown("#### Data Reset")
    st.caption("Reset progress while preserving Parents page configurations (assigned Surahs and milestone settings).")

    confirm_keep_parental = st.checkbox(
        "I confirm that I want to reset all progress but keep parental configurations.",
        key="confirm_keep_parental_reset",
    )
    if st.button(
        "Reset Progress (Keep Parental Configurations)",
        key="btn_keep_parental_reset",
        disabled=not confirm_keep_parental,
    ):
        reset_application_data(preserve_parental_config=True)
        st.success("Progress data has been reset. Parental configurations were preserved.")
        st.rerun()

    confirm_reset = st.checkbox(
        "I confirm that I want to reset all progress data.",
        key="confirm_full_reset",
    )
    if st.button("Reset Entire Application Data", key="btn_full_reset", disabled=not confirm_reset):
        reset_application_data(preserve_parental_config=False)
        st.success("Application data has been successfully reset!")
        st.rerun()


ensure_selection_state()
today = datetime.date.today()
apply_inactivity_penalty_if_needed(today)
current_level, level_title, surahs_completed, juz_completion_pct, total_ayahs_memorized = get_summary_metrics()

render_sidebar_profile(
    current_level,
    level_title,
    total_ayahs_memorized,
)
render_level_celebration()
selected_page = render_top_navigation()

if selected_page == "🏠 Dashboard":
    importlib.reload(dashboard_page)
    dashboard_page.render_dashboard_page(
        today,
        current_level,
        level_title,
        surahs_completed,
        juz_completion_pct,
        total_ayahs_memorized,
        len(SURAH_LIST),
        get_milestone_items,
    )
elif selected_page == "📖 Memorization & Revision":
    render_memorization_revision_page(today)
elif selected_page == "🏆 Achievements & Rewards":
    render_achievements_rewards_page(current_level, level_title, surahs_completed, juz_completion_pct, total_ayahs_memorized)
elif selected_page == "📜 Journal":
    render_journal_page()
elif selected_page == "⚙️ Parents":
    render_parents_page(total_ayahs_memorized)

# Persist state at the end of every successful script run.
save_app_state()
