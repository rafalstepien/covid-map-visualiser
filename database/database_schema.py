from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine, Date
from sqlalchemy.orm import relationship
import os


# Get environment variables from database
user = 'rafalstepien'
password = 'admin123'
host = 'localhost'
port = '5432'
database = 'covid_map'


while True:
    try:
        engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')
        connection = engine.connect()
    except Exception as e:
        print(e)
    else:
        break

Base = declarative_base()


class CountryStatistics(Base):
    __tablename__ = 'country_statistics'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    country = Column(String())
    population = Column(Integer())
    capital_city = Column(String())
    area = Column(Float())


class CovidStatistics(Base):
    __tablename__ = 'covid_statistics'
    country_id = Column(Integer(), ForeignKey('country_statistics.id'), nullable=False)
    id = Column(Integer(), primary_key=True)

    date = Column(Date())
    confirmed_cases = Column(Integer())
    deaths = Column(Integer())
    recovered = Column(Integer())
    active_cases = Column(Integer())
    incidence_rate = Column(Float())
    case_fatality_ratio = Column(Float())
