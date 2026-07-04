"""
This file writes simple, human-readable sentences about the data.
Instead of the user reading numbers themselves, we summarize the story
in plain English - like a mini data analyst report.
"""


def generate_insights(df, column_types, original_row_count):
    """
    Looks at the cleaned data and column types, and writes out
    a list of easy-to-read insight sentences.
    Each insight is returned as a dict with a 'type' (used for icon/color)
    and the 'text' itself.
    """
    insights = []

    # Insight about how many rows were removed during cleaning
    current_row_count = len(df)
    removed_rows = original_row_count - current_row_count
    if removed_rows > 0:
        insights.append({
            'type': 'cleaning',
            'text': f"{removed_rows} rows were removed during cleaning "
                    f"(started with {original_row_count}, now {current_row_count})."
        })

    # Insight for each numeric column - show its range and average
    for column, col_type in column_types.items():
        if col_type == 'numeric':
            col_min = df[column].min()
            col_max = df[column].max()
            col_avg = df[column].mean()
            insights.append({
                'type': 'numeric',
                'text': f"'{column}' ranges from {col_min:.1f} to {col_max:.1f}, "
                        f"with an average of {col_avg:.1f}."
            })

        elif col_type == 'categorical':
            mode_series = df[column].mode()
            top_value = mode_series[0] if not mode_series.empty else "N/A"
            insights.append({
                'type': 'categorical',
                'text': f"The most common value in '{column}' is '{top_value}'."
            })

        elif col_type == 'date':
            date_min = df[column].min()
            date_max = df[column].max()
            insights.append({
                'type': 'date',
                'text': f"'{column}' covers the period from {date_min} to {date_max}."
            })

    return insights
