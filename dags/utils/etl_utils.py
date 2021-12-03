import os
import datetime
import pandas as pd
import random
from sqlalchemy import create_engine

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_DATA_PATH = '/Users/danielcollins/airflow/processed_data.csv'

def transform_poopoo(**kwargs):
    print('transform_poopoo')
    print(kwargs)
    data = {}
    data['time'] = datetime.datetime.now()
    data['id'] = int(random.random()*10000)
    df = pd.DataFrame([data])
    print(df.shape)
    kwargs['ti'].xcom_push(key='df', value=df)
    try:
        if (os.path.getsize(PROCESSED_DATA_PATH) == 0):
            df.to_csv(PROCESSED_DATA_PATH, index=False)
        else:
            df.to_csv(PROCESSED_DATA_PATH, mode='a', header=False, index=False)
        # df.to_csv(PROCESSED_DATA_PATH, index=False)
    except Exception as e:
        print('error saving to csv')
        print(e)

def load_poopoo(**kwargs):
    print(kwargs)
    passed_df = kwargs['ti'].xcom_pull(task_ids='transform_poopoo', key='df')
    df = pd.read_csv(PROCESSED_DATA_PATH)
    # print(f'passed: {passed_df.shape} read: {df.shape}')
    print(df.shape)
    # assert passed_df == df
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey')
    try:
        df.to_sql('time_airflow', engine, index=False)
    except ValueError as e:
        print(e)
    print('loaded_poopoo from bum')

def get_team_stats(**kwargs):
    print('fetching team stats')