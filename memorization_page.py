"""Memorization (Hifdh) page — log newly memorized ayahs.

All app-level helpers are accessed via a deferred ``import app`` inside the
render function to avoid a circular import at module-load time.
"""
import datetime
import random
import sys

import streamlit as st


def render_memorization_page(today: datetime.date) -> None:
    """Memorization (Hifdh) page — shows only unmemorized ayahs.

    Marking an ayah as memorized awards +5 XP and creates the first SRS
    schedule entry (stage=0, first revision due the next day).
    """
    # Access the main app module without re-importing (avoids re-running set_page_config).
    _a = sys.modules["__main__"]

    st.markdown("## 📖 Memorization (Hifdh)")
    if st.session_state.recent_praise:
        st.info(st.session_state.recent_praise)

    assigned_surahs = _a.get_assigned_surahs()
    if not assigned_surahs:
        st.warning(
            "No Surahs are assigned yet. Ask a parent to assign Surahs under ⚙️ Parents."
        )
        return

    sorted_assigned = sorted(
        assigned_surahs, key=lambda s: int(str(s).split(".", 1)[0])
    )
    if st.session_state.get("selected_surah") not in sorted_assigned:
        st.session_state["selected_surah"] = sorted_assigned[0]

    surah_choice = st.selectbox(
        "📖 Select a Surah", options=sorted_assigned, key="selected_surah"
    )
    st.session_state["hifdh_selected_surah"] = surah_choice

    surah_short = _a.get_surah_short_name(surah_choice)
    total_ayahs = _a.get_ayah_count(surah_choice)
    memorized_list = st.session_state.memorized.get(surah_choice, [])
    memorized_count = len(memorized_list)
    remaining_ayahs = [i for i in range(1, total_ayahs + 1) if i not in memorized_list]

    pct = (memorized_count / total_ayahs * 100) if total_ayahs else 0
    st.markdown(
        f"""<div class="hifdh-stats-strip">
            <div class="hifdh-stat"><span class="hifdh-stat-val">{memorized_count}/{total_ayahs}</span><span class="hifdh-stat-lbl">📖 Memorized</span></div>
            <div class="hifdh-stat"><span class="hifdh-stat-val">{len(remaining_ayahs)}</span><span class="hifdh-stat-lbl">⏳ Remaining</span></div>
            <div class="hifdh-stat"><span class="hifdh-stat-val">{pct:.0f}%</span><span class="hifdh-stat-lbl">✅ Done</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="hifdh-banner">
            🌱 <strong>Log Memorization</strong> &nbsp;·&nbsp; ⭐ +5 XP per Ayah &nbsp;·&nbsp; Revision starts tomorrow
        </div>""",
        unsafe_allow_html=True,
    )

    ayah_grid_columns = _a.get_responsive_column_count(5, 8, 12)
    status_grid_columns = _a.get_responsive_column_count(6, 10, 14)
    surah_key = _a.sanitize_widget_key(surah_choice)

    st.markdown(f"##### *{surah_short}* — 🟢 Memorized · ⚪ Not Yet")
    _a.render_ayah_status_grid(
        total_ayahs,
        status_grid_columns,
        lambda n: ("🟢", "Memorized") if n in memorized_list else ("⚪", "Not Memorized"),
    )
    st.markdown("<br/>", unsafe_allow_html=True)

    with st.form(f"hifdh_form_{surah_key}", clear_on_submit=False):
        selected_ayahs = []
        if not remaining_ayahs:
            st.success(
                "🏆 SubhanAllah! Rayyan has memorized all Ayahs of this Surah! "
                "Head to 🔁 Revision to keep them fresh."
            )
            submit_hifdh = st.form_submit_button("Submit Memorization! 🚀", disabled=True)
        else:
            st.write("Select the Ayah numbers you memorized today:")
            selected_ayahs = _a.render_ayah_checkbox_grid(
                remaining_ayahs, ayah_grid_columns, f"hifdh_{surah_key}"
            )
            submit_hifdh = st.form_submit_button("Submit Memorization! 🚀")

        if submit_hifdh:
            if not selected_ayahs:
                st.error("Please select at least one Ayah! 📖")
            else:
                pts = len(selected_ayahs) * _a.XP_PER_AYAH_LEARNED
                selected_ayahs.sort()

                prev_count = len(st.session_state.memorized.get(surah_choice, []))
                current_memorized = set(st.session_state.memorized.get(surah_choice, []))
                current_memorized.update(selected_ayahs)
                st.session_state.memorized[surah_choice] = sorted(list(current_memorized))
                st.session_state["hifdh_selected_surah"] = surah_choice

                # ── Create SRS schedule entries (stage=0, first revision tomorrow) ──
                if "revision_schedule" not in st.session_state:
                    st.session_state.revision_schedule = {}
                today_str = today.isoformat()
                first_rev_due = (
                    today + datetime.timedelta(days=_a.get_next_interval_days(0))
                ).isoformat()
                for ayah in selected_ayahs:
                    st.session_state.revision_schedule.setdefault(
                        surah_choice, {}
                    )[str(ayah)] = {
                        "memorized_date": today_str,
                        "stage": 0,
                        "next_due": first_rev_due,
                        "last_revised": "",
                        "overdue_penalty_applied": False,
                    }

                ayah_ranges = f"Ayah(s): {', '.join(map(str, selected_ayahs))}"
                _a.add_xp(pts, "Memorization", surah_choice, ayah_ranges)
                st.session_state.recent_praise = (
                    random.choice(_a.HIFDH_PRAISES)
                    + f" (Log: {ayah_ranges} memorized!)"
                )
                st.toast(
                    f"✨ Great job! +{pts} XP · First revision due tomorrow!",
                    icon="📖",
                )
                if prev_count < total_ayahs <= len(current_memorized):
                    st.balloons()
                    st.toast(
                        f"🏅 Achievement unlocked: Completed {surah_short}", icon="🎉"
                    )
                st.rerun()
