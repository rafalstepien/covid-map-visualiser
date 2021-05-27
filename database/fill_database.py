import os
import glob
import requests
import psycopg2
import pandas as pd
import numpy as np
from io import StringIO
from database_schema import *
from datetime import datetime, timedelta, date


connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=database,
    port=port)


def process_covid_stats_from_file(paths):
    for i, path in enumerate(glob.glob(paths)):
        print(path)
        date = os.path.basename(path).replace('.csv', '')
        covid_df = pd.read_csv(path)
        covid_df = covid_df.apply(lambda x: x.fillna(0) if x.dtype.kind in 'biufc' else x.fillna('.'))
        covid_df = covid_df.astype({'Country_Region': 'object',
                                    'Province_State': 'object',
                                    'Confirmed': 'int64',
                                    'Deaths': 'int64',
                                    'Recovered': 'int64',
                                    'Active': 'int64',
                                    'Incident_Rate': 'float64',
                                    'Case_Fatality_Ratio': 'float64',
                                    })
        covid_df = covid_df[['Country_Region', 'Province_State', 'Admin2', 'Confirmed', 'Deaths', 'Recovered', 'Active', 'Incident_Rate', 'Case_Fatality_Ratio']]
        covid_df['date'] = date
        if i == 0:
            fill_country_stats(covid_df)
        fill_covid_stats(covid_df)


def make_request(date_to_request):
    """Send the request for COVID data from given day, month, year and
    return StringIO.

    Args:
        date_to_request [datetime]: Date for which we want to obtain COVID statistics.

    Returns:
        [StringIO]: StringIO object from page content.
    """
    date_formatted = date_to_request.strftime('%m-%d-%Y')
    url_adress = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date_formatted}.csv'
    print(url_adress)
    response_string = requests.get(url_adress).text
    response_io = StringIO(response_string)
    return response_io


def process_covid_stats(date_start, date_end):
    """Insert COVID statistics in given date interval into database.

    Args:
        date_start (str): Start date of interval.
        date_end (str): End date of interval.
    """
    date_start = datetime.strptime(date_start, '%m-%d-%Y')
    date_end = datetime.strptime(date_end, '%m-%d-%Y')
    interval = date_end - date_start

    for i in range(interval.days + 1):
        date_to_request = date_start + timedelta(days=i)
        response_io = make_request(date_to_request)
        covid_df = pd.read_csv(response_io, usecols=['Country_Region', 'Confirmed', 'Deaths', 'Recovered', 'Active', 'Incident_Rate', 'Case_Fatality_Ratio'])
        covid_df = covid_df.apply(lambda x: x.fillna(0))
        covid_df['Case_Fatality_Ratio'] = covid_df['Case_Fatality_Ratio'].astype(str).str.replace('#DIV/0!', '0')
        covid_df = covid_df.astype({'Country_Region': 'object',
                                    'Confirmed': 'int64',
                                    'Deaths': 'int64',
                                    'Recovered': 'int64',
                                    'Active': 'int64',
                                    'Incident_Rate': 'float64',
                                    'Case_Fatality_Ratio': 'float64',
                                    })
        covid_df['date'] = date_to_request.strftime('%m-%d-%Y')
        covid_df = sum_values_for_country(covid_df)
        if i == 0:
            fill_country_stats(covid_df)
        fill_covid_stats(covid_df)


def sum_values_for_country(dataframe):
    pd.set_option('display.max_columns', None)
    final_df = pd.DataFrame()
    grouped = dataframe.groupby(by=['Country_Region'])
    for tuple_ in grouped:
        country, dataframe = tuple_
        confirmed = dataframe['Confirmed'].sum()
        deaths = dataframe['Deaths'].sum()
        recovered = dataframe['Recovered'].sum()
        active = dataframe['Active'].sum()
        incident_rate = round(dataframe['Incident_Rate'].mean(), 3)
        case_fatality_ratio = round(dataframe['Case_Fatality_Ratio'].mean(), 3)
        date = pd.unique(dataframe['date'])[0]
        to_append = pd.DataFrame({
            'Country_Region': [country],
            'Confirmed': [confirmed],
            'Deaths': [deaths],
            'Recovered': [recovered],
            'Active': [active],
            'Incident_Rate': [incident_rate],
            'Case_Fatality_Ratio': [case_fatality_ratio],
            'Date': [date]
        }, index=[0])
        final_df = final_df.append(to_append)
    return final_df
        

def fill_country_stats(countries_df):
    mapping_df = pd.read_csv('country_capital_city.tsv', sep='\t', header=None)
    mapping_df.columns = ['Country', 'Capital']
    with connection.cursor() as cursor:
        for id_, row in countries_df.iterrows():
            country = row.Country_Region.replace("'", "").strip()
            capital_city = mapping_df[mapping_df['Country'] == country]['Capital'].item()
            query_countries = f""" INSERT INTO country_statistics (country,
                                                                   population, 
                                                                   capital_city, 
                                                                   area) 
                                                            VALUES
                                                                  ('{country}', 
                                                                  0, 
                                                                  '{capital_city}', 
                                                                  0);"""
            cursor.execute(query_countries)
        connection.commit()


def fill_covid_stats(covid_df):
    with connection.cursor() as cursor:
        for id_, row in covid_df.iterrows():
            query_statistics = f""" INSERT INTO covid_statistics (country_id, 
                                                                  date, 
                                                                  confirmed_cases, 
                                                                  deaths, 
                                                                  recovered, 
                                                                  active_cases, 
                                                                  incidence_rate, 
                                                                  case_fatality_ratio)
                                                          VALUES ((SELECT id FROM country_statistics WHERE country='{row.Country_Region.replace("'", "")}'),
                                                                 '{row.Date}', 
                                                                 {int(row.Confirmed)}, 
                                                                 {int(row.Deaths)}, 
                                                                 {int(row.Recovered)}, 
                                                                 {int(row.Active)}, 
                                                                 {float(row.Incident_Rate)}, 
                                                                 {float(row.Case_Fatality_Ratio)});"""
            try:
                cursor.execute(query_statistics)
            except psycopg2.errors.NotNullViolation:
                connection.rollback()
                add_new_country_id(cursor, row, query_statistics)
        connection.commit()


def add_new_country_id(cursor, row, query_statistics):
    country = row.Country_Region.replace("'", "")
    query_insert_country = f""" INSERT INTO country_statistics (country,
                                                                population, 
                                                                capital_city, 
                                                                area) 
                                                            VALUES
                                                                ('{country}', 
                                                                0, 
                                                                'City', 
                                                                0);"""
    cursor.execute(query_insert_country)
    cursor.execute(query_statistics)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # process_covid_stats_from_file('/home/rafcio/Studia/Pracownia informatyczna/covid-map-visualiser/database/example_data/*csv')
    process_covid_stats('01-01-2021', '01-30-2021')
