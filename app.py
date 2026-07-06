"""
MAIN APP FILE
Run with: streamlit run app.py

The app walks the user through 6 stages, shown as a connected rail on the
sidebar so they always know where they are:

    Upload -> Diagnose -> Clean -> Explore -> Dashboard -> Export

UPLOAD    - read the file in
DIAGNOSE  - show what's wrong with the data (missing values, duplicates, etc.)
CLEAN     - fix those problems, with the user's confirmation at every step
EXPLORE   - real EDA: statistics, single-column charts, and group comparisons
DASHBOARD - the user picks which charts/insights to keep, in one place
EXPORT    - download the dashboard as an image, or the data as Excel
"""

import streamlit as st
import pandas as pd
import uuid

# ---- Our own modules (the files inside modules/) ----
from modules.data_loader import load_file
from modules.type_detector import detect_all_types
from modules.quality_check import (
    missing_value_report, duplicate_report, outlier_report,
    detect_currency_like_columns, detect_messy_text_columns,
    recommend_column_drops, recommend_row_drops
)
from modules.cleaner import (
    remove_duplicate_rows, fill_missing_values, remove_outlier_rows,
    standardize_text_column, clean_currency_column,
    drop_columns, drop_rows_by_index
)
from modules.visualizer import (
    plot_numeric_column, plot_categorical_column,
    plot_timeseries, plot_correlation_heatmap, plot_grouped_comparison,
    plot_scatter, plot_boxplot
)
from modules.eda import summary_statistics_table, grouped_comparison, detect_skewness
from modules.insights import generate_insights
from modules.dashboard import render_chart_from_config
from modules.export import export_cleaned_data_excel


# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(
    page_title="Datawash | Data Cleaner & Analyzer",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DESIGN SYSTEM - custom fonts, colors, and component styling
# ============================================================
st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
        /* ---------- COLOR TOKENS ----------
           Ink Navy   #10192E  -> headings, primary text, hero band
           Paper      #F7F7F5  -> page background
           Slate      #5B6478  -> secondary text
           Teal       #1B8A7A  -> clean / success states
           Amber      #E8A33D  -> insights / highlights
           Coral      #E85D4E  -> issues / warnings found
        */

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        /* ---------- FORCE LIGHT THEME REGARDLESS OF BROWSER/OS DARK MODE ----------
           Root cause of the "invisible text" bug: this app hardcodes light
           backgrounds (white cards, light page bg) but never forced a text
           color for Streamlit's own generic elements (widget labels, plain
           markdown, dataframe headers, alerts, etc). Those elements read
           Streamlit's theme CSS variables, so when a visitor's browser/OS is
           set to dark mode (or they pick "Dark" in the app's Settings menu),
           Streamlit swaps text to a light color while our CSS keeps the
           backgrounds light -> light text on light background = invisible.
           Setting the variables below, plus the safety-net rules further
           down, keeps everything readable no matter the visitor's theme. */
        :root, html, body, .stApp {
            --text-color: #10192E !important;
            --background-color: #F7F7F5 !important;
            --secondary-background-color: #FFFFFF !important;
            --primary-color: #1B8A7A !important;
        }
        .stApp { background-color: #F7F7F5; color: #10192E; }
        #MainMenu, header, footer { visibility: hidden; }
        .block-container { padding-top: 1.5rem; max-width: 1100px; }

        /* Safety net: force a readable ink color on generic Streamlit text
           elements that don't pick up the CSS variables above reliably.
           This is intentionally low-specificity so every hardcoded color
           already in this stylesheet (e.g. white button/masthead text)
           still wins where it's meant to. */
        .stApp p, .stApp span, .stApp li, .stApp label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        [data-testid="stText"],
        [data-testid="stAlert"] p,
        [data-testid="stExpanderDetails"] p,
        h1, h2, h3, h4, h5, h6 {
            color: #10192E;
        }
        section[data-testid="stSidebar"] * { color: #10192E; }
        /* Re-assert intentionally light/white text that must stay light on
           dark backgrounds, so the safety net above never swallows these. */
        .masthead-mark { color: #FFFFFF !important; }
        .masthead-mark span { color: #4DD9C0 !important; }
        .masthead-tag, .masthead-sub { color: #B8C2D4 !important; }
        .stButton button, .stButton button *,
        .stDownloadButton button, .stDownloadButton button * { color: #FFFFFF !important; }
        .stage-number { color: #FFFFFF !important; }

        /* ---------- HERO BAND ---------- */
        .hero-band {
            background: linear-gradient(135deg, #10192E 0%, #172440 60%, #1B8A7A 180%);
            border-radius: 16px;
            padding: 36px 40px;
            margin-bottom: 28px;
            box-shadow: 0 8px 24px rgba(16, 25, 46, 0.18);
            position: relative;
            overflow: hidden;
        }
        .hero-band::after {
            content: "";
            position: absolute;
            top: -40%;
            right: -8%;
            width: 260px;
            height: 260px;
            background: radial-gradient(circle, rgba(232,163,61,0.16) 0%, rgba(232,163,61,0) 70%);
        }
        .masthead { display: flex; align-items: baseline; gap: 14px; margin-bottom: 6px; position: relative; }
        .masthead-mark { font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 32px; color: #FFFFFF; letter-spacing: -0.5px; }
        .masthead-mark span { color: #4DD9C0; }
        .masthead-tag { font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; color: #B8C2D4; text-transform: uppercase; letter-spacing: 1.5px; border-left: 2px solid #E8A33D; padding-left: 10px; }
        .masthead-sub { font-size: 15px; color: #B8C2D4; margin-top: 6px; position: relative; max-width: 560px; }

        /* ---------- STAGE SECTIONS ---------- */
        .stage-header { font-family: 'Space Grotesk', sans-serif; font-size: 21px; font-weight: 600; color: #10192E; margin-top: 6px; margin-bottom: 4px; display: flex; align-items: center; gap: 10px; }
        .stage-number { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600; color: #FFFFFF; background-color: #10192E; border-radius: 50%; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(16,25,46,0.25); }
        .stage-caption { font-size: 13.5px; color: #5B6478; margin-bottom: 18px; margin-left: 36px; }
        .stage-divider { height: 1px; background: linear-gradient(90deg, #E9E7E0 0%, #E9E7E0 70%, transparent 100%); margin: 28px 0; border: none; }

        /* ---------- METRIC CARDS ---------- */
        div[data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #E9E7E0; border-radius: 12px; padding: 18px 20px; box-shadow: 0 2px 8px rgba(16,25,46,0.05); transition: box-shadow 0.15s ease, transform 0.15s ease; }
        div[data-testid="stMetric"]:hover { box-shadow: 0 6px 16px rgba(16,25,46,0.09); transform: translateY(-1px); }
        div[data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; color: #10192E; font-weight: 600; }
        div[data-testid="stMetricLabel"] { font-family: 'Inter', sans-serif; color: #5B6478; }

        /* ---------- BUTTONS ---------- */
        .stButton button, .stDownloadButton button { background-color: #10192E; color: white; border-radius: 8px; border: none; font-family: 'Inter', sans-serif; font-weight: 600; padding: 10px 22px; box-shadow: 0 2px 6px rgba(16,25,46,0.15); transition: all 0.15s ease; }
        .stButton button:hover, .stDownloadButton button:hover { background-color: #1B8A7A; color: white; box-shadow: 0 4px 12px rgba(27,138,122,0.28); transform: translateY(-1px); }

        /* ---------- RECOMMENDATION CARDS (for column/row drop suggestions) ---------- */
        .recommend-card { background-color: #FFF9F0; border: 1px solid #F0D9AE; border-left: 3px solid #E8A33D; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; font-size: 14px; color: #10192E; }
        .recommend-card b { color: #10192E; }

        /* ---------- INSIGHT CARDS ---------- */
        .insight-card { background-color: #FFFFFF; border: 1px solid #E9E7E0; border-left: 3px solid #E8A33D; border-radius: 10px; padding: 13px 18px; margin-bottom: 9px; font-size: 14.5px; color: #10192E; display: flex; gap: 12px; align-items: center; box-shadow: 0 1px 4px rgba(16,25,46,0.04); transition: box-shadow 0.15s ease; }
        .insight-card:hover { box-shadow: 0 4px 12px rgba(16,25,46,0.08); }
        .insight-tag { font-family: 'IBM Plex Mono', monospace; font-size: 10px; font-weight: 600; text-transform: uppercase; color: #E8A33D; white-space: nowrap; }

        /* ---------- DASHBOARD CHART CARDS ---------- */
        .dash-card-label { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #5B6478; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

        /* ---------- SIDEBAR PIPELINE RAIL ---------- */
        section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E9E7E0; }
        .pipeline-step { font-family: 'Inter', sans-serif; font-size: 14px; color: #5B6478; padding: 9px 0 9px 18px; border-left: 2px solid #E9E7E0; margin-bottom: 2px; transition: color 0.15s ease; }
        .pipeline-step.active { color: #10192E; font-weight: 600; border-left: 2px solid #1B8A7A; }
        .pipeline-step .step-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background-color: #1B8A7A; margin-right: 8px; box-shadow: 0 0 0 3px rgba(27,138,122,0.15); }

        /* ---------- DATA TABLES ---------- */
        [data-testid="stDataFrame"] { font-family: 'IBM Plex Mono', monospace; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(16,25,46,0.06); }

        /* ---------- EXPANDERS ---------- */
        div[data-testid="stExpander"] { border: 1px solid #E9E7E0; border-radius: 10px; box-shadow: 0 1px 4px rgba(16,25,46,0.04); background-color: #FFFFFF; }
        div[data-testid="stExpander"] summary { font-family: 'Space Grotesk', sans-serif; font-weight: 600; color: #10192E; }

        /* ---------- TABS ---------- */
        button[data-baseweb="tab"] { font-family: 'Inter', sans-serif; font-weight: 600; color: #5B6478; }
        button[data-baseweb="tab"][aria-selected="true"] { color: #10192E; }
        div[data-baseweb="tab-highlight"] { background-color: #1B8A7A !important; height: 3px !important; }
        div[data-baseweb="tab-border"] { background-color: #E9E7E0; }

      /* ---------- SELECT / CHECKBOX polish ---------- */
div[data-baseweb="select"] > div { border-radius: 8px; border-color: #E9E7E0; }
div[data-baseweb="select"] > div:focus-within { border-color: #1B8A7A; box-shadow: 0 0 0 1px #1B8A7A; }
div[data-baseweb="select"] * { color: #FFFFFF !important; }
ul[role="listbox"] { background-color: #10192E !important; }
ul[role="listbox"] li { color: #FFFFFF !important; }

        /* Dropdown option lists (selectbox/multiselect) render in an overlay
           outside the main app container, so the .stApp-scoped rules above
           never reach them. Force them explicitly here. */
        div[data-baseweb="popover"],
        ul[data-baseweb="menu"] {
            background-color: #FFFFFF !important;
        }
        div[data-baseweb="popover"] *,
        ul[data-baseweb="menu"] * {
            color: #10192E !important;
        }
        div[data-baseweb="popover"] li:hover,
        ul[data-baseweb="menu"] li:hover {
            background-color: #F0F0EE !important;
        }

        div[data-testid="stAlert"] { border-radius: 10px; box-shadow: 0 1px 4px rgba(16,25,46,0.04); }

        /* ---------- FILE UPLOADER (drag-and-drop box) ----------
           This widget renders its own dark dropzone by default and was not
           covered by the earlier text-color fix, leaving "Browse files" and
           the size/type caption invisible (dark text on a dark box). Force
           it to match the rest of the app's light card style. */
        [data-testid="stFileUploaderDropzone"] {
            background-color: #FFFFFF !important;
            border: 1px dashed #E9E7E0 !important;
            border-radius: 10px !important;
        }
        /* Broad safety net: the uploaded-file chip (filename + size) uses a
           low-contrast style Streamlit doesn't expose through theme options,
           so it stays unreadable even after the fixes above. Force it here. */
        [data-testid="stFileUploader"] * {
            color:  #10192E !important;
        }
        [data-testid="stFileUploaderFile"] {
            background-color: #FFFFFF !important;
            border-radius: 8px !important;
        }
        [data-testid="stFileUploaderFile"] svg,
        [data-testid="stFileUploaderDeleteBtn"] svg {
            fill: #5B6478 !important;
        }
        [data-testid="stFileUploaderDropzone"] * {
            color: #f6f8ff !important;
        }
        [data-testid="stFileUploaderDropzone"] svg {
            fill: #5B6478 !important;
        }
        [data-testid="stFileUploaderDropzone"] button,
        [data-testid="stFileUploaderDropzone"] button * ,
        [data-testid="stFileUploaderDropzone"] button svg {
            background-color: #10192E !important;
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            border: none !important;
        }
        [data-testid="stFileUploaderDropzone"] button:hover,
        [data-testid="stFileUploaderDropzone"] button:hover * ,
        [data-testid="stFileUploaderDropzone"] button:hover svg {
            background-color: #1B8A7A !important;
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }
        [data-testid="stFileUploaderFileName"],
        [data-testid="stFileUploaderFileName"] * {
            color: #10192E !important;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# HERO / MASTHEAD
# ============================================================
st.markdown("""
    <div class="hero-band">
        <div class="masthead">
            <div class="masthead-mark">data<span>wash</span></div>
            <div class="masthead-tag">Clean → Explore → Dashboard → Export</div>
        </div>
        <div class="masthead-sub">
            Upload messy data, fix it with confidence, explore what it's really telling you,
            then build and export a dashboard - no coding required.
        </div>
    </div>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# Streamlit reruns the whole script top-to-bottom on every click, so we
# use session_state to "remember" things between those reruns - the
# uploaded data, and the dashboard the user is building.
# ============================================================
if 'df' not in st.session_state:
    st.session_state.df = None
if 'original_row_count' not in st.session_state:
    st.session_state.original_row_count = 0
if 'dashboard_charts' not in st.session_state:
    st.session_state.dashboard_charts = []      # list of chart "recipe" dicts
if 'dashboard_insights' not in st.session_state:
    st.session_state.dashboard_insights = []    # list of insight dicts
if 'dashboard_title' not in st.session_state:
    st.session_state.dashboard_title = "My Dashboard"


def add_chart_to_dashboard(chart_type, title, **params):
    """
    Helper used by every "+ Add to Dashboard" button. Stores a lightweight
    description of the chart (not the chart itself) so it can be rebuilt
    later, and shows a small confirmation toast.
    """
    config = {'id': str(uuid.uuid4()), 'type': chart_type, 'title': title, **params}
    st.session_state.dashboard_charts.append(config)
    st.toast(f"Added '{title}' to dashboard")


def add_insight_to_dashboard(insight):
    """Adds one insight dict to the dashboard's insight list, avoiding exact duplicates."""
    if insight not in st.session_state.dashboard_insights:
        st.session_state.dashboard_insights.append(insight)
        st.toast("Insight added to dashboard")


# ============================================================
# SIDEBAR - pipeline rail
# ============================================================
with st.sidebar:
    st.markdown("<div style='font-family:Space Grotesk,sans-serif; font-weight:700; font-size:15px; color:#10192E; margin-bottom:14px;'>THE PIPELINE</div>", unsafe_allow_html=True)

    stages = ["Upload", "Diagnose", "Clean", "Explore", "Dashboard", "Export"]
    active = st.session_state.df is not None
    for stage in stages:
        css_class = "pipeline-step active" if active else "pipeline-step"
        st.markdown(f"<div class='{css_class}'><span class='step-dot'></span>{stage}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.dashboard_charts or st.session_state.dashboard_insights:
        st.caption(f"📊 {len(st.session_state.dashboard_charts)} chart(s), {len(st.session_state.dashboard_insights)} insight(s) in your dashboard")

    st.caption("Built with Python, pandas, and Streamlit.")


# ============================================================
# STAGE 1: UPLOAD
# ============================================================
st.markdown("<div class='stage-header'><span class='stage-number'>1</span> Upload your file</div>", unsafe_allow_html=True)
st.markdown("<div class='stage-caption'>CSV or Excel, any structure. We'll figure out what's inside.</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'xls'], label_visibility="collapsed")

if uploaded_file is not None:
    if st.session_state.df is None:
        df, error = load_file(uploaded_file)
        if error:
            st.error(f"⚠ {error}")
        else:
            st.session_state.df = df
            st.session_state.original_row_count = len(df)
            st.success(f"Loaded successfully — {len(df):,} rows, {len(df.columns)} columns detected.")

if st.session_state.df is not None:
    if st.button("↺ Start over with a new file"):
        st.session_state.df = None
        st.session_state.original_row_count = 0
        st.session_state.dashboard_charts = []
        st.session_state.dashboard_insights = []
        st.rerun()


# ============================================================
# Everything below only runs once a file is loaded
# ============================================================
if st.session_state.df is not None:
    df = st.session_state.df

    with st.expander("Preview raw data (first 10 rows)"):
        st.dataframe(df.head(10), width='stretch')

    column_types = detect_all_types(df)

    st.markdown("<div class='stage-divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # STAGE 2: DIAGNOSE
    # ============================================================
    st.markdown("<div class='stage-header'><span class='stage-number'>2</span> Diagnose data quality</div>", unsafe_allow_html=True)
    st.markdown("<div class='stage-caption'>A health check before we touch anything.</div>", unsafe_allow_html=True)

    missing_data = missing_value_report(df)
    duplicate_count = duplicate_report(df)
    outliers = outlier_report(df, column_types)
    currency_columns = detect_currency_like_columns(df, column_types)
    messy_text_columns = detect_messy_text_columns(df, column_types)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total rows", f"{len(df):,}")
    col2.metric("Total columns", len(df.columns))
    col3.metric("Duplicate rows", duplicate_count)
    col4.metric("Columns with gaps", len(missing_data))

    st.markdown("<br>", unsafe_allow_html=True)

    if missing_data:
        st.markdown("**Missing values found**")
        st.dataframe(pd.DataFrame(missing_data), width='stretch', hide_index=True)
    else:
        st.success("No missing values found.")

    if outliers:
        st.markdown("**Potential outliers found** (IQR method — values far outside the normal spread)")
        st.dataframe(pd.DataFrame(outliers), width='stretch', hide_index=True)

    if currency_columns:
        st.markdown(f"**Currency-formatted columns found:** {', '.join(currency_columns)} — numbers hidden behind symbols like $ or commas.")

    if messy_text_columns:
        st.markdown(f"**Inconsistent text formatting found:** {', '.join(messy_text_columns)} — extra spaces or mixed capitalization.")

    st.markdown("<div class='stage-divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # STAGE 3: CLEAN
    # ============================================================
    st.markdown("<div class='stage-header'><span class='stage-number'>3</span> Clean your data</div>", unsafe_allow_html=True)
    st.markdown("<div class='stage-caption'>Every fix here is a suggestion. Nothing changes until you tick the box.</div>", unsafe_allow_html=True)

    cleaned_df = df.copy()

    # ---- 3a. Duplicate rows ----
    if duplicate_count > 0:
        if st.checkbox(f"Remove {duplicate_count} duplicate row(s)"):
            cleaned_df = remove_duplicate_rows(cleaned_df)

    # ---- 3b. High-missingness COLUMN drop recommendations ----
    st.markdown("**Drop columns that are mostly empty**")
    column_missing_threshold = st.slider(
        "A column gets flagged if this % (or more) of it is missing",
        min_value=10, max_value=95, value=50, step=5,
        key="column_threshold"
    )
    column_drop_recs = recommend_column_drops(cleaned_df, missing_threshold=column_missing_threshold)

    if column_drop_recs:
        columns_to_drop = []
        for rec in column_drop_recs:
            st.markdown(f"""
                <div class="recommend-card">
                    Column <b>'{rec['column']}'</b> is <b>{rec['missing_percent']}%</b> empty
                    ({rec['missing_count']} of {rec['total_rows']} rows missing).
                    Filling this much data in wouldn't be trustworthy.
                </div>
            """, unsafe_allow_html=True)
            if st.checkbox(f"Drop column '{rec['column']}'", key=f"dropcol_{rec['column']}"):
                columns_to_drop.append(rec['column'])
        if columns_to_drop:
            cleaned_df = drop_columns(cleaned_df, columns_to_drop)
    else:
        st.caption(f"No columns are {column_missing_threshold}%+ empty.")

    # ---- 3c. High-missingness ROW drop recommendation ----
    st.markdown("**Drop rows that are mostly empty**")
    row_missing_threshold = st.slider(
        "A row gets flagged if this % (or more) of ITS fields are missing",
        min_value=10, max_value=95, value=50, step=5,
        key="row_threshold"
    )
    row_drop_rec = recommend_row_drops(cleaned_df, missing_threshold=row_missing_threshold)

    if row_drop_rec['row_count'] > 0:
        st.markdown(f"""
            <div class="recommend-card">
                <b>{row_drop_rec['row_count']} row(s)</b> ({row_drop_rec['percent_of_data']}% of your data)
                have {row_missing_threshold}%+ of their fields empty.
            </div>
        """, unsafe_allow_html=True)
        if st.checkbox(f"Drop these {row_drop_rec['row_count']} row(s)", key="droprows_check"):
            cleaned_df = drop_rows_by_index(cleaned_df, row_drop_rec['row_indices'])
    else:
        st.caption(f"No rows are {row_missing_threshold}%+ empty.")

    # ---- Recompute column types now, since drops above may have changed the data ----
    current_column_types = detect_all_types(cleaned_df)

    # ---- 3d. Currency cleaning (runs before missing-value fill, since it changes column type) ----
    current_currency_columns = detect_currency_like_columns(cleaned_df, current_column_types)
    if current_currency_columns:
        st.markdown("**Fix currency-formatted columns**")
        for column in current_currency_columns:
            if st.checkbox(f"Convert '{column}' from currency text to numbers (e.g. \"$1,200\" → 1200)", key=f"currency_{column}"):
                cleaned_df = clean_currency_column(cleaned_df, column)
                current_column_types[column] = 'numeric'

    # ---- 3e. Text standardization ----
    current_messy_columns = detect_messy_text_columns(cleaned_df, current_column_types)
    if current_messy_columns:
        st.markdown("**Standardize inconsistent text formatting**")
        for column in current_messy_columns:
            if st.checkbox(f"Clean up spacing/capitalization in '{column}'", key=f"standardize_{column}"):
                cleaned_df = standardize_text_column(cleaned_df, column)

    # ---- 3f. Missing value handling, column by column ----
    current_missing = missing_value_report(cleaned_df)
    if current_missing:
        st.markdown("**Handle remaining missing values, column by column**")
        for item in current_missing:
            column = item['column']
            col_type = current_column_types.get(column)

            if col_type == 'numeric':
                options = ["Leave as-is", "Fill with mean", "Fill with median", "Drop rows"]
            else:
                options = ["Leave as-is", "Fill with most common value", "Drop rows"]

            choice = st.selectbox(f"{column} ({item['missing_percent']}% missing)", options, key=f"missing_{column}")

            if choice == "Fill with mean":
                cleaned_df = fill_missing_values(cleaned_df, column, "mean")
            elif choice == "Fill with median":
                cleaned_df = fill_missing_values(cleaned_df, column, "median")
            elif choice == "Fill with most common value":
                cleaned_df = fill_missing_values(cleaned_df, column, "mode")
            elif choice == "Drop rows":
                cleaned_df = fill_missing_values(cleaned_df, column, "drop")

    # ---- 3g. Outlier handling ----
    current_outliers = outlier_report(cleaned_df, current_column_types)
    if current_outliers:
        st.markdown("**Handle outliers**")
        for item in current_outliers:
            column = item['column']
            if st.checkbox(f"Remove {item['outlier_count']} outlier row(s) in '{column}' (outside {item['lower_bound']} to {item['upper_bound']})", key=f"outlier_{column}"):
                cleaned_df = remove_outlier_rows(cleaned_df, column, item['lower_bound'], item['upper_bound'])

    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"Rows before cleaning: **{len(df):,}**  →  Rows after cleaning: **{len(cleaned_df):,}**  |  Columns before: **{len(df.columns)}**  →  after: **{len(cleaned_df.columns)}**")

    with st.expander("Preview cleaned data"):
        st.dataframe(cleaned_df.head(10), width='stretch')

    st.markdown("<div class='stage-divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # STAGE 4: EXPLORE (real EDA)
    # ============================================================
    st.markdown("<div class='stage-header'><span class='stage-number'>4</span> Explore</div>", unsafe_allow_html=True)
    st.markdown("<div class='stage-caption'>Click <b>+ Add to Dashboard</b> on anything you want to keep.</div>", unsafe_allow_html=True)

    cleaned_column_types = detect_all_types(cleaned_df)
    numeric_columns = [c for c, t in cleaned_column_types.items() if t == 'numeric']
    categorical_columns = [c for c, t in cleaned_column_types.items() if t == 'categorical']
    date_columns = [c for c, t in cleaned_column_types.items() if t == 'date']

    # ---- Summary statistics table - the classic "describe()" every DA checks first ----
    if numeric_columns:
        st.markdown("**Summary statistics**")
        stats_df = summary_statistics_table(cleaned_df, numeric_columns)
        st.dataframe(stats_df, width='stretch')

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Numeric", "Categorical", "Time trends", "Compare groups", "Relationships", "Spread"]
    )

    # ---- Numeric tab ----
    with tab1:
        if numeric_columns:
            selected_numeric = st.selectbox("Column", numeric_columns, key="viz_numeric")
            fig = plot_numeric_column(cleaned_df, selected_numeric)
            st.plotly_chart(fig, width='stretch')

            skew_info = detect_skewness(cleaned_df[selected_numeric])
            st.caption(f"Skewness: {skew_info['skew_value']} — {skew_info['interpretation']}")

            if st.button("+ Add to Dashboard", key="add_numeric"):
                add_chart_to_dashboard('numeric', f"Distribution of {selected_numeric}", column=selected_numeric)

            if len(numeric_columns) >= 2:
                st.markdown("<br>", unsafe_allow_html=True)
                corr_fig = plot_correlation_heatmap(cleaned_df, numeric_columns)
                st.plotly_chart(corr_fig, width='stretch')
                if st.button("+ Add to Dashboard", key="add_correlation"):
                    add_chart_to_dashboard('correlation', "Correlation Heatmap", columns=numeric_columns)
        else:
            st.caption("No numeric columns detected in this dataset.")

    # ---- Categorical tab ----
    with tab2:
        if categorical_columns:
            selected_cat = st.selectbox("Column", categorical_columns, key="viz_cat")

            c1, c2 = st.columns([2, 1])
            search_term = c1.text_input("Search for a specific category (optional)", key="cat_search", placeholder="e.g. Data Analyst")
            top_n = c2.slider("Show top N", min_value=5, max_value=50, value=15, step=5, key="cat_topn")

            fig = plot_categorical_column(cleaned_df, selected_cat, top_n=top_n, search_term=search_term if search_term else None)

            if fig is None:
                st.warning(f"No categories matching '{search_term}' were found in '{selected_cat}'.")
            else:
                st.plotly_chart(fig, width='stretch')
                if st.button("+ Add to Dashboard", key="add_categorical"):
                    add_chart_to_dashboard('categorical', f"Count of {selected_cat}", column=selected_cat, top_n=top_n)
        else:
            st.caption("No categorical columns detected in this dataset.")

    # ---- Time trends tab ----
    with tab3:
        if date_columns and numeric_columns:
            c1, c2 = st.columns(2)
            selected_date = c1.selectbox("Date column", date_columns, key="viz_date")
            selected_value = c2.selectbox("Value to plot", numeric_columns, key="viz_value")
            fig = plot_timeseries(cleaned_df, selected_date, selected_value)
            st.plotly_chart(fig, width='stretch')
            if st.button("+ Add to Dashboard", key="add_timeseries"):
                add_chart_to_dashboard('timeseries', f"{selected_value} over time", date_column=selected_date, value_column=selected_value)
        else:
            st.caption("Need at least one date column and one numeric column for time trends.")

    # ---- Compare groups tab (bivariate EDA) - bar shows the average, box shows the full spread ----
    with tab4:
        if categorical_columns and numeric_columns:
            c1, c2, c3, c4 = st.columns(4)
            group_col = c1.selectbox("Group by", categorical_columns, key="cmp_group")
            value_col = c2.selectbox("Compare", numeric_columns, key="cmp_value")
            chart_style = c3.selectbox("Chart style", ["Bar (aggregate)", "Box (full spread)"], key="cmp_style")

            if chart_style == "Bar (aggregate)":
                agg_method = c4.selectbox("Using", ["mean", "median", "sum", "count"], key="cmp_agg")
                grouped_df = grouped_comparison(cleaned_df, group_col, value_col, agg_method)
                value_label = f"{agg_method.title()} {value_col}"
                fig = plot_grouped_comparison(grouped_df, group_col, value_label)
                st.plotly_chart(fig, width='stretch')

                if st.button("+ Add to Dashboard", key="add_grouped"):
                    add_chart_to_dashboard(
                        'grouped', f"{value_label} by {group_col}",
                        group_column=group_col, value_column=value_col, agg=agg_method
                    )
            else:
                st.caption("A bar shows one average per group - a box shows the FULL spread, so you can see if a group's 'average' is hiding a wide range.")
                fig = plot_boxplot(cleaned_df, value_col, group_column=group_col)
                st.plotly_chart(fig, width='stretch')

                if st.button("+ Add to Dashboard", key="add_box_grouped"):
                    add_chart_to_dashboard(
                        'boxplot', f"Spread of {value_col} by {group_col}",
                        numeric_column=value_col, group_column=group_col
                    )
        else:
            st.caption("Need at least one categorical column and one numeric column to compare groups.")

    # ---- Relationships tab (scatter plot) ----
    with tab5:
        if len(numeric_columns) >= 2:
            c1, c2, c3 = st.columns(3)
            x_col = c1.selectbox("X axis", numeric_columns, key="scatter_x")
            y_options = [c for c in numeric_columns if c != x_col]
            y_col = c2.selectbox("Y axis", y_options, key="scatter_y")
            color_options = ["None"] + categorical_columns
            color_col = c3.selectbox("Color by (optional)", color_options, key="scatter_color")
            color_col = None if color_col == "None" else color_col

            st.caption("The correlation heatmap tells you HOW STRONGLY two columns relate - this shows you the actual SHAPE of that relationship, including clusters or outliers a single number can't reveal.")

            fig = plot_scatter(cleaned_df, x_col, y_col, color_column=color_col)
            st.plotly_chart(fig, width='stretch')

            if st.button("+ Add to Dashboard", key="add_scatter"):
                title = f"{y_col} vs {x_col}" + (f" by {color_col}" if color_col else "")
                add_chart_to_dashboard('scatter', title, x_column=x_col, y_column=y_col, color_column=color_col)
        else:
            st.caption("Need at least two numeric columns to plot a relationship.")

    # ---- Spread tab (box plot, single column - visualizes the same IQR logic used in cleaning) ----
    with tab6:
        if numeric_columns:
            selected_spread_col = st.selectbox("Column", numeric_columns, key="spread_col")
            st.caption("This is the same IQR method used in the Clean stage to detect outliers - now you can actually see it. Dots beyond the whiskers are the flagged outliers.")

            fig = plot_boxplot(cleaned_df, selected_spread_col)
            st.plotly_chart(fig, width='stretch')

            if st.button("+ Add to Dashboard", key="add_boxplot_single"):
                add_chart_to_dashboard('boxplot', f"Spread of {selected_spread_col}", numeric_column=selected_spread_col)
        else:
            st.caption("No numeric columns detected in this dataset.")

    # ---- Auto-generated insights, each addable to the dashboard ----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Key insights**")
    insights = generate_insights(cleaned_df, cleaned_column_types, st.session_state.original_row_count)

    for index, insight in enumerate(insights):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"""
            <div class="insight-card">
                <span class="insight-tag">{insight['type']}</span>
                <span>{insight['text']}</span>
            </div>
        """, unsafe_allow_html=True)
        if c2.button("+ Add", key=f"add_insight_{index}"):
            add_insight_to_dashboard(insight)

    st.markdown("<div class='stage-divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # STAGE 5: DASHBOARD
    # ============================================================
    st.markdown("<div class='stage-header'><span class='stage-number'>5</span> Your dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='stage-caption'>Everything you've added, in one place. Remove anything you don't want.</div>", unsafe_allow_html=True)

    st.session_state.dashboard_title = st.text_input("Dashboard title", value=st.session_state.dashboard_title)

    if not st.session_state.dashboard_charts and not st.session_state.dashboard_insights:
        st.markdown("""
            <div style="background-color:#FFFFFF; border:1px dashed #E9E7E0; border-radius:12px;
                        padding:32px; text-align:center; color:#5B6478;">
                Nothing here yet — go back to <b>Explore</b> and click <b>+ Add to Dashboard</b>
                on any chart or insight you'd like to keep.
            </div>
        """, unsafe_allow_html=True)
    else:
        # Render charts in a 2-column grid, each with a remove button
        if st.session_state.dashboard_charts:
            st.markdown("**Charts**")
            chart_columns = st.columns(2)
            for index, config in enumerate(st.session_state.dashboard_charts):
                with chart_columns[index % 2]:
                    st.markdown(f"<div class='dash-card-label'>{config['title']}</div>", unsafe_allow_html=True)
                    fig = render_chart_from_config(cleaned_df, config)
                    if fig is not None:
                        st.plotly_chart(fig, width='stretch', key=f"dash_chart_{config['id']}")
                    if st.button("Remove", key=f"remove_chart_{config['id']}"):
                        st.session_state.dashboard_charts = [
                            c for c in st.session_state.dashboard_charts if c['id'] != config['id']
                        ]
                        st.rerun()

        # Render insights below the charts, each with a remove button
        if st.session_state.dashboard_insights:
            st.markdown("**Insights**")
            for index, insight in enumerate(st.session_state.dashboard_insights):
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"""
                    <div class="insight-card">
                        <span class="insight-tag">{insight['type']}</span>
                        <span>{insight['text']}</span>
                    </div>
                """, unsafe_allow_html=True)
                if c2.button("Remove", key=f"remove_insight_{index}"):
                    st.session_state.dashboard_insights.pop(index)
                    st.rerun()

    st.markdown("<div class='stage-divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # STAGE 6: EXPORT
    # ============================================================
    st.markdown("<div class='stage-header'><span class='stage-number'>6</span> Export</div>", unsafe_allow_html=True)
    st.markdown("<div class='stage-caption'>Take your work with you.</div>", unsafe_allow_html=True)

    st.caption("💡 Want just one chart? Hover over any chart above and click the camera icon in its top-right corner to download that single chart as a PNG.")

    st.markdown("**Full Excel report**")
    st.caption("One workbook: your cleaned data, summary statistics, saved insights, and every dashboard chart as an embedded image - all in one file you can open, filter, and build on.")

    dashboard_figures = [
        render_chart_from_config(cleaned_df, config)
        for config in st.session_state.dashboard_charts
    ]
    dashboard_figures = [f for f in dashboard_figures if f is not None]

    if 'excel_bytes' not in st.session_state:
        st.session_state.excel_bytes = None

    if st.button("Generate Excel report"):
        summary_for_export = summary_statistics_table(cleaned_df, numeric_columns) if numeric_columns else None
        with st.spinner("Preparing your Excel report..."):
            st.session_state.excel_bytes = export_cleaned_data_excel(
                cleaned_df,
                summary_stats_df=summary_for_export,
                insights_list=st.session_state.dashboard_insights if st.session_state.dashboard_insights else insights,
                dashboard_figures=dashboard_figures if dashboard_figures else None
            )

    if st.session_state.excel_bytes:
        st.download_button(
            "⬇ Download Excel report",
            data=st.session_state.excel_bytes,
            file_name="datawash_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if not dashboard_figures:
        st.caption("No charts added yet - the report will still include your cleaned data and insights. Go to Explore and click '+ Add to Dashboard' to include charts too.")

else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background-color:#FFFFFF; border:1px dashed #E9E7E0; border-radius:12px;
                    padding:40px; text-align:center; color:#5B6478;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:17px; color:#10192E; margin-bottom:6px;">
                Waiting for a file
            </div>
            <div style="font-size:14px;">
                Upload a CSV or Excel file above to begin the pipeline.
            </div>
        </div>
    """, unsafe_allow_html=True)
