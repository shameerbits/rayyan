import datetime
import html
import re
import textwrap

import streamlit as st

from game_scene_section import build_game_hero_scene_html


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


LEVEL_CHARACTER_MAP = {
1:  ("🚶", "First Steps"),
2:  ("🏃", "Fast Walker"),
3:  ("🛴", "Scooter Rider"),
4:  ("🚲", "Bicycle Explorer"),
5:  ("🏍️", "Mini Bike Rider"),
6:  ("🏎️", "Speed Racer"),
7:  ("🚗", "Road Adventurer"),
8:  ("🚙", "Trail Explorer"),
9:  ("🚓", "Journey Guardian"),
10: ("🚕", "City Navigator"),

11: ("🚚", "Knowledge Carrier"),
12: ("🚛", "Heavy Duty Learner"),
13: ("🚜", "Field Explorer"),
14: ("🏇", "Horse Champion"),
15: ("🚤", "River Voyager"),
16: ("⛵", "Sailing Seeker"),
17: ("🛥️", "Ocean Explorer"),
18: ("🚁", "Sky Rider"),
19: ("🛩️", "Cloud Navigator"),
20: ("✈️", "Air Adventurer"),

21: ("🪂", "Sky Jumper"),
22: ("🚀", "Rocket Cadet"),
23: ("🛰️", "Space Explorer"),
24: ("🌕", "Moon Traveler"),
25: ("🪐", "Planet Discoverer"),
26: ("⭐", "Star Collector"),
27: ("🌠", "Galaxy Runner"),
28: ("🎮", "Game Challenger"),
29: ("🕹️", "Level Grinder"),
30: ("👾", "Quest Hero"),

31: ("⚽", "Football Star"),
32: ("🏀", "Basketball Pro"),
33: ("🏈", "Team Captain"),
34: ("⚾", "Home Run Hero"),
35: ("🎾", "Tennis Ace"),
36: ("🏸", "Shuttle Master"),
37: ("🏓", "Ping Pong Expert"),
38: ("🥊", "Boxing Warrior"),
39: ("🥋", "Martial Champion"),
40: ("🏆", "Tournament Winner"),

41: ("🐎", "Swift Stallion"),
42: ("🦅", "Sky Eagle"),
43: ("🐆", "Speed Panther"),
44: ("🦍", "Power Gorilla"),
45: ("🦏", "Strong Rhino"),
46: ("🐘", "Wise Elephant"),
47: ("🦁", "Courageous Lion"),
48: ("🐉", "Legend Dragon"),
49: ("🦄", "Mythic Unicorn"),
50: ("👑", "King of Learning"),

51: ("🛡️", "Knowledge Guardian"),
52: ("⚔️", "Verse Defender"),
53: ("🏰", "Castle Keeper"),
54: ("🗺️", "Master Navigator"),
55: ("🧭", "Path Finder"),
56: ("💎", "Gem Collector"),
57: ("🌟", "Shining Star"),
58: ("🔥", "Legendary Learner"),
59: ("🏅", "Grand Champion"),
60: ("🕌", "Hafiz")
}


def get_journey_progress_percent(milestone_items):
    active_items = [item for item in milestone_items if item.get("is_active", True)]
    if not active_items:
        return 0.0

    completed_items = [item for item in active_items if item["state"] in {"claimed", "ready_to_claim"}]
    in_progress_items = [item for item in active_items if item["state"] == "in_progress"]

    partial_ratio = 0.0
    if in_progress_items:
        partial_ratio = max(
            (item["progress"] / item["target"]) if item["target"] else 0.0
            for item in in_progress_items
        )

    raw_percent = ((len(completed_items) + partial_ratio) / len(active_items)) * 100
    return max(0.0, min(100.0, raw_percent))


def get_journey_character(current_level):
    safe_level = max(1, min(60, int(current_level)))
    return LEVEL_CHARACTER_MAP.get(safe_level, LEVEL_CHARACTER_MAP[60])


def get_level_title(level):
    safe_level = max(1, min(MAX_LEVEL, int(level)))
    return LEVEL_TITLES.get(safe_level, "Hafiz")


def select_single_road_items(milestone_items):
    claimed_date_map = st.session_state.get("milestone_claims", {})

    def claim_sort_key(item):
        claim_date_str = str(claimed_date_map.get(item.get("id"), ""))
        try:
            claim_dt = datetime.date.fromisoformat(claim_date_str)
        except Exception:
            claim_dt = datetime.date.min
        return (
            claim_dt,
            item.get("target", 0),
            item.get("progress", 0),
            str(item.get("title", "")),
        )

    claimed_items = sorted(
        [item for item in milestone_items if item.get("state") == "claimed"],
        key=claim_sort_key,
        reverse=True,
    )

    ready_items = [
        item
        for item in milestone_items
        if item.get("is_active", True) and item.get("state") == "ready_to_claim"
    ]
    in_progress_items = [
        item
        for item in milestone_items
        if item.get("is_active", True) and item.get("state") == "in_progress"
    ]

    # Best achievable ordering: ready first, then closest in-progress milestones.
    ready_items = sorted(
        ready_items,
        key=lambda item: (
            item.get("target", 0),
            item.get("progress", 0),
            str(item.get("title", "")),
        ),
        reverse=True,
    )
    in_progress_items = sorted(
        in_progress_items,
        key=lambda item: (
            item.get("rank_score", 0.0),
            -item.get("eta_days", float("inf")),
            (item.get("progress", 0) / max(1, item.get("target", 1))),
            item.get("progress", 0),
            -max(0, item.get("target", 0) - item.get("progress", 0)),
            str(item.get("title", "")),
        ),
        reverse=True,
    )

    selected_items = []

    # Requested composition: up to 1 claimed + up to 3 ready + 2 best next milestones.
    selected_items.extend(claimed_items[:1])
    selected_items.extend(ready_items[:3])
    selected_items.extend(in_progress_items[:2])

    selected_ids = {item.get("id") for item in selected_items if item.get("id")}

    # If claimed/ready slots are missing, fill with next-best milestones.
    in_progress_fill = [item for item in in_progress_items if item.get("id") not in selected_ids]
    selected_items.extend(in_progress_fill[: max(0, 6 - len(selected_items))])
    selected_ids = {item.get("id") for item in selected_items if item.get("id")}

    # Final backfill to reach 6 using remaining ready/claimed if needed.
    if len(selected_items) < 6:
        ready_fill = [item for item in ready_items if item.get("id") not in selected_ids]
        selected_items.extend(ready_fill[: (6 - len(selected_items))])
        selected_ids = {item.get("id") for item in selected_items if item.get("id")}

    if len(selected_items) < 6:
        claimed_fill = [item for item in claimed_items if item.get("id") not in selected_ids]
        selected_items.extend(claimed_fill[: (6 - len(selected_items))])

    return selected_items[:6]


def format_target_label(item):
    goal_type = str(item.get("goal_type", ""))
    target = int(item.get("target", 1))
    if goal_type == "surahs_completed":
        return f"{target} Surah" if target == 1 else f"{target} Surahs"
    if goal_type == "ayahs_memorized":
        return f"{target} Ayah" if target == 1 else f"{target} Ayahs"
    if goal_type == "xp_total":
        return f"{target} XP Point" if target == 1 else f"{target} XP Points"
    if goal_type == "streak_days":
        return f"{target} Day" if target == 1 else f"{target} Days"
    if goal_type == "level_reached":
        return f"Level {target}"
    if goal_type == "juz_completion_pct":
        return f"{target}% Juz"
    return str(target)


def split_icon_and_title(raw_title):
    safe_title = str(raw_title or "Milestone").strip()
    if not safe_title:
        return "🎯", "Milestone"
    parts = safe_title.split(" ", 1)
    if len(parts) == 2 and any(ord(ch) > 127 for ch in parts[0]):
        return parts[0], parts[1].strip()
    return "🎯", safe_title


def build_journey_boards_html(row_items):
    if not row_items:
        return ""

    board_html = []
    for item in row_items:
        title_text = str(item.get("title", "Milestone")).strip() or "Milestone"
        reward_text = str(item.get("reward", "Reward"))
        goal_text = format_target_label(item)

        state = item.get("state", "in_progress")
        state_class = "state-progress"
        if state == "claimed":
            state_class = "state-claimed"
        elif state == "ready_to_claim":
            state_class = "state-ready"
        elif state == "locked":
            state_class = "state-locked"

        board_html.append(
            f"<div class=\"road-board {state_class}\">"
            f"<div class=\"board-status-dot\" aria-hidden=\"true\"></div>"
            f"<p class=\"board-title\">{html.escape(title_text)}</p>"
            f"<p class=\"board-reward\">{html.escape(reward_text)}</p>"
            f"<p class=\"board-goal\">{html.escape(goal_text)}</p>"
            f"</div>"
        )
    return "".join(board_html)


def build_last_30_day_trend_rows(today):
    start_date = today - datetime.timedelta(days=29)
    day_map = {}
    for day_offset in range(30):
        day_obj = start_date + datetime.timedelta(days=day_offset)
        day_map[day_obj.isoformat()] = {
            "date": day_obj,
            "ayahs_memorized": 0,
            "ayahs_revised": 0,
        }

    for event in st.session_state.history:
        event_date_str = event.get("date", "")
        if event_date_str not in day_map:
            continue

        activity = event.get("activity", "")
        details = str(event.get("details", ""))
        if activity == "Memorization":
            ayah_matches = re.findall(r"\d+", details)
            ayah_count = len(ayah_matches)
            if ayah_count == 0:
                ayah_count = 1
            day_map[event_date_str]["ayahs_memorized"] += ayah_count
        elif activity == "Revision":
            ayah_matches = re.findall(r"\d+", details)
            ayah_count = len(ayah_matches)
            if ayah_count == 0:
                ayah_count = 1
            day_map[event_date_str]["ayahs_revised"] += ayah_count

    rows = []
    for day_offset in range(30):
        day_obj = start_date + datetime.timedelta(days=day_offset)
        day_key = day_obj.isoformat()
        rows.append(
            {
                "date_iso": day_key,
                "date_label": day_obj.strftime("%m-%d"),
                "Ayahs Memorized": day_map[day_key]["ayahs_memorized"],
                "Ayahs Revised": day_map[day_key]["ayahs_revised"],
            }
        )
    return rows


def render_dashboard_page(
    today,
    current_level,
    level_title,
    surahs_completed,
    juz_completion_pct,
    total_ayahs_memorized,
    total_surah_count,
    get_milestone_items,
):
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&display=swap');

        .game-dashboard-wrap { display: grid; gap: 14px; }
        .game-hero {
            position: relative;
            border-radius: 26px;
            border: 2px solid #d7e8fc;
            overflow: hidden;
            background: linear-gradient(175deg, #f8fcff 0%, #f4f9ff 50%, #fffaf1 100%);
            box-shadow: 0 18px 36px rgba(34, 62, 98, 0.14);
        }
        .scene-map-header {
            position: absolute;
            top: 14px;
            left: 14px;
            right: 14px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
            z-index: 11;
            pointer-events: none;
        }
        .scene-map-title-wrap {
            max-width: min(78%, 760px);
            border: none;
            background: transparent;
            box-shadow: none;
            padding: 0;
        }
        .scene-map-title {
            margin: 0;
            color: #f5fbff;
            text-shadow: 0 2px 8px rgba(10, 31, 52, 0.55);
            font-size: clamp(1.1rem, 0.9rem + 0.8vw, 1.5rem);
            font-weight: 900;
            line-height: 1.15;
        }
        .scene-map-subtitle {
            margin: 5px 0 0 0;
            color: #e6f2ff;
            text-shadow: 0 1px 6px rgba(10, 31, 52, 0.45);
            font-size: clamp(0.76rem, 0.68rem + 0.36vw, 0.93rem);
            font-weight: 700;
            line-height: 1.32;
        }
        .game-level-badge {
            min-width: 180px;
            border-radius: 20px;
            border: 2px solid #f2cc79;
            background: linear-gradient(165deg, #fff8de 0%, #ffe8a6 46%, #f0c76f 100%);
            box-shadow: inset 0 2px 8px rgba(255, 255, 255, 0.5), 0 12px 22px rgba(117, 84, 30, 0.25);
            padding: 10px 14px;
            text-align: center;
            position: relative;
        }
        .game-level-badge::before {
            content: "★";
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            color: #f0a911;
            font-size: 1rem;
        }
        .game-level-icon { margin: 0; font-size: 1.15rem; }
        .game-level-number { margin: 2px 0 0 0; font-size: 1.45rem; color: #6a4509; font-weight: 900; }
        .game-level-name { margin: 2px 0 0 0; font-size: 0.82rem; color: #7a5315; font-weight: 800; }
        .scene-map-ready-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            border: 1px solid #efc26e;
            background: linear-gradient(180deg, rgba(255, 246, 226, 0.93) 0%, rgba(255, 236, 191, 0.9) 100%);
            color: #7a4f18;
            font-size: 0.74rem;
            font-weight: 900;
            padding: 6px 11px;
            box-shadow: 0 6px 14px rgba(109, 79, 31, 0.2);
            white-space: nowrap;
        }

        .game-scene {
            position: relative;
            height: var(--scene-height, 470px);
            border-top: 1px solid rgba(170, 142, 76, 0.3);
            background:
                radial-gradient(92% 58% at 16% 18%, rgba(206, 228, 242, 0.18) 0%, rgba(206, 228, 242, 0) 58%),
                radial-gradient(120% 75% at 86% 10%, rgba(255, 211, 132, 0.22) 0%, rgba(255, 211, 132, 0) 56%),
                linear-gradient(180deg, #97b9cf 0%, #bed3e1 34%, #9aaea2 55%, #88a772 71%, #7aa260 100%);
            animation: gameSkyShift 24s ease-in-out infinite alternate;
            overflow: hidden;
            isolation: isolate;
        }
        .game-scene::before {
            content: "";
            position: absolute;
            left: -10%;
            right: -10%;
            bottom: 124px;
            height: 162px;
            background:
                radial-gradient(72% 94% at 12% 100%, rgba(58, 84, 72, 0.58) 0%, rgba(58, 84, 72, 0) 72%),
                radial-gradient(74% 98% at 48% 100%, rgba(52, 77, 67, 0.62) 0%, rgba(52, 77, 67, 0) 74%),
                radial-gradient(70% 96% at 86% 100%, rgba(57, 82, 70, 0.6) 0%, rgba(57, 82, 70, 0) 73%);
            opacity: 0.88;
            z-index: 0;
            pointer-events: none;
            animation: gameHillDrift 22s ease-in-out infinite alternate;
        }
        .game-scene::after {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(122% 28% at 50% 49%, rgba(232, 245, 255, 0) 0%, rgba(232, 245, 255, 0.34) 45%, rgba(232, 245, 255, 0) 70%),
                radial-gradient(132% 104% at 50% 130%, rgba(24, 38, 28, 0.24) 0%, rgba(24, 38, 28, 0) 58%),
                radial-gradient(118% 90% at -10% 4%, rgba(21, 29, 43, 0.2) 0%, rgba(21, 29, 43, 0) 52%),
                radial-gradient(118% 90% at 110% 4%, rgba(21, 29, 43, 0.2) 0%, rgba(21, 29, 43, 0) 52%);
            z-index: 0;
            pointer-events: none;
            animation: gameMistFloat 14s ease-in-out infinite;
        }
        .scene-daycycle {
            position: absolute;
            inset: 0;
            z-index: 1;
            pointer-events: none;
            background:
                radial-gradient(72% 54% at 88% 12%, rgba(255, 216, 148, 0.22) 0%, rgba(255, 216, 148, 0) 62%),
                linear-gradient(180deg, rgba(255, 197, 129, 0.08) 0%, rgba(255, 197, 129, 0.02) 35%, rgba(63, 123, 116, 0.07) 100%);
            mix-blend-mode: soft-light;
            animation: gameDayCycle 28s ease-in-out infinite;
        }
        .scene-grain {
            position: absolute;
            inset: 0;
            z-index: 2;
            pointer-events: none;
            opacity: 0.04;
            background-image:
                radial-gradient(rgba(30, 40, 52, 0.55) 0.45px, transparent 0.45px),
                radial-gradient(rgba(240, 246, 255, 0.5) 0.35px, transparent 0.35px);
            background-size: 3px 3px, 5px 5px;
            background-position: 0 0, 1px 2px;
            animation: gameGrainShift 1.4s steps(2) infinite;
        }
        .scene-sun {
            position: absolute;
            right: 11%;
            top: 24px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: radial-gradient(circle at 32% 30%, #fff6d2 0%, #ffd681 52%, #f8ae2a 100%);
            box-shadow: 0 0 0 7px rgba(255, 208, 110, 0.3), 0 0 0 16px rgba(255, 219, 140, 0.17);
            z-index: 3;
            animation: gameSunGlow 16s ease-in-out infinite;
        }
        .scene-cloud-layer {
            position: absolute;
            left: -24%;
            right: -24%;
            pointer-events: none;
            z-index: 2;
        }
        .scene-cloud-layer.far {
            top: 42px;
            height: 52px;
            opacity: 0.42;
            filter: blur(1.8px);
            animation: gameCloudDriftFar 62s linear infinite;
        }
        .scene-cloud-layer.mid {
            top: 82px;
            height: 74px;
            opacity: 0.5;
            filter: blur(1px);
            animation: gameCloudDriftMid 42s linear infinite;
        }
        .scene-cloud {
            position: absolute;
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(247, 252, 255, 0.88) 0%, rgba(229, 240, 248, 0.64) 100%);
            box-shadow: inset 0 -8px 14px rgba(191, 211, 224, 0.28);
        }
        .scene-cloud::before,
        .scene-cloud::after {
            content: "";
            position: absolute;
            border-radius: 999px;
            background: rgba(242, 250, 255, 0.86);
        }
        .scene-cloud::before {
            width: 44%;
            height: 120%;
            left: 14%;
            bottom: 35%;
        }
        .scene-cloud::after {
            width: 36%;
            height: 95%;
            right: 14%;
            bottom: 30%;
        }
        .scene-cloud.c1 { width: 132px; height: 36px; top: 2px; left: 8%; }
        .scene-cloud.c2 { width: 112px; height: 30px; top: 14px; left: 39%; }
        .scene-cloud.c3 { width: 124px; height: 34px; top: 8px; left: 70%; }
        .scene-cloud.c4 { width: 174px; height: 48px; top: 6px; left: 16%; }
        .scene-cloud.c5 { width: 142px; height: 40px; top: 18px; left: 54%; }

        .scene-bird-lane {
            position: absolute;
            left: -22%;
            right: -22%;
            top: 96px;
            height: 86px;
            pointer-events: none;
            z-index: 4;
            animation: gameBirdLane 26s linear infinite;
        }
        .scene-bird {
            position: absolute;
            width: 14px;
            height: 7px;
            opacity: 0.74;
            transform-origin: center;
            --bird-scale: 1;
            animation: gameBirdFlap 1.1s ease-in-out infinite;
        }
        .scene-bird::before,
        .scene-bird::after {
            content: "";
            position: absolute;
            width: 8px;
            height: 2px;
            top: 2px;
            background: rgba(40, 56, 70, 0.58);
            border-radius: 2px;
        }
        .scene-bird::before { left: 0; transform: rotate(26deg); transform-origin: right center; }
        .scene-bird::after { right: 0; transform: rotate(-26deg); transform-origin: left center; }
        .scene-bird.b1 { left: 12%; top: 20px; }
        .scene-bird.b2 { left: 20%; top: 8px; --bird-scale: 0.9; animation-delay: 0.22s; }
        .scene-bird.b3 { left: 27%; top: 28px; --bird-scale: 0.8; animation-delay: 0.44s; }
        .scene-bird.b4 { left: 72%; top: 18px; --bird-scale: 0.92; animation-delay: 0.14s; }
        .scene-bird.b5 { left: 79%; top: 30px; --bird-scale: 0.78; animation-delay: 0.36s; }

        .scene-ridge {
            position: absolute;
            left: -6%;
            right: -6%;
            bottom: 186px;
            height: 102px;
            background:
                radial-gradient(62% 120% at 14% 100%, rgba(64, 87, 102, 0.44) 0%, rgba(64, 87, 102, 0) 72%),
                radial-gradient(58% 130% at 48% 100%, rgba(57, 79, 94, 0.48) 0%, rgba(57, 79, 94, 0) 74%),
                radial-gradient(56% 125% at 82% 100%, rgba(61, 84, 99, 0.46) 0%, rgba(61, 84, 99, 0) 73%);
            z-index: 2;
            pointer-events: none;
        }
        .scene-ridge::after {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 14px;
            height: 44px;
            background: linear-gradient(180deg, rgba(233, 244, 252, 0.18) 0%, rgba(233, 244, 252, 0) 100%);
            filter: blur(5px);
            opacity: 0.7;
        }

        .scene-foreground {
            position: absolute;
            left: -8%;
            right: -8%;
            bottom: 108px;
            height: 84px;
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(170, 200, 136, 0.7) 0%, rgba(124, 166, 97, 0.78) 100%);
            box-shadow: inset 0 8px 14px rgba(102, 138, 76, 0.22);
            filter: blur(0.6px);
            z-index: 4;
            pointer-events: none;
        }
        .scene-fence {
            position: absolute;
            left: 4%;
            right: 4%;
            bottom: 146px;
            height: 34px;
            z-index: 5;
            pointer-events: none;
        }
        .scene-fence::before {
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 15px;
            height: 1px;
            background: repeating-linear-gradient(90deg, rgba(95, 76, 48, 0.45) 0 14px, rgba(95, 76, 48, 0) 14px 46px);
        }


        .game-road-layout {
            position: absolute;
            left: 4%;
            right: 4%;
            bottom: 40px;
            height: 118px;
            z-index: 4;
            pointer-events: none;
        }
        .road-strip {
            position: absolute;
            left: 0;
            right: 0;
            height: 98px;
            border-radius: 999px;
            border: 2px solid rgba(106, 74, 50, 0.38);
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.10), rgba(0, 0, 0, 0.10)),
                linear-gradient(90deg, #8f6c56 0%, #a27e66 38%, #b18a70 100%);
            box-shadow: inset 0 10px 18px rgba(0, 0, 0, 0.2), 0 6px 14px rgba(52, 36, 22, 0.2);
        }
        .road-strip.single { top: 10px; }
        .road-strip::before {
            content: "";
            position: absolute;
            left: 5%;
            right: 5%;
            top: 50%;
            height: 3px;
            transform: translateY(-50%);
            background: repeating-linear-gradient(90deg, #fff2c1 0 18px, transparent 18px 31px);
            opacity: 0.92;
            animation: gameRoadDashFlow 1.2s linear infinite;
        }
        .road-row {
            position: absolute;
            left: 0;
            right: 0;
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 10px;
            z-index: 6;
            padding: 0;
            justify-items: center;
        }
        .road-row.single { top: -92px; }

        .road-board {
            position: relative;
            border-radius: 12px;
            border: 2px solid #bfd7f6;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 8px 14px rgba(21, 54, 88, 0.18);
            padding: 8px 10px;
            min-height: 86px;
            width: 100%;
            max-width: none;
            text-align: center;
        }
        .road-board::after {
            content: "";
            position: absolute;
            left: 50%;
            bottom: -24px;
            width: 6px;
            height: 24px;
            transform: translateX(-50%);
            background: #8e673e;
            border-radius: 2px;
        }
        .board-status-dot {
            position: absolute;
            top: 8px;
            right: 8px;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #60a5fa;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
        }
        .board-title {
            margin: 8px 18px 0 8px;
            font-size: 12px;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 800;
            color: #173e66;
            line-height: 1.25;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .board-reward {
            margin: 8px 0 0 0;
            font-size: 12px;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 700;
            color: #35608b;
            line-height: 1.25;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .board-goal {
            margin: 3px 0 0 0;
            font-size: 12px;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 700;
            color: #153c62;
            line-height: 1.25;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .road-board.state-claimed { border-color: #7fd2bc; background: rgba(255, 255, 255, 0.8); }
        .road-board.state-ready { border-color: #ffcd83; background: rgba(255, 255, 255, 0.84); box-shadow: 0 8px 16px rgba(250, 189, 80, 0.18); }
        .road-board.state-progress { border-color: #97c4fa; background: rgba(255, 255, 255, 0.78); }
        .road-board.state-locked { border-color: #cfd5dd; background: rgba(255, 255, 255, 0.72); }
        .road-board.state-claimed .board-status-dot { background: #34d399; }
        .road-board.state-ready .board-status-dot { background: #fbbf24; animation: gamePulse 1.8s ease-in-out infinite; }
        .road-board.state-progress .board-status-dot { background: #60a5fa; }
        .road-board.state-locked .board-status-dot { background: #9ca3af; }

        .game-rider {
            position: absolute;
            left: var(--rider-target, 18%);
            top: var(--rider-top, 67%);
            transform: translate(-50%, -50%) scaleX(-1);
            font-size: 6.05rem;
            z-index: 9;
            animation: gameRiderEntry 1.2s ease-out both, gameRiderFloat 0.52s ease-in-out 1.2s infinite alternate;
        }

        .game-cards { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 12px; }
        .game-card {
            border-radius: 18px;
            border: 1px solid #dce8f6;
            background: linear-gradient(165deg, #ffffff 0%, #f4f9ff 100%);
            box-shadow: 0 12px 24px rgba(34, 61, 95, 0.1);
            padding: 14px;
            min-height: 132px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .game-card:hover,
        .game-highlight:hover,
        .game-progress-card:hover,
        .game-motivation:hover {
            transform: translateY(-3px);
            box-shadow: 0 16px 28px rgba(24, 49, 81, 0.16);
        }
        .game-card.t1 { background: linear-gradient(165deg, #e7f4ff 0%, #f2f9ff 100%); border-color: #b8dbff; }
        .game-card.t2 { background: linear-gradient(165deg, #f2eaff 0%, #f7f3ff 100%); border-color: #d0befa; }
        .game-card.t3 { background: linear-gradient(165deg, #fff0e3 0%, #fff6ef 100%); border-color: #ffd3ae; }
        .game-card.t4 { background: linear-gradient(165deg, #ebfaed 0%, #f4fdf5 100%); border-color: #bae5c0; }
        .game-card.t5 { background: linear-gradient(165deg, #e9f2ff 0%, #f2f7ff 100%); border-color: #bfd2fa; }
        .game-card.t6 { background: linear-gradient(165deg, #fff6dc 0%, #fffaf0 100%); border-color: #f4d393; }
        .game-card-head { margin: 0; font-size: 0.83rem; font-weight: 900; color: #3d6186; }
        .game-card-icon { font-size: 2rem; line-height: 1; margin-top: 6px; }
        .game-card-value { margin: 7px 0 0 0; color: #183e63; font-size: clamp(1.35rem, 1rem + 1vw, 2rem); font-weight: 900; line-height: 1.1; }
        .game-card-sub { margin: 4px 0 0 0; color: #3b638a; font-size: 0.86rem; font-weight: 700; }
        .game-highlights { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 12px; }
        .game-highlight {
            border-radius: 20px;
            border: 1px solid #d7e5f6;
            background: linear-gradient(160deg, #ffffff 0%, #f7fbff 100%);
            box-shadow: 0 12px 22px rgba(35, 62, 95, 0.1);
            padding: 16px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .game-highlight-label { margin: 0; color: #4d6f90; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }
        .game-highlight-value { margin: 8px 0 0 0; color: #173a5f; font-weight: 900; font-size: clamp(1.3rem, 1rem + 0.9vw, 2rem); line-height: 1.15; }
        .game-progress-card {
            border-radius: 22px;
            border: 1px solid #d8e5f6;
            background: linear-gradient(165deg, #ffffff 0%, #f5faff 58%, #fff8e7 100%);
            box-shadow: 0 14px 24px rgba(35, 62, 95, 0.12);
            padding: 16px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .game-progress-title { margin: 0; color: #17395e; font-size: 1.02rem; font-weight: 900; }
        .game-progress-track {
            margin-top: 11px;
            position: relative;
            height: 17px;
            border-radius: 999px;
            border: 1px solid #b8d1ee;
            overflow: hidden;
            background: linear-gradient(180deg, #e7f2ff 0%, #dbe9fa 100%);
        }
        .game-progress-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #46b0ff 0%, #478eff 56%, #f7b45f 100%);
        }
        .game-progress-star {
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 1rem;
        }
        .game-progress-grid {
            margin-top: 12px;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
        }
        .game-progress-stat {
            border-radius: 12px;
            border: 1px solid #d9e7f6;
            background: #ffffff;
            padding: 9px;
        }
        .game-progress-stat-label { margin: 0; color: #5f7d9a; font-size: 0.68rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
        .game-progress-stat-value { margin: 4px 0 0 0; color: #173c62; font-size: 1.01rem; font-weight: 900; line-height: 1.2; }
        .game-motivation {
            border-radius: 22px;
            border: 1px solid #e2d1a9;
            background: linear-gradient(160deg, #fff8e8 0%, #fff4dc 44%, #f3f8ff 100%);
            box-shadow: 0 14px 26px rgba(80, 63, 32, 0.14);
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .game-motivation-title { margin: 0; color: #173c62; font-size: 1.25rem; font-weight: 900; }
        .game-motivation-quote { margin: 7px 0 0 0; color: #345e84; font-size: 0.93rem; font-weight: 700; line-height: 1.45; }
        .game-motivation-source { margin: 6px 0 0 0; color: #6e4f1e; font-size: 0.82rem; font-weight: 800; }
        .game-motivation-art { font-size: 2.2rem; opacity: 0.92; }

        @keyframes gameSkyShift { 0% { filter: saturate(0.95) brightness(0.98); } 100% { filter: saturate(1.04) brightness(1.03); } }
        @keyframes gameDayCycle {
            0%, 100% { opacity: 0.74; filter: hue-rotate(0deg); }
            50% { opacity: 0.96; filter: hue-rotate(-14deg); }
        }
        @keyframes gameSunGlow {
            0%, 100% { transform: scale(1); opacity: 0.88; }
            50% { transform: scale(1.05); opacity: 1; }
        }
        @keyframes gameCloudDriftFar { 0% { transform: translateX(0); } 100% { transform: translateX(28%); } }
        @keyframes gameCloudDriftMid { 0% { transform: translateX(0); } 100% { transform: translateX(42%); } }
        @keyframes gameBirdLane { 0% { transform: translateX(0); } 100% { transform: translateX(48%); } }
        @keyframes gameBirdFlap {
            0%, 100% { transform: translateY(0) scale(var(--bird-scale)); opacity: 0.72; }
            50% { transform: translateY(-2px) scale(calc(var(--bird-scale) * 1.06)); opacity: 0.86; }
        }
        @keyframes gameHillDrift { 0% { transform: translateX(0); } 100% { transform: translateX(3.8%); } }
        @keyframes gameMistFloat { 0%, 100% { transform: translateX(0); opacity: 0.66; } 50% { transform: translateX(1.6%); opacity: 0.86; } }
        @keyframes gameGrainShift {
            0% { transform: translate(0, 0); }
            50% { transform: translate(-0.6px, 0.6px); }
            100% { transform: translate(0.4px, -0.4px); }
        }
        @keyframes gameRoadDashFlow { 0% { background-position: 0 0; } 100% { background-position: -62px 0; } }
        @keyframes gameRiderEntry {
            0% { left: var(--rider-start, 8%); opacity: 0.2; }
            60% { opacity: 1; }
            100% { left: var(--rider-target, 18%); opacity: 1; }
        }
        @keyframes gameRiderFloat { 0% { transform: translate(-50%, -50%) scaleX(-1) translateY(0); } 100% { transform: translate(-50%, -50%) scaleX(-1) translateY(-4px); } }
        @keyframes gamePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }

        @media (max-width: 1200px) {
            .game-cards { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .game-highlights { grid-template-columns: 1fr 1fr; }
            .road-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        }
        @media (max-width: 900px) {
            .game-scene { height: 600px; }
            .game-cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .game-highlights { grid-template-columns: 1fr; }
            .game-motivation { flex-direction: column; align-items: flex-start; }
            .game-road-layout { height: 150px; }
            .road-strip.single { height: 130px; top: 10px; }
            .road-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .scene-map-header { flex-direction: column; align-items: flex-start; }
            .scene-map-title-wrap { max-width: 100%; }
        }
        @media (max-width: 640px) {
            .game-cards { grid-template-columns: 1fr; }
            .game-progress-grid { grid-template-columns: 1fr; }
            .game-level-badge { width: 100%; }
            .game-scene { height: 740px; }
            .game-road-layout { height: 220px; }
            .road-strip.single { height: 200px; top: 10px; }
            .road-row { grid-template-columns: 1fr; }
            .scene-map-header { top: 10px; left: 10px; right: 10px; }
            .scene-map-title { font-size: 1rem; }
            .scene-map-subtitle { font-size: 0.73rem; }
            .scene-map-ready-chip { font-size: 0.7rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if current_level >= MAX_LEVEL:
        level_progress_percent = 100.0
        ayahs_remaining = 0
        ayahs_memorized_this_level = AYAHS_PER_LEVEL
    else:
        ayahs_memorized_this_level = total_ayahs_memorized % AYAHS_PER_LEVEL
        level_progress_percent = (ayahs_memorized_this_level / AYAHS_PER_LEVEL) * 100
        ayahs_remaining = AYAHS_PER_LEVEL - ayahs_memorized_this_level

    milestone_items = get_milestone_items(
        current_level,
        surahs_completed,
        juz_completion_pct,
        total_ayahs_memorized,
    )

    active_road_items = [item for item in milestone_items if item.get("is_active", True)]
    road_selection_items = milestone_items[:] if milestone_items else active_road_items

    single_road_items = select_single_road_items(road_selection_items)
    ready_items = [item for item in active_road_items if item["state"] == "ready_to_claim"]
    in_progress_items = [item for item in active_road_items if item["state"] == "in_progress"]
    journey_progress_pct = get_journey_progress_percent(milestone_items)

    character_icon = get_journey_character(current_level)[0]
    character_mode = get_journey_character(current_level)[1]
    rider_top = "76%"
    rider_target = 8 + (level_progress_percent / 100.0) * 84

    single_boards_html = build_journey_boards_html(single_road_items)
    longest_card_text = 0
    for item in single_road_items:
        reward_text = str(item.get("reward", "Reward"))
        goal_text = format_target_label(item)
        longest_card_text = max(longest_card_text, len(reward_text), len(goal_text), len(f"{reward_text} {goal_text}"))

    scene_height_px = 470
    if longest_card_text >= 28:
        scene_height_px = 520
    if longest_card_text >= 40:
        scene_height_px = 560

    next_level = min(MAX_LEVEL, current_level + 1)
    next_level_title = get_level_title(next_level)
    progress_marker = max(2.0, min(98.0, level_progress_percent))
    hero_scene_html = build_game_hero_scene_html(
        character_mode=character_mode,
        level_progress_percent=level_progress_percent,
        ready_rewards_count=len(ready_items),
        single_boards_html=single_boards_html,
        rider_target=rider_target,
        rider_top=rider_top,
        scene_height_px=scene_height_px,
        character_icon=character_icon,
    )

    dashboard_html = textwrap.dedent(
        f"""
        <div class="game-dashboard-wrap">
            {hero_scene_html}

            <div class="game-cards">
                <div class="game-card t1">
                    <p class="game-card-head">Current Level</p>
                    <div class="game-card-icon">🎓</div>
                    <p class="game-card-value">{current_level}</p>
                    <p class="game-card-sub">{html.escape(level_title)}</p>
                </div>

                <div class="game-card t2">
                    <p class="game-card-head">XP Points</p>
                    <div class="game-card-icon">⭐</div>
                    <p class="game-card-value">{st.session_state.xp}</p>
                    <p class="game-card-sub">Keep earning!</p>
                </div>

                <div class="game-card t3">
                    <p class="game-card-head">Current Streak</p>
                    <div class="game-card-icon">🔥</div>
                    <p class="game-card-value">{st.session_state.streak}</p>
                    <p class="game-card-sub">Keep it going!</p>
                </div>

                <div class="game-card t4">
                    <p class="game-card-head">Surahs Completed</p>
                    <div class="game-card-icon">📖</div>
                    <p class="game-card-value">{surahs_completed}/{total_surah_count}</p>
                    <p class="game-card-sub">You're doing great!</p>
                </div>

                <div class="game-card t5">
                    <p class="game-card-head">Total Ayahs Memorized</p>
                    <div class="game-card-icon">📚</div>
                    <p class="game-card-value">{total_ayahs_memorized}</p>
                    <p class="game-card-sub">MashaAllah!</p>
                </div>

                <div class="game-card t6">
                    <p class="game-card-head">Ayahs to Next Level</p>
                    <div class="game-card-icon">🎯</div>
                    <p class="game-card-value">{ayahs_remaining}</p>
                    <p class="game-card-sub">Keep climbing!</p>
                </div>
            </div>

            <div class="game-progress-card">
                <p class="game-progress-title">Level Progress</p>
                <div class="game-progress-track">
                    <div class="game-progress-fill" style="width:{level_progress_percent:.1f}%;"></div>
                    <div class="game-progress-star" style="left:{progress_marker:.1f}%">⭐</div>
                </div>
                <div class="game-progress-grid">
                    <div class="game-progress-stat">
                        <p class="game-progress-stat-label">Ayahs Memorized</p>
                        <p class="game-progress-stat-value">{ayahs_memorized_this_level} / {AYAHS_PER_LEVEL}</p>
                    </div>
                    <div class="game-progress-stat">
                        <p class="game-progress-stat-label">Ayahs Remaining</p>
                        <p class="game-progress-stat-value">{ayahs_remaining}</p>
                    </div>
                    <div class="game-progress-stat">
                        <p class="game-progress-stat-label">Progress</p>
                        <p class="game-progress-stat-value">{level_progress_percent:.1f}% Complete</p>
                    </div>
                    <div class="game-progress-stat">
                        <p class="game-progress-stat-label">Next Level Title</p>
                        <p class="game-progress-stat-value">{html.escape(next_level_title)}</p>
                    </div>
                </div>
            </div>

            <div class="game-motivation">
                <div>
                    <p class="game-motivation-title">Keep Going, Rayyan!</p>
                    <p class="game-motivation-quote">"Read the Qur'an, for it will come as an intercessor for its companions on the Day of Resurrection."</p>
                    <p class="game-motivation-source">(Sahih Muslim)</p>
                </div>
                <div class="game-motivation-art">📖✨</div>
            </div>
        </div>
        """
    ).strip()

    dashboard_html = "\n".join(line.lstrip() for line in dashboard_html.splitlines())
    st.markdown(dashboard_html, unsafe_allow_html=True)

    if ready_items:
        if st.button("Open Achievements to Claim Rewards", width="stretch", type="primary"):
            st.session_state.nav_section = "🏆 Achievements & Rewards"
            st.rerun()

    if in_progress_items:
        next_focus = max(
            in_progress_items,
            key=lambda item: (
                item.get("rank_score", 0.0),
                (item["progress"] / item["target"]) if item["target"] else 0,
            ),
        )
        remaining = max(0, next_focus["target"] - next_focus["progress"])
        st.info(
            f"Next focus: {next_focus['title']} | Remaining: {remaining} | Reward: {next_focus['reward']}"
        )
    else:
        st.success("All active milestones are complete. Open Achievements & Rewards to claim pending gifts.")

