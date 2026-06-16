# Guide de revue des identités

Le fichier `review/revue_identites_a_traiter.csv` contient les cas où un rapprochement automatique doit être confirmé ou rejeté manuellement.

## Colonnes de décision

- `statut_revue` : statut de traitement du cas.
- `decision_revue` : décision finale du relecteur.
- `elite_id_accepte` : identifiant interne retenu si la fusion est confirmée.
- `url_preuve` : lien vers la source permettant de justifier la décision.
- `note_revue` : commentaire libre.

## Priorités

- `P1_quick_review` : cas probablement faciles, à traiter en premier.
- `P2_ambiguous` : cas ambigus nécessitant une vérification plus attentive.
- `P3_hard_conflict` : conflits forts, à traiter uniquement avec preuve documentaire solide.

Les valeurs de code sont conservées afin de rester compatibles avec les scripts existants.
