"""
generer_trajets.py
──────────────────
Génère un CSV simulé d'historique de trajets Anfa et le dépose
dans MinIO sous anfa-raw/trajets/. Appelé par le DAG Airflow.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from io import StringIO

import boto3

random.seed(2026)

NB_JOURS      = 7        # 1 semaine pour aller vite en TP
LIGNES        = [f"L{i:02d}" for i in range(1, 13)]
BUS_PAR_LIGNE = 8
DATE_DEBUT    = datetime(2026, 5, 1, 5, 0, 0)

HEURES_POIDS = {
    5: 1, 6: 5, 7: 15, 8: 18, 9: 10, 10: 6, 11: 5, 12: 7,
    13: 6, 14: 5, 15: 5, 16: 8, 17: 17, 18: 18, 19: 12,
    20: 6, 21: 3, 22: 1,
}


def generer_csv() -> str:
    """Construit le CSV des trajets en mémoire et le renvoie."""
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["trajet_id", "ligne_id", "bus_id", "depart",
                     "duree_min", "passagers", "retard_min"])

    trajet_id = 1
    for jour in range(NB_JOURS):
        date_jour = DATE_DEBUT + timedelta(days=jour)
        for ligne in LIGNES:
            for bus_num in range(BUS_PAR_LIGNE):
                bus_id = f"B{(LIGNES.index(ligne) * BUS_PAR_LIGNE + bus_num + 1):03d}"
                heures = random.choices(
                    population=list(HEURES_POIDS.keys()),
                    weights=list(HEURES_POIDS.values()),
                    k=random.randint(20, 35),
                )
                for heure in heures:
                    depart = date_jour.replace(hour=heure, minute=random.randint(0, 59))
                    passagers = max(5, HEURES_POIDS[heure] * 2 + random.randint(-5, 15))
                    retard = max(0, int(random.gauss(HEURES_POIDS[heure] * 0.5, 3)))
                    writer.writerow([
                        f"T{trajet_id:07d}", ligne, bus_id,
                        depart.strftime("%Y-%m-%d %H:%M:%S"),
                        random.randint(20, 60), passagers, retard,
                    ])
                    trajet_id += 1
    print(f"[OK] {trajet_id - 1} trajets générés.")
    return buffer.getvalue()


def main():
    print(f"[INFO] Génération de {NB_JOURS} jours de trajets...")
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://minio:9000"),
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "anfa-app-key"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "anfa-app-secret-2026"),
        region_name="us-east-1",
    )
    s3.put_object(
        Bucket="anfa-raw",
        Key="trajets/trajets_recent.csv",
        Body=generer_csv().encode("utf-8"),
    )
    print("[OK] Déposé dans s3://anfa-raw/trajets/trajets_recent.csv")


if __name__ == "__main__":
    main()
