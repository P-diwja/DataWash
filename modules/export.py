"""
This file handles getting the user's work OUT of the app.

We only export to Excel, not as a combined dashboard image. Here's why:
combining many different chart types (bars, scatter, heatmaps) into one
image with a hand-built grid layout is fragile - every new chart size or
combination is a new way for text to overlap or get clipped. Individual
chart downloads already work perfectly (Plotly's built-in camera icon on
each chart), so instead of fighting that, we embed each chart as an image
directly INTO the Excel workbook - same reliable per-chart rendering, just
placed somewhere more useful: next to the actual data.
"""

import pandas as pd
import io
import math
from PIL import Image
from openpyxl.drawing.image import Image as XLImage


def figure_to_png_bytes(fig, width=700, height=420):
    """
    Converts a single Plotly chart into PNG image bytes.
    Requires the 'kaleido' package (pinned to 0.2.1 in requirements.txt,
    since newer versions need a separate Chrome install we can't rely on).
    scale=2 renders at higher resolution so it looks sharp when embedded.
    """
    return fig.to_image(format="png", scale=2, width=width, height=height)


def export_cleaned_data_excel(cleaned_df, summary_stats_df=None, insights_list=None, dashboard_figures=None):
    """
    Builds a multi-sheet Excel workbook and returns it as raw bytes,
    ready to hand to a Streamlit download button.

    Sheet 1: the cleaned data itself
    Sheet 2: summary statistics (only added if provided)
    Sheet 3: insights written out as plain sentences (only added if provided)
    Sheet 4: "Dashboard" - the actual chart IMAGES the user built, embedded
             directly into the workbook (only added if dashboard_figures given)
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        cleaned_df.to_excel(writer, sheet_name='Cleaned Data', index=False)

        if summary_stats_df is not None and not summary_stats_df.empty:
            summary_stats_df.to_excel(writer, sheet_name='Summary Statistics')

        if insights_list:
            insights_text = [item['text'] for item in insights_list]
            insights_df = pd.DataFrame({'Insight': insights_text})
            insights_df.to_excel(writer, sheet_name='Insights', index=False)

        if dashboard_figures:
            placeholder_df = pd.DataFrame({'Dashboard': ['Your saved charts are below']})
            placeholder_df.to_excel(writer, sheet_name='Dashboard', index=False)
            worksheet = writer.sheets['Dashboard']

            # DISPLAY size is what the chart actually looks like in Excel -
            # kept deliberately compact so multiple charts fit on screen
            # without endless scrolling, like a real dashboard overview.
            #
            # We still RENDER each chart at 2x that resolution (see
            # figure_to_png_bytes below) so it stays crisp when someone
            # zooms in - the image data is high-res, but openpyxl displays
            # it at the smaller DISPLAY size we set explicitly below.
            display_width_px = 480
            display_height_px = 290

            # Excel's default row height is ~20 pixels. We calculate exactly
            # how many rows the image will actually occupy on screen, plus
            # a little padding - instead of guessing a fixed number of rows
            # and hoping it's enough (which is what caused the overlap bug).
            default_row_height_px = 20
            padding_rows = 2
            rows_per_chart = math.ceil(display_height_px / default_row_height_px) + padding_rows

            current_row = 3
            for fig in dashboard_figures:
                png_bytes = figure_to_png_bytes(fig, width=700, height=420)

                img_buffer = io.BytesIO(png_bytes)
                img_buffer.name = 'chart.png'
                excel_image = XLImage(img_buffer)

                # Force the DISPLAY size regardless of the image's actual
                # pixel dimensions - this is what actually fixes the overlap,
                # since row spacing is now calculated against this same number.
                excel_image.width = display_width_px
                excel_image.height = display_height_px

                worksheet.add_image(excel_image, f'A{current_row}')
                current_row += rows_per_chart

    output.seek(0)
    return output.getvalue()
