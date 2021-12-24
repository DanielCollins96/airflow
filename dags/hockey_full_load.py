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

current_season = 20212022

with DAG(
    dag_id='daily_load',
    default_args=default_args,
    # schedule_interval='0 0 * * *',

) as daily_load_dag:

    task_1 = PythonOperator(
        task_id='get_player_stats',
        python_callable=get_current_player_stats,
        provide_context=True,
        dag=daily_load_dag,
    )

    task_2 = PythonOperator(
        task_id='get_schedule',
        python_callable=get_schedule,
        provide_context=True,
        op_kwargs={'timedelta': 12},
        dag=daily_load_dag,
    )

    task_3 = PythonOperator(
        task_id='get_team_stats',
        python_callable=get_team_info,
        provide_context=True,
        op_kwargs={'table_name': 'team_expanded'},
        dag=daily_load_dag,
    )
    



with DAG(
        dag_id='full_load',
        default_args=default_args,
) as ingestion_dag:

    with TaskGroup('Hockey_ETL') as hockey_group:

        task_1 = PythonOperator(
            task_id='get_team_info',
            python_callable=get_team_info,
            op_kwargs={'table_name': 'team'},
            dag=ingestion_dag,
        )

        task_2 = PythonOperator(
            task_id='hook_check_ids',
            python_callable=query_and_push_ids,
            op_kwargs={
                "sql": 'SELECT team_id, "firstYearOfPlay" from team',
            },
            provide_context=True,
            dag=ingestion_dag,
        )

        task_3 = PythonOperator(
            task_id='get_teams_player_info',
            python_callable=get_teams_roster_history,
            provide_context=True,
            op_kwargs={'table_name': 'roster'},
            dag=ingestion_dag,
        )

        task_4 = PythonOperator(
            task_id='get_player_stats',
            python_callable=get_current_player_stats,
            provide_context=True,
            dag=ingestion_dag,
        )
        task_1 >> task_2 >> task_3 >> task_4


# hockey_group



