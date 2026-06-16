\set ON_ERROR_STOP on

DO $$
DECLARE
    expected_columns CONSTANT TEXT[] := ARRAY[
        'default_status',
        'default_confidence'
    ];
    missing_columns TEXT[];
BEGIN
    SELECT ARRAY_AGG(expected.column_name ORDER BY expected.column_name)
    INTO missing_columns
    FROM UNNEST(expected_columns) AS expected(column_name)
    LEFT JOIN information_schema.columns actual
      ON actual.table_schema = 'public'
     AND actual.table_name = 'membership_rules'
     AND actual.column_name = expected.column_name
    WHERE actual.column_name IS NULL;

    IF missing_columns IS NOT NULL THEN
        RAISE EXCEPTION 'Missing membership_rules column(s): %',
            array_to_string(missing_columns, ', ');
    END IF;
END
$$;

DO $$
DECLARE
    invalid_columns TEXT[];
BEGIN
    SELECT ARRAY_AGG(column_name ORDER BY column_name)
    INTO invalid_columns
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'membership_rules'
      AND (
          (column_name = 'default_status' AND data_type <> 'text')
          OR
          (
              column_name = 'default_confidence'
              AND (
                  data_type <> 'numeric'
                  OR numeric_precision <> 4
                  OR numeric_scale <> 3
              )
          )
      );

    IF invalid_columns IS NOT NULL THEN
        RAISE EXCEPTION 'Invalid membership_rules column type(s): %',
            array_to_string(invalid_columns, ', ');
    END IF;
END
$$;

DO $$
DECLARE
    expected_tables CONSTANT TEXT[] := ARRAY[
        'source_import_batches',
        'person_external_ids',
        'person_memberships',
        'identity_match_candidates',
        'career_organizations',
        'stg_prefets',
        'stg_government_members',
        'stg_mdh_fafl',
        'stg_mdh_deportes',
        'stg_mdh_medailles',
        'stg_mdh_homologations',
        'stg_wikidata_matches'
    ];
    missing_tables TEXT[];
BEGIN
    SELECT ARRAY_AGG(expected.table_name ORDER BY expected.table_name)
    INTO missing_tables
    FROM UNNEST(expected_tables) AS expected(table_name)
    LEFT JOIN information_schema.tables actual
      ON actual.table_schema = 'public'
     AND actual.table_name = expected.table_name
     AND actual.table_type = 'BASE TABLE'
    WHERE actual.table_name IS NULL;

    IF missing_tables IS NOT NULL THEN
        RAISE EXCEPTION 'Missing v3 BASE TABLE(s): %', array_to_string(missing_tables, ', ');
    END IF;
END
$$;

DO $$
DECLARE
    expected_indexes CONSTANT TEXT[] := ARRAY[
        'uq_identity_match_candidates_source_candidate',
        'uq_career_organizations_idempotency'
    ];
    missing_indexes TEXT[];
BEGIN
    SELECT ARRAY_AGG(expected.index_name ORDER BY expected.index_name)
    INTO missing_indexes
    FROM UNNEST(expected_indexes) AS expected(index_name)
    LEFT JOIN (
        SELECT index_class.relname AS index_name
        FROM pg_index index_meta
        JOIN pg_class index_class ON index_class.oid = index_meta.indexrelid
        JOIN pg_namespace index_namespace ON index_namespace.oid = index_class.relnamespace
        WHERE index_namespace.nspname = 'public'
          AND index_meta.indisunique
          AND index_meta.indnullsnotdistinct
    ) actual ON actual.index_name = expected.index_name
    WHERE actual.index_name IS NULL;

    IF missing_indexes IS NOT NULL THEN
        RAISE EXCEPTION 'Missing UNIQUE NULLS NOT DISTINCT index(es): %',
            array_to_string(missing_indexes, ', ');
    END IF;
END
$$;

DO $$
DECLARE
    expected_checks CONSTANT TEXT[] := ARRAY[
        'ck_membership_rules_default_status',
        'ck_membership_rules_default_confidence',
        'ck_source_import_batches_counts',
        'ck_person_memberships_status',
        'ck_person_memberships_confidence',
        'ck_person_memberships_valid_dates',
        'ck_person_memberships_source_semantics',
        'ck_identity_match_candidates_decision_candidate',
        'ck_career_organizations_dates',
        'ck_stg_prefets_processing_status',
        'ck_stg_government_members_processing_status',
        'ck_stg_mdh_fafl_processing_status',
        'ck_stg_mdh_deportes_processing_status',
        'ck_stg_mdh_medailles_processing_status',
        'ck_stg_mdh_homologations_processing_status',
        'ck_stg_wikidata_matches_processing_status',
        'ck_stg_wikidata_matches_decision'
    ];
    missing_checks TEXT[];
BEGIN
    SELECT ARRAY_AGG(expected.constraint_name ORDER BY expected.constraint_name)
    INTO missing_checks
    FROM UNNEST(expected_checks) AS expected(constraint_name)
    LEFT JOIN (
        SELECT constraint_meta.conname AS constraint_name
        FROM pg_constraint constraint_meta
        JOIN pg_namespace constraint_namespace
          ON constraint_namespace.oid = constraint_meta.connamespace
        WHERE constraint_namespace.nspname = 'public'
          AND constraint_meta.contype = 'c'
          AND constraint_meta.convalidated
    ) actual ON actual.constraint_name = expected.constraint_name
    WHERE actual.constraint_name IS NULL;

    IF missing_checks IS NOT NULL THEN
        RAISE EXCEPTION 'Missing validated CHECK constraint(s): %',
            array_to_string(missing_checks, ', ');
    END IF;
END
$$;

DO $$
DECLARE
    missing_foreign_keys TEXT[];
BEGIN
    WITH expected(
        table_name,
        column_name,
        foreign_table_name,
        foreign_column_name
    ) AS (
        VALUES
            ('person_memberships', 'rule_id', 'membership_rules', 'rule_id'),
            ('person_memberships', 'evidence_source_id', 'sources', 'source_id'),
            ('person_memberships', 'org_id', 'organizations', 'org_id')
    ),
    actual AS (
        SELECT
            source_table.relname AS table_name,
            source_column.attname AS column_name,
            target_table.relname AS foreign_table_name,
            target_column.attname AS foreign_column_name
        FROM pg_constraint constraint_meta
        JOIN pg_class source_table
          ON source_table.oid = constraint_meta.conrelid
        JOIN pg_class target_table
          ON target_table.oid = constraint_meta.confrelid
        JOIN LATERAL UNNEST(
            constraint_meta.conkey,
            constraint_meta.confkey
        ) AS key_pair(source_attnum, target_attnum) ON TRUE
        JOIN pg_attribute source_column
          ON source_column.attrelid = source_table.oid
         AND source_column.attnum = key_pair.source_attnum
        JOIN pg_attribute target_column
          ON target_column.attrelid = target_table.oid
         AND target_column.attnum = key_pair.target_attnum
        WHERE constraint_meta.contype = 'f'
    )
    SELECT ARRAY_AGG(
        expected.table_name || '.' || expected.column_name
        ORDER BY expected.column_name
    )
    INTO missing_foreign_keys
    FROM expected
    LEFT JOIN actual USING (
        table_name,
        column_name,
        foreign_table_name,
        foreign_column_name
    )
    WHERE actual.table_name IS NULL;

    IF missing_foreign_keys IS NOT NULL THEN
        RAISE EXCEPTION 'Missing foreign key(s): %',
            array_to_string(missing_foreign_keys, ', ');
    END IF;
END
$$;
