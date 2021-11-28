from airflow import DAG
import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator

with DAG("my_dag_name") as dag:
    op = DummyOperator(task_id="task")