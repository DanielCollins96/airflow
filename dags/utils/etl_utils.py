import os
from datetime import datetime
import pandas as pd
import random
import requests
import psycopg2
# from ..config import TeamStart
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_DATA_PATH = '/Users/danielcollins/airflow/processed_data.csv'
NHL_API_PATH = 'https://statsapi.web.nhl.com/api/v1/'


def get_season_standings(**kwargs):
    '''
    This function will get information about each NHL team. It will then insert that to a team table.
    '''
    print('fetching team stats')
    r = requests.get(NHL_API_PATH + 'standings')
    res = r.json()
    team_data = res['records']
    df = pd.json_normalize(team_data, sep='_')
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey')
    df.to_sql(name=kwargs['table_name'], con=engine, if_exists='replace', index=False)
    
    # return df

def get_team_info(**kwargs):
    '''
    This function will get information about each NHL team. It will then insert that to a team table.
    '''
    print('fetching team stats')
    r = requests.get(NHL_API_PATH + 'teams')
    res = r.json()
    team_data = res['teams']
    df = pd.json_normalize(team_data, sep='_')
    df.rename(columns={'id': 'team_id'}, inplace=True)
    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey', echo=True)
    df.to_sql(kwargs['table_name'], engine, if_exists='replace', index=False)
    kwargs['ti'].xcom_push('rows_inserted', df.shape[0])
    # return df

def query_and_push_ids(**kwargs):
    '''
    Takes
    '''
    sql = kwargs['sql']
    pg_hook = PostgresHook(postgres_conn_id='postgres_hockey')
    records = pg_hook.get_records(sql=sql)
    print(sql)
    print(records)
    # record_list = [element for tupl in records for element in tupl]
    # print(record_list)
    kwargs['ti'].xcom_push('ids', records)
    # return record_list
    
def get_teams_player_info(ti):
    id = 4
    f'https://statsapi.web.nhl.com/api/v1/teams/{id}?expand=team.roster'
    print('fetching team info hoe')
    team_ids = ti.xcom_pull(key='ids', task_ids='Hockey_ETL.hook_check_ids')
    print(team_ids)
    if (team_ids is None):
        raise KeyError('No team ids found')
    for id, yr in team_ids[10:]:
        season = int(yr)
        while season <= datetime.now().year:
            season_id = f'{season}{season+1}'
            r = requests.get(f'https://statsapi.web.nhl.com/api/v1/teams/{id}?expand=team.roster&season={season}{season+1}')
            try:
                roster = r.json()['teams'][0]['roster']['roster']
                the_df = pd.json_normalize(roster, sep='_')
                the_df['team_id'] = id
                the_df['season_id'] = season_id
                engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey')
                the_df.to_sql('roster', engine, if_exists='append', index=False)
                # breakpoint()
            except KeyError:
                print(f'No roster for {id} in {season_id}')
                pass
            season += 1

def get_player_stats():
    sql = '''   
    SELECT distinct person_id
    FROM public.roster;
    '''
    results = PostgresHook(postgres_conn_id='postgres_hockey').get_records(sql=sql)
    print(results)
    url = f'https://statsapi.web.nhl.com/api/v1/people/{id}/stats?stats=yearByYear'
    return results

def get_player_image():
    pass

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


def load_s3_data(**kwargs):
    '''
    Loads data into s3 from a database or json file.
    '''
    