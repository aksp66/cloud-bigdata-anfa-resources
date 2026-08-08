"""
demo_drift.py — démonstration de data drift pour le rapport de fin de module.
Charge le modèle en Production (alias) et compare son erreur sur des données
"normales" (même distribution que l'entraînement) vs des données "après drift"
(2 nouvelles lignes L13/L14 jamais vues + décalage des habitudes horaires),
exactement le scénario de Kossi dans le CM séance 10.
"""
import random
import mlflow
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score

random.seed(7)
mlflow.set_tracking_uri("http://localhost:5000")

modele = mlflow.sklearn.load_model("models:/anfa-prediction-affluence@production")
print("[OK] Modèle 'anfa-prediction-affluence@production' chargé.")

HEURES_POIDS = {
    5: 1, 6: 5, 7: 15, 8: 18, 9: 10, 10: 6, 11: 5, 12: 7,
    13: 6, 14: 5, 15: 5, 16: 8, 17: 17, 18: 18, 19: 12,
    20: 6, 21: 3, 22: 1,
}


def generer(lignes, heures_poids, n_par_couple=15, bruit=3):
    rows = []
    for ligne in lignes:
        niveau_base_ligne = random.uniform(0.7, 1.4)
        for heure, poids in heures_poids.items():
            for _ in range(n_par_couple):
                base = poids * niveau_base_ligne
                b = random.uniform(-bruit, bruit)
                nb = max(0, round(base * 3 + b))
                rows.append({"ligne_id": ligne, "heure": heure, "nb_passagers": nb})
    return pd.DataFrame(rows)


# 1) Données "normales" : mêmes 12 lignes, mêmes habitudes horaires que l'entraînement
LIGNES_CONNUES = [f"L{i:02d}" for i in range(1, 13)]
df_normal = generer(LIGNES_CONNUES, HEURES_POIDS)
X_n, y_n = df_normal[["ligne_id", "heure"]], df_normal["nb_passagers"]
pred_n = modele.predict(X_n)
mae_n = mean_absolute_error(y_n, pred_n)
r2_n = r2_score(y_n, pred_n)

# 2) Données "après drift" : 2 nouvelles lignes (L13, L14) jamais vues à l'entraînement
#    + décalage des habitudes horaires (nouveau pic à 20h-21h, ex. sortie d'usine tardive)
LIGNES_APRES_DRIFT = LIGNES_CONNUES + ["L13", "L14"]
HEURES_POIDS_DRIFT = dict(HEURES_POIDS)
HEURES_POIDS_DRIFT[20] = 16  # nouveau pic (était 6)
HEURES_POIDS_DRIFT[21] = 14  # nouveau pic (était 3)
df_drift = generer(LIGNES_APRES_DRIFT, HEURES_POIDS_DRIFT)
X_d, y_d = df_drift[["ligne_id", "heure"]], df_drift["nb_passagers"]
pred_d = modele.predict(X_d)
mae_d = mean_absolute_error(y_d, pred_d)
r2_d = r2_score(y_d, pred_d)

# 3) Uniquement sur les 2 nouvelles lignes (jamais vues) : le cas le plus parlant
df_nouvelles = df_drift[df_drift["ligne_id"].isin(["L13", "L14"])]
pred_nv = modele.predict(df_nouvelles[["ligne_id", "heure"]])
mae_nv = mean_absolute_error(df_nouvelles["nb_passagers"], pred_nv)

print("\n=== Comparaison avant / après drift (modèle Production inchangé) ===")
print(f"Données normales (12 lignes connues)      : MAE = {mae_n:.2f}  R² = {r2_n:.3f}")
print(f"Données après drift (12+2 lignes, horaires modifiés) : MAE = {mae_d:.2f}  R² = {r2_d:.3f}")
print(f"Uniquement sur L13/L14 (jamais vues à l'entraînement) : MAE = {mae_nv:.2f}")
print(f"\nDégradation du MAE : {(mae_d - mae_n) / mae_n * 100:+.1f} %")
