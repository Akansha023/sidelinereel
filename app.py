"""
SidelineReel: Smart Player Match Review Prototype
==================================================
Role: AI-Assisted Youth Sports Highlight Verification Platform
Context: Product Manager Interview Prototype for Ajaia
Author: Senior Full-Stack Python Developer & AI Product Engineer
"""

from datetime import date, datetime
import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIG & STYLING
# ==============================================================================

st.set_page_config(
    page_title="SidelineReel | Smart Player Match Review",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    /* Global layout & typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Subtle background adjustment */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Professional Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        color: #F1F5F9;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-weight: 500;
        font-size: 0.95rem;
    }

    /* Metric & Action Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .metric-title {
        color: #64748B;
        font-size: 0.825rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 1.85rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.775rem;
        color: #94A3B8;
        margin-top: 6px;
    }

    /* Badges */
    .badge-review {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-matched {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-corrected {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-unidentified {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    .badge-published {
        background-color: #EDE9FE;
        color: #5B21B6;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }

    /* Banner styling */
    .app-banner {
        background: linear-gradient(90deg, #1E293B 0%, #334155 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Compact Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.15s ease-in-out;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# 2. SYNTHETIC ASSET GENERATOR (Ensures Zero Missing Image Dependencies)
# ==============================================================================


@st.cache_data(show_spinner=False)
def generate_synthetic_jersey_frame(
    jersey_text: str, confidence: float, is_ambiguous: bool
) -> Image.Image:
    """Generates a clean synthetic video crop representing detected jersey frames."""
    img_width, img_height = 420, 240
    bg_color = (30, 41, 59)  # Slate dark
    img = Image.new("RGB", (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw simulated soccer pitch grass background stripe at bottom
    draw.rectangle([0, 180, img_width, img_height], fill=(22, 101, 52))
    draw.line([(0, 180), (img_width, 180)], fill=(255, 255, 255), width=2)

    # Draw simulated jersey silhouette
    body_fill = (29, 78, 216)  # Team Royal Blue
    jersey_points = [
        (130, 50),
        (290, 50),
        (330, 90),
        (300, 110),
        (280, 80),
        (280, 190),
        (140, 190),
        (140, 80),
        (120, 110),
        (90, 90),
    ]
    draw.polygon(jersey_points, fill=body_fill, outline=(255, 255, 255))

    # Draw bounding box overlay
    box_color = (239, 68, 68) if is_ambiguous else (34, 197, 94)
    draw.rectangle([110, 35, 310, 200], outline=box_color, width=3)

    # Jersey Number Text
    num_str = str(jersey_text)
    # Basic centered text simulation using default font
    draw.text(
        (185, 95),
        num_str,
        fill=(255, 255, 255),
        font_size=42,
        anchor="ms" if hasattr(draw, "textbbox") else None,
    )

    # Overlay metadata label inside frame
    tag_bg = (15, 23, 42)
    draw.rectangle([10, 10, 230, 32], fill=tag_bg)
    draw.text(
        (16, 14),
        f"DETECTION CONF: {int(confidence * 100)}%",
        fill=(255, 255, 255),
    )

    return img


# ==============================================================================
# 3. INITIAL STATE SETUP & BUSINESS LOGIC
# ==============================================================================


def init_session_state():
    """Initializes persistent application session state with standard demo data."""

    # Club & Team Metadata
    if "club_info" not in st.session_state:
        st.session_state.club_info = {
            "club_name": "Ridgeline Youth Soccer Club",
            "team_name": "U14 Falcons",
            "season": "2026–27",
            "active_match": "Fall League Quarterfinal vs. Metro Stars",
            "match_date": date(2026, 10, 14),
        }

    # Authoritative Team Roster
    if "roster" not in st.session_state:
        st.session_state.roster = [
            {
                "player_id": "P-101",
                "name": "Liam Anderson",
                "jersey_num": 1,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-102",
                "name": "Oliver Brown",
                "jersey_num": 11,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-103",
                "name": "Noah Wilson",
                "jersey_num": 4,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-104",
                "name": "Ethan Carter",
                "jersey_num": 14,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-105",
                "name": "James Miller",
                "jersey_num": 7,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-106",
                "name": "Daniel Lewis",
                "jersey_num": 9,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-107",
                "name": "Mason Taylor",
                "jersey_num": 10,
                "team": "U14 Falcons",
            },
            {
                "player_id": "P-108",
                "name": "Lucas Martin",
                "jersey_num": 8,
                "team": "U14 Falcons",
            },
        ]

    # Core Highlight Clips Dataset (Deterministic sample cases matching Section 7)
    if "clips" not in st.session_state:
        st.session_state.clips = [
            {
                "clip_id": "SR-1042",
                "time_offset": "14:22",
                "event_type": "Goal",
                "detected_num": 14,
                "ai_suggested_player": "Ethan Carter",
                "ai_suggested_jersey": 14,
                "alt_candidate_player": "Noah Wilson",
                "alt_candidate_jersey": 4,
                "confidence": 0.68,
                "is_ambiguous": True,
                "reason": "Similar jersey number detected (#14 vs #4).",
                "status": "Needs review",
                "assigned_player": None,
                "assigned_jersey": None,
                "coach_decision": None,
                "decision_timestamp": None,
                "published": False,
            },
            {
                "clip_id": "SR-1043",
                "time_offset": "27:45",
                "event_type": "Goalkeeper Save",
                "detected_num": 1,
                "ai_suggested_player": "Liam Anderson",
                "ai_suggested_jersey": 1,
                "alt_candidate_player": "Oliver Brown",
                "alt_candidate_jersey": 11,
                "confidence": 0.72,
                "is_ambiguous": True,
                "reason": "Visually similar jersey numbers (#1 vs #11).",
                "status": "Needs review",
                "assigned_player": None,
                "assigned_jersey": None,
                "coach_decision": None,
                "decision_timestamp": None,
                "published": False,
            },
            {
                "clip_id": "SR-1044",
                "time_offset": "33:10",
                "event_type": "Key Assist",
                "detected_num": 7,
                "ai_suggested_player": "James Miller",
                "ai_suggested_jersey": 7,
                "alt_candidate_player": None,
                "alt_candidate_jersey": None,
                "confidence": 0.98,
                "is_ambiguous": False,
                "reason": "High-confidence identification without roster conflict.",
                "status": "Automatically matched",
                "assigned_player": "James Miller",
                "assigned_jersey": 7,
                "coach_decision": "Auto-Confirmed by AI Rule Engine",
                "decision_timestamp": "2026-10-14 18:02:11",
                "published": False,
            },
            {
                "clip_id": "SR-1045",
                "time_offset": "48:19",
                "event_type": "Tackle",
                "detected_num": None,
                "ai_suggested_player": None,
                "ai_suggested_jersey": None,
                "alt_candidate_player": None,
                "alt_candidate_jersey": None,
                "confidence": 0.25,
                "is_ambiguous": False,
                "reason": "Poor visibility; occluded player back angle.",
                "status": "Unidentified",
                "assigned_player": None,
                "assigned_jersey": None,
                "coach_decision": None,
                "decision_timestamp": None,
                "published": False,
            },
            {
                "clip_id": "SR-1046",
                "time_offset": "56:04",
                "event_type": "Shot on Target",
                "detected_num": 9,
                "ai_suggested_player": "Daniel Lewis",
                "ai_suggested_jersey": 9,
                "alt_candidate_player": None,
                "alt_candidate_jersey": None,
                "confidence": 0.96,
                "is_ambiguous": False,
                "reason": "High-confidence single-digit match.",
                "status": "Automatically matched",
                "assigned_player": "Daniel Lewis",
                "assigned_jersey": 9,
                "coach_decision": "Auto-Confirmed by AI Rule Engine",
                "decision_timestamp": "2026-10-14 18:02:11",
                "published": False,
            },
            {
                "clip_id": "SR-1047",
                "time_offset": "64:30",
                "event_type": "Corner Kick Header",
                "detected_num": 4,
                "ai_suggested_player": "Noah Wilson",
                "ai_suggested_jersey": 4,
                "alt_candidate_player": "Ethan Carter",
                "alt_candidate_jersey": 14,
                "confidence": 0.61,
                "is_ambiguous": True,
                "reason": "Similar jersey number detected (#4 vs #14).",
                "status": "Needs review",
                "assigned_player": None,
                "assigned_jersey": None,
                "coach_decision": None,
                "decision_timestamp": None,
                "published": False,
            },
        ]

    # Persistent Activity Audit Trail
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = [
            {
                "timestamp": "2026-10-14 18:02:12",
                "action": "Ingestion",
                "detail": "Processed match recording 'Fall League Quarterfinal' (6 clips sliced).",
            },
            {
                "timestamp": "2026-10-14 18:02:13",
                "action": "Ambiguity Flag",
                "detail": "Clip #SR-1042 flagged for jersey number ambiguity (#14 vs #4).",
            },
            {
                "timestamp": "2026-10-14 18:02:13",
                "action": "Ambiguity Flag",
                "detail": "Clip #SR-1043 flagged for jersey number ambiguity (#1 vs #11).",
            },
            {
                "timestamp": "2026-10-14 18:02:14",
                "action": "Auto-Match",
                "detail": "Clip #SR-1044 automatically attributed to James Miller (#7).",
            },
        ]

    # Active target clip for deep review modal/panel
    if "selected_review_clip_id" not in st.session_state:
        st.session_state.selected_review_clip_id = "SR-1042"

    # Active page state helper
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"


init_session_state()

# Helper Functions
def log_audit(action: str, detail: str):
    """Appends an event to the persistent operational audit log."""
    st.session_state.audit_logs.insert(
        0,
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "detail": detail,
        },
    )


def get_player_by_name(name: str):
    """Finds player record from roster."""
    for p in st.session_state.roster:
        if p["name"] == name:
            return p
    return None


def get_player_by_jersey(num: int):
    """Finds player record by jersey number."""
    for p in st.session_state.roster:
        if p["jersey_num"] == num:
            return p
    return None


def update_clip_assignment(
    clip_id: str, action_type: str, selected_player_name: str | None = None
):
    """Executes state-safe coach decision logic."""
    for clip in st.session_state.clips:
        if clip["clip_id"] == clip_id:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if action_type == "CONFIRM_SUGGESTION":
                clip["assigned_player"] = clip["ai_suggested_player"]
                clip["assigned_jersey"] = clip["ai_suggested_jersey"]
                clip["status"] = "Coach corrected"
                clip["coach_decision"] = (
                    f"Confirmed suggested player ({clip['assigned_player']} #{clip['assigned_jersey']})"
                )
                clip["decision_timestamp"] = now_str
                log_audit(
                    "Coach Confirmation",
                    f"Clip #{clip_id} confirmed to {clip['assigned_player']} (#{clip['assigned_jersey']}) by coach.",
                )

            elif action_type == "OVERRIDE_ASSIGNMENT":
                player = get_player_by_name(selected_player_name)
                if player:
                    clip["assigned_player"] = player["name"]
                    clip["assigned_jersey"] = player["jersey_num"]
                    clip["status"] = "Coach corrected"
                    clip["coach_decision"] = (
                        f"Reassigned to {player['name']} #{player['jersey_num']} (Original AI: {clip['ai_suggested_player'] or 'None'})"
                    )
                    clip["decision_timestamp"] = now_str
                    log_audit(
                        "Coach Override",
                        f"Clip #{clip_id} overridden to {player['name']} (#{player['jersey_num']}). Previous recommendation: {clip['ai_suggested_player']}.",
                    )

            elif action_type == "MARK_UNIDENTIFIED":
                clip["assigned_player"] = None
                clip["assigned_jersey"] = None
                clip["status"] = "Unidentified"
                clip["coach_decision"] = (
                    "Marked as Unidentified / Held by coach."
                )
                clip["decision_timestamp"] = now_str
                clip["published"] = False
                log_audit(
                    "Hold Decision",
                    f"Clip #{clip_id} marked as Unidentified/Held. Restricted from publication.",
                )
            break


# ==============================================================================
# 4. SIDEBAR NAVIGATION & CONTEXT
# ==============================================================================

with st.sidebar:
    st.markdown("### ⚽ SidelineReel")
    st.caption("AI Youth Sports Highlights • Coach Console")

    st.markdown("---")

    # Team Snapshot Card
    st.markdown(
        f"""
        <div style="background-color: #1E293B; padding: 12px; border-radius: 8px; margin-bottom: 16px;">
            <div style="font-size:0.75rem; color:#94A3B8; text-transform:uppercase; font-weight:600;">Active Roster</div>
            <div style="font-size:1.0rem; color:#FFFFFF; font-weight:700;">{st.session_state.club_info['team_name']}</div>
            <div style="font-size:0.8rem; color:#CBD5E1;">{st.session_state.club_info['club_name']}</div>
            <div style="font-size:0.75rem; color:#38BDF8; margin-top:4px;">Season {st.session_state.club_info['season']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = [
        "1. Dashboard",
        "2. Game Footage",
        "3. Player Match Review",
        "4. Team Roster",
        "5. Publication Center",
        "6. Analytics",
    ]

    selected_nav = st.radio(
        "Navigation",
        nav_options,
        index=[
            "Dashboard",
            "Game Footage",
            "Player Match Review",
            "Team Roster",
            "Publication Center",
            "Analytics",
        ].index(st.session_state.current_page)
        if st.session_state.current_page
        in [
            "Dashboard",
            "Game Footage",
            "Player Match Review",
            "Team Roster",
            "Publication Center",
            "Analytics",
        ]
        else 0,
        label_visibility="collapsed",
    )

    clean_nav_name = selected_nav.split(". ")[1]
    st.session_state.current_page = clean_nav_name

    st.markdown("---")
    st.markdown("#### Review Queue Status")
    pending_count = sum(
        1 for c in st.session_state.clips if c["status"] == "Needs review"
    )
    if pending_count > 0:
        st.warning(
            f"⚠️ **{pending_count} Clip{'s' if pending_count > 1 else ''}** await review"
        )
    else:
        st.success("✅ Review queue clear")

    st.caption("v2.4-interview-prototype • Streamlit Cloud Ready")

# ==============================================================================
# 5. SCREEN 1: DASHBOARD
# ==============================================================================

if st.session_state.current_page == "Dashboard":
    # Top Context Header
    st.markdown(
        f"""
        <div class="app-banner">
            <div>
                <h2 style="margin:0; font-size:1.35rem; font-weight:700;">{st.session_state.club_info['team_name']} — Match Intelligence</h2>
                <p style="margin:4px 0 0 0; font-size:0.85rem; color:#94A3B8;">
                    {st.session_state.club_info['club_name']} • Match: {st.session_state.club_info['active_match']} ({st.session_state.club_info['match_date'].strftime('%b %d, %Y')})
                </p>
            </div>
            <div>
                <span class="badge-review" style="font-size:0.85rem; padding:6px 14px;">Review Mode Active</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Explanatory Value Proposition Banner
    st.info(
        "🛡️ **Safety Protocol Active:** Review uncertain player matches before highlight reels are generated and delivered to families."
    )

    # Calculate live metrics strictly from application state
    total_clips = len(st.session_state.clips)
    auto_matched = sum(
        1
        for c in st.session_state.clips
        if c["status"] == "Automatically matched"
    )
    pending_review = sum(
        1 for c in st.session_state.clips if c["status"] == "Needs review"
    )
    unidentified_clips = sum(
        1 for c in st.session_state.clips if c["status"] == "Unidentified"
    )
    coach_corrected = sum(
        1 for c in st.session_state.clips if c["status"] == "Coach corrected"
    )

    # Verified attribution accuracy calculation:
    # Attribution accuracy reflects verified decisions over completed non-unidentified events
    resolved_count = auto_matched + coach_corrected
    accuracy_metric = (
        round((resolved_count / (total_clips - unidentified_clips)) * 100, 1)
        if (total_clips - unidentified_clips) > 0
        else 100.0
    )

    # Metric KPI Cards Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Clips Processed</div>
                <div class="metric-value">{total_clips}</div>
                <div class="metric-sub">Full 80-minute footage slice</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Automatically Matched</div>
                <div class="metric-value" style="color:#166534;">{auto_matched}</div>
                <div class="metric-sub">Conf ≥ 85% & zero conflict</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #F59E0B;">
                <div class="metric-title">Pending Coach Review</div>
                <div class="metric-value" style="color:#B45309;">{pending_review}</div>
                <div class="metric-sub">Requires verification</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Unidentified Clips</div>
                <div class="metric-value" style="color:#991B1B;">{unidentified_clips}</div>
                <div class="metric-sub">Blocked from release</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Attribution Accuracy</div>
                <div class="metric-value" style="color:#2563EB;">{accuracy_metric}%</div>
                <div class="metric-sub">Illustrative sample baseline</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Primary Action CTA
    col_cta, col_status = st.columns([2, 3])
    with col_cta:
        if st.button(
            "👉 Review Pending Clips Now",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.current_page = "Player Match Review"
            st.rerun()

    with col_status:
        st.caption(
            f"Status: {pending_review} items awaiting coach confirmation before weekly team recap and reels can be distributed."
        )

    st.markdown("---")

    # Lower Section: Recent Operational Activity Audit Trail & Snapshot
    dash_col_left, dash_col_right = st.columns([3, 2])

    with dash_col_left:
        st.subheader("Recent Verification & Activity Log")
        log_df = pd.DataFrame(st.session_state.audit_logs)
        st.dataframe(
            log_df[["timestamp", "action", "detail"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.TextColumn(
                    "Time", width="medium"
                ),
                "action": st.column_config.TextColumn("Event", width="small"),
                "detail": st.column_config.TextColumn(
                    "Description", width="large"
                ),
            },
        )

    with dash_col_right:
        st.subheader("Queue Status Breakdown")
        status_counts = pd.DataFrame(
            [
                {
                    "Status": "Auto-Matched",
                    "Count": auto_matched,
                    "Color": "#22C55E",
                },
                {
                    "Status": "Needs Review",
                    "Count": pending_review,
                    "Color": "#F59E0B",
                },
                {
                    "Status": "Coach Corrected",
                    "Count": coach_corrected,
                    "Color": "#3B82F6",
                },
                {
                    "Status": "Unidentified",
                    "Count": unidentified_clips,
                    "Color": "#EF4444",
                },
            ]
        )
        fig_donut = px.pie(
            status_counts,
            values="Count",
            names="Status",
            hole=0.6,
            color="Status",
            color_discrete_map={
                "Auto-Matched": "#22C55E",
                "Needs Review": "#F59E0B",
                "Coach Corrected": "#3B82F6",
                "Unidentified": "#EF4444",
            },
        )
        fig_donut.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5
            ),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# ==============================================================================
# 6. SCREEN 2: GAME FOOTAGE MANAGEMENT
# ==============================================================================

elif st.session_state.current_page == "Game Footage":
    st.title("Game Footage Ingestion & Processing")
    st.caption(
        "Upload raw match recordings to trigger player detection, event extraction, and ambiguity scoring."
    )

    tab_upload, tab_active = st.tabs(
        ["Upload New Match", "Current Match Assets"]
    )

    with tab_upload:
        st.markdown("#### Match Recording Parameters")

        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            match_title = st.text_input(
                "Match Name",
                value="Championship Semi-Final vs. Westside SC",
            )
            sport = st.selectbox("Sport", ["Soccer", "Basketball", "Lacrosse"])

        with col_meta2:
            team_sel = st.selectbox(
                "Team",
                [st.session_state.club_info["team_name"], "U16 Falcons Girls"],
            )
            match_date = st.date_input("Match Date", value=date.today())

        uploaded_video = st.file_uploader(
            "Select Match Footage (MP4, MOV, AVI)",
            type=["mp4", "mov", "avi"],
            help="In production, this uploads directly to an S3/GCS bucket for asynchronous GPU batch processing.",
        )

        st.markdown("---")

        c_proc, c_demo = st.columns([2, 3])
        with c_proc:
            process_btn = st.button(
                "⚡ Process Footage with AI",
                type="primary",
                use_container_width=True,
            )

        with c_demo:
            load_demo_btn = st.button(
                "🔄 Reset / Load Standard Demonstration Match",
                use_container_width=True,
            )

        if process_btn:
            if uploaded_video is not None:
                st.success(
                    f"Uploaded `{uploaded_video.name}` ({round(uploaded_video.size / (1024*1024), 2)} MB). Running automated tagging..."
                )
            else:
                st.info(
                    "Simulating match ingestion workflow using mock footage pipeline..."
                )

            with st.status(
                "Executing AI Player Identification Pipeline...", expanded=True
            ) as status:
                st.write("1. Slicing match video into high-leverage key moments...")
                st.write(
                    "2. Performing jersey OCR and player tracking on frames..."
                )
                st.write(
                    "3. Cross-referencing detected digits with active U14 Falcons Roster..."
                )
                st.write(
                    "4. Calculating ambiguity scores and confidence intervals..."
                )
                status.update(
                    label="Processing complete! 6 clips tagged.",
                    state="complete",
                    expanded=False,
                )

            st.session_state.club_info["active_match"] = match_title
            st.session_state.club_info["match_date"] = match_date
            log_audit(
                "Match Ingest",
                f"Processed footage '{match_title}'. 6 clips populated in review queue.",
            )
            st.success(
                "Match processed! Navigate to 'Player Match Review' to inspect flagged clips."
            )

        if load_demo_btn:
            init_session_state()
            st.success("Default demonstration match and clips reloaded!")
            st.rerun()

    with tab_active:
        st.subheader("Active Match Manifest")
        st.write(
            f"**Match:** {st.session_state.club_info['active_match']} | **Date:** {st.session_state.club_info['match_date']}"
        )

        manifest_data = []
        for c in st.session_state.clips:
            manifest_data.append(
                {
                    "Clip ID": c["clip_id"],
                    "Timestamp": c["time_offset"],
                    "Event": c["event_type"],
                    "Raw Detected #": c["detected_num"]
                    if c["detected_num"] is not None
                    else "Occluded",
                    "Confidence": f"{int(c['confidence']*100)}%",
                    "Ambiguity Flag": "⚠️ Yes" if c["is_ambiguous"] else "No",
                    "Status": c["status"],
                }
            )
        st.dataframe(
            pd.DataFrame(manifest_data),
            use_container_width=True,
            hide_index=True,
        )

# ==============================================================================
# 7. SCREEN 3: PLAYER MATCH REVIEW (THE PRIMARY WORKFLOW)
# ==============================================================================

elif st.session_state.current_page == "Player Match Review":
    st.title("Player Match Review")
    st.markdown(
        """
        Verify AI-detected jersey attributions before highlight packages are finalized.  
        **Principle:** *AI automates obvious identifications; coaches decide ambiguous calls.*
        """
    )

    # Filter Toolbar
    f_col1, f_col2 = st.columns([3, 2])
    with f_col1:
        status_filter = st.radio(
            "Filter Queue By Status:",
            [
                "Needs review",
                "All clips",
                "Automatically matched",
                "Coach corrected",
                "Unidentified",
            ],
            horizontal=True,
        )

    # Filter data
    filtered_clips = st.session_state.clips
    if status_filter != "All clips":
        filtered_clips = [
            c for c in st.session_state.clips if c["status"] == status_filter
        ]

    st.markdown("---")

    # Main Master-Detail Split Screen
    list_col, detail_col = st.columns([5, 6])

    with list_col:
        st.subheader(f"Clips Queue ({len(filtered_clips)})")

        if not filtered_clips:
            st.info(f"No clips currently in '{status_filter}' status.")
        else:
            for clip in filtered_clips:
                # Determine card accent styling
                border_color = (
                    "#F59E0B"
                    if clip["status"] == "Needs review"
                    else (
                        "#22C55E"
                        if clip["status"] == "Automatically matched"
                        else (
                            "#3B82F6"
                            if clip["status"] == "Coach corrected"
                            else "#EF4444"
                        )
                    )
                )

                badge_class = (
                    "badge-review"
                    if clip["status"] == "Needs review"
                    else (
                        "badge-matched"
                        if clip["status"] == "Automatically matched"
                        else (
                            "badge-corrected"
                            if clip["status"] == "Coach corrected"
                            else "badge-unidentified"
                        )
                    )
                )

                # Card Container
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background:white; border:1px solid #E2E8F0; border-left:5px solid {border_color}; border-radius:8px; padding:12px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="font-size:1.0rem; color:#0F172A;">{clip['clip_id']} — {clip['event_type']}</strong>
                                <span class="{badge_class}">{clip['status']}</span>
                            </div>
                            <div style="font-size:0.85rem; color:#475569; margin-top:4px;">
                                ⏱️ Offset: <b>{clip['time_offset']}</b> | Detected: <b>#{clip['detected_num'] if clip['detected_num'] else 'None'}</b> | AI Conf: <b>{int(clip['confidence']*100)}%</b>
                            </div>
                            <div style="font-size:0.8rem; color:#64748B; margin-top:2px;">
                                AI Suggestion: <b>{clip['ai_suggested_player'] or 'Unidentified'}</b>
                                {f' | Alt: <i>{clip["alt_candidate_player"]}</i>' if clip['alt_candidate_player'] else ''}
                            </div>
                            <div style="font-size:0.75rem; color:#94A3B8; margin-top:4px;">
                                <i>{clip['reason']}</i>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    btn_c1, btn_c2 = st.columns([3, 2])
                    with btn_c1:
                        if st.button(
                            f"Inspect & Review #{clip['clip_id']}",
                            key=f"btn_sel_{clip['clip_id']}",
                            use_container_width=True,
                        ):
                            st.session_state.selected_review_clip_id = clip[
                                "clip_id"
                            ]
                            st.rerun()
                    with btn_c2:
                        if clip["assigned_player"]:
                            st.caption(
                                f"Assigned: **{clip['assigned_player']}**"
                            )
                        else:
                            st.caption("Assigned: *Unassigned*")

    # Detailed Interactive Coach Review Panel
    with detail_col:
        # Fetch active clip
        target_clip = next(
            (
                c
                for c in st.session_state.clips
                if c["clip_id"] == st.session_state.selected_review_clip_id
            ),
            st.session_state.clips[0],
        )

        st.subheader(
            f"Review Console: Clip #{target_clip['clip_id']}"
        )

        with st.container():
            # Synthetic crop visualization representing actual detected frame
            preview_img = generate_synthetic_jersey_frame(
                jersey_text=str(target_clip["detected_num"])
                if target_clip["detected_num"]
                else "?",
                confidence=target_clip["confidence"],
                is_ambiguous=target_clip["is_ambiguous"],
            )
            st.image(
                preview_img,
                caption=f"AI Crop Frame — Detected Jersey: #{target_clip['detected_num'] or 'Occluded'} (Frame Offset {target_clip['time_offset']})",
                use_container_width=True,
            )

            # Metadata Pill Grid
            p1, p2, p3 = st.columns(3)
            with p1:
                st.markdown(
                    f"**Detected Jersey:** #{target_clip['detected_num'] or 'Unknown'}"
                )
                st.markdown(f"**Event:** {target_clip['event_type']}")
            with p2:
                st.markdown(
                    f"**AI Confidence:** {int(target_clip['confidence'] * 100)}%"
                )
                st.markdown(
                    f"**Ambiguity Flag:** {'⚠️ Flagged' if target_clip['is_ambiguous'] else 'Clean'}"
                )
            with p3:
                st.markdown(f"**Current Status:** `{target_clip['status']}`")
                st.markdown(
                    f"**Assigned:** {target_clip['assigned_player'] or 'None'}"
                )

            st.info(f"**AI Engine Diagnostics:** {target_clip['reason']}")

            st.markdown("---")
            st.markdown("#### Coach Verification Action")

            # ACTION 1: Quick Confirm AI Suggested Player
            if target_clip["ai_suggested_player"]:
                sugg_p = get_player_by_name(target_clip["ai_suggested_player"])
                st.markdown(
                    f"**Primary AI Recommendation:** `{target_clip['ai_suggested_player']} (#{target_clip['ai_suggested_jersey']})`"
                )
                if st.button(
                    f"✅ Confirm Attribution: {target_clip['ai_suggested_player']} (#{target_clip['ai_suggested_jersey']})",
                    type="primary",
                    use_container_width=True,
                    key=f"act_confirm_{target_clip['clip_id']}",
                ):
                    update_clip_assignment(
                        target_clip["clip_id"], "CONFIRM_SUGGESTION"
                    )
                    st.success(
                        f"Clip #{target_clip['clip_id']} assigned to {target_clip['ai_suggested_player']}!"
                    )
                    st.rerun()

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # ACTION 2: Correct to Alternative Candidate or Any Roster Player
            st.markdown("**Override / Assign Different Player:**")

            # Collect active roster player names
            roster_names = [
                f"{p['name']} (#{p['jersey_num']})"
                for p in st.session_state.roster
            ]

            # Set sensible default index if alternative candidate exists
            default_override_idx = 0
            if target_clip["alt_candidate_player"]:
                alt_full = f"{target_clip['alt_candidate_player']} (#{target_clip['alt_candidate_jersey']})"
                if alt_full in roster_names:
                    default_override_idx = roster_names.index(alt_full)

            selected_override = st.selectbox(
                "Select Player from Roster",
                options=roster_names,
                index=default_override_idx,
                key=f"select_override_{target_clip['clip_id']}",
            )

            if st.button(
                f"🔄 Reassign Clip to {selected_override.split(' (')[0]}",
                use_container_width=True,
                key=f"act_override_{target_clip['clip_id']}",
            ):
                chosen_name = selected_override.split(" (")[0]
                update_clip_assignment(
                    target_clip["clip_id"], "OVERRIDE_ASSIGNMENT", chosen_name
                )
                st.success(
                    f"Clip #{target_clip['clip_id']} manually updated to {chosen_name}!"
                )
                st.rerun()

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # ACTION 3: Hold / Mark Unidentified
            if st.button(
                "🛑 Mark Clip as Unidentified / Hold from Reel",
                use_container_width=True,
                key=f"act_hold_{target_clip['clip_id']}",
            ):
                update_clip_assignment(
                    target_clip["clip_id"], "MARK_UNIDENTIFIED"
                )
                st.warning(
                    f"Clip #{target_clip['clip_id']} marked as unidentified and withheld from reels."
                )
                st.rerun()

            # Audit record for this clip
            if target_clip["coach_decision"]:
                st.caption(
                    f"Decision History: {target_clip['coach_decision']} at {target_clip['decision_timestamp']}"
                )

# ==============================================================================
# 8. SCREEN 4: TEAM ROSTER MANAGEMENT (SOURCE OF TRUTH)
# ==============================================================================

elif st.session_state.current_page == "Team Roster":
    st.title("Team Roster Management")
    st.caption(
        "The authoritative source of truth. Player numbers modified here immediately sync with AI tagging models."
    )

    col_r1, col_r2 = st.columns([3, 2])

    with col_r1:
        st.subheader(
            f"Active Roster — {st.session_state.club_info['team_name']} ({len(st.session_state.roster)} Athletes)"
        )

        search_query = st.text_input(
            "🔍 Search athlete by name or jersey number...", ""
        )

        # Build table representation
        roster_table = []
        for p in st.session_state.roster:
            # Calculate how many confirmed highlights are assigned to this player
            assigned_clips = sum(
                1
                for c in st.session_state.clips
                if c["assigned_player"] == p["name"]
            )
            roster_table.append(
                {
                    "Player ID": p["player_id"],
                    "Name": p["name"],
                    "Jersey #": p["jersey_num"],
                    "Team": p["team"],
                    "Assigned Clips": assigned_clips,
                }
            )

        roster_df = pd.DataFrame(roster_table)

        if search_query:
            roster_df = roster_df[
                roster_df["Name"]
                .str.lower()
                .contains(search_query.lower())
                | roster_df["Jersey #"].astype(str).str.contains(search_query)
            ]

        st.dataframe(
            roster_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Jersey #": st.column_config.NumberColumn(
                    "Jersey #", format="#%d"
                ),
                "Assigned Clips": st.column_config.NumberColumn(
                    "Verified Clips", format="%d 🎬"
                ),
            },
        )

    with col_r2:
        st.subheader("Roster Modifications")

        with st.expander("➕ Add New Player to Team", expanded=False):
            with st.form("add_player_form"):
                new_name = st.text_input("Player Full Name")
                new_num = st.number_input(
                    "Jersey Number", min_value=0, max_value=99, value=15, step=1
                )
                submitted_add = st.form_submit_button("Save Player to Roster")

                if submitted_add:
                    if not new_name.strip():
                        st.error("Player name cannot be empty.")
                    elif any(
                        p["jersey_num"] == new_num
                        for p in st.session_state.roster
                    ):
                        st.error(
                            f"Jersey #{new_num} is already assigned to another athlete on this team."
                        )
                    else:
                        new_id = f"P-{100 + len(st.session_state.roster) + 1}"
                        st.session_state.roster.append(
                            {
                                "player_id": new_id,
                                "name": new_name.strip(),
                                "jersey_num": int(new_num),
                                "team": st.session_state.club_info["team_name"],
                            }
                        )
                        log_audit(
                            "Roster Added",
                            f"Added {new_name.strip()} (#{new_num}) to roster.",
                        )
                        st.success(
                            f"Added {new_name} (#{new_num}) successfully!"
                        )
                        st.rerun()

        with st.expander("✏️ Edit Jersey Number", expanded=False):
            target_edit_name = st.selectbox(
                "Select Player",
                [p["name"] for p in st.session_state.roster],
                key="edit_p_select",
            )
            curr_player = get_player_by_name(target_edit_name)
            updated_num = st.number_input(
                "New Jersey Number",
                min_value=0,
                max_value=99,
                value=curr_player["jersey_num"] if curr_player else 0,
                key="edit_num_input",
            )

            if st.button("Update Jersey Number"):
                if updated_num != curr_player["jersey_num"] and any(
                    p["jersey_num"] == updated_num
                    for p in st.session_state.roster
                ):
                    st.error(
                        f"Jersey #{updated_num} is already taken by another player."
                    )
                else:
                    old_num = curr_player["jersey_num"]
                    curr_player["jersey_num"] = int(updated_num)
                    log_audit(
                        "Roster Edit",
                        f"Updated {curr_player['name']} from #{old_num} to #{updated_num}.",
                    )
                    st.success(
                        f"Updated {curr_player['name']} to #{updated_num}."
                    )
                    st.rerun()

        with st.expander("🗑️ Remove Player", expanded=False):
            remove_name = st.selectbox(
                "Select Player to Remove",
                [p["name"] for p in st.session_state.roster],
                key="rem_p_select",
            )
            confirm_delete = st.checkbox(
                f"Confirm deletion of {remove_name} from active roster."
            )

            if st.button("Remove from Roster", type="secondary"):
                if confirm_delete:
                    st.session_state.roster = [
                        p
                        for p in st.session_state.roster
                        if p["name"] != remove_name
                    ]
                    log_audit(
                        "Roster Removed",
                        f"Removed athlete {remove_name} from active roster.",
                    )
                    st.warning(f"Player {remove_name} removed.")
                    st.rerun()
                else:
                    st.error("Please check the confirmation box first.")

# ==============================================================================
# 9. SCREEN 5: PUBLICATION CENTER (THE SAFETY MECHANISM)
# ==============================================================================

elif st.session_state.current_page == "Publication Center":
    st.title("Publication & Reel Delivery Center")
    st.markdown(
        """
        <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 12px; border-radius: 6px; margin-bottom: 20px;">
            <strong style="color: #991B1B;">Zero-Leakage Distribution Policy:</strong>
            <span style="color: #7F1D1D;">Only coach-verified or high-confidence auto-matched clips are eligible for family reels. Unresolved or ambiguous clips are strictly blocked.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate status buckets
    eligible_clips = [
        c
        for c in st.session_state.clips
        if c["status"] in ["Automatically matched", "Coach corrected"]
        and c["assigned_player"] is not None
    ]
    unresolved_clips = [
        c for c in st.session_state.clips if c["status"] == "Needs review"
    ]
    unidentified_clips = [
        c for c in st.session_state.clips if c["status"] == "Unidentified"
    ]
    published_clips = [c for c in st.session_state.clips if c.get("published")]

    # Publication Metric Cards
    pub_c1, pub_c2, pub_c3, pub_c4 = st.columns(4)
    with pub_c1:
        st.metric("Eligible for Publish", f"{len(eligible_clips)} Clips")
    with pub_c2:
        st.metric(
            "Blocked: Needs Review",
            f"{len(unresolved_clips)} Clips",
            delta="-Pending" if unresolved_clips else "Clean",
            delta_color="inverse",
        )
    with pub_c3:
        st.metric("Blocked: Unidentified", f"{len(unidentified_clips)} Clips")
    with pub_c4:
        st.metric("Already Distributed", f"{len(published_clips)} Clips")

    st.markdown("---")

    # Publishing Action Controls
    st.subheader("Publication Gate Controls")
    if unresolved_clips:
        st.warning(
            f"⚠️ **{len(unresolved_clips)} clips remain unresolved.** You may publish the {len(eligible_clips)} verified clips, but unresolved clips will be withheld from athlete reels."
        )

    pub_col_btn, pub_col_txt = st.columns([2, 3])
    with pub_col_btn:
        publish_btn = st.button(
            "🚀 Publish Verified Highlights to Family Reels",
            type="primary",
            use_container_width=True,
        )

    if publish_btn:
        if not eligible_clips:
            st.error("No verified clips are currently eligible for publishing.")
        else:
            for c in eligible_clips:
                c["published"] = True
            log_audit(
                "Publication Event",
                f"Published {len(eligible_clips)} verified clips to individual player highlight reels.",
            )
            st.success(
                f"✅ Successfully published {len(eligible_clips)} verified clips! Parents and athletes now have access to their updated reels."
            )
            st.balloons()
            st.rerun()

    st.markdown("---")

    # Athlete Highlight Reel Preview
    st.subheader("Athlete Highlight Reel Preview")
    st.caption(
        "Select a player to preview their verified highlight bundle before family delivery."
    )

    roster_choices = [p["name"] for p in st.session_state.roster]
    preview_athlete = st.selectbox(
        "Select Athlete to Inspect Reel:", roster_choices
    )

    athlete_clips = [
        c
        for c in st.session_state.clips
        if c["assigned_player"] == preview_athlete
    ]

    if not athlete_clips:
        st.info(
            f"No verified clips currently attributed to **{preview_athlete}**."
        )
    else:
        st.write(
            f"**{preview_athlete}** has **{len(athlete_clips)} verified highlight clip{'s' if len(athlete_clips) > 1 else ''}:**"
        )
        for ac in athlete_clips:
            pub_badge = (
                '<span class="badge-published">Published to Parents</span>'
                if ac.get("published")
                else '<span class="badge-review">Verified (Pending Distribution)</span>'
            )
            st.markdown(
                f"""
                <div style="background:white; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong>{ac['clip_id']} — {ac['event_type']}</strong> (Match Time: {ac['time_offset']})
                        <div style="font-size:0.8rem; color:#64748B;">Attribution: #{ac['assigned_jersey']} {ac['assigned_player']} • AI Confidence: {int(ac['confidence']*100)}%</div>
                    </div>
                    <div>{pub_badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# 10. SCREEN 6: PRODUCT ANALYTICS
# ==============================================================================

elif st.session_state.current_page == "Analytics":
    st.title("Attribution Performance & Model Analytics")
    st.caption(
        "Operational telemetry tracking AI accuracy, coach intervention rates, and review queue turnaround."
    )

    # Real Metrics from Application State
    total_clips = len(st.session_state.clips)
    auto_matched = sum(
        1
        for c in st.session_state.clips
        if c["status"] == "Automatically matched"
    )
    coach_corrected = sum(
        1 for c in st.session_state.clips if c["status"] == "Coach corrected"
    )
    pending_review = sum(
        1 for c in st.session_state.clips if c["status"] == "Needs review"
    )
    unidentified_count = sum(
        1 for c in st.session_state.clips if c["status"] == "Unidentified"
    )

    avg_conf = (
        sum(c["confidence"] for c in st.session_state.clips) / total_clips
        if total_clips
        else 0
    )
    resolution_rate = (
        round(((total_clips - pending_review) / total_clips) * 100, 1)
        if total_clips
        else 0
    )

    # Top Metric Tiles
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Clips Processed", total_clips)
    with m2:
        st.metric(
            "Review Queue Resolution",
            f"{resolution_rate}%",
            delta=f"{pending_review} remaining",
            delta_color="inverse",
        )
    with m3:
        st.metric("AI Auto-Attribution Rate", f"{round((auto_matched / total_clips)*100, 1)}%")
    with m4:
        st.metric("Mean Model Confidence", f"{int(avg_conf * 100)}%")

    st.markdown("---")

    # AI Model Confidence vs Actual Attribution Accuracy Note
    st.info(
        """
        ℹ️ **Product Evaluation Principle: Model Confidence vs. Ground Truth Accuracy**  
        • **Model Confidence** is the machine's mathematical estimate from image contrast, digit clarity, and player bounding box geometry.  
        • **Verified Attribution Accuracy** requires human ground-truth labels. A 90% confidence score on digit `1` during jersey occlusion can still be an attribution error if player `#11` is obscured. The Smart Review Queue catches this gap.
        """
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Attribution Decision Breakdown")
        breakdown_df = pd.DataFrame(
            [
                {
                    "Decision Category": "Automatically Matched",
                    "Clips": auto_matched,
                },
                {
                    "Decision Category": "Coach Overridden / Verified",
                    "Clips": coach_corrected,
                },
                {"Decision Category": "Pending Review", "Clips": pending_review},
                {
                    "Decision Category": "Unidentified / Held",
                    "Clips": unidentified_count,
                },
            ]
        )
        fig_bar = px.bar(
            breakdown_df,
            x="Decision Category",
            y="Clips",
            color="Decision Category",
            color_discrete_map={
                "Automatically Matched": "#22C55E",
                "Coach Overridden / Verified": "#3B82F6",
                "Pending Review": "#F59E0B",
                "Unidentified / Held": "#EF4444",
            },
            text="Clips",
        )
        fig_bar.update_layout(
            showlegend=False,
            height=320,
            margin=dict(t=20, b=20, l=20, r=20),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader("Historical Attribution Accuracy (Illustrative)")
        # Clearly labeled illustrative baseline trend
        weeks_data = pd.DataFrame(
            {
                "Match Week": [
                    "Week 1",
                    "Week 2",
                    "Week 3",
                    "Week 4",
                    "Week 5 (Current)",
                ],
                "Verified Accuracy (%)": [82.0, 87.5, 89.0, 93.2, 96.0],
                "Confidence Threshold": [85.0, 85.0, 85.0, 85.0, 85.0],
            }
        )
        fig_line = px.line(
            weeks_data,
            x="Match Week",
            y="Verified Accuracy (%)",
            markers=True,
            title="Accuracy Trend Post-Coach Verification",
        )
        fig_line.add_trace(
            go.Scatter(
                x=weeks_data["Match Week"],
                y=weeks_data["Confidence Threshold"],
                mode="lines",
                name="Confidence Baseline",
                line=dict(dash="dash", color="#94A3B8"),
            )
        )
        fig_line.update_layout(
            height=320,
            margin=dict(t=30, b=20, l=20, r=20),
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5
            ),
        )
        st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # Coach Intervention Telemetry
    st.subheader("Coach Review Efficiency Telemetry")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Avg Review Turnaround</div>
                <div class="metric-value">4.2 min</div>
                <div class="metric-sub">Average time for coaches to resolve flagged clips</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">False Positive Catch Rate</div>
                <div class="metric-value" style="color:#166534;">100%</div>
                <div class="metric-sub">Zero misattributed clips leaked to parents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Coach Agreement with AI</div>
                <div class="metric-value" style="color:#2563EB;">66.7%</div>
                <div class="metric-sub">On flagged ambiguous clips</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #94A3B8; font-size: 0.8rem; padding-bottom: 20px;">
        SidelineReel Prototype • Smart Player Match Review • Built for Ajaia Product Manager Technical Walkthrough
    </div>
    """,
    unsafe_allow_html=True,
)
