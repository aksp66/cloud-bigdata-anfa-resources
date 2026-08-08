"""
anfa_logic.py
─────────────
Logique métier du pipeline Anfa, séparée du DAG Airflow.
Ces fonctions sont pures (pas d'appel réseau, pas d'objet Airflow) :
elles peuvent être testées en CI sans rien installer d'autre que Python.
"""


def construire_cle_trajets(prefixe: str = "trajets") -> str:
    """Construit la clé S3/MinIO où sont stockés les trajets générés."""
    return f"{prefixe}/trajets_recent.csv"


def verifier_liste_fichiers(objets: list) -> dict:
    """
    Vérifie qu'une liste d'objets S3/MinIO n'est pas vide et calcule un résumé.

    Args:
        objets: liste de dicts au format renvoyé par boto3 (clé "Size" en octets).

    Returns:
        Un résumé avec le nombre de fichiers et leur taille totale en Ko.

    Raises:
        ValueError: si la liste est vide (aucun résultat produit par Spark).
    """
    if not objets:
        raise ValueError("Aucun fichier de résultat trouvé dans MinIO.")

    nb_fichiers = len(objets)
    taille_totale_octets = sum(o["Size"] for o in objets)

    return {
        "nb_fichiers": nb_fichiers,
        "taille_totale_ko": round(taille_totale_octets / 1024, 1),
    }


def construire_message_notification(resume: dict) -> str:
    """Construit le message de notification à partir du résumé de vérification."""
    return (
        f"Pipeline Anfa terminé avec succès : "
        f"{resume['nb_fichiers']} fichier(s), "
        f"{resume['taille_totale_ko']} Ko au total."
    )
