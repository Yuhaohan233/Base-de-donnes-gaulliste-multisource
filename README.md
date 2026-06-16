# Base de données gaulliste multisource (version v3)

Ce dépôt présente une version de diffusion de la base de données construite pour le projet de recherche sur les élites et réseaux gaullistes. Le contenu reprend la base locale actuelle, avec une documentation en français afin de faciliter la relecture par l'encadrant.

## Contenu du dépôt

- `schema/` : schéma SQL PostgreSQL, schéma DBML pour dbdiagram.io, schémas JSON et scripts SQL d'import/vérification.
- `data/` : tables CSV maîtresses, registre des identifiants et fichiers sources disponibles.
- `json/` : fichiers JSON visibles par source et par organisation ; l'export complet des personnes est fourni dans la release.
- `docs/` : description de l'architecture, logique de revue des identités et guide de restauration.
- `review/` : fichier des cas d'identité à vérifier manuellement et synthèse de la file de revue.
- `metadata/` : catalogue des sources, organisations, règles d'appartenance et manifeste de diffusion.
- `scripts/` : scripts Python utilisés pour construire le registre multisource et exporter les fichiers JSON.

## Assets à joindre dans GitHub Release

Les fichiers volumineux ne doivent pas être placés directement dans le dépôt Git. Ils sont préparés dans `github_package_fr/release_assets` :

- `gaullist_db_v3.dump` : sauvegarde PostgreSQL restaurable.
- `json_v3.zip` : export JSON v3 complet.
- `data_registry_outputs_v3.zip` : exports CSV/JSON issus du registre multisource.
- `raw_source_data_1944_1969.zip` : fichiers sources et données brutes disponibles.

## État des données

- 66 059 individus dans la table d'identité principale.
- 66 553 liens d'identité multisource.
- 65 449 identifiants externes.
- 66 912 lignes d'appartenance à un groupe/source.
- 3 837 cas restant à vérifier manuellement, dont 899 en priorité rapide.

## Restauration PostgreSQL

Après avoir téléchargé `gaullist_db_v3.dump` depuis la release GitHub :

```bash
createdb gaullist_db
pg_restore -d gaullist_db gaullist_db_v3.dump
```

Le schéma relationnel est documenté dans `schema/database_v3_multisource.sql` et visualisable avec `schema/database_v3_multisource.dbml` sur dbdiagram.io.
