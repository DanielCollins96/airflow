import os
import datetime
import pandas as pd
import random
import requests
import psycopg2
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_DATA_PATH = '/Users/danielcollins/airflow/processed_data.csv'
NHL_API_PATH = 'https://statsapi.web.nhl.com/api/v1/'

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




def get_team_info(**kwargs):
    '''
    This function will get information about each NHL team. It will then insert that to a team table.
    '''
    print('fetching team stats')
    r = requests.get(NHL_API_PATH + 'teams')
    res = r.json()
    team_data = res['teams']
    df = pd.json_normalize(team_data, sep='_')
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey')
    df.to_sql(kwargs['table_name'], engine, if_exists='replace', index=False)
    # return df

def query_and_push(**kwargs):
    '''
    Takes
    '''
    sql = kwargs['sql']
    pg_hook = PostgresHook(postgres_conn_id='postgres_hockey')
    records = pg_hook.get_records(sql=sql)
    print(sql)
    record_list = [element for tupl in records for element in tupl]
    kwargs['ti'].xcom_push('ids', 'record_list')
    
    print(record_list)
    # return record_list
    
def get_teams_player_info(ti):
    print('fetching team info')
    glory = ti.xcom_pull(key='ids', task_ids='hook_check_ids')
    print(dir(ti))
    try:
        print(glory)
        print(f'glory: {glory.shape}')
    except Exception as e:
        print(e)

def query_hockey_db(query: str):
    '''
    psycopg2 connection and query execution. Repalced by query_and_push.
    '''
    try:
        conn = psycopg2.connect(host="localhost", database="hockey", user="airflow_user", password="airflow_pass")
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
    
    except Exception as e:
        print(e)
        return 'Error querying database'
    return rows