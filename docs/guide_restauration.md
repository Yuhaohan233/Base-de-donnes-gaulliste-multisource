# Guide de restauration

## Option PostgreSQL

Après téléchargement de `gaullist_db_v3.dump`, la base peut être restaurée avec :

```bash
createdb gaullist_db
pg_restore -d gaullist_db gaullist_db_v3.dump
```

## Option JSON

Après téléchargement de `json_v3.zip`, l'archive contient :

- `persons/` : un fichier JSON par individu.
- `sources/` : catalogue des sources documentaires.
- `organizations/` : catalogue des organisations et groupes.

Les schémas de validation sont disponibles dans :

- `schema/person_v3.schema.json`
- `schema/source_v3.schema.json`
- `schema/organization_v3.schema.json`

## Option CSV

L'archive `data_registry_outputs_v3.zip` contient les exports produits par le registre multisource, notamment la table d'identité principale, les liens d'identité, les identifiants externes, les appartenances et les fichiers de revue.
