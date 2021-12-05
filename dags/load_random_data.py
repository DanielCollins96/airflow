from airflow import DAG
import datetime
import pandas as pd
# from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.dates import days_ago
from utils.etl_utils import *

import psycopg2
import csv

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

with DAG(
        dag_id='load_poopoo',
        default_args=default_args,
) as ingestion_dag:


    with TaskGroup('poopoo_stuff') as poopoo_group:
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

        task_3 = PostgresOperator(
            task_id='load_poopoo_to_postgres',
            postgres_conn_id="postgres_hockey",    
            sql='SELECT * FROM time_airflow',
            dag=ingestion_dag,
        )

        task_4 = PostgresOperator(
            task_id='load_poopoo_to_postgres_2',
            postgres_conn_id="postgres_hockey",
            sql='SELECT * FROM time_airflow WHERE id > %(num)s',
            parameters={"num": 4000},
            dag=ingestion_dag,
        )
        task_1 >> task_2
        # task_3 >> task_4

    with TaskGroup('Hockey_ETL') as hockey_group:
        task_5 = PythonOperator(
            task_id='get_team_stats',
            python_callable=get_team_info,
            op_kwargs={'table_name': 'team'},
            dag=ingestion_dag,
        )

        # task_6 = PostgresOperator(
        #     task_id='check_ids_in_db',
        #     postgres_conn_id="postgres_hockey",
        #     sql='SELECT id from team',
        # )   

        task_7 = PythonOperator(
            task_id='hook_check_ids',
            python_callable=query_and_push,
            op_kwargs={
                "sql": "SELECT id from team",
            },
            provide_context=True,
            dag=ingestion_dag,
        )


        # pullout = BashOperator(
        #     task_id='pull_out_data',
        #     bash_command='echo "pulling out data"',
        #     dag=ingestion_dag,
        # )
        task_8 = PythonOperator(
            task_id='pull_harder',
            python_callable=get_teams_player_info,
            provide_context=True,
            dag=ingestion_dag,
        )

# poopoo_group

hockey_group