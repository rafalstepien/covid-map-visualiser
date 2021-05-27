import pandas as pd
from datetime import timedelta, datetime
import plotly.graph_objects as go


def _get_histogram(dataframe, statistics, start_date, end_date):
    if start_date and end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        values_to_plot = dataframe[f'{statistics}']
        date_range = pd.date_range(start_date, end_date, freq='d').astype(str).tolist()
        fig = fig = go.Figure([go.Bar(x=date_range, y=values_to_plot)])
        return fig
