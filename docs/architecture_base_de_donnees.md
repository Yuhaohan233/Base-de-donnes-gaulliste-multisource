# Architecture de la base de données

## Objectif

La base organise un corpus prosopographique sur les personnes rattachées au mouvement gaulliste, à la France libre, aux réseaux de résistance et aux institutions politiques ou administratives associées. L'architecture conserve les métadonnées de source afin que chaque inclusion puisse être justifiée et revue.

## Niveaux de données

1. `identity_master_v3` : table centrale des individus, avec identifiant stable `elite_id`, nom, prénom, dates et lieux de naissance/décès, indicateurs de revue et sources d'origine.
2. `id_registry_v3` : registre de correspondance entre l'identifiant interne et l'empreinte/fingerprint utilisée pour stabiliser les rapprochements.
3. `person_external_ids` : couche d'alignement avec les identifiants externes, par exemple Sycomore, Wikidata ou autres bases.
4. `person_memberships` : justification de l'appartenance au corpus, par source et règle de sélection.
5. `career_entries_v3` et `career_organizations` : parcours institutionnels, fonctions, mandats, organisations et périodes.
6. `identity_match_candidates` : candidats d'appariement multisource, avec scores et indicateurs de conflit.

## Logique de traçabilité

Chaque individu peut être rattaché à plusieurs sources. La base distingue l'identité canonique, les données d'origine et les liens externes afin d'éviter de perdre les variantes présentes dans les documents. Les cas ambigus sont conservés dans une file de revue plutôt que fusionnés automatiquement.

## Visualisation

Le fichier `schema/database_v3_multisource.dbml` peut être importé dans dbdiagram.io pour produire un schéma ER visuel. Le fichier SQL équivalent est `schema/database_v3_multisource.sql`.
