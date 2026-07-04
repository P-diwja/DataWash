"""
This file supports the DASHBOARD BUILDER feature.

Here's the idea: as the user explores charts in the Explore stage, each
chart has an "Add to Dashboard" button. Instead of storing the actual
chart object (which is heavy and doesn't survive Streamlit's reruns well),
we store a small, lightweight description of the chart - like a recipe -
in st.session_state. Example:

    {"type": "numeric", "column": "Sales", "title": "Distribution of Sales"}

Then, whenever we need to actually DRAW the dashboard, we take each saved
"recipe" and rebuild the real chart from it. This function is that rebuilder.
"""

from modules.visualizer import (
    plot_numeric_column, plot_categorical_column,
    plot_timeseries, plot_correlation_heatmap, plot_grouped_comparison,
    plot_scatter, plot_boxplot
)
from modules.eda import grouped_comparison


def render_chart_from_config(df, config):
    """
    Takes one saved chart "recipe" (a dict) and the current cleaned data,
    and rebuilds the actual Plotly chart object to display.

    Returns None if the chart type isn't recognized, so calling code can
    skip it safely instead of crashing.
    """
    chart_type = config.get('type')

    if chart_type == 'numeric':
        return plot_numeric_column(df, config['column'])

    elif chart_type == 'categorical':
        return plot_categorical_column(df, config['column'], top_n=config.get('top_n', 15))

    elif chart_type == 'correlation':
        return plot_correlation_heatmap(df, config['columns'])

    elif chart_type == 'timeseries':
        return plot_timeseries(df, config['date_column'], config['value_column'])

    elif chart_type == 'grouped':
        grouped_df = grouped_comparison(
            df, config['group_column'], config['value_column'], config.get('agg', 'mean')
        )
        value_label = f"{config.get('agg', 'mean').title()} {config['value_column']}"
        return plot_grouped_comparison(grouped_df, config['group_column'], value_label)

    elif chart_type == 'scatter':
        return plot_scatter(df, config['x_column'], config['y_column'], config.get('color_column'))

    elif chart_type == 'boxplot':
        return plot_boxplot(df, config['numeric_column'], config.get('group_column'))

    return None
