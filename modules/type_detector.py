"""
This file looks at each column of data and figures out what TYPE of data it is:
- date (like "2024-01-15")
- numeric (like 100, 45.5)
- categorical (like "Yes"/"No" or "Small"/"Medium"/"Large" - few repeated values)
- text (like free-form comments or names - lots of unique values)

We need to know the type of each column so we can decide:
- how to clean it
- what chart to draw for it
"""

import pandas as pd
import warnings
import streamlit as st


@st.cache_data(show_spinner=False)
def detect_column_type(series):
    """
    Looks at ONE column of data and returns its type as a simple string.
    """
    # Drop empty values first, since they don't help us guess the type
    clean_series = series.dropna()

    if len(clean_series) == 0:
        return 'unknown'  # column is entirely empty

    # STEP 1: Try to see if this looks like a date column
    # We only test a small sample (first 20 values) to keep it fast
    # We skip this check for columns that are already numbers, since pandas
    # can wrongly interpret plain numbers (like "2024") as dates.
    if not pd.api.types.is_numeric_dtype(series):
        try:
            sample = clean_series.iloc[:20]
            # Suppress the "could not infer format" warning - we're just
            # testing IF this looks like a date, not parsing it for real yet
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pd.to_datetime(sample, errors='raise')
            return 'date'
        except Exception:
            pass  # not a date, move to next check

    # STEP 2: Check if pandas already thinks this is a number
    if pd.api.types.is_numeric_dtype(series):
        return 'numeric'

    # STEP 3: For everything else (text-based columns),
    # decide categorical vs free text based on how many unique values exist.
    # Example: a "Gender" column might only have 2-3 unique values (categorical)
    # but a "Comments" column will have almost all unique values (free text)
    unique_ratio = clean_series.nunique() / len(clean_series)

    if unique_ratio < 0.5:
        return 'categorical'
    else:
        return 'text'


@st.cache_data(show_spinner=False)
def detect_all_types(df):
    """
    Runs detect_column_type() on every column in the table.
    Returns a dictionary like: {"Sales": "numeric", "Region": "categorical"}
    """
    column_types = {}
    for column_name in df.columns:
        column_types[column_name] = detect_column_type(df[column_name])
    return column_types
