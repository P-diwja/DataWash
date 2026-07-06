"""
This file creates the CHARTS shown to the user.
It picks the right chart type automatically based on the column's data type.
We use Plotly because it makes charts you can zoom/hover on, which looks
more professional than a plain static image.

IMPORTANT FONT NOTE:
The app's page (headings, buttons, etc.) uses custom Google Fonts loaded
via an HTML <link> tag - that works because your browser fetches them.
But when a chart gets exported as a static PNG (see modules/export.py),
the export engine (Kaleido) renders the chart completely separately from
the web page, and has NO access to those Google Fonts. If we told Plotly
to use "Space Grotesk" for chart titles, Kaleido would silently substitute
some other font with different letter widths - which is exactly what was
cutting off titles and axis labels in exported dashboard images.

The fix: charts use plain, universally available fonts ("Arial, sans-serif")
instead of the custom web fonts. This keeps on-screen charts and exported
images looking identical and correctly sized, everywhere.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---- Shared theme values, matching the app's CSS palette ----
INK_NAVY = "#10192E"
SIGNAL_AMBER = "#9C6318"  # darkened from #E8A33D - original failed WCAG 3:1 minimum against white chart background
CIRCUIT_TEAL = "#1B8A7A"
ALERT_CORAL = "#E85D4E"
SLATE = "#5B6478"
PAPER = "#F7F7F5"
MUTED_BLUE = "#4A7A93"

# A base layout style reused across every chart for visual consistency.
# Font family is intentionally plain/universal (see note above) so charts
# render identically on-screen and in exported PNG images.
BASE_LAYOUT = dict(
    font=dict(family="Arial, sans-serif", color=INK_NAVY, size=13),
    title_font=dict(family="Arial, sans-serif", size=17, color=INK_NAVY),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=50, r=40, t=65, b=45),
)


def plot_numeric_column(df, column):
    """
    For a numeric column, we show a histogram (how the values are spread out).
    Example: shows most sales fall between 100-200, with a few very high ones.
    """
    fig = px.histogram(df, x=column, nbins=30)
    fig.update_traces(marker_color=CIRCUIT_TEAL, marker_line_color="white", marker_line_width=1)
    fig.update_layout(
        title=f"Distribution of {column}",
        bargap=0.08,
        **BASE_LAYOUT
    )
    # automargin=True tells Plotly to measure the actual rendered text and
    # expand the margin if needed, instead of trusting our fixed guess -
    # this is what prevents titles/labels from ever getting clipped.
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="#eef0f4", automargin=True)
    return fig


def plot_categorical_column(df, column, top_n=15, search_term=None):
    """
    For a categorical column, we show a bar chart counting how many times
    each category appears. Example: how many "Small", "Medium", "Large" orders.

    Real-world columns like "Job Title" can have hundreds of different values -
    plotting all of them makes the chart unreadable. So by default we only
    show the top_n most frequent categories, grouping the rest into "Other".

    If the user types a search_term, we skip the top_n grouping entirely and
    instead show only categories whose name contains that search text - this
    lets someone find a specific category (like "Data Analyst") even if it
    wasn't common enough to make the top 15.

    Returns None if a search_term was given but nothing matched, so the
    calling code can show a friendly "no matches" message instead of an
    empty chart.
    """
    value_counts = df[column].value_counts()
    total_categories = len(value_counts)

    if search_term:
        matched = value_counts[
            value_counts.index.astype(str).str.contains(search_term, case=False, na=False)
        ]
        if len(matched) == 0:
            return None

        chart_data = matched.reset_index()
        chart_data.columns = [column, 'count']
        chart_title = f"Categories in {column} matching '{search_term}'"

    elif total_categories > top_n:
        top_values = value_counts.head(top_n)
        other_count = value_counts.iloc[top_n:].sum()
        top_values = pd.concat([top_values, pd.Series({'Other': other_count})])
        chart_data = top_values.reset_index()
        chart_data.columns = [column, 'count']
        chart_title = f"Top {top_n} categories in {column} (of {total_categories} total)"

    else:
        chart_data = value_counts.reset_index()
        chart_data.columns = [column, 'count']
        chart_title = f"Count of each category in {column}"

    chart_data = chart_data.sort_values('count', ascending=True)

    real_categories = chart_data[chart_data[column] != 'Other']
    top_category = real_categories.sort_values('count', ascending=False)[column].iloc[0] if not real_categories.empty else None

    bar_colors = [
        INK_NAVY if val == top_category else MUTED_BLUE
        for val in chart_data[column]
    ]

    fig = go.Figure(go.Bar(
        x=chart_data['count'],
        y=chart_data[column],
        orientation='h',
        marker_color=bar_colors,
        marker_line_color="white",
        marker_line_width=1,
        text=chart_data['count'],
        textposition='outside',
        textfont=dict(color=INK_NAVY, size=12, family="Arial, sans-serif")
    ))

    fig.update_layout(
        title=chart_title,
        xaxis_title="Count",
        yaxis_title="",
        **BASE_LAYOUT
    )
    # automargin is critical here specifically - horizontal bars put category
    # names (which can be long, like job titles) directly on the y-axis, and
    # value labels just past the bar end on the x-axis. Both need room that
    # depends on the actual text, not a fixed guess.
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="white", automargin=True)
    return fig


def plot_timeseries(df, date_column, numeric_column):
    """
    Shows how a numeric value changes over time.
    Example: how Sales changed month by month.
    """
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df = df.dropna(subset=[date_column]).sort_values(by=date_column)

    fig = px.line(df, x=date_column, y=numeric_column)
    fig.update_traces(line_color=INK_NAVY, line_width=2.5)
    fig.update_layout(
        title=f"{numeric_column} over time",
        **BASE_LAYOUT
    )
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="#eef0f4", automargin=True)
    return fig


def plot_correlation_heatmap(df, numeric_columns):
    """
    Shows how strongly numeric columns are related to each other.
    Example: does higher "Marketing Spend" relate to higher "Sales"?
    A value close to 1 means strong positive relationship,
    close to -1 means strong negative relationship, close to 0 means no relationship.
    """
    corr_matrix = df[numeric_columns].corr()

    # Teal endpoint is lightened from the brand CIRCUIT_TEAL specifically
    # here - the navy cell-number text on top needs 4.5:1 contrast even at
    # the strongest correlation values, which full-strength CIRCUIT_TEAL fails.
    custom_scale = [
        [0.0, ALERT_CORAL],
        [0.5, "#f5f2ea"],
        [1.0, "#3DB5A1"],
    ]

    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale=custom_scale,
        zmin=-1, zmax=1,
    )
    fig.update_layout(
        title="Correlation Heatmap - how numeric columns relate to each other",
        **BASE_LAYOUT
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def plot_grouped_comparison(grouped_df, group_column, value_label):
    """
    Shows a bar chart comparing an aggregated numeric value (like average
    Sales) across categories of another column (like Region).

    This is the core "bivariate" chart for real EDA - it answers questions
    like "does Region actually affect Sales?" instead of just showing each
    column separately.

    grouped_df is expected to have two columns: the group column, and the
    aggregated value column (already computed by eda.grouped_comparison).
    """
    value_column = grouped_df.columns[1]
    grouped_df = grouped_df.sort_values(value_column, ascending=True)

    max_value = grouped_df[value_column].max()
    bar_colors = [
        INK_NAVY if val == max_value else CIRCUIT_TEAL
        for val in grouped_df[value_column]
    ]

    fig = go.Figure(go.Bar(
        x=grouped_df[value_column],
        y=grouped_df[group_column],
        orientation='h',
        marker_color=bar_colors,
        marker_line_color="white",
        marker_line_width=1,
        text=grouped_df[value_column].round(1),
        textposition='outside',
        textfont=dict(color=INK_NAVY, size=12, family="Arial, sans-serif")
    ))

    fig.update_layout(
        title=f"{value_label} by {group_column}",
        xaxis_title=value_label,
        yaxis_title="",
        **BASE_LAYOUT
    )
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="white", automargin=True)
    return fig


def plot_scatter(df, x_column, y_column, color_column=None):
    """
    Shows the relationship between TWO numeric columns as individual dots -
    one dot per row of data.

    Why this matters beyond the correlation heatmap: the heatmap gives you
    a single number summarizing how related two columns are, but it can't
    show you the SHAPE of that relationship. A scatter plot reveals things
    the number alone hides - like whether the relationship is truly a
    straight line, whether there are distinct clusters of points, or
    whether a few extreme outliers are secretly driving the whole
    correlation number.

    If color_column is given (a categorical column), each category gets
    its own color, so you can also see whether the relationship differs
    by group - for example, does Sales vs Quantity look different for
    Electronics vs Furniture?
    """
    if color_column:
        fig = px.scatter(
            df, x=x_column, y=y_column, color=color_column,
            color_discrete_sequence=[INK_NAVY, CIRCUIT_TEAL, SIGNAL_AMBER, ALERT_CORAL, MUTED_BLUE, SLATE]
        )
        title = f"{y_column} vs {x_column}, colored by {color_column}"
    else:
        fig = px.scatter(df, x=x_column, y=y_column)
        fig.update_traces(marker=dict(color=CIRCUIT_TEAL, size=7, opacity=0.7))
        title = f"{y_column} vs {x_column}"

    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")))
    fig.update_layout(
        title=title,
        **BASE_LAYOUT
    )
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="#eef0f4", automargin=True)
    return fig


def plot_boxplot(df, numeric_column, group_column=None, top_n=12):
    """
    Shows the spread of a numeric column as a "box" - the box covers the
    middle 50% of values (Q1 to Q3), the line inside is the median, and
    the whiskers extend to the normal range. Individual dots beyond the
    whiskers are the statistical outliers - the exact same IQR method
    used in the cleaning stage, but now you can actually SEE it.

    If group_column is given (a categorical column), you get one box per
    category side by side - example: does the spread of Sales look
    different in the North region compared to the South region, not just
    the average?

    Same lesson as the categorical bar chart: if group_column has many
    unique values (like Job Title), showing a box for every single one
    makes the chart unreadable. So we limit to the top_n most frequent
    groups by row count, same pattern used everywhere else in this app.
    """
    if group_column:
        top_groups = df[group_column].value_counts().head(top_n).index
        total_groups = df[group_column].nunique()
        chart_df = df[df[group_column].isin(top_groups)]

        fig = px.box(chart_df, x=group_column, y=numeric_column, color=group_column,
                     color_discrete_sequence=[INK_NAVY, CIRCUIT_TEAL, SIGNAL_AMBER, ALERT_CORAL, MUTED_BLUE, SLATE])

        if total_groups > top_n:
            title = f"Spread of {numeric_column} by {group_column} (top {top_n} of {total_groups} groups by frequency)"
        else:
            title = f"Spread of {numeric_column} by {group_column}"
        fig.update_layout(showlegend=False)
    else:
        fig = px.box(df, y=numeric_column)
        fig.update_traces(marker_color=CIRCUIT_TEAL, line_color=INK_NAVY)
        title = f"Spread of {numeric_column}"

    fig.update_layout(
        title=title,
        **BASE_LAYOUT
    )
    fig.update_xaxes(gridcolor="#eef0f4", automargin=True)
    fig.update_yaxes(gridcolor="#eef0f4", automargin=True)
    return fig
