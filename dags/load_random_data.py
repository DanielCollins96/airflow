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

    with TaskGroup('Hockey_ETL') as hockey_group:
        task_5 = PythonOperator(
            task_id='get_team_info',
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
            python_callable=query_and_push_ids,
            op_kwargs={
                "sql": 'SELECT team_id, "firstYearOfPlay" from team',
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
            task_id='get_teams_player_info',
            python_callable=get_teams_player_info,
            provide_context=True,
            dag=ingestion_dag,
        )
        
        task_9 = PythonOperator(
            task_id='get_player_stats',
            python_callable=get_player_stats,
            provide_context=True,
            dag=ingestion_dag,
        )

        
# poopoo_group

hockey_group