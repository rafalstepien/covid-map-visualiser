import sys
import pandas as pd
from sqlalchemy.orm import sessionmaker

sys.path.append('..')
from database.database_schema import *


def _get_all_countries():
    Session = sessionmaker(bind=engine)
    session = Session()

    countries = session.query(CountryStatistics.country).distinct() \
        .all()

    session.close()

    return [country[0] for country in countries]


def _get_stats_for_country(country, start_date, end_date):
    Session = sessionmaker(bind=engine)
    session = Session()

    country_id = session.query(CountryStatistics.id) \
        .filter(CountryStatistics.country == country) \
        .subquery()

    countries = session.query(CovidStatistics) \
        .filter(CovidStatistics.country_id.in_(country_id)) \
        .filter(CovidStatistics.date.between(start_date, end_date)) \
        .all()

    session.close()

    if countries:
        attributes = dir(countries[0])[-10:-2]
        rows = [[getattr(country, attr) for attr in attributes] for country in countries]
        countries = pd.DataFrame(rows, columns=attributes)

    return countries

def get_stats_for_one_day(date, statistic):
    if date:
        query = f"SELECT country, {statistic} FROM covid_statistics JOIN country_statistics ON covid_statistics.country_id=country_statistics.id WHERE date = '{date}';"
        result = connection.execute(query)
        
        df = pd.DataFrame()
        for row in result:
            row = {'Country': row[0],
                f'{statistic}': row[1],
                }
            df = df.append(row, ignore_index=True)
        return df
