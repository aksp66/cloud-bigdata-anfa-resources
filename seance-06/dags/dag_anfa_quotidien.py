"""
dag_anfa_quotidien.py
─────────────────────
Pipeline quotidien d'Anfa :
  génération des trajets → analyse Spark → vérification → notification.
"""

import os
import subprocess
from datetime import datetime, timedelta

import boto3
import docker
from airflow import DAG
from airflow.operators.python import PythonOperator


def generer_trajets():
    """Tâche 1 : exécute le script de génération (dépose le CSV dans MinIO)."""
    result = subprocess.run(
        ["python", "/opt/airflow/scripts/generer_trajets.py"],
        capture_output=True, text=True, check=True,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)


def analyser_heures_pointe():
    """
    Tâche 2 : soumet le job Spark au cluster.
    On exécute spark-submit DANS le conteneur Spark Master (qui a Java + Spark),
    via le SDK Docker (socket monté dans Airflow). Plus simple qu'un JDK dans Airflow.
    """
    client = docker.from_env()
    master = client.containers.get("anfa-spark-master")
    cmd = (
        "/opt/spark/bin/spark-submit "
        "--master spark://spark-master:7077 "
        "--conf spark.jars.ivy=/tmp/.ivy2 "          # HOME=/nonexistent dans l'image Spark
        "--packages org.apache.hadoop:hadoop-aws:3.3.4,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.262 "
        "/opt/scripts/heures_de_pointe.py"
    )
    code, output = master.exec_run(cmd, stream=False, demux=False)
    print(output.decode("utf-8", errors="replace"))
    if code != 0:
        raise RuntimeError(f"[ERREUR] spark-submit a échoué (exit {code})")


def verifier_resultats():
    """Tâche 3 : vérifie que les Parquet sont bien dans MinIO. Échoue si vide."""
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
        region_name="us-east-1",
    )
    objets = s3.list_objects_v2(
        Bucket="anfa-processed", Prefix="heures_de_pointe/",
    ).get("Contents", [])

    if not objets:
        raise ValueError("[ERREUR] Aucun fichier de résultat trouvé dans MinIO !")

    taille_ko = sum(o["Size"] for o in objets) / 1024
    print(f"[OK] {len(objets)} fichiers trouvés ({taille_ko:.1f} Ko)")
    for obj in objets[:5]:
        print(f"  - {obj['Key']} ({obj['Size']} octets)")
    if len(objets) > 5:
        print(f"  ... et {len(objets) - 5} autres")


def notifier():
    """Tâche 4 : notification (ici un log ; en prod : email/Slack/PagerDuty)."""
    print("=" * 60)
    print("  PIPELINE ANFA QUOTIDIEN : SUCCÈS")
    print(f"  Heure de fin : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Résultats : s3a://anfa-processed/heures_de_pointe/")
    print("=" * 60)


default_args = {
    "owner": "anfa-data-team",
    "retries": 2,
    "retry_delay": timedelta(seconds=30),
    "email_on_failure": False,
}

with DAG(
    dag_id="anfa_pipeline_quotidien",
    description="Pipeline : génération → Spark → vérification → notification",
    schedule=None,                     # déclenchement manuel pour le TP
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["anfa", "production"],
) as dag:

    t_generer = PythonOperator(
        task_id="generer_trajets",
        python_callable=generer_trajets,
    )

    t_analyser = PythonOperator(
        task_id="analyser_heures_pointe",
        python_callable=analyser_heures_pointe,
    )

    t_verifier = PythonOperator(
        task_id="verifier_resultats",
        python_callable=verifier_resultats,
    )

    t_notifier = PythonOperator(
        task_id="notifier",
        python_callable=notifier,
    )

    t_generer >> t_analyser >> t_verifier >> t_notifier
