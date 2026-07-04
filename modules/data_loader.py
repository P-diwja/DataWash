"""
This file handles reading the uploaded file (CSV or Excel).
It doesn't care what the file contains yet - just gets it into a table (DataFrame).
"""

import pandas as pd


def load_file(uploaded_file):
    """
    Takes the file the user uploaded and turns it into a pandas DataFrame.
    Returns (dataframe, error_message).
    If everything is fine, error_message will be None.
    """
    try:
        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > 200:
            return None, f"File is {size_mb:.0f}MB, exceeding the 200MB limit. Try a smaller file."

        # Check the file extension to decide how to read it
        file_name = uploaded_file.name.lower()

        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
        else:
            # If it's not csv or excel, we don't support it
            return None, "Unsupported file type. Please upload a .csv or .xlsx file."

        # If the file was empty, pandas will give us a DataFrame with 0 rows
        if df.empty:
            return None, "The uploaded file appears to be empty."

        return df, None

    except Exception as e:
        # Catch any unexpected error (corrupted file, wrong format, etc.)
        return None, f"Something went wrong while reading the file: {str(e)}"
