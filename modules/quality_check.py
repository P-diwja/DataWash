"""
This file checks the HEALTH of the data before cleaning.
It answers questions like:
- How many values are missing?
- Are there duplicate rows?
- Are there any weird outlier numbers?

Think of this as a doctor's check-up report for the dataset.
"""

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def missing_value_report(df):
    """
    For each column, counts how many values are missing (blank/null)
    and what percentage of the column that represents.
    """
    report = []
    total_rows = len(df)

    for column in df.columns:
        missing_count = df[column].isnull().sum()
        missing_percent = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0

        # Only include columns that actually have missing data
        if missing_count > 0:
            report.append({
                'column': column,
                'missing_count': int(missing_count),
                'missing_percent': missing_percent
            })

    return report


@st.cache_data(show_spinner=False)
def duplicate_report(df):
    """
    Counts how many rows are exact duplicates of another row.
    """
    duplicate_count = df.duplicated().sum()
    return int(duplicate_count)


@st.cache_data(show_spinner=False)
def detect_outliers_iqr(series):
    """
    Uses the IQR (Interquartile Range) method to find unusual/extreme values.

    How it works in simple terms:
    - Q1 = the value below which 25% of the data falls
    - Q3 = the value below which 75% of the data falls
    - IQR = the "normal spread" of the middle 50% of data
    - Anything far below Q1 or far above Q3 is considered an outlier
    """
    clean_series = series.dropna()

    Q1 = clean_series.quantile(0.25)
    Q3 = clean_series.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = clean_series[(clean_series < lower_bound) | (clean_series > upper_bound)]

    return {
        'outlier_count': len(outliers),
        'lower_bound': round(lower_bound, 2),
        'upper_bound': round(upper_bound, 2)
    }


@st.cache_data(show_spinner=False)
def outlier_report(df, column_types):
    """
    Runs outlier detection on every NUMERIC column only
    (outliers don't make sense for text or category columns).
    """
    report = []
    for column, col_type in column_types.items():
        if col_type == 'numeric':
            result = detect_outliers_iqr(df[column])
            if result['outlier_count'] > 0:
                report.append({
                    'column': column,
                    **result
                })
    return report


@st.cache_data(show_spinner=False)
def detect_currency_like_columns(df, column_types):
    """
    Looks at columns that got detected as 'text' and checks if they're
    actually numbers hiding behind currency symbols, like "$1,200.50".

    Real-world currency columns are often inconsistent - some rows have
    the symbol, some don't (e.g. "$500" and "500" in the same column).
    So instead of requiring most values to LOOK like currency, we check
    whether most values become valid numbers once we strip out symbols.
    If they do, it's a numeric column that just needs cleaning.
    """
    import re
    currency_columns = []

    for column, col_type in column_types.items():
        if col_type != 'text':
            continue

        sample = df[column].dropna().astype(str).head(30)
        if len(sample) == 0:
            continue

        def looks_numeric_after_cleaning(value):
            cleaned = re.sub(r'[^\d.-]', '', value)
            if cleaned in ('', '-', '.'):
                return False
            try:
                float(cleaned)
                return True
            except ValueError:
                return False

        numeric_ratio = sample.apply(looks_numeric_after_cleaning).mean()

        # If most values become valid numbers after stripping symbols,
        # this is very likely a currency/number column stored as text
        if numeric_ratio > 0.8:
            currency_columns.append(column)

    return currency_columns


@st.cache_data(show_spinner=False)
def detect_messy_text_columns(df, column_types):
    """
    Looks at categorical/text columns and checks if they have inconsistent
    formatting - extra spaces or mixed capitalization, like " north" vs "North".
    Returns a list of column names worth standardizing.
    """
    messy_columns = []

    for column, col_type in column_types.items():
        if col_type not in ('categorical', 'text'):
            continue

        sample = df[column].dropna().astype(str)
        if len(sample) == 0:
            continue

        has_whitespace_issue = (sample != sample.str.strip()).any()
        # Check if the same value appears in different cases, e.g. "North" and "north"
        lowered_unique = sample.str.strip().str.lower().nunique()
        original_unique = sample.str.strip().nunique()
        has_case_issue = lowered_unique < original_unique

        if has_whitespace_issue or has_case_issue:
            messy_columns.append(column)

    return messy_columns


@st.cache_data(show_spinner=False)
def recommend_column_drops(df, missing_threshold=50):
    """
    Recommends dropping entire COLUMNS where too much data is missing to be useful.

    Example: if 'Additional Notes' is 85% empty, filling it in wouldn't be
    trustworthy - it's more honest to drop it than to guess most of its values.

    missing_threshold is a percentage (0-100). Only columns at or above this
    percentage of missing data get recommended for dropping.

    Returns a list of dicts, each describing one recommended column drop -
    nothing is actually deleted here, this just calculates the recommendation
    so the user can review and confirm it themselves.
    """
    recommendations = []
    total_rows = len(df)

    if total_rows == 0:
        return recommendations

    for column in df.columns:
        missing_count = df[column].isnull().sum()
        missing_percent = round((missing_count / total_rows) * 100, 1)

        if missing_percent >= missing_threshold:
            recommendations.append({
                'column': column,
                'missing_count': int(missing_count),
                'missing_percent': missing_percent,
                'total_rows': total_rows
            })

    return recommendations


@st.cache_data(show_spinner=False)
def recommend_row_drops(df, missing_threshold=50):
    """
    Recommends dropping individual ROWS where most of that row's fields
    are empty - a row with 8 out of 10 columns blank usually isn't
    reliable enough to analyze, no matter how you fill the gaps.

    missing_threshold is a percentage (0-100) of a SINGLE ROW's columns
    that must be empty for that row to be flagged.

    Returns a summary dict (not the actual rows) so the user sees the
    IMPACT of this recommendation before deciding to apply it.
    """
    total_columns = len(df.columns)
    total_rows = len(df)

    if total_columns == 0 or total_rows == 0:
        return {'row_count': 0, 'percent_of_data': 0, 'row_indices': []}

    # Count how many columns are empty, for each row individually
    missing_per_row = df.isnull().sum(axis=1)
    missing_percent_per_row = (missing_per_row / total_columns) * 100

    flagged_rows = missing_percent_per_row[missing_percent_per_row >= missing_threshold]

    return {
        'row_count': len(flagged_rows),
        'percent_of_data': round((len(flagged_rows) / total_rows) * 100, 1),
        'row_indices': flagged_rows.index.tolist()
    }
