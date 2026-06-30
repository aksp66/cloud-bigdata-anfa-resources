"""
analyse_referentiel_cluster.py
──────────────────────────────
Analyse du référentiel Anfa, exécutée sur un cluster Spark distribué.
Lit les CSV depuis MinIO (S3A), calcule des statistiques, et écrit
les résultats agrégés au format Parquet dans MinIO.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as spark_sum, count, avg, desc, col


def creer_spark_session() -> SparkSession:
    """
    Crée une SparkSession configurée pour :
    - Tourner sur le cluster (master=spark://spark-master:7077)
    - Lire/écrire depuis MinIO via le connecteur S3A
    """
    return (
        SparkSession.builder
        .appName("Anfa - Analyse référentiel (cluster)")
        # ── Mode CLUSTER : on pointe vers le master Spark ──
        # (en mode local on aurait .master("local[*]"))
        .master("spark://spark-master:7077")
        # ── Connecteur S3A pour parler à MinIO ──
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", "anfa-app-key")
        .config("spark.hadoop.fs.s3a.secret.key", "anfa-app-secret-2026")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        # ── Packages Maven : on inclut hadoop-aws ──
        # spark-submit téléchargera ces dépendances automatiquement
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )


def main() -> None:
    spark = creer_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    print("\n" + "=" * 60)
    print("  ANALYSE DU RÉFÉRENTIEL ANFA  CLUSTER")
    print("=" * 60)

    # ──────────────────────────────────────────────────────
    # Lecture des CSV depuis MinIO
    # ──────────────────────────────────────────────────────
    lignes = spark.read.csv("s3a://anfa-raw/referentiel/lignes.csv", header=True, inferSchema=True)
    arrets = spark.read.csv("s3a://anfa-raw/referentiel/arrets.csv", header=True, inferSchema=True)
    bus    = spark.read.csv("s3a://anfa-raw/referentiel/bus.csv",    header=True, inferSchema=True)
    tarifs = spark.read.csv("s3a://anfa-raw/referentiel/tarifs.csv", header=True, inferSchema=True)

    # ──────────────────────────────────────────────────────
    # Calculs
    # ──────────────────────────────────────────────────────
    nb_lignes         = lignes.count()
    nb_arrets_uniques = arrets.select("arret_id").distinct().count()
    nb_bus            = bus.count()
    nb_bus_actifs     = bus.filter(col("statut") == "actif").count()

    capacite_totale = (
        bus.filter(col("statut") == "actif")
           .agg(spark_sum("capacite").alias("total"))
           .collect()[0]["total"]
    )

    print(f"\n  Nombre de lignes        : {nb_lignes}")
    print(f"  Nombre d'arrêts uniques  : {nb_arrets_uniques}")
    print(f"  Nombre total de bus      : {nb_bus}")
    print(f"  Dont actifs              : {nb_bus_actifs}")
    print(f"  Capacité totale flotte   : {capacite_totale} places")

    # ──────────────────────────────────────────────────────
    # Bus actifs par ligne  calcul plus intéressant
    # car il implique un groupBy (= shuffle)
    # ──────────────────────────────────────────────────────
    print("\n  Répartition des bus actifs par ligne :")
    bus_par_ligne = (
        bus.filter(col("statut") == "actif")
           .groupBy("ligne_assignee")
           .agg(
               count("*").alias("nb_bus"),
               spark_sum("capacite").alias("capacite_totale"),
           )
           .orderBy(desc("nb_bus"))
    )
    bus_par_ligne.show(15, truncate=False)

    # ──────────────────────────────────────────────────────
    # ÉCRITURE des résultats dans MinIO (anfa-processed)
    # ──────────────────────────────────────────────────────
    print("\n  Écriture des résultats dans s3a://anfa-processed/...")
    bus_par_ligne.write \
        .mode("overwrite") \
        .parquet("s3a://anfa-processed/bus_par_ligne")
    print("  [OK] Résultats écrits en Parquet.")

    print("\n" + "=" * 60)
    print("  Analyse terminée.\n")

    spark.stop()


if __name__ == "__main__":
    main()
