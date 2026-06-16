# Plan de publication GitHub

## Dépôt cible

`Yuhaohan233/Base-de-donn-es-gaulliste-multisource`

## Description courte du dépôt

Base de données multisource sur les élites, réseaux et appartenances gaullistes, avec schéma PostgreSQL, export JSON, tables CSV et documentation de revue.

## Contenu à placer dans le dépôt

Le contenu du dossier suivant doit être placé à la racine du dépôt :

`github_package_fr/repository`

Il contient la documentation, les schémas, les scripts et les petits fichiers de revue/métadonnées.

## Release recommandée

- Tag : `v3-multisource-2026-06-16`
- Titre : `Base de données gaulliste multisource - version v3`
- Description : utiliser le contenu de `github_package_fr/release_description_fr.md`.

## Assets à joindre à la release

- `github_package_fr/release_assets/gaullist_db_v3.dump`
- `github_package_fr/release_assets/json_v3.zip`
- `github_package_fr/release_assets/data_registry_outputs_v3.zip`
- `github_package_fr/release_assets/raw_source_data_1944_1969.zip`

## Pourquoi utiliser une release

Les fichiers de données complets sont volumineux. Le dépôt Git doit contenir la documentation, les schémas et les scripts ; les exports complets doivent être distribués comme assets de release.
