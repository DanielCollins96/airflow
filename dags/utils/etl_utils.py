import os
from datetime import datetime
import pandas as pd
import random
import requests
import psycopg2
from psycopg2 import errors
# from ..config import TeamStart
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_DATA_PATH = '/Users/danielcollins/airflow/processed_data.csv'
NHL_API_PATH = 'https://statsapi.web.nhl.com/api/v1/'

def get_schedule(timedelta = 10,**kwargs):
    print(timedelta)
    print('hey')
    

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

def get_team_stats(ids: list = [4]) :
    all_data = []
    for id in ids:
        url = f'https://statsapi.web.nhl.com/api/v1/teams/{id}/stats'
        r = requests.get(url)
        tm_stats = r.json()['stats'][0]['splits'][0]['stat']
        tm_stats = pd.DataFrame([tm_stats])
        tm_stats['team_id'] = id
        all_data.append(tm_stats)   
    all_data = pd.concat(all_data) 
    all_data.set_index('team_id', inplace=True)
    return all_data


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
    df.set_index('team_id', inplace=True)
    team_stats_df = get_team_stats(df.index.values)
    df = df.join(team_stats_df)

    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey', echo=True)
    df.to_sql(kwargs['table_name'], engine, if_exists='replace', index=False)
    kwargs['ti'].xcom_push('rows_inserted', df.shape[0])

    return df

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
    return records
    
def get_teams_roster_history(ti):
    '''
    Function used to get a full historical record of each teams roster and insert the information into the roster table. Each row is 

    SQL Constraint on the roster table, unique person/team/season id
    '''

    print('fetching team info hoe')
    team_ids = ti.xcom_pull(key='ids', task_ids='Hockey_ETL.hook_check_ids')
    print(team_ids)
    if (team_ids is None):
        raise KeyError('No team ids found')
    insert_records = 0
    insert_failures = 0

    for id, yr in team_ids:
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
                print(id,season_id)
                try:
                    the_df.to_sql('roster', engine, if_exists='append', index=False)
                    insert_records += 1
                except IntegrityError as err:
                    print(f'skipping yo stank coochie')
                    insert_failures += 1
                    pass
                except Exception as err:
                    print('error yo')
                    raise err
            except KeyError:
                print(f'No roster for {id} in {season_id}')
                pass
        return {'insert_records': insert_records, 'insert_failures': insert_failures}

def get_current_player_stats():
    sql = '''   
    SELECT distinct person_id
    FROM public.roster
    WHERE season_id = '20212022'
    --LIMIT 50;
    '''
    results = PostgresHook(postgres_conn_id='postgres_hockey').get_records(sql=sql)
    players = []
    for id in results:
        player = f'https://statsapi.web.nhl.com/api/v1/people/{id[0]}/stats?stats=statsSingleSeason&stats=gameLog'
        try:
            r = requests.get(player).json()['stats'][0]['splits']
            # breakpoint()
            if r:
                r[0]['person_id'] = id[0]
                players.append(r[0])
        except Exception as err:
            print(err)
            print(id[0])
            pass
    player_stats = pd.json_normalize(players, sep='_')

def get_career_stats():
    sql = '''   
    SELECT distinct person_id
    FROM public.roster
    --LIMIT 50;
    '''
    results = PostgresHook(postgres_conn_id='postgres_hockey').get_records(sql=sql)
    print(results[0])

    engine = create_engine('postgresql://postgres:postgres@localhost:5432/hockey')

    for id in results[:10]:
        game_log_dict, yr_by_yr_dict = requests.get(f'https://statsapi.web.nhl.com/api/v1/people/{id[0]}/stats?stats=gameLog&stats=yearByYear').json()['stats']
        game_log_dict['splits'][0]['person_id'] = id[0]
        yr_by_yr_dict['splits'][0]['person_id'] = id[0]
        try:
            game_log_df = pd.json_normalize(game_log_dict['splits'], sep='_').to_sql('player_gamelog', engine, if_exists='replace', index=False)
            # yr_by_yr_df = pd.json_normalize(yr_by_yr_dict['splits'], sep='_').to_sql('player_season', engine, if_exists='replace', index=False)
        except Exception as err:
            print(err)
            print(id[0])
            pass
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
    client = boto3.client('s3')
    bucket = 'hockey-data'
