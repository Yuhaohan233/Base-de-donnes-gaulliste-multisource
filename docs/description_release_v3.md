# Base de données gaulliste multisource - version v3

Cette release fournit la version de diffusion de la base de données gaulliste multisource. Elle accompagne le dépôt GitHub contenant la documentation en français, le schéma SQL/DBML, les schémas JSON, les fichiers de revue et les scripts de construction/export.

## Contenu principal

- 66 059 individus dans la table d'identité principale.
- 66 553 liens d'identité multisource.
- 65 449 identifiants externes.
- 66 912 lignes d'appartenance à un groupe ou à une source.
- 3 837 cas restant à vérifier manuellement, dont 899 en priorité rapide.

## Fichiers joints

- `gaullist_db_v3.dump` : dump PostgreSQL restaurable.
- `json_v3.zip` : export JSON complet, avec un fichier par personne, source et organisation.
- `data_registry_outputs_v3.zip` : exports CSV/JSON du registre multisource, incluant les tables d'identité, les liens, les appartenances, les identifiants externes et les fichiers de revue.

## Restauration PostgreSQL

```bash
createdb gaullist_db
pg_restore -d gaullist_db gaullist_db_v3.dump
```

## Structure documentaire

Le dépôt associé contient :

- `schema/database_v3_multisource.sql` : schéma relationnel PostgreSQL.
- `schema/database_v3_multisource.dbml` : schéma DBML importable dans dbdiagram.io.
- `schema/person_v3.schema.json`, `source_v3.schema.json`, `organization_v3.schema.json` : schémas de validation JSON.
- `docs/architecture_base_de_donnees.md` : présentation de l'architecture.
- `docs/guide_revue_identites.md` : méthode de traitement des cas d'identité à vérifier.
- `docs/guide_restauration.md` : instructions de restauration et d'utilisation des exports.

## Remarque méthodologique

Les fichiers conservent les identifiants internes, les métadonnées de source et les indicateurs de revue afin de maintenir la traçabilité des décisions d'inclusion. Les cas ambigus ne sont pas fusionnés automatiquement : ils sont placés dans une file de revue pour validation documentaire.
