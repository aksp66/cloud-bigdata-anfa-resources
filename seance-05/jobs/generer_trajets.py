"""
generer_trajets.py
──────────────────
Génère un fichier CSV simulé d'historique de trajets Anfa.
Stocké directement dans MinIO sous anfa-raw/trajets/.
"""

import csv
import random
from datetime import datetime, timedelta
from io import StringIO

import boto3

random.seed(2026)

# Paramètres de génération
NB_JOURS         = 30        # 1 mois d'historique
LIGNES           = [f"L{i:02d}" for i in range(1, 13)]   # L01 à L12
BUS_PAR_LIGNE    = 8         # ~8 bus par ligne en moyenne
DATE_DEBUT       = datetime(2026, 5, 1, 5, 0, 0)         # 1er mai 2026

# Distribution réaliste des heures de pointe
HEURES_POIDS = {
    5: 1, 6: 5, 7: 15, 8: 18, 9: 10, 10: 6, 11: 5, 12: 7,
    13: 6, 14: 5, 15: 5, 16: 8, 17: 17, 18: 18, 19: 12,
    20: 6, 21: 3, 22: 1,
}

def main():
    print(f"Génération de {NB_JOURS} jours de trajets...")
    
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["trajet_id", "ligne_id", "bus_id", "depart", "duree_min", "passagers", "retard_min"])

    trajet_id = 1
    for jour in range(NB_JOURS):
        date_jour = DATE_DEBUT + timedelta(days=jour)
        for ligne in LIGNES:
            for bus_num in range(BUS_PAR_LIGNE):
                bus_id = f"B{(LIGNES.index(ligne) * BUS_PAR_LIGNE + bus_num + 1):03d}"
                # ~30 trajets par bus et par jour, répartis selon les heures de pointe
                nb_trajets = random.randint(20, 35)
                heures_choisies = random.choices(
                    population=list(HEURES_POIDS.keys()),
                    weights=list(HEURES_POIDS.values()),
                    k=nb_trajets,
                )
                for heure in heures_choisies:
                    minute = random.randint(0, 59)
                    depart = date_jour.replace(hour=heure, minute=minute)
                    duree = random.randint(20, 60)
                    # Plus de passagers aux heures de pointe
                    passagers_base = HEURES_POIDS[heure] * 2
                    passagers = max(5, passagers_base + random.randint(-5, 15))
                    # Retard plus fréquent aux heures de pointe
                    retard = max(0, int(random.gauss(HEURES_POIDS[heure] * 0.5, 3)))
                    writer.writerow([
                        f"T{trajet_id:07d}", ligne, bus_id,
                        depart.strftime("%Y-%m-%d %H:%M:%S"),
                        duree, passagers, retard,
                    ])
                    trajet_id += 1

    # Upload direct dans MinIO
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="anfa-app-key",
        aws_secret_access_key="anfa-app-secret-2026",
        region_name="us-east-1",
    )
    s3.put_object(
        Bucket="anfa-raw",
        Key="trajets/trajets_30j.csv",
        Body=buffer.getvalue().encode("utf-8"),
    )
    print(f"[OK] {trajet_id - 1} trajets générés et stockés dans s3://anfa-raw/trajets/trajets_30j.csv")


if __name__ == "__main__":
    main()
