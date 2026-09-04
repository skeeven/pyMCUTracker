"""Administrator family and movie-management page."""

import streamlit as st

from auth.service import reset_user_password_as_admin
from database.movies import (
    PRIORITY_OPTIONS,
    add_movie,
    get_all_movies_with_priority,
    set_movie_active,
    update_movie,
)
from database.users import get_all_users, set_user_active, update_user_name

CATEGORY_OPTIONS = [
    "MCU",
    "Mutant Legacy",
    "Fantastic Four Legacy",
    "Sony Spider-Man",
    "Marvel Legacy",
    "Other",
]


def _render_family_management(current_user_id: int) -> None:
    """Render family account controls."""
    users = get_all_users()
    active_count = sum(1 for user in users if bool(user[3]))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Accounts", len(users))
    col2.metric("Active", active_count)
    col3.metric("Inactive", len(users) - active_count)

    st.caption(
        "Inactive accounts keep their saved movie history but are hidden from "
        "family progress and recommendations."
    )

    for user in users:
        user_id, name, email, is_active, is_admin, created_at = user
        user_id = int(user_id)
        is_active = bool(is_active)
        is_admin = bool(is_admin)
        is_current_user = user_id == int(current_user_id)

        title = name
        if is_current_user:
            title += " (You)"
        if is_admin:
            title += " · Administrator"

        with st.expander(title, expanded=is_current_user):
            st.caption(email)
            st.caption(f"Account created: {created_at}")
            new_name = st.text_input(
                "Display name",
                value=name,
                key=f"admin_name_{user_id}",
            )

            if st.button("Save Display Name", key=f"admin_save_name_{user_id}"):
                try:
                    update_user_name(current_user_id, user_id, new_name)
                    if is_current_user:
                        st.session_state.user_name = new_name.strip()
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))

            st.markdown("**Password recovery**")
            with st.form(f"admin_password_reset_{user_id}"):
                new_password = st.text_input(
                    "New password",
                    type="password",
                    autocomplete="new-password",
                    key=f"admin_password_{user_id}",
                )
                confirm_password = st.text_input(
                    "Confirm new password",
                    type="password",
                    autocomplete="new-password",
                    key=f"admin_password_confirm_{user_id}",
                )
                reset_submitted = st.form_submit_button("Reset Password")

            if reset_submitted:
                try:
                    errors = reset_user_password_as_admin(
                        current_user_id,
                        user_id,
                        new_password,
                        confirm_password,
                    )
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        st.success(f"Password reset for {name}.")
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))

            st.write(f"**Status:** {'Active' if is_active else 'Inactive'}")
            if is_current_user:
                st.info("Your administrator account cannot be deactivated here.")
            elif is_active:
                if st.button("Deactivate Account", key=f"admin_deactivate_{user_id}"):
                    try:
                        set_user_active(current_user_id, user_id, False)
                        st.rerun()
                    except (PermissionError, ValueError) as exc:
                        st.error(str(exc))
            elif st.button("Reactivate Account", key=f"admin_reactivate_{user_id}"):
                try:
                    set_user_active(current_user_id, user_id, True)
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))


def _render_add_movie(current_user_id: int, next_order: int) -> None:
    """Render the add-movie form."""
    with st.expander("➕ Add Movie", expanded=False):
        with st.form("admin_add_movie"):
            title = st.text_input("Title")
            col1, col2, col3 = st.columns(3)
            release_year_text = col1.text_input("Release year", placeholder="2026")
            release_date = col2.text_input("Release date", placeholder="YYYY-MM-DD")
            phase = col3.number_input("MCU phase", min_value=0, max_value=6, value=0)

            col4, col5, col6 = st.columns(3)
            watch_order = col4.number_input(
                "Watch order",
                min_value=1,
                value=max(next_order, 1),
                step=1,
            )
            category = col5.selectbox("Category", CATEGORY_OPTIONS)
            priority = col6.selectbox(
                "Doomsday priority",
                list(PRIORITY_OPTIONS),
                index=list(PRIORITY_OPTIONS).index("Recommended"),
            )

            universe = st.text_input(
                "Universe / continuity",
                value="Marvel Cinematic Universe",
            )
            core_col, relevant_col = st.columns(2)
            is_core_mcu = core_col.checkbox("Core MCU title", value=False)
            is_doomsday_relevant = relevant_col.checkbox(
                "Doomsday relevant",
                value=True,
            )
            notes = st.text_area("Notes", placeholder="Why this title matters...")
            submitted = st.form_submit_button("Add Movie", use_container_width=True)

        if submitted:
            try:
                release_year = int(release_year_text) if release_year_text.strip() else None
                add_movie(
                    current_user_id,
                    title,
                    release_year,
                    release_date.strip() or None,
                    int(phase),
                    int(watch_order),
                    category,
                    universe,
                    is_core_mcu,
                    is_doomsday_relevant,
                    notes,
                    priority,
                )
                st.success(f"Added {title.strip()} to the Road to Doomsday catalog.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(
                    "The movie could not be added. Make sure the title and watch "
                    "order are unique."
                )
                st.caption(str(exc))


def _render_movie_management(current_user_id: int) -> None:
    """Render catalog creation, editing, ordering, and activation controls."""
    movies = list(get_all_movies_with_priority())
    active_count = sum(1 for movie in movies if bool(movie[11]))
    next_order = max((int(movie[5]) for movie in movies), default=0) + 1

    col1, col2, col3 = st.columns(3)
    col1.metric("Catalog Titles", len(movies))
    col2.metric("Active", active_count)
    col3.metric("Inactive", len(movies) - active_count)

    st.caption(
        "Use Phase 0 for supplemental/non-MCU titles. Priority controls whether "
        "a movie appears in Essential, Recommended, or Completionist watch paths."
    )
    _render_add_movie(current_user_id, next_order)

    show_inactive = st.toggle("Show inactive movies", value=False)
    visible_movies = [movie for movie in movies if show_inactive or bool(movie[11])]

    for movie in visible_movies:
        (
            movie_id,
            title,
            release_year,
            release_date,
            phase,
            watch_order,
            category,
            universe,
            is_core_mcu,
            is_doomsday_relevant,
            doomsday_priority,
            is_active,
            notes,
        ) = movie
        movie_id = int(movie_id)
        status = "Active" if bool(is_active) else "Inactive"
        priority_text = str(doomsday_priority or "Recommended")

        with st.expander(
            f"#{int(watch_order):02d} · {title} · {priority_text} · {status}"
        ):
            with st.form(f"admin_edit_movie_{movie_id}"):
                edit_title = st.text_input(
                    "Title",
                    value=str(title),
                    key=f"movie_title_{movie_id}",
                )
                col1, col2, col3 = st.columns(3)
                edit_year = col1.text_input(
                    "Release year",
                    value=str(release_year) if release_year else "",
                    key=f"movie_year_{movie_id}",
                )
                edit_date = col2.text_input(
                    "Release date",
                    value=str(release_date) if release_date else "",
                    key=f"movie_date_{movie_id}",
                )
                edit_phase = col3.number_input(
                    "MCU phase",
                    min_value=0,
                    max_value=6,
                    value=int(phase),
                    key=f"movie_phase_{movie_id}",
                )

                col4, col5, col6 = st.columns(3)
                edit_order = col4.number_input(
                    "Watch order",
                    min_value=1,
                    value=int(watch_order),
                    step=1,
                    key=f"movie_order_{movie_id}",
                )
                category_values = CATEGORY_OPTIONS.copy()
                if category not in category_values:
                    category_values.append(str(category))
                edit_category = col5.selectbox(
                    "Category",
                    category_values,
                    index=category_values.index(str(category)),
                    key=f"movie_category_{movie_id}",
                )

                priority_values = list(PRIORITY_OPTIONS)
                if priority_text not in priority_values:
                    priority_values.append(priority_text)
                edit_priority = col6.selectbox(
                    "Doomsday priority",
                    priority_values,
                    index=priority_values.index(priority_text),
                    key=f"movie_priority_{movie_id}",
                )

                edit_universe = st.text_input(
                    "Universe / continuity",
                    value=str(universe),
                    key=f"movie_universe_{movie_id}",
                )
                core_col, relevant_col = st.columns(2)
                edit_core = core_col.checkbox(
                    "Core MCU title",
                    value=bool(is_core_mcu),
                    key=f"movie_core_{movie_id}",
                )
                edit_relevant = relevant_col.checkbox(
                    "Doomsday relevant",
                    value=bool(is_doomsday_relevant),
                    key=f"movie_relevant_{movie_id}",
                )
                edit_notes = st.text_area(
                    "Notes",
                    value=str(notes or ""),
                    key=f"movie_notes_{movie_id}",
                )
                save_movie = st.form_submit_button("Save Movie")

            if save_movie:
                try:
                    year_value = int(edit_year) if edit_year.strip() else None
                    update_movie(
                        current_user_id,
                        movie_id,
                        edit_title,
                        year_value,
                        edit_date.strip() or None,
                        int(edit_phase),
                        int(edit_order),
                        edit_category,
                        edit_universe,
                        edit_core,
                        edit_relevant,
                        edit_notes,
                        edit_priority,
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(
                        "The movie could not be saved. Make sure the title and "
                        "watch order are unique."
                    )
                    st.caption(str(exc))

            action_label = "Deactivate Movie" if bool(is_active) else "Reactivate Movie"
            if st.button(action_label, key=f"movie_active_{movie_id}"):
                try:
                    set_movie_active(current_user_id, movie_id, not bool(is_active))
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))


def render_admin_page(current_user_id: int) -> None:
    """Render administrator-only controls."""
    if not st.session_state.is_admin:
        st.error("Administrator access is required.")
        return

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Initiative Administration</div>
            <h1>Administration</h1>
            <p>Manage family accounts and the Road to Doomsday movie catalog.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    family_tab, movies_tab = st.tabs(["👥 Family", "🎬 Movies"])
    with family_tab:
        _render_family_management(current_user_id)
    with movies_tab:
        _render_movie_management(current_user_id)
