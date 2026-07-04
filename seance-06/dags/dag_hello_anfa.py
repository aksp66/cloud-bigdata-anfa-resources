"""
dag_hello_anfa.py
─────────────────
DAG minimal d'introduction : deux tâches Python qui s'enchaînent.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator


def dire_bonjour():
    print("[OK] Bonjour de la plateforme Anfa !")
    print("[OK] Cette tâche s'exécute dans Airflow.")


def lister_lignes():
    lignes = [f"L{i:02d}" for i in range(1, 13)]
    print(f"[OK] Anfa exploite {len(lignes)} lignes de bus :")
    for ligne in lignes:
        print(f"    - {ligne}")


default_args = {
    "owner": "anfa-data-team",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

with DAG(
    dag_id="hello_anfa",
    description="DAG d'introduction : premiers pas avec Airflow",
    schedule_interval=None,        # déclenchement manuel
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["initiation", "anfa"],
) as dag:

    t1 = PythonOperator(task_id="dire_bonjour", python_callable=dire_bonjour)
    t2 = PythonOperator(task_id="lister_lignes", python_callable=lister_lignes)

    t1 >> t2
