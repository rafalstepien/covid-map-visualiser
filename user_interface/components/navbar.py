import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from datetime import date


from queries.queries import _get_all_countries

countries = _get_all_countries()

dropdown_country = dcc.Dropdown(
        id='country-dropdown',
        options=[{'label': country, 'value': country} for country in countries],
        value='Poland')

date_picker = dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed=date(2021, 1, 1),
            max_date_allowed=date.today(),)
            # initial_visible_month=date(2021, 1, 1))

statistics = ['active_cases', 'case_fatality_ratio', 'confirmed_cases', 'deaths', 'incidence_rate']

stat_dropdown = dcc.Dropdown(
    id='statistics-dropdown',
    options=[{'label': stat.replace('_', ' ').capitalize(), 'value': stat} for stat in statistics],
    value='deaths')

navbar = html.Div([
    dbc.Row([
        dbc.Col(html.Div(dropdown_country), width=3),
        dbc.Col(html.Div(date_picker), width=3),
        dbc.Col(html.Div(stat_dropdown), width=3),
    ], className='bck-navbar', align='center'
)])
