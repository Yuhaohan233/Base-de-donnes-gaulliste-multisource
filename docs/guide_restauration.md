# Guide de restauration

## Option recommandée : PostgreSQL

1. Télécharger `gaullist_db_v3.dump` depuis les assets de la release GitHub.
2. Créer une base vide.
3. Restaurer le dump avec `pg_restore`.

```bash
createdb gaullist_db
pg_restore -d gaullist_db gaullist_db_v3.dump
```

## Option JSON

Télécharger `json_v3.zip`, puis extraire le dossier. Il contient :

- `persons/` : un fichier JSON par individu.
- `sources/` : catalogue des sources documentaires.
- `organizations/` : catalogue des organisations et groupes.

Les schémas de validation sont disponibles dans `schema/person_v3.schema.json`, `schema/source_v3.schema.json` et `schema/organization_v3.schema.json`.

## Option CSV

Télécharger `data_registry_outputs_v3.zip`, puis extraire le dossier. Il contient les exports produits par le registre multisource, notamment la table d'identité principale, les liens d'identité, les identifiants externes, les appartenances et les fichiers de revue.
