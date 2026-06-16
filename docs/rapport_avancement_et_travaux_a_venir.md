# Rapport d'avancement et travaux à venir

## 1. État actuel du projet

Le projet dispose désormais d'une première version structurée de la base de données : architecture relationnelle, intégration multisource, table CSV maîtresse, export JSON, sauvegarde PostgreSQL et publication dans le dépôt GitHub privé.

Le dépôt GitHub est disponible ici :

https://github.com/Yuhaohan233/Base-de-donn-es-gaulliste-multisource

Le dépôt est actuellement privé. Le contenu principal du dépôt et les fichiers volumineux placés en release ont été téléversés.

## 2. Travaux déjà réalisés

### 2.1 Schéma de stockage JSON

Le schéma JSON v3 a été défini pour trois types d'objets :

- personnes ;
- sources documentaires ;
- organisations.

Les fichiers principaux sont :

- `schema/person_v3.schema.json`
- `schema/source_v3.schema.json`
- `schema/organization_v3.schema.json`
- `json/sources/`
- `json/organizations/`

L'export JSON complet des personnes est fourni dans l'asset de release `json_v3.zip`. Il contient 66 059 fichiers JSON individuels.

### 2.2 Table CSV maîtresse et identifiants uniques

Une table CSV maîtresse a été créée afin de recenser les individus et de leur attribuer un identifiant unique interne `elite_id`.

Les fichiers principaux sont :

- `data/master/identity_master_v3.csv`
- `data/master/id_registry_v3.csv`
- `data/master/identity_links_v3.csv`
- `data/master/person_external_ids.csv`
- `data/master/person_memberships.csv`
- `data/master/career_entries_v3.csv`

La table maîtresse contient actuellement 66 059 individus.

### 2.3 Fichiers JSON par source

Des fichiers JSON séparés ont été générés pour les principales sources et organisations.

Le dépôt contient directement :

- `json/sources/` : 12 fichiers JSON de sources ;
- `json/organizations/` : 14 fichiers JSON d'organisations.

Chaque fichier de source contient les métadonnées de la source, les personnes concernées, les champs fournis, les règles d'appariement et les identifiants d'enregistrement source.

### 2.4 Architecture logique de la base

L'architecture relationnelle PostgreSQL, le schéma DBML et les scripts d'import/vérification sont disponibles.

Les fichiers principaux sont :

- `schema/database_v3_multisource.sql`
- `schema/database_v3_multisource.dbml`
- `schema/import_multisource_v3.sql`
- `schema/verify_multisource_v3.sql`

Le fichier `database_v3_multisource.dbml` peut être importé dans dbdiagram.io pour générer un diagramme ER.

### 2.5 Données sources et fichiers intermédiaires

Le dossier `data/raw/` contient les fichiers sources et intermédiaires pouvant être suivis directement dans le dépôt.

L'ensemble complet des données sources est disponible dans l'asset de release :

- `raw_source_data_1944_1969.zip`

Les autres assets complets sont :

- `gaullist_db_v3.dump`
- `json_v3.zip`
- `data_registry_outputs_v3.zip`

### 2.6 Publication GitHub

Le dépôt GitHub contient actuellement :

- `README.md`
- `data/`
- `json/`
- `docs/`
- `schema/`
- `review/`
- `metadata/`
- `scripts/`

La release contient quatre fichiers complets :

- `gaullist_db_v3.dump`
- `json_v3.zip`
- `data_registry_outputs_v3.zip`
- `raw_source_data_1944_1969.zip`

## 3. Volume actuel des données

À ce stade, la base contient :

- 66 059 individus dans la table maîtresse ;
- 66 553 liens d'identité multisource ;
- 65 449 identifiants externes ;
- 66 912 lignes d'appartenance ou de qualification ;
- 1 891 lignes de carrière ou de mandat ;
- 12 sources documentaires ;
- 14 organisations ;
- 3 837 cas restant à vérifier manuellement.

## 4. Travaux restant à réaliser

### 4.1 Revue manuelle des conflits d'identité

Il reste 3 837 cas à vérifier manuellement.

Parmi eux :

- `P1_quick_review` : 899 cas à traiter en priorité ;
- `P2_ambiguous` : cas ambigus nécessitant une vérification plus attentive ;
- `P3_hard_conflict` : conflits forts exigeant une preuve documentaire solide.

Cette étape est prioritaire, car les erreurs d'identité peuvent ensuite affecter les carrières, les professions, la mobilité sociale et les réseaux.

### 4.2 Extraction plus fine des champs Sycomore

Les informations de base issues de Sycomore sont déjà intégrées :

- dates de début et de fin de mandat ;
- législature ;
- département ;
- groupe parlementaire ;
- appartenance gaulliste du groupe.

Cependant, plusieurs champs demandés restent largement incomplets :

- `circonscription` ;
- `a_eu_suppleant` ;
- `suppleant_de`.

Ces champs devront être extraits à partir du texte biographique des notices Sycomore.

### 4.3 Données de mobilité sociale

Les champs nécessaires à l'analyse de mobilité sociale sont prévus dans la structure, mais ne sont pas encore renseignés de manière systématique.

Il reste à collecter :

- les professions successives des individus ;
- la profession du père ;
- la profession de la mère ;
- la formation et les établissements fréquentés ;
- les codes de catégorie sociale ;
- le type de mobilité sociale.

### 4.4 Réseau relationnel

La base contient déjà des appartenances institutionnelles, des groupes politiques et des sources communes. En revanche, le réseau relationnel entre individus n'est pas encore construit de manière systématique.

Il faudra distinguer :

- les liens prouvés : parenté, mariage, appartenance à une même organisation, réseau de résistance, groupe politique ;
- les liens potentiels : même commune d'origine, même école, même administration, même entreprise ou même unité militaire.

Cette étape devrait être menée après la revue des identités.

### 4.5 Documentation détaillée des champs sources

Les fichiers JSON par source existent, mais certaines sources nécessitent encore une documentation plus détaillée.

Il serait utile d'ajouter :

- la signification de chaque champ source ;
- le mapping entre les champs sources et les champs unifiés ;
- les niveaux de fiabilité des sources ;
- les règles de gestion des valeurs manquantes ou conflictuelles.

## 5. Prochaines étapes recommandées

### Étape 1 : traiter les cas d'identité prioritaires

Commencer par les 899 cas `P1_quick_review`.

Pour chaque cas, il faut déterminer :

- s'il s'agit de la même personne ;
- si les enregistrements doivent être fusionnés ;
- quel `elite_id` doit être conservé ;
- quelle preuve justifie la décision.

Fichier concerné :

- `review/revue_identites_a_traiter.csv`

### Étape 2 : compléter les champs Sycomore manquants

Compléter en priorité :

- `circonscription`
- `a_eu_suppleant`
- `suppleant_de`

Ces champs correspondent à une demande explicite de l'encadrement.

### Étape 3 : collecter les données de mobilité sociale

Après stabilisation des identités, collecter :

- professions ;
- professions des parents ;
- formation ;
- codes sociaux ;
- type de mobilité.

### Étape 4 : construire le réseau relationnel

Une fois les identités et les informations de carrière plus stables, construire les relations entre individus en distinguant les liens prouvés et les liens potentiels.

## 6. État de livrabilité

La version actuelle peut être transmise comme première version de l'architecture logique à Jean-Pascal Bassino.

Il est conseillé d'accompagner l'envoi en précisant que :

1. l'architecture générale de la base est en place ;
2. la table maîtresse CSV et les identifiants uniques sont créés ;
3. les principales sources sont intégrées ;
4. les formats SQL, DBML et JSON sont disponibles ;
5. les données sources et les exports sont accessibles dans le dépôt privé et dans la release ;
6. les prochaines étapes concernent la revue des identités, l'extraction fine des champs Sycomore, la mobilité sociale et les réseaux.
