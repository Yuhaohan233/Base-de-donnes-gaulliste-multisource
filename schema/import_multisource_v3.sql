\set ON_ERROR_STOP on
\encoding UTF8

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM identity_master)
       OR EXISTS (SELECT 1 FROM id_registry)
       OR EXISTS (SELECT 1 FROM identity_links)
       OR EXISTS (SELECT 1 FROM career_entries)
       OR EXISTS (SELECT 1 FROM identity_resolution_reviews)
       OR EXISTS (SELECT 1 FROM ambiguous_matches)
       OR EXISTS (SELECT 1 FROM network_edges)
       OR EXISTS (SELECT 1 FROM source_import_batches)
       OR EXISTS (SELECT 1 FROM person_external_ids)
       OR EXISTS (SELECT 1 FROM person_memberships)
       OR EXISTS (SELECT 1 FROM identity_match_candidates)
       OR EXISTS (SELECT 1 FROM career_organizations)
       OR EXISTS (SELECT 1 FROM stg_prefets)
       OR EXISTS (SELECT 1 FROM stg_government_members)
       OR EXISTS (SELECT 1 FROM stg_mdh_fafl)
       OR EXISTS (SELECT 1 FROM stg_mdh_deportes)
       OR EXISTS (SELECT 1 FROM stg_mdh_medailles)
       OR EXISTS (SELECT 1 FROM stg_mdh_homologations)
       OR EXISTS (SELECT 1 FROM stg_wikidata_matches)
       OR EXISTS (SELECT 1 FROM organization_aliases)
       OR EXISTS (SELECT 1 FROM organizations)
       OR EXISTS (SELECT 1 FROM sources)
       OR (SELECT COUNT(*) FROM membership_rules) <> 5
       OR EXISTS (
           SELECT 1
           FROM membership_rules
           WHERE rule_id NOT IN ('RULE_01','RULE_02','RULE_03','RULE_04','RULE_99')
       )
    THEN
        RAISE EXCEPTION
            'import_multisource_v3.sql may only run against a new empty v3 database';
    END IF;
END
$$;

TRUNCATE TABLE stg_wikidata_matches, stg_mdh_homologations, stg_mdh_medailles, stg_mdh_deportes, stg_mdh_fafl, stg_government_members, stg_prefets, career_organizations, identity_match_candidates, person_memberships, person_external_ids, source_import_batches RESTART IDENTITY;
TRUNCATE TABLE organization_aliases RESTART IDENTITY;
DELETE FROM organizations;
DELETE FROM sources;
DELETE FROM membership_rules;

\copy membership_rules (rule_id, description, active, created_at, default_status, default_confidence) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/membership_rules.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy sources (source_id, source_system, source_file, title, publisher, url, lang, access_date, reliability_tier, extraction_date, extracted_by, notes, extensions) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/sources.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy organizations (org_id, nom_officiel, nom_court, org_type, org_level, country, parent_org_id, is_gaulliste_marker, start_date, end_date, notes, extensions) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/organizations.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy organization_aliases (org_id, alias, alias_type, source_id) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/organization_aliases.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy identity_master (elite_id, fingerprint_id, nom, prenom, nom_complet, sexe, birth_date, birth_year, birth_place, death_date, source_groups, sycomore_id, sycomore_url, father_name, father_job, mother_name, mother_job, source_systems, candidate_count, review_status, match_confidence, identity_key) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/identity_master_v3.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy id_registry (elite_id, fingerprint_id, nom, prenom, birth_year, birth_place, source_systems, candidate_count, review_status, match_confidence) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/id_registry_v3.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy identity_links (elite_id, source_system, source_file, source_record_id, source_url, match_rule, match_confidence) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/identity_links_v3.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy career_entries (elite_id, source_system, source_record_id, career_source_row, position, regime, legislature, mandat_debut, mandat_fin, departement, circonscription, groupe, groupe_abrev, is_gaulliste, status, suppleant_de, a_eu_suppleant, source_url) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/career_entries_v3.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy identity_resolution_reviews (resolution_id, name_key, candidate_ids, review_decision, confidence, evidence_urls, rationale) FROM 'D:/pythonProject_stage/data_registry/outputs/reviewed_identity_resolutions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy ambiguous_matches (name_key, candidate_ids, fingerprint_ids, birth_years, birth_places, note) FROM 'D:/pythonProject_stage/data_registry/outputs/ambiguous_matches_pending.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy source_import_batches (batch_id, source_id, source_file, imported_at, row_count, success_count, error_count, mapping_version, status) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/source_import_batches.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy identity_match_candidates (source_system, source_record_id, candidate_elite_id, match_method, name_score, birth_score, place_score, external_id_score, total_score, has_hard_conflict, decision, review_status) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/identity_match_candidates.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy person_external_ids (elite_id, id_system, external_id, source_id, match_confidence, verification_status, url) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/person_external_ids.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy person_memberships (elite_id, rule_id, status, confidence, evidence_source_id, evidence_record_id, org_id, valid_from, valid_to, rationale, reviewed_by, reviewed_at) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/person_memberships.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy career_organizations (elite_id, org_id, source_id, source_record_id, position, start_date, end_date, details) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/career_organizations.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

\copy stg_prefets (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_prefets.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy stg_government_members (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error, role_type, position, start_date, end_date, government_name) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_government.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy stg_mdh_fafl (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_mdh_fafl.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy stg_mdh_deportes (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_mdh_deportes.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy stg_mdh_medailles (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_mdh_medailles.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy stg_mdh_homologations (batch_id, source_record_id, nom, prenom, birth_date, birth_year, birth_place, death_date, external_id, raw_record, processing_status, processing_error, movement_family, movement_name, network_name) FROM 'D:/pythonProject_stage/data_registry/outputs/multisource/staging_mdh_homologations.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

SELECT setval(pg_get_serial_sequence('organization_aliases', 'alias_id'), COALESCE((SELECT MAX(alias_id) FROM organization_aliases), 1), EXISTS (SELECT 1 FROM organization_aliases));
SELECT setval(pg_get_serial_sequence('identity_links', 'link_id'), COALESCE((SELECT MAX(link_id) FROM identity_links), 1), EXISTS (SELECT 1 FROM identity_links));
SELECT setval(pg_get_serial_sequence('career_entries', 'career_id'), COALESCE((SELECT MAX(career_id) FROM career_entries), 1), EXISTS (SELECT 1 FROM career_entries));
SELECT setval(pg_get_serial_sequence('ambiguous_matches', 'ambiguous_id'), COALESCE((SELECT MAX(ambiguous_id) FROM ambiguous_matches), 1), EXISTS (SELECT 1 FROM ambiguous_matches));
SELECT setval(pg_get_serial_sequence('person_external_ids', 'external_id_id'), COALESCE((SELECT MAX(external_id_id) FROM person_external_ids), 1), EXISTS (SELECT 1 FROM person_external_ids));
SELECT setval(pg_get_serial_sequence('person_memberships', 'membership_id'), COALESCE((SELECT MAX(membership_id) FROM person_memberships), 1), EXISTS (SELECT 1 FROM person_memberships));
SELECT setval(pg_get_serial_sequence('identity_match_candidates', 'match_id'), COALESCE((SELECT MAX(match_id) FROM identity_match_candidates), 1), EXISTS (SELECT 1 FROM identity_match_candidates));
SELECT setval(pg_get_serial_sequence('career_organizations', 'career_org_id'), COALESCE((SELECT MAX(career_org_id) FROM career_organizations), 1), EXISTS (SELECT 1 FROM career_organizations));
SELECT setval(pg_get_serial_sequence('stg_prefets', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_prefets), 1), EXISTS (SELECT 1 FROM stg_prefets));
SELECT setval(pg_get_serial_sequence('stg_government_members', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_government_members), 1), EXISTS (SELECT 1 FROM stg_government_members));
SELECT setval(pg_get_serial_sequence('stg_mdh_fafl', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_mdh_fafl), 1), EXISTS (SELECT 1 FROM stg_mdh_fafl));
SELECT setval(pg_get_serial_sequence('stg_mdh_deportes', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_mdh_deportes), 1), EXISTS (SELECT 1 FROM stg_mdh_deportes));
SELECT setval(pg_get_serial_sequence('stg_mdh_medailles', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_mdh_medailles), 1), EXISTS (SELECT 1 FROM stg_mdh_medailles));
SELECT setval(pg_get_serial_sequence('stg_mdh_homologations', 'staging_id'), COALESCE((SELECT MAX(staging_id) FROM stg_mdh_homologations), 1), EXISTS (SELECT 1 FROM stg_mdh_homologations));

COMMIT;
