"""
heures_de_pointe.py
───────────────────
Analyse les heures de pointe par ligne de bus.
Lit les trajets depuis MinIO, agrège, et écrit les résultats.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    hour, count, sum as spark_sum, avg, desc, col
)


def creer_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("Anfa - Heures de pointe")
        .master("spark://spark-master:7077")
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "anfa-app-key")
        .config("spark.hadoop.fs.s3a.secret.key", "anfa-app-secret-2026")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.jars.packages",
                "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )


def main():
    spark = creer_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("\n" + "=" * 60)
    print("  ANFA  ANALYSE DES HEURES DE POINTE")
    print("=" * 60)

    # Lecture des trajets
    trajets = spark.read.csv(
        "s3a://anfa-raw/trajets/trajets_30j.csv",
        header=True,
        inferSchema=True,
    )
    nb_trajets = trajets.count()
    print(f"\n  Trajets analysés : {nb_trajets:,}")

    # Extraction de l'heure depuis le timestamp
    trajets_avec_heure = trajets.withColumn("heure", hour(col("depart")))

    # ──────────────────────────────────────────────────────
    # Agrégation principale : par ligne et par heure
    # ──────────────────────────────────────────────────────
    print("\n  Calcul des agrégats par ligne et par heure...")
    pointe = (
        trajets_avec_heure
        .groupBy("ligne_id", "heure")
        .agg(
            count("*").alias("nb_trajets"),
            spark_sum("passagers").alias("total_passagers"),
            avg("retard_min").alias("retard_moyen"),
        )
        .orderBy("ligne_id", "heure")
    )

    # ──────────────────────────────────────────────────────
    # Top 5 des combinaisons (ligne, heure) les plus chargées
    # ──────────────────────────────────────────────────────
    print("\n  Top 10 des heures les plus chargées par ligne :")
    top10 = pointe.orderBy(desc("total_passagers")).limit(10)
    top10.show(truncate=False)

    # ──────────────────────────────────────────────────────
    # Écriture des résultats au format Parquet
    # ──────────────────────────────────────────────────────
    print("\n  Écriture des résultats dans s3a://anfa-processed/heures_de_pointe/...")
    pointe.write \
        .mode("overwrite") \
        .partitionBy("ligne_id") \
        .parquet("s3a://anfa-processed/heures_de_pointe")
    print("  [OK] Résultats écrits, partitionnés par ligne.")

    print("\n" + "=" * 60)
    print("  Analyse terminée.\n")

    spark.stop()


if __name__ == "__main__":
    main()
