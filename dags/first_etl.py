from airflow import DAG
import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
import os

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}
with DAG("my_dag_name",default_args=default_args) as dag:
    op = DummyOperator(task_id="task")