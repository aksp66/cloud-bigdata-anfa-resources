# Fiche de conformité — Application mobile passagers Anfa

> Gabarit fourni. Complétez chaque section **en 2-4 lignes**, en vous appuyant sur le CM.
> Il n'y a pas de "bonne réponse" unique sur certains points — l'important est le raisonnement.

## 1. Finalité du traitement

Trois finalités distinctes et non interchangeables : la position GPS sert uniquement à
proposer le trajet/l'arrêt le plus proche en temps réel ; l'historique mobile money sert
à facturer l'abonnement ; le numéro de téléphone sert d'identifiant de compte. Le principe
de finalité (RGPD, repris par la loi togolaise) interdit de réutiliser, par exemple, la
position GPS collectée pour le trajet à des fins de profilage marketing sans nouvelle base
légale.

## 2. Données collectées et leur sensibilité

Position GPS (donnée de géolocalisation, potentiellement identifiante si croisée avec les
horaires de trajet), historique de paiements mobile money (donnée financière) et numéro de
téléphone (identifiant direct de la personne). La donnée la plus sensible est
l'**historique mobile money** : combinée au numéro de téléphone, elle révèle des habitudes
de déplacement et de dépense d'une personne identifiée, avec un risque de préjudice élevé
en cas de fuite (fraude, chantage).

## 3. Base légale applicable

Le numéro de téléphone et la position GPS relèvent de la **loi n° 2019-014** (protection
des données à caractère personnel) : Anfa est responsable de traitement et doit justifier
d'une base légale (ici, l'exécution du service demandé par le passager). L'historique
mobile money relève **en plus** de la **loi n° 2017-007 modifiée par la loi 2023-012**
(transactions électroniques), car il s'agit d'un paiement électronique. Une même donnée
(le paiement mobile money d'un passager identifié) est donc soumise aux deux textes
simultanément.

## 4. Durée de conservation

Par principe de minimisation, chaque donnée ne devrait être conservée que le temps
nécessaire à sa finalité : la position GPS en temps réel n'a pas besoin d'être gardée
au-delà de la session de trajet (sauf agrégation anonymisée pour les statistiques de
lignes, séance 5-6) ; l'historique de paiement doit être conservé le temps légal minimal
imposé pour la comptabilité/les litiges, pas indéfiniment "au cas où".

## 5. Hébergement et souveraineté

Ces données doivent rester hébergées sur une infrastructure sous juridiction togolaise (ou
a minima non soumise à une loi étrangère extraterritoriale), exactement le choix du 100%
local/open source fait depuis la séance 1 (MinIO, Postgres, etc.). Héberger chez un cloud
américain exposerait ces données au **Patriot Act** : les autorités américaines pourraient
y accéder même si les serveurs sont physiquement hors des États-Unis, ce qui complique la
conformité vis-à-vis de l'autorité togolaise de protection des données.

## 6. Droit des personnes concernées

Oui, un passager doit pouvoir exercer un droit à l'oubli (loi 2019-014, inspirée du RGPD).
Le système technique actuel d'Anfa le permettrait raisonnablement : les données vivent dans
MinIO/Postgres sous forme de fichiers/tables identifiables par `bus_id`/utilisateur, donc
supprimables sur demande. Ce qui manquerait en l'état, c'est une procédure organisationnelle
formalisée (qui traite la demande, sous quel délai) et un mécanisme de traçabilité
(catalogue de données, lineage, évoqués en CM) pour garantir qu'aucune copie oubliée ne
subsiste dans un export ou une sauvegarde.
