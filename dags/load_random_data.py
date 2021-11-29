from airflow import DAG
import datetime
import pandas as pd
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
# from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
import random
import os
import psycopg2
import csv

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

PROCESSED_DATA_PATH = f'{os.getcwd()}/processed_data.csv'

ingestion_dag = DAG(
        'load_poopoo',
        default_args=default_args,
)

def transform_poopoo():
    print('transform_poopoo')
    data = {}
    data['time'] = datetime.datetime.now()
    data['id'] = int(random.random()*10000)
    df = pd.DataFrame([data])
    print(df.shape)

    if (os.path.getsize(PROCESSED_DATA_PATH) == 0):
        df.to_csv(PROCESSED_DATA_PATH, index=False)
    else:
        df.to_csv(PROCESSED_DATA_PATH, mode='a', header=False, index=False)
    # df.to_csv(PROCESSED_DATA_PATH, index=False)


def load_poopoo():
    df = pd.read_csv(PROCESSED_DATA_PATH)
    conn = psycopg2.connect(
        host='localhost',
        database='hockey',
        user='postgres',
        password='postgres'
    )
    df.to_sql('time', con=conn, if_exists='append', index=False)
    print('loaded_poopoo from bum')

task_1 = PythonOperator(
    task_id='transform_poopoo',
    python_callable=transform_poopoo,
    dag=ingestion_dag,
)

task_2 = PythonOperator(
    task_id='load_poopoo',
    python_callable=load_poopoo,
    dag=ingestion_dag,
)

task_1 >> task_2
