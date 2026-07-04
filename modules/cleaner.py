"""
This file actually FIXES the problems found in quality_check.py.
Each function takes the messy data and returns a cleaner version.
"""

import pandas as pd
import re


def remove_duplicate_rows(df):
    """Removes rows that are exact copies of another row."""
    return df.drop_duplicates().reset_index(drop=True)


def fill_missing_values(df, column, method):
    """
    Fills missing (blank) values in one column.

    method options:
    - "mean"   -> fills with the average (good for numeric columns)
    - "median" -> fills with the middle value (good for numeric columns with outliers)
    - "mode"   -> fills with the most common value (good for categorical columns)
    - "drop"   -> removes rows where this column is empty
    """
    df = df.copy()  # work on a copy so we don't accidentally change the original

    if method == "mean":
        df[column] = df[column].fillna(df[column].mean())
    elif method == "median":
        df[column] = df[column].fillna(df[column].median())
    elif method == "mode":
        # mode() can return multiple values if there's a tie, so we just take the first
        mode_series = df[column].mode()
        if not mode_series.empty:
            df[column] = df[column].fillna(mode_series[0])
    elif method == "drop":
        df = df.dropna(subset=[column])

    return df


def remove_outlier_rows(df, column, lower_bound, upper_bound):
    """
    Removes rows where the given column's value falls outside the
    "normal" range calculated by the IQR method.
    """
    df = df.copy()
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)].reset_index(drop=True)


def standardize_text_column(df, column):
    """
    Cleans up messy text formatting:
    - removes extra spaces at the start/end
    - makes capitalization consistent (Title Case)
    Example: "  new york " and "NEW YORK" both become "New York"
    """
    df = df.copy()
    df[column] = df[column].astype(str).str.strip().str.title()
    return df


def clean_currency_column(df, column):
    """
    Removes currency symbols and commas from a column so it can be
    treated as a proper number.
    Example: "$1,200.50" becomes 1200.50
    """
    df = df.copy()

    def clean_value(value):
        if pd.isnull(value):
            return value
        # Remove anything that isn't a digit, dot, or minus sign
        cleaned = re.sub(r'[^\d.-]', '', str(value))
        try:
            return float(cleaned)
        except ValueError:
            return None  # if it still can't be converted, mark as missing

    df[column] = df[column].apply(clean_value)
    return df


def drop_columns(df, columns_to_drop):
    """
    Removes one or more entire columns from the data.
    Used when a column has too much missing data to be trustworthy.
    """
    df = df.copy()
    return df.drop(columns=columns_to_drop, errors='ignore')


def drop_rows_by_index(df, row_indices):
    """
    Removes specific rows (identified by their index number) from the data.
    Used when a row has too many empty fields to be reliable.
    Resets the index afterward so row numbers stay clean and sequential.
    """
    df = df.copy()
    return df.drop(index=row_indices, errors='ignore').reset_index(drop=True)
