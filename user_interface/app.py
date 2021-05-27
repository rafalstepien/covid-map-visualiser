import pandas as pd
import sys
import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from flask import Flask, request, Response
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly_express as px

from components.navbar import *
from queries.queries import _get_stats_for_country, get_stats_for_one_day
from plots.plots import _get_histogram


from dotenv import load_dotenv
dotenv_path = '../database/database.env'
load_dotenv(dotenv_path)

## < SETTINGS >
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"
external_stylesheets = [dbc.themes.CERULEAN, FONT_AWESOME]

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
## < /SETTINGS >

empty_histogram = dcc.Graph(
            figure=go.Figure(),
            id="histogram-plot")


body_left = html.Div([
    html.Div([html.Div([
        dcc.Graph(id='map'),
        # html.Div(id='map'),
        html.Div(id='stats-output')
        ])], className='centered')
    ], className='split left')


body_right = html.Div([
    html.Div([html.Div([
        html.Div(empty_histogram)
        ])], className='centered')
    ], className='split right')


app.layout = html.Div([
    html.Div([
        navbar,
        body_left,
        body_right,
    ])])


@app.callback(
    Output('histogram-plot', 'figure'),
    [Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input('country-dropdown', 'value'),
    Input('statistics-dropdown', 'value')]
)
def stats_for_country_callback(start_date, end_date, country, statistics):
    data_for_plot = _get_stats_for_country(country, start_date, end_date)
    stats_histograms = _get_histogram(data_for_plot, statistics, start_date, end_date)
    if stats_histograms:
        return stats_histograms
    else:
        return go.Figure()


@app.callback(
    Output('map', 'figure'),
    [Input('date-picker', 'start_date'),
    Input('statistics-dropdown', 'value')]
)
def map_dataframe_callback(start_date, statistic):
    try:
        data = get_stats_for_one_day(start_date, statistic)
        data.index = data.Country

        df = px.data.gapminder().query("year==2007")
        df.index = df.country

        together = pd.merge(data, df, left_index=True, right_index=True)

        fig = px.choropleth(together, locations="iso_alpha", color=f"{statistic}", hover_name="Country")

        return fig
    except AttributeError:
        return {}


if __name__ == "__main__":
    app.run_server(debug=True, port=sys.argv[1])
