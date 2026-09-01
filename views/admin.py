"""Administrator family-management page."""

import streamlit as st

from database.users import (
    get_all_users,
    set_user_active,
    update_user_name,
)


def render_admin_page(current_user_id: int) -> None:
    """Render administrator-only family account controls."""
    if not st.session_state.is_admin:
        st.error("Administrator access is required.")
        return

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Administration</div>
            <h1>Manage Family</h1>
            <p>
                Update display names and control which accounts participate
                in the shared family tracker.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    users = get_all_users()
    active_count = sum(1 for user in users if bool(user[3]))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Accounts", len(users))
    col2.metric("Active", active_count)
    col3.metric("Inactive", len(users) - active_count)

    st.caption(
        "Inactive accounts keep their saved movie history but are hidden from "
        "family progress, recommendations, and the Family Tracker."
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

            name_key = f"admin_name_{user_id}"
            new_name = st.text_input(
                "Display name",
                value=name,
                key=name_key,
            )

            if st.button(
                "Save Display Name",
                key=f"admin_save_name_{user_id}",
            ):
                try:
                    update_user_name(current_user_id, user_id, new_name)
                    if is_current_user:
                        st.session_state.user_name = new_name.strip()
                    st.success("Display name updated.")
                    st.rerun()
                except (PermissionError, ValueError) as exc:
                    st.error(str(exc))

            status_text = "Active" if is_active else "Inactive"
            st.write(f"**Status:** {status_text}")

            if is_current_user:
                st.info(
                    "Your administrator account cannot be deactivated from "
                    "this page."
                )
            elif is_active:
                if st.button(
                    "Deactivate Account",
                    key=f"admin_deactivate_{user_id}",
                ):
                    try:
                        set_user_active(current_user_id, user_id, False)
                        st.success(f"{name} has been deactivated.")
                        st.rerun()
                    except (PermissionError, ValueError) as exc:
                        st.error(str(exc))
            else:
                if st.button(
                    "Reactivate Account",
                    key=f"admin_reactivate_{user_id}",
                ):
                    try:
                        set_user_active(current_user_id, user_id, True)
                        st.success(f"{name} has been reactivated.")
                        st.rerun()
                    except (PermissionError, ValueError) as exc:
                        st.error(str(exc))
