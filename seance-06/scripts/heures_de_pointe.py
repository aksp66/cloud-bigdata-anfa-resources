"""
heures_de_pointe.py
───────────────────
Analyse les heures de pointe par ligne. Soumis au cluster Spark
par Airflow (spark-submit). Reprend le job de la séance 5.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import hour, count, sum as spark_sum, avg, col


def creer_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("Anfa - Heures de pointe (Airflow)")
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

    print("[INFO] Lecture des trajets depuis MinIO...")
    trajets = spark.read.csv(
        "s3a://anfa-raw/trajets/trajets_recent.csv",
        header=True,
        inferSchema=True,
    )
    print(f"[INFO] {trajets.count()} trajets analysés.")

    pointe = (
        trajets
        .withColumn("heure", hour(col("depart")))
        .groupBy("ligne_id", "heure")
        .agg(
            count("*").alias("nb_trajets"),
            spark_sum("passagers").alias("total_passagers"),
            avg("retard_min").alias("retard_moyen"),
        )
        .orderBy("ligne_id", "heure")
    )

    print("[INFO] Écriture des résultats dans MinIO...")
    pointe.write \
        .mode("overwrite") \
        .partitionBy("ligne_id") \
        .parquet("s3a://anfa-processed/heures_de_pointe")

    print("[OK] Analyse terminée.")
    spark.stop()


if __name__ == "__main__":
    main()
