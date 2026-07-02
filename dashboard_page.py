import datetime
import html
import re
import textwrap

import streamlit as st

from game_scene_section import build_game_hero_scene_html


AYAHS_PER_LEVEL = 26
MAX_LEVEL = 60
RESPONSIVE_TIERS = {"phone", "tablet", "laptop"}


def normalize_ui_tier(ui_tier):
    safe_tier = str(ui_tier or "laptop").lower().strip()
    if safe_tier not in RESPONSIVE_TIERS:
        return "laptop"
    return safe_tier


def pick_tier_value(ui_tier, phone_value, tablet_value, laptop_value):
    safe_tier = normalize_ui_tier(ui_tier)
    if safe_tier == "phone":
        return phone_value
    if safe_tier == "tablet":
        return tablet_value
    return laptop_value

LEVEL_TITLES = {
    1: "First Step",
    2: "Young Explorer",
    3: "Little Learner",
    4: "Verse Finder",
    5: "Ayah Explorer",
    6: "Beginner",
    7: "Path Walker",
    8: "Faith Starter",
    9: "Learning Heart",
    10: "Growing Student",
    11: "Verse Collector",
    12: "Quran Seeker",
    13: "Knowledge Seeker",
    14: "Steady Learner",
    15: "Young Reciter",
    16: "Memorization Scout",
    17: "Hopeful Student",
    18: "Faith Builder",
    19: "Dedicated Learner",
    20: "Foundation Builder",

    21: "Ayah Apprentice",
    22: "Verse Apprentice",
    23: "Knowledge Apprentice",
    24: "Learning Adventurer",
    25: "Quran Adventurer",
    26: "Rising Student",
    27: "Growing Memorizer",
    28: "Verse Hunter",
    29: "Ayah Hunter",
    30: "Steady Memorizer",
    31: "Dedicated Student",
    32: "Faithful Reciter",
    33: "Verse Guardian",
    34: "Quran Companion",
    35: "Wisdom Builder",
    36: "Knowledge Builder",
    37: "Verse Protector",
    38: "Ayah Protector",
    39: "Focused Student",
    40: "Committed Learner",

    41: "Disciplined Memorizer",
    42: "Verse Champion",
    43: "Ayah Champion",
    44: "Quran Champion",
    45: "Trusted Student",
    46: "Knowledge Guardian",
    47: "Faith Guardian",
    48: "Verse Keeper",
    49: "Ayah Keeper",
    50: "Quran Keeper",
    51: "Wisdom Keeper",
    52: "Light Seeker",
    53: "Path Guardian",
    54: "Dedicated Reciter",
    55: "Strong Memorizer",
    56: "Elite Student",
    57: "Verse Defender",
    58: "Ayah Defender",
    59: "Knowledge Defender",
    60: "Noble Learner",

    61: "Rising Guardian",
    62: "Light Bearer",
    63: "Faith Bearer",
    64: "Verse Bearer",
    65: "Ayah Bearer",
    66: "Quran Steward",
    67: "Trusted Guardian",
    68: "Wisdom Carrier",
    69: "Noble Reciter",
    70: "Distinguished Student",
    71: "Master Learner",
    72: "Master Reciter",
    73: "Master Memorizer",
    74: "Verse Master",
    75: "Ayah Master",
    76: "Quran Pathfinder",
    77: "Path Illuminator",
    78: "Guided Soul",
    79: "Steadfast Guardian",
    80: "Respected Student",

    81: "Elite Memorizer",
    82: "Elite Guardian",
    83: "Elite Reciter",
    84: "Verse Commander",
    85: "Ayah Commander",
    86: "Knowledge Commander",
    87: "Guardian of Light",
    88: "Guardian of Wisdom",
    89: "Guardian of Faith",
    90: "Guardian of Verses",
    91: "Guardian of Ayahs",
    92: "Champion of Learning",
    93: "Champion of Faith",
    94: "Champion of Wisdom",
    95: "Champion of Verses",
    96: "Champion of Ayahs",
    97: "Champion Memorizer",
    98: "Champion Reciter",
    99: "Champion Guardian",
    100: "Quran Champion",

    101: "Noble Guardian",
    102: "Sacred Keeper",
    103: "Keeper of Light",
    104: "Keeper of Wisdom",
    105: "Keeper of Faith",
    106: "Keeper of Verses",
    107: "Keeper of Ayahs",
    108: "Keeper of Revelation",
    109: "Light Guardian",
    110: "Wisdom Guardian",
    111: "Faith Protector",
    112: "Verse Protector",
    113: "Ayah Protector",
    114: "Noble Protector",
    115: "Trusted Protector",
    116: "Sacred Protector",
    117: "Quran Protector",
    118: "Guardian of Revelation",
    119: "Guardian of Guidance",
    120: "Guardian Supreme",

    121: "Wisdom Sage",
    122: "Verse Sage",
    123: "Ayah Sage",
    124: "Quran Sage",
    125: "Master Guardian",
    126: "Master Keeper",
    127: "Master Protector",
    128: "Master Champion",
    129: "Master Steward",
    130: "Master of Light",
    131: "Master of Wisdom",
    132: "Master of Faith",
    133: "Master of Verses",
    134: "Master of Ayahs",
    135: "Master of Revelation",
    136: "Master Pathfinder",
    137: "Master Companion",
    138: "Master Builder",
    139: "Master Guide",
    140: "Master Mentor",

    141: "Grand Mentor",
    142: "Grand Guardian",
    143: "Grand Reciter",
    144: "Grand Memorizer",
    145: "Grand Scholar",
    146: "Grand Keeper",
    147: "Grand Protector",
    148: "Grand Champion",
    149: "Grand Steward",
    150: "Grand Pathfinder",
    151: "Legendary Student",
    152: "Legendary Reciter",
    153: "Legendary Memorizer",
    154: "Legendary Guardian",
    155: "Legendary Keeper",
    156: "Legendary Protector",
    157: "Legendary Champion",
    158: "Legendary Steward",
    159: "Legendary Guide",
    160: "Legendary Mentor",

    161: "Radiant Soul",
    162: "Radiant Learner",
    163: "Radiant Guardian",
    164: "Radiant Memorizer",
    165: "Radiant Reciter",
    166: "Radiant Scholar",
    167: "Radiant Champion",
    168: "Radiant Steward",
    169: "Radiant Guide",
    170: "Radiant Sage",
    171: "Brilliant Guardian",
    172: "Brilliant Scholar",
    173: "Brilliant Mentor",
    174: "Brilliant Champion",
    175: "Brilliant Steward",
    176: "Brilliant Keeper",
    177: "Brilliant Protector",
    178: "Brilliant Memorizer",
    179: "Brilliant Reciter",
    180: "Brilliant Pathfinder",

    181: "Eternal Guardian",
    182: "Eternal Scholar",
    183: "Eternal Guide",
    184: "Eternal Mentor",
    185: "Eternal Champion",
    186: "Eternal Keeper",
    187: "Eternal Protector",
    188: "Eternal Steward",
    189: "Eternal Memorizer",
    190: "Eternal Reciter",
    191: "Royal Guardian",
    192: "Royal Scholar",
    193: "Royal Champion",
    194: "Royal Keeper",
    195: "Royal Protector",
    196: "Royal Steward",
    197: "Royal Memorizer",
    198: "Royal Reciter",
    199: "Royal Mentor",
    200: "Royal Sage",

    201: "Crowned Guardian",
    202: "Crowned Scholar",
    203: "Crowned Memorizer",
    204: "Crowned Reciter",
    205: "Crowned Champion",
    206: "Crowned Keeper",
    207: "Crowned Protector",
    208: "Crowned Steward",
    209: "Crowned Guide",
    210: "Crowned Sage",
    211: "Servant of the Quran",
    212: "Custodian of Revelation",
    213: "Bearer of Guidance",
    214: "Keeper of Revelation",
    215: "Beacon of Light",
    216: "Beacon of Wisdom",
    217: "Beacon of Faith",
    218: "Beacon of Revelation",
    219: "Beacon of the Quran",
    220: "Nearing Hafiz",

    221: "Hafiz Candidate I",
    222: "Hafiz Candidate II",
    223: "Hafiz Candidate III",
    224: "Hafiz Candidate IV",
    225: "Hafiz Candidate V",
    226: "Hafiz Aspirant",
    227: "Dedicated Hafiz",
    228: "Honored Hafiz",
    229: "Noble Hafiz",
    230: "Elite Hafiz",
    231: "Distinguished Hafiz",
    232: "Respected Hafiz",
    233: "Trusted Hafiz",
    234: "Guardian Hafiz",
    235: "Champion Hafiz",
    236: "Master Hafiz",
    237: "Beacon Hafiz",
    238: "Legendary Hafiz",
    239: "Hafiz of the Quran",
    240: "The Hafiz"
}


LEVEL_CHARACTER_MAP = {
    1: ("🚶", "Adventurer 1"),
    2: ("🏃", "Adventurer 2"),
    3: ("🧍", "Adventurer 3"),
    4: ("🧑", "Adventurer 4"),
    5: ("👨", "Adventurer 5"),
    6: ("👩", "Adventurer 6"),
    7: ("🧒", "Adventurer 7"),
    8: ("👦", "Adventurer 8"),
    9: ("👧", "Adventurer 9"),
    10: ("🥷", "Adventurer 10"),
    11: ("🦸", "Adventurer 11"),
    12: ("🦹", "Adventurer 12"),
    13: ("🧙", "Adventurer 13"),
    14: ("🧑‍🚀", "Adventurer 14"),
    15: ("🧑‍✈️", "Adventurer 15"),
    16: ("👮", "Adventurer 16"),
    17: ("🕵️", "Adventurer 17"),
    18: ("🤠", "Adventurer 18"),
    19: ("👷", "Adventurer 19"),
    20: ("🧑‍🔬", "Adventurer 20"),
    21: ("🛴", "Vehicle 21"),
    22: ("🚲", "Vehicle 22"),
    23: ("🏍️", "Vehicle 23"),
    24: ("🏎️", "Vehicle 24"),
    25: ("🚗", "Vehicle 25"),
    26: ("🚕", "Vehicle 26"),
    27: ("🚙", "Vehicle 27"),
    28: ("🚌", "Vehicle 28"),
    29: ("🚐", "Vehicle 29"),
    30: ("🚚", "Vehicle 30"),
    31: ("🚛", "Vehicle 31"),
    32: ("🚜", "Vehicle 32"),
    33: ("🚓", "Vehicle 33"),
    34: ("🚑", "Vehicle 34"),
    35: ("🚒", "Vehicle 35"),
    36: ("🚂", "Vehicle 36"),
    37: ("🚆", "Vehicle 37"),
    38: ("🚄", "Vehicle 38"),
    39: ("🚅", "Vehicle 39"),
    40: ("🚁", "Vehicle 40"),
    41: ("✈️", "Space 41"),
    42: ("🛩️", "Space 42"),
    43: ("🛸", "Space 43"),
    44: ("🚀", "Space 44"),
    45: ("🛰️", "Space 45"),
    46: ("🌕", "Space 46"),
    47: ("🌖", "Space 47"),
    48: ("🌗", "Space 48"),
    49: ("🌘", "Space 49"),
    50: ("🌑", "Space 50"),
    51: ("🌒", "Space 51"),
    52: ("🪐", "Space 52"),
    53: ("⭐", "Space 53"),
    54: ("🌟", "Space 54"),
    55: ("🌠", "Space 55"),
    56: ("☄️", "Space 56"),
    57: ("🌌", "Space 57"),
    58: ("🌍", "Space 58"),
    59: ("🌎", "Space 59"),
    60: ("🌏", "Space 60"),
    61: ("🐶", "Animal 61"),
    62: ("🐺", "Animal 62"),
    63: ("🦊", "Animal 63"),
    64: ("🐱", "Animal 64"),
    65: ("🦁", "Animal 65"),
    66: ("🐯", "Animal 66"),
    67: ("🐴", "Animal 67"),
    68: ("🦄", "Animal 68"),
    69: ("🦓", "Animal 69"),
    70: ("🦌", "Animal 70"),
    71: ("🐮", "Animal 71"),
    72: ("🐷", "Animal 72"),
    73: ("🐘", "Animal 73"),
    74: ("🦏", "Animal 74"),
    75: ("🦛", "Animal 75"),
    76: ("🐪", "Animal 76"),
    77: ("🦒", "Animal 77"),
    78: ("🦘", "Animal 78"),
    79: ("🦬", "Animal 79"),
    80: ("🐃", "Animal 80"),
    81: ("🦅", "BirdSea 81"),
    82: ("🦉", "BirdSea 82"),
    83: ("🦜", "BirdSea 83"),
    84: ("🦢", "BirdSea 84"),
    85: ("🦩", "BirdSea 85"),
    86: ("🦚", "BirdSea 86"),
    87: ("🐧", "BirdSea 87"),
    88: ("🦆", "BirdSea 88"),
    89: ("🐦", "BirdSea 89"),
    90: ("🐤", "BirdSea 90"),
    91: ("🐬", "BirdSea 91"),
    92: ("🐳", "BirdSea 92"),
    93: ("🐋", "BirdSea 93"),
    94: ("🦈", "BirdSea 94"),
    95: ("🐙", "BirdSea 95"),
    96: ("🦀", "BirdSea 96"),
    97: ("🦞", "BirdSea 97"),
    98: ("🦐", "BirdSea 98"),
    99: ("🐠", "BirdSea 99"),
    100: ("🐟", "BirdSea 100"),
    101: ("🌳", "Nature 101"),
    102: ("🌴", "Nature 102"),
    103: ("🌲", "Nature 103"),
    104: ("🌵", "Nature 104"),
    105: ("🌿", "Nature 105"),
    106: ("🍀", "Nature 106"),
    107: ("🍁", "Nature 107"),
    108: ("🍂", "Nature 108"),
    109: ("🍄", "Nature 109"),
    110: ("🌺", "Nature 110"),
    111: ("🌸", "Nature 111"),
    112: ("🌼", "Nature 112"),
    113: ("🌻", "Nature 113"),
    114: ("🌷", "Nature 114"),
    115: ("🌹", "Nature 115"),
    116: ("🌱", "Nature 116"),
    117: ("🪴", "Nature 117"),
    118: ("🌾", "Nature 118"),
    119: ("🌈", "Nature 119"),
    120: ("⛰️", "Nature 120"),
    121: ("⚽", "Sports 121"),
    122: ("🏀", "Sports 122"),
    123: ("🏈", "Sports 123"),
    124: ("⚾", "Sports 124"),
    125: ("🎾", "Sports 125"),
    126: ("🏐", "Sports 126"),
    127: ("🏉", "Sports 127"),
    128: ("🥏", "Sports 128"),
    129: ("🎱", "Sports 129"),
    130: ("🏓", "Sports 130"),
    131: ("🏸", "Sports 131"),
    132: ("🥊", "Sports 132"),
    133: ("🥋", "Sports 133"),
    134: ("⛳", "Sports 134"),
    135: ("🏒", "Sports 135"),
    136: ("🏑", "Sports 136"),
    137: ("🥅", "Sports 137"),
    138: ("🎯", "Sports 138"),
    139: ("🏆", "Sports 139"),
    140: ("🥇", "Sports 140"),
    141: ("🛡️", "Tools 141"),
    142: ("⚔️", "Tools 142"),
    143: ("🏹", "Tools 143"),
    144: ("🪃", "Tools 144"),
    145: ("🔨", "Tools 145"),
    146: ("🪓", "Tools 146"),
    147: ("⛏️", "Tools 147"),
    148: ("⚒️", "Tools 148"),
    149: ("🪛", "Tools 149"),
    150: ("🔧", "Tools 150"),
    151: ("🔩", "Tools 151"),
    152: ("⚙️", "Tools 152"),
    153: ("🧰", "Tools 153"),
    154: ("🪜", "Tools 154"),
    155: ("🧲", "Tools 155"),
    156: ("💡", "Tools 156"),
    157: ("🔦", "Tools 157"),
    158: ("📡", "Tools 158"),
    159: ("📻", "Tools 159"),
    160: ("🧭", "Tools 160"),
    161: ("💎", "Treasure 161"),
    162: ("💍", "Treasure 162"),
    163: ("👑", "Treasure 163"),
    164: ("🏅", "Treasure 164"),
    165: ("🥈", "Treasure 165"),
    166: ("🥉", "Treasure 166"),
    167: ("🥇", "Treasure 167"),
    168: ("🎖️", "Treasure 168"),
    169: ("🏆", "Treasure 169"),
    170: ("💰", "Treasure 170"),
    171: ("🪙", "Treasure 171"),
    172: ("💸", "Treasure 172"),
    173: ("💵", "Treasure 173"),
    174: ("💴", "Treasure 174"),
    175: ("💶", "Treasure 175"),
    176: ("💷", "Treasure 176"),
    177: ("💳", "Treasure 177"),
    178: ("📿", "Treasure 178"),
    179: ("🔮", "Treasure 179"),
    180: ("✨", "Treasure 180"),
    181: ("🐉", "Fantasy 181"),
    182: ("🦄", "Fantasy 182"),
    183: ("👑", "Fantasy 183"),
    184: ("🧙", "Fantasy 184"),
    185: ("🧝", "Fantasy 185"),
    186: ("🧞", "Fantasy 186"),
    187: ("🧜", "Fantasy 187"),
    188: ("🧚", "Fantasy 188"),
    189: ("🪄", "Fantasy 189"),
    190: ("🔮", "Fantasy 190"),
    191: ("⚡", "Fantasy 191"),
    192: ("🔥", "Fantasy 192"),
    193: ("🌟", "Fantasy 193"),
    194: ("💫", "Fantasy 194"),
    195: ("✨", "Fantasy 195"),
    196: ("🌠", "Fantasy 196"),
    197: ("☄️", "Fantasy 197"),
    198: ("🌙", "Fantasy 198"),
    199: ("☀️", "Fantasy 199"),
    200: ("⭐", "Fantasy 200"),
    201: ("💻", "Technology 201"),
    202: ("🖥️", "Technology 202"),
    203: ("⌨️", "Technology 203"),
    204: ("🖱️", "Technology 204"),
    205: ("📱", "Technology 205"),
    206: ("📲", "Technology 206"),
    207: ("⌚", "Technology 207"),
    208: ("🕹️", "Technology 208"),
    209: ("🎮", "Technology 209"),
    210: ("📷", "Technology 210"),
    211: ("📸", "Technology 211"),
    212: ("🎥", "Technology 212"),
    213: ("🎬", "Technology 213"),
    214: ("🎧", "Technology 214"),
    215: ("🎤", "Technology 215"),
    216: ("📡", "Technology 216"),
    217: ("🛰️", "Technology 217"),
    218: ("🤖", "Technology 218"),
    219: ("💾", "Technology 219"),
    220: ("🖨️", "Technology 220"),
    221: ("🏠", "Building 221"),
    222: ("🏡", "Building 222"),
    223: ("🏰", "Building 223"),
    224: ("🏯", "Building 224"),
    225: ("🗼", "Building 225"),
    226: ("🗽", "Building 226"),
    227: ("🏛️", "Building 227"),
    228: ("⛪", "Building 228"),
    229: ("🕌", "Building 229"),
    230: ("🛕", "Building 230"),
    231: ("🕍", "Building 231"),
    232: ("🏫", "Building 232"),
    233: ("🏢", "Building 233"),
    234: ("🏬", "Building 234"),
    235: ("🏭", "Building 235"),
    236: ("🏦", "Building 236"),
    237: ("🏨", "Building 237"),
    238: ("🏥", "Building 238"),
    239: ("🏟️", "Building 239"),
    240: ("🌉", "Building 240"),
    241: ("🍎", "Food 241"),
    242: ("🍊", "Food 242"),
    243: ("🍉", "Food 243"),
    244: ("🍇", "Food 244"),
    245: ("🍓", "Food 245"),
    246: ("🥭", "Food 246"),
    247: ("🍍", "Food 247"),
    248: ("🥥", "Food 248"),
    249: ("🍌", "Food 249"),
    250: ("🍒", "Food 250"),
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


def get_xp_character(xp):
    """Return (icon, mode) from LEVEL_CHARACTER_MAP cycling every 150 XP."""
    safe_xp = max(0, int(xp))
    stage = safe_xp // 150          # 0-based stage
    level_key = min(60, stage + 1)  # map to keys 1-60
    return LEVEL_CHARACTER_MAP.get(level_key, LEVEL_CHARACTER_MAP[60])


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
    ui_tier="laptop",
):
    safe_tier = normalize_ui_tier(ui_tier)
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

        .game-scene.scene-density-minimal .scene-bird-lane,
        .game-scene.scene-density-minimal .scene-grain {
            display: none;
        }
        .game-scene.scene-density-minimal .scene-cloud-layer.far {
            opacity: 0.25;
        }
        .game-scene.scene-density-minimal .scene-cloud-layer.mid {
            opacity: 0.34;
        }
        .game-scene.scene-density-balanced .scene-bird-lane {
            opacity: 0.75;
        }
        .game-scene.scene-tier-phone .scene-map-ready-chip {
            font-size: 0.68rem;
            padding: 5px 9px;
        }
        .game-scene.scene-tier-phone {
            --reward-card-scale: 0.84;
            --reward-font-scale: 0.86;
            --reward-row-bottom: 34px;
        }
        .game-scene.scene-tier-phone .road-row {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .game-scene.scene-tier-tablet {
            --reward-card-scale: 0.92;
            --reward-font-scale: 0.93;
            --reward-row-bottom: 26px;
        }
        .game-scene.scene-tier-tablet .road-row {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .game-scene {
            --reward-card-scale: 1;
            --reward-font-scale: 1;
            --reward-row-bottom: 20px;
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
            z-index: 7;
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
            z-index: 6;
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
            z-index: 8;
            padding: 0;
            justify-items: center;
        }
        .road-row.single {
            top: auto;
            bottom: var(--reward-row-bottom);
            transform: scale(var(--reward-card-scale));
            transform-origin: bottom center;
        }

        .road-board {
            position: relative;
            border-radius: 12px;
            border: 2px solid #bfd7f6;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 8px 14px rgba(21, 54, 88, 0.18);
            padding: calc(8px * var(--reward-font-scale)) calc(10px * var(--reward-font-scale));
            min-height: calc(86px * var(--reward-font-scale));
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
            font-size: calc(12px * var(--reward-font-scale)) !important;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 800;
            color: #173e66;
            line-height: 1.25 !important;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .board-reward {
            margin: 8px 0 0 0;
            font-size: calc(12px * var(--reward-font-scale)) !important;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 700;
            color: #35608b;
            line-height: 1.25 !important;
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .board-goal {
            margin: 3px 0 0 0;
            font-size: calc(12px * var(--reward-font-scale)) !important;
            font-family: "Baloo 2", "Comic Sans MS", "Trebuchet MS", sans-serif;
            font-weight: 700;
            color: #153c62;
            line-height: 1.25 !important;
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
            0% { transform: translate(-50%, -50%) scaleX(-1) translateX(-80px); opacity: 0.2; }
            60% { opacity: 1; }
            100% { transform: translate(-50%, -50%) scaleX(-1) translateX(0); opacity: 1; }
        }
        @keyframes gameRiderFloat { 0% { transform: translate(-50%, -50%) scaleX(-1) translateY(0); } 100% { transform: translate(-50%, -50%) scaleX(-1) translateY(-4px); } }
        @keyframes gamePulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }

        @media (max-width: 1200px) {
            .game-cards { grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .game-highlights { grid-template-columns: 1fr 1fr; }
            .road-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        }
        @media (max-width: 1024px) {
            .game-scene {
                --reward-card-scale: 0.9;
                --reward-font-scale: 0.92;
                --reward-row-bottom: 26px;
            }
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
        @media (max-width: 767px) {
            .game-scene {
                --reward-card-scale: 0.8;
                --reward-font-scale: 0.82;
                --reward-row-bottom: 34px;
            }
            .game-cards { grid-template-columns: 1fr; }
            .game-progress-grid { grid-template-columns: 1fr; }
            .game-level-badge { width: 100%; }
            .game-scene { height: 740px; }
            .game-road-layout { height: 220px; }
            .road-strip.single { height: 200px; top: 10px; }
            .road-row { grid-template-columns: 1fr; }
            .road-row.single {
                top: auto;
                bottom: var(--reward-row-bottom);
                display: flex;
                flex-direction: column-reverse;
                align-items: stretch;
                gap: 8px;
            }
            .road-board { width: 100%; }
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

    current_xp = st.session_state.get("xp", 0)
    xp_character = get_xp_character(current_xp)
    character_icon = xp_character[0]
    character_mode = xp_character[1]
    rider_top = pick_tier_value(safe_tier, "78%", "77%", "76%")
    xp_stage_progress_raw = (max(0, current_xp) % 150) / 150 * 100
    xp_stage_progress_pct = (int(xp_stage_progress_raw) // 10) * 10  # snap to 0,10,20,...,90,100
    rider_target = 8 + (xp_stage_progress_pct / 100.0) * 84
    scene_density = pick_tier_value(safe_tier, "minimal", "balanced", "rich")

    single_boards_html = build_journey_boards_html(single_road_items)
    longest_card_text = 0
    for item in single_road_items:
        reward_text = str(item.get("reward", "Reward"))
        goal_text = format_target_label(item)
        longest_card_text = max(longest_card_text, len(reward_text), len(goal_text), len(f"{reward_text} {goal_text}"))

    scene_height_px = int(pick_tier_value(safe_tier, 620, 520, 470))
    if longest_card_text >= 28:
        scene_height_px = int(pick_tier_value(safe_tier, 660, 560, 520))
    if longest_card_text >= 40:
        scene_height_px = int(pick_tier_value(safe_tier, 700, 600, 560))

    next_level = min(MAX_LEVEL, current_level + 1)
    next_level_title = get_level_title(next_level)
    progress_marker = max(2.0, min(98.0, level_progress_percent))
    try:
        hero_scene_html = build_game_hero_scene_html(
            character_mode=character_mode,
            level_progress_percent=level_progress_percent,
            ready_rewards_count=len(ready_items),
            single_boards_html=single_boards_html,
            rider_target=rider_target,
            rider_top=rider_top,
            scene_height_px=scene_height_px,
            character_icon=character_icon,
            scene_tier=safe_tier,
            scene_density=scene_density,
        )
    except TypeError:
        # Backward-compatible fallback for hot-reload sessions with stale scene module cache.
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
        if st.button("Open Achievements to Claim Rewards", use_container_width=True, type="primary"):
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

