"""
This file builds the "Explore" stage - real exploratory data analysis (EDA)
beyond single-column charts. It answers questions a data analyst actually
asks, like:
- What's the statistical summary of every numeric column at once?
- Does one column's average actually differ across categories of another?
  (Example: is average Sales really different across Regions, or about the same?)
- Is a column's distribution lopsided, and should that change how we interpret it?
"""

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def summary_statistics_table(df, numeric_columns):
    """
    Builds one table showing count, mean, median, standard deviation, and
    quartiles for every numeric column at once - this is the classic
    statistical summary a data analyst checks first on any new dataset.
    """
    if not numeric_columns:
        return pd.DataFrame()

    stats = df[numeric_columns].describe().T  # transpose so each row = one column
    stats = stats.rename(columns={
        'count': 'Count',
        'mean': 'Mean',
        'std': 'Std Dev',
        'min': 'Min',
        '25%': 'Q1 (25%)',
        '50%': 'Median',
        '75%': 'Q3 (75%)',
        'max': 'Max'
    })
    stats = stats.round(2)
    return stats


@st.cache_data(show_spinner=False)
def grouped_comparison(df, group_column, value_column, agg='mean'):
    """
    Groups the data by a categorical column and aggregates a numeric column
    within each group - this is the core "bivariate" analysis technique.

    Example: grouped_comparison(df, 'Region', 'Sales', 'mean')
    answers "what's the average Sales in each Region?"

    agg options: 'mean', 'median', 'sum', 'count'
    """
    grouped = df.groupby(group_column)[value_column].agg(agg).reset_index()
    grouped.columns = [group_column, f'{agg}_{value_column}']
    grouped = grouped.sort_values(f'{agg}_{value_column}', ascending=False)
    return grouped


@st.cache_data(show_spinner=False)
def detect_skewness(series):
    """
    Measures whether a numeric column's distribution leans left or right,
    rather than being evenly spread around its average.

    Why this matters for an analyst: if a column is heavily skewed, the
    MEAN can be misleading (a few extreme values pull it up or down), and
    the MEDIAN becomes a more honest "typical value" to report instead.

    Skewness near 0   -> roughly symmetric (normal-like)
    Positive skewness -> long tail to the right (a few unusually HIGH values)
    Negative skewness -> long tail to the left (a few unusually LOW values)
    """
    skew_value = series.dropna().skew()

    if skew_value > 1:
        interpretation = "Strongly right-skewed - a few unusually high values are pulling the average up. Consider using the median instead of the mean."
    elif skew_value > 0.5:
        interpretation = "Moderately right-skewed."
    elif skew_value < -1:
        interpretation = "Strongly left-skewed - a few unusually low values are pulling the average down. Consider using the median instead of the mean."
    elif skew_value < -0.5:
        interpretation = "Moderately left-skewed."
    else:
        interpretation = "Roughly symmetric - the mean is a reliable summary here."

    return {
        'skew_value': round(skew_value, 2),
        'interpretation': interpretation
    }
