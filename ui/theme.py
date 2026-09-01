"""Shared visual styling for the MCU family tracker."""

import streamlit as st


def apply_theme() -> None:
    """Apply the app's cinematic superhero-inspired theme."""
    st.markdown(
        """
        <style>
        :root {
            --bg: #090b10;
            --panel: #11151d;
            --panel-soft: #171c26;
            --text: #f5f7fb;
            --muted: #a7afbd;
            --accent: #d7263d;
            --accent-soft: #7f1424;
            --metal: #c7ced8;
        }

        .stApp {
            background:
                radial-gradient(circle at top right,
                    rgba(215, 38, 61, 0.16), transparent 28%),
                linear-gradient(180deg, #090b10 0%, #0c1017 100%);
            color: var(--text);
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        .hero {
            padding: 2.25rem;
            border: 1px solid rgba(199, 206, 216, 0.22);
            border-radius: 22px;
            background:
                linear-gradient(135deg,
                    rgba(215, 38, 61, 0.16),
                    rgba(17, 21, 29, 0.96) 45%);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
            margin-bottom: 1.5rem;
        }

        .eyebrow {
            color: var(--accent);
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.18rem;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2rem, 5vw, 4rem);
            letter-spacing: -0.05em;
            line-height: 0.95;
        }

        .hero p {
            color: var(--muted);
            max-width: 720px;
            font-size: 1.05rem;
            margin-top: 1rem;
            margin-bottom: 0;
        }

        .metric-card {
            background: rgba(17, 21, 29, 0.88);
            border: 1px solid rgba(199, 206, 216, 0.16);
            border-radius: 16px;
            padding: 1.1rem 1.25rem;
            min-height: 116px;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08rem;
        }

        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }

        .phase-card {
            padding: 1rem 1.1rem;
            background: rgba(23, 28, 38, 0.78);
            border-left: 4px solid var(--accent);
            border-radius: 10px;
            margin: 0.55rem 0;
        }

        .library-card {
            display: flex;
            gap: 1rem;
            align-items: center;
            padding: 1rem 1.15rem;
            margin: 0.55rem 0;
            border: 1px solid rgba(199, 206, 216, 0.14);
            border-radius: 14px;
            background: rgba(17, 21, 29, 0.84);
        }

        .library-order {
            min-width: 3.2rem;
            color: var(--accent);
            font-weight: 800;
            letter-spacing: 0.05rem;
        }

        .library-title {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 750;
        }

        .library-meta {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }

        .family-status {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 2.4rem;
            font-size: 1.45rem;
            font-weight: 800;
            color: #4fd17b;
        }

        .family-status-off {
            color: #687180;
        }

        [data-testid="stSidebar"] {
            background: #0c1017;
            border-right: 1px solid rgba(199, 206, 216, 0.12);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(215, 38, 61, 0.6);
            background: linear-gradient(180deg, #d7263d, #9f182a);
            color: white;
            font-weight: 700;
        }

        .stButton > button:hover {
            border-color: #f25d70;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
