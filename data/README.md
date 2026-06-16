# Données CSV et sources

Ce dossier rend visibles les fichiers demandés pour la construction de la base.

## `master/`

Ce dossier contient les tables CSV principales issues du registre multisource :

- `identity_master_v3.csv` : table maîtresse des individus, avec l'identifiant unique `elite_id`.
- `id_registry_v3.csv` : registre des identifiants et fingerprints.
- `identity_links_v3.csv` : correspondances entre les identités internes et les enregistrements sources.
- `person_external_ids.csv` : identifiants externes.
- `person_memberships.csv` : appartenances au corpus et règles de sélection.
- `career_entries_v3.csv` : mandats, fonctions et parcours institutionnels.
- `sources.csv`, `organizations.csv`, `membership_rules.csv` : catalogues de référence.

## `raw/`

Ce dossier contient les fichiers sources suffisamment petits pour être suivis directement dans le dépôt, ainsi qu'un manifeste complet :

- `raw_sources_manifest.csv` : liste des fichiers sources disponibles dans l'espace de travail.
- `data_registry_inputs/` : fichiers d'entrée utilisés par le registre d'identité.
- `data_1944_1969/` : principaux fichiers sources de la période étudiée.

Les fichiers sources trop volumineux sont fournis dans l'asset de release `raw_source_data_1944_1969.zip`.
