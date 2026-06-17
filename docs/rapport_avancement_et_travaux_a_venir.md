# Rapport d'avancement et travaux à venir

## 1. État du projet

La base de données gaulliste multisource comprend une architecture relationnelle, une table CSV maîtresse, des exports JSON, une sauvegarde PostgreSQL et une organisation documentaire publiée dans le dépôt GitHub du projet.

Le dépôt GitHub est disponible à l'adresse suivante :

https://github.com/Yuhaohan233/Base-de-donn-es-gaulliste-multisource

## 2. Travaux réalisés

### 2.1 Schéma de stockage JSON

Le schéma JSON v3 distingue trois types d'objets :

- personnes ;
- sources documentaires ;
- organisations.

Les fichiers principaux sont :

- `schema/person_v3.schema.json`
- `schema/source_v3.schema.json`
- `schema/organization_v3.schema.json`
- `json/sources/`
- `json/organizations/`

L'archive `json_v3.zip` contient l'export JSON complet des personnes, soit 66 059 fichiers JSON individuels.

### 2.2 Table CSV maîtresse et identifiants uniques

La table CSV maîtresse recense les individus et associe à chacun un identifiant interne unique `elite_id`.

Les fichiers principaux sont :

- `data/master/identity_master_v3.csv`
- `data/master/id_registry_v3.csv`
- `data/master/identity_links_v3.csv`
- `data/master/person_external_ids.csv`
- `data/master/person_memberships.csv`
- `data/master/career_entries_v3.csv`

La table maîtresse contient 66 059 individus.

### 2.3 Fichiers JSON par source

Les principales sources et organisations disposent de fichiers JSON séparés.

Le dépôt contient :

- `json/sources/` : 12 fichiers JSON de sources ;
- `json/organizations/` : 14 fichiers JSON d'organisations.

Chaque fichier de source contient les métadonnées de la source, les personnes concernées, les champs fournis, les règles d'appariement et les identifiants d'enregistrement source.

### 2.4 Architecture logique de la base

L'architecture relationnelle PostgreSQL, le schéma DBML et les scripts d'import/vérification sont présents dans le dépôt.

Les fichiers principaux sont :

- `schema/database_v3_multisource.sql`
- `schema/database_v3_multisource.dbml`
- `schema/import_multisource_v3.sql`
- `schema/verify_multisource_v3.sql`

Le fichier `database_v3_multisource.dbml` peut être importé dans dbdiagram.io pour générer un diagramme ER.

### 2.5 Données sources et fichiers intermédiaires

Le dossier `data/raw/` contient les fichiers sources et intermédiaires suivis directement dans le dépôt.

L'ensemble complet des données sources est disponible dans l'archive :

- `raw_source_data_1944_1969.zip`

Les autres archives complètes sont :

- `gaullist_db_v3.dump`
- `json_v3.zip`
- `data_registry_outputs_v3.zip`

### 2.6 Organisation du dépôt

Le dépôt GitHub contient les répertoires suivants :

- `README.md`
- `data/`
- `json/`
- `docs/`
- `schema/`
- `review/`
- `metadata/`
- `scripts/`

La release associée contient quatre fichiers complets :

- `gaullist_db_v3.dump`
- `json_v3.zip`
- `data_registry_outputs_v3.zip`
- `raw_source_data_1944_1969.zip`

## 3. Volume des données

La base contient :

- 66 059 individus dans la table maîtresse ;
- 66 553 liens d'identité multisource ;
- 65 449 identifiants externes ;
- 66 912 lignes d'appartenance ou de qualification ;
- 1 891 lignes de carrière ou de mandat ;
- 12 sources documentaires ;
- 14 organisations ;
- 3 837 cas à vérifier manuellement.

## 4. Travaux restant à réaliser

### 4.1 Revue manuelle des conflits d'identité

La file de revue contient 3 837 cas.

Répartition :

- `P1_quick_review` : 899 cas à traiter en priorité ;
- `P2_ambiguous` : cas ambigus nécessitant une vérification plus attentive ;
- `P3_hard_conflict` : conflits forts exigeant une preuve documentaire solide.

Cette étape conditionne la fiabilité des carrières, des professions, de la mobilité sociale et des réseaux.

### 4.2 Extraction plus fine des champs Sycomore

Les informations de base issues de Sycomore sont intégrées :

- dates de début et de fin de mandat ;
- législature ;
- département ;
- groupe parlementaire ;
- appartenance gaulliste du groupe.

Plusieurs champs restent largement incomplets :

- `circonscription` ;
- `a_eu_suppleant` ;
- `suppleant_de`.

Ces champs doivent être extraits à partir du texte biographique des notices Sycomore.

### 4.3 Données de mobilité sociale

La structure prévoit les champs nécessaires à l'analyse de mobilité sociale. Leur renseignement systématique reste à effectuer.

Champs à compléter :

- professions successives des individus ;
- profession du père ;
- profession de la mère ;
- formation et établissements fréquentés ;
- codes de catégorie sociale ;
- type de mobilité sociale.

### 4.4 Réseau relationnel

La base contient des appartenances institutionnelles, des groupes politiques et des sources communes. Le réseau relationnel entre individus reste à construire.

Deux catégories de liens doivent être distinguées :

- liens prouvés : parenté, mariage, appartenance à une même organisation, réseau de résistance, groupe politique ;
- liens potentiels : même commune d'origine, même école, même administration, même entreprise ou même unité militaire.

Cette étape dépend de la stabilisation préalable des identités.

### 4.5 Documentation détaillée des champs sources

Les fichiers JSON par source sont disponibles. Certaines sources nécessitent encore une documentation plus détaillée.

Compléments à produire :

- signification de chaque champ source ;
- correspondance entre les champs sources et les champs unifiés ;
- niveaux de fiabilité des sources ;
- règles de gestion des valeurs manquantes ou conflictuelles.

## 5. Étapes suivantes

### Étape 1 : revue des cas d'identité prioritaires

Les 899 cas `P1_quick_review` constituent le premier lot de revue.

Pour chaque cas, les éléments suivants doivent être établis :

- identité ou non-identité des enregistrements comparés ;
- décision de fusion ou de maintien séparé ;
- `elite_id` à conserver ;
- preuve documentaire associée à la décision.

Fichier concerné :

- `review/revue_identites_a_traiter.csv`

### Étape 2 : complétion des champs Sycomore manquants

Champs prioritaires :

- `circonscription`
- `a_eu_suppleant`
- `suppleant_de`

Ces champs correspondent à une demande explicite de l'encadrement.

### Étape 3 : collecte des données de mobilité sociale

Après stabilisation des identités, les données suivantes doivent être collectées :

- professions ;
- professions des parents ;
- formation ;
- codes sociaux ;
- type de mobilité.

### Étape 4 : construction du réseau relationnel

Après stabilisation des identités et des informations de carrière, les relations entre individus peuvent être construites en distinguant les liens prouvés et les liens potentiels.
