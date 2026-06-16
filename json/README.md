# Exports JSON

Ce dossier rend visibles les fichiers JSON structurés demandés pour la documentation du modèle de données.

## `sources/`

Un fichier JSON par source ou corpus documentaire. Chaque fichier décrit la source, ses métadonnées bibliographiques et les personnes auxquelles elle contribue.

## `organizations/`

Un fichier JSON par organisation ou groupe politique/institutionnel référencé dans la base.

## Export complet des personnes

Les 66 059 fichiers JSON individuels ne sont pas suivis directement dans le dépôt afin d'éviter un dépôt trop lourd. Ils sont fournis dans l'asset de release :

- `json_v3.zip`

Après extraction, le dossier `persons/` contient un fichier JSON par individu, relié à la table CSV maîtresse par le même identifiant `elite_id`.
