"""Revision (Muraja'ah) page — spaced-repetition revision scheduling.

All app-level helpers are accessed via a deferred ``import app`` inside each
function to avoid a circular import at module-load time.
"""
import datetime
import random
import sys

import streamlit as st


def _render_srs_revision_form(
    section_ayahs: list,
    section_key: str,
    today: datetime.date,
    xp_per_ayah: int,
) -> None:
    """Render a Streamlit form for a scheduled-revision section.

    Advances the SRS schedule and awards XP on submit.
    section_ayahs: list of (surah_name, ayah_str, entry_dict)
    """
    # Access the main app module without re-importing (avoids re-running set_page_config).
    _a = sys.modules["__main__"]

    if not section_ayahs:
        return

    by_surah: dict = {}
    for surah, ayah_str, _entry in section_ayahs:
        by_surah.setdefault(surah, []).append(int(ayah_str))

    ayah_grid_cols = _a.get_responsive_column_count(4, 6, 10)

    with st.form(f"srs_form_{section_key}"):
        all_selections: list = []
        for surah, ayah_numbers in by_surah.items():
            st.markdown(f"**{_a.get_surah_short_name(surah)}**")
            selected = _a.render_ayah_checkbox_grid(
                sorted(ayah_numbers),
                ayah_grid_cols,
                f"srs_{section_key}_{_a.sanitize_widget_key(surah)}",
            )
            for n in selected:
                all_selections.append((surah, str(n)))

        submitted = st.form_submit_button(
            f"✅ Submit Revision  (+{xp_per_ayah} XP per Ayah)"
        )
        if submitted:
            if not all_selections:
                st.error("Please select at least one Ayah to mark as revised.")
            else:
                for surah, ayah_str in all_selections:
                    _a.complete_scheduled_revision(surah, ayah_str, today)

                total_xp = len(all_selections) * xp_per_ayah
                surah_names = sorted({s for s, _ in all_selections})
                surah_label = (
                    surah_names[0] if len(surah_names) == 1 else "Multiple Surahs"
                )
                details = f"Revised {len(all_selections)} ayah(s)"
                _a.add_xp(total_xp, "Revision", surah_label, details)
                st.session_state.recent_praise = random.choice(_a.MURAJAH_PRAISES)
                st.toast(f"✨ Revision logged! +{total_xp} XP earned.", icon="⭐")
                st.rerun()


def _render_practice_section(all_memorized: list, today: datetime.date) -> None:
    """Practice Anytime — optional, +1 XP per ayah, max once per ayah per day."""
    # Access the main app module without re-importing (avoids re-running set_page_config).
    _a = sys.modules["__main__"]

    if not all_memorized:
        st.info("No memorized ayahs yet. Start memorizing to unlock practice!")
        return

    today_str = today.isoformat()
    practice_log = st.session_state.get("practice_log", {})
    practiced_today = practice_log.get(today_str, {})  # {surah_name: [ayah_ints]}

    st.caption(
        "Optional free practice — does **not** change your spaced-repetition schedule. "
        "Each ayah can be practiced **once per day** (+1 XP each)."
    )

    surah_order = {s: i for i, s in enumerate(_a.SURAH_LIST)}
    by_surah: dict = {}
    for surah, ayah_str, _entry in all_memorized:
        by_surah.setdefault(surah, []).append(int(ayah_str))

    surah_options = sorted(by_surah.keys(), key=lambda s: surah_order.get(s, 9999))
    practice_surah = st.selectbox(
        "Choose a Surah to practice:",
        options=surah_options,
        key="practice_surah_selector",
        format_func=_a.get_surah_short_name,
    )

    if practice_surah and practice_surah in by_surah:
        all_ayahs = sorted(by_surah[practice_surah])
        done_today = set(practiced_today.get(practice_surah, []))
        available_ayahs = [n for n in all_ayahs if n not in done_today]

        if done_today:
            done_str = ", ".join(str(n) for n in sorted(done_today))
            st.info(f"✅ Already practiced today: Ayah(s) {done_str}")

        if not available_ayahs:
            st.success("🎯 All ayahs in this Surah have been practiced today. Come back tomorrow!")
            return

        ayah_grid_cols = _a.get_responsive_column_count(4, 6, 10)
        with st.form("srs_practice_form"):
            st.write(
                f"Select ayahs from **{_a.get_surah_short_name(practice_surah)}** to practice:"
            )
            selected = _a.render_ayah_checkbox_grid(
                available_ayahs,
                ayah_grid_cols,
                f"practice_{_a.sanitize_widget_key(practice_surah)}",
            )
            submitted = st.form_submit_button("🎯 Log Practice  (+1 XP each)")
            if submitted:
                if not selected:
                    st.error("Please select at least one Ayah.")
                else:
                    total_xp = len(selected)
                    details = f"Practice: Ayah(s) {', '.join(map(str, sorted(selected)))}"
                    _a.add_xp(total_xp, "Practice", practice_surah, details)

                    # Record in practice_log so these ayahs are locked for the rest of today
                    if today_str not in st.session_state.practice_log:
                        st.session_state.practice_log[today_str] = {}
                    existing = set(st.session_state.practice_log[today_str].get(practice_surah, []))
                    existing.update(selected)
                    st.session_state.practice_log[today_str][practice_surah] = sorted(existing)

                    st.toast(f"🎯 Practice logged! +{total_xp} XP", icon="🎯")
                    st.rerun()


def render_revision_page(today: datetime.date) -> None:
    """Spaced-revision page with four sections.

    1. Due Today      – scheduled for today              → +2 XP, advance schedule
    2. Grace Period   – 1–3 days past due                → +2 XP, advance schedule
    3. Overdue        – >3 days past due (−5 XP already) → +2 XP, advance schedule
    4. Practice Anytime – all memorized ayahs            → +1 XP, schedule unchanged
    """
    # Access the main app module without re-importing (avoids re-running set_page_config).
    _a = sys.modules["__main__"]

    st.markdown("## 🔁 Revision")

    if st.session_state.recent_praise:
        st.info(st.session_state.recent_praise)

    _a.ensure_revision_schedule(today)
    _a.apply_overdue_penalties_once(today)

    due_today, grace_period, overdue, all_memorized = _a.classify_revision_ayahs(today)

    if not all_memorized:
        st.info(
            "You have not memorized any Ayahs yet. "
            "Go to **📖 Memorization** to get started! 🌱"
        )
        return

    # Summary bar
    summary_cols = st.columns(4)
    with summary_cols[0]:
        st.metric("📅 Due Today", len(due_today))
    with summary_cols[1]:
        st.metric("⏳ Grace Period", len(grace_period))
    with summary_cols[2]:
        st.metric("⚠️ Overdue", len(overdue))
    with summary_cols[3]:
        st.metric("📚 All Memorized", len(all_memorized))

    st.markdown("---")

    # ── Section 1: Due Today ──────────────────────────────────────────────
    with st.expander(
        f"📅 Due Today — {len(due_today)} ayah(s)", expanded=bool(due_today)
    ):
        if due_today:
            st.markdown(
                "These ayahs are **scheduled for revision today**. "
                "Completing them earns **+2 XP each** and advances your schedule."
            )
            _render_srs_revision_form(due_today, "due_today", today, xp_per_ayah=_a.XP_PER_AYAH_REVISED)
        else:
            st.success("✅ No revisions due today — great work!")

    # ── Section 2: Grace Period ───────────────────────────────────────────
    with st.expander(
        f"⏳ Grace Period — {len(grace_period)} ayah(s)", expanded=bool(grace_period)
    ):
        if grace_period:
            st.markdown(
                "These ayahs were due **within the last 3 days**. "
                "Revising them still counts as normal — **+2 XP each**, no penalty."
            )
            _render_srs_revision_form(grace_period, "grace_period", today, xp_per_ayah=_a.XP_PER_AYAH_REVISED)
        else:
            st.success("✅ Nothing in the grace period!")

    # ── Section 3: Overdue ────────────────────────────────────────────────
    with st.expander(
        f"⚠️ Overdue — {len(overdue)} ayah(s)", expanded=bool(overdue)
    ):
        if overdue:
            st.warning(
                "These ayahs missed the 3-day grace period. "
                "A one-time **−5 XP penalty** has already been applied. "
                "Revise them to get back on track — **+2 XP each**."
            )
            _render_srs_revision_form(overdue, "overdue", today, xp_per_ayah=_a.XP_PER_AYAH_REVISED)
        else:
            st.success("✅ No overdue ayahs — keep up the great pace!")

    # ── Section 4: Practice Anytime ──────────────────────────────────────
    with st.expander(
        f"🎯 Practice Anytime — {len(all_memorized)} memorized ayah(s)", expanded=False
    ):
        _render_practice_section(all_memorized, today)
