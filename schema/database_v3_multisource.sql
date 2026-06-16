-- ============================================================================
-- Gaullist Personalities Database - PostgreSQL DDL v3.0
-- Multi-source import, membership evidence, and identity matching extensions.
-- IMPORTANT: Run only against a new, empty database. This script includes the
-- complete v2 DDL and must not be applied again to an existing v2 database.
-- ============================================================================

\set ON_ERROR_STOP on
\ir database_v2_identity.sql

BEGIN;

ALTER TABLE membership_rules
    ADD COLUMN default_status TEXT
        CONSTRAINT ck_membership_rules_default_status
        CHECK (default_status IN ('Verified','Inferred','Pending','Rejected')),
    ADD COLUMN default_confidence NUMERIC(4,3)
        CONSTRAINT ck_membership_rules_default_confidence
        CHECK (default_confidence BETWEEN 0 AND 1);

-- ============================================================================
-- 1. Source import batches
-- ============================================================================

CREATE TABLE source_import_batches (
    batch_id          TEXT PRIMARY KEY,
    source_id         TEXT NOT NULL REFERENCES sources(source_id),
    source_file       TEXT NOT NULL,
    imported_at       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count         BIGINT NOT NULL CHECK (row_count >= 0),
    success_count     BIGINT NOT NULL CHECK (success_count >= 0),
    error_count       BIGINT NOT NULL CHECK (error_count >= 0),
    mapping_version   TEXT NOT NULL,
    status            TEXT NOT NULL CHECK (status IN ('loaded','partial','failed')),
    CONSTRAINT ck_source_import_batches_counts
        CHECK (success_count + error_count = row_count)
);

CREATE INDEX idx_source_import_batches_source
    ON source_import_batches(source_id, imported_at);
CREATE INDEX idx_source_import_batches_status
    ON source_import_batches(status);


-- ============================================================================
-- 2. Multi-source identity and membership extensions
-- ============================================================================

CREATE TABLE person_external_ids (
    external_id_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    elite_id            TEXT NOT NULL REFERENCES identity_master(elite_id) ON DELETE CASCADE,
    id_system           TEXT NOT NULL,
    external_id         TEXT NOT NULL,
    source_id           TEXT REFERENCES sources(source_id),
    match_confidence    NUMERIC(4,3)
                        CHECK (match_confidence IS NULL OR match_confidence BETWEEN 0 AND 1),
    verification_status TEXT NOT NULL
                        CHECK (verification_status IN ('verified','auto_matched','needs_review','rejected')),
    url                 TEXT,
    UNIQUE (id_system, external_id)
);

CREATE INDEX idx_person_external_ids_elite
    ON person_external_ids(elite_id);
CREATE INDEX idx_person_external_ids_source
    ON person_external_ids(source_id);
CREATE INDEX idx_person_external_ids_verification
    ON person_external_ids(verification_status);


CREATE TABLE person_memberships (
    membership_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    elite_id           TEXT NOT NULL REFERENCES identity_master(elite_id) ON DELETE CASCADE,
    rule_id            TEXT NOT NULL REFERENCES membership_rules(rule_id),
    status             TEXT NOT NULL
                       CONSTRAINT ck_person_memberships_status
                       CHECK (status IN ('Verified','Inferred','Pending','Rejected')),
    confidence         NUMERIC(4,3) NOT NULL
                       CONSTRAINT ck_person_memberships_confidence
                       CHECK (confidence BETWEEN 0 AND 1),
    evidence_source_id TEXT NOT NULL REFERENCES sources(source_id),
    evidence_record_id TEXT NOT NULL,
    org_id             TEXT REFERENCES organizations(org_id),
    valid_from         DATE,
    valid_to           DATE,
    rationale          TEXT NOT NULL,
    reviewed_by        TEXT,
    reviewed_at        TIMESTAMPTZ,
    UNIQUE (elite_id, rule_id, evidence_source_id, evidence_record_id),
    CONSTRAINT ck_person_memberships_valid_dates
        CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to),
    CONSTRAINT ck_person_memberships_source_semantics
        CHECK (
            evidence_source_id <> 'SRC_PREFECTS'
            AND (
                evidence_source_id NOT IN (
                    'SRC_PRESIDENTS',
                    'SRC_PRIME_MINISTERS',
                    'SRC_GOVERNMENT_MEMBERS',
                    'SRC_HISTORICAL_MINISTERS'
                )
                OR (
                    rule_id = 'RULE_GAULLIST_GOVERNMENT_SERVICE'
                    AND status = 'Inferred'
                    AND valid_from IS NOT NULL
                    AND valid_from <= DATE '1973-12-31'
                    AND COALESCE(valid_to, DATE '9999-12-31') >= DATE '1940-01-01'
                )
            )
        )
);

CREATE INDEX idx_person_memberships_elite
    ON person_memberships(elite_id);
CREATE INDEX idx_person_memberships_rule_status
    ON person_memberships(rule_id, status);
CREATE INDEX idx_person_memberships_evidence_source
    ON person_memberships(evidence_source_id, evidence_record_id);
CREATE INDEX idx_person_memberships_org
    ON person_memberships(org_id);


CREATE TABLE identity_match_candidates (
    match_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_system       TEXT NOT NULL,
    source_record_id    TEXT NOT NULL,
    candidate_elite_id  TEXT REFERENCES identity_master(elite_id),
    match_method        TEXT NOT NULL,
    name_score          NUMERIC(4,3) NOT NULL CHECK (name_score BETWEEN 0 AND 1),
    birth_score         NUMERIC(4,3) NOT NULL CHECK (birth_score BETWEEN 0 AND 1),
    place_score         NUMERIC(4,3) NOT NULL CHECK (place_score BETWEEN 0 AND 1),
    external_id_score   NUMERIC(4,3) NOT NULL CHECK (external_id_score BETWEEN 0 AND 1),
    total_score         NUMERIC(4,3) NOT NULL CHECK (total_score BETWEEN 0 AND 1),
    has_hard_conflict   BOOLEAN NOT NULL DEFAULT FALSE,
    decision            TEXT NOT NULL
                        CHECK (decision IN ('auto_link','needs_review','no_match','promote_new')),
    review_status       TEXT NOT NULL DEFAULT 'pending'
                        CHECK (review_status IN ('pending','accepted','rejected','not_required')),
    CONSTRAINT ck_identity_match_candidates_decision_candidate
        CHECK (
            (decision IN ('auto_link','needs_review') AND candidate_elite_id IS NOT NULL)
            OR
            (decision IN ('no_match','promote_new') AND candidate_elite_id IS NULL)
        ),
    CONSTRAINT uq_identity_match_candidates_source_candidate
        UNIQUE NULLS NOT DISTINCT (source_system, source_record_id, candidate_elite_id)
);

CREATE INDEX idx_identity_match_candidates_source
    ON identity_match_candidates(source_system, source_record_id);
CREATE INDEX idx_identity_match_candidates_candidate
    ON identity_match_candidates(candidate_elite_id);
CREATE INDEX idx_identity_match_candidates_review
    ON identity_match_candidates(review_status, decision);
CREATE INDEX idx_identity_match_candidates_score
    ON identity_match_candidates(total_score DESC);


CREATE TABLE career_organizations (
    career_org_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    elite_id         TEXT NOT NULL REFERENCES identity_master(elite_id) ON DELETE CASCADE,
    org_id           TEXT NOT NULL REFERENCES organizations(org_id),
    source_id        TEXT NOT NULL REFERENCES sources(source_id),
    source_record_id TEXT NOT NULL,
    position         TEXT,
    start_date       DATE,
    end_date         DATE,
    details          JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT ck_career_organizations_dates
        CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date),
    CONSTRAINT uq_career_organizations_idempotency
        UNIQUE NULLS NOT DISTINCT (
            elite_id,
            org_id,
            source_id,
            source_record_id,
            position,
            start_date
        )
);

CREATE INDEX idx_career_organizations_elite
    ON career_organizations(elite_id);
CREATE INDEX idx_career_organizations_org
    ON career_organizations(org_id);
CREATE INDEX idx_career_organizations_source
    ON career_organizations(source_id, source_record_id);


-- ============================================================================
-- 3. Staging tables
-- ============================================================================

CREATE TABLE stg_prefets (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_prefets_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_prefets_processing
    ON stg_prefets(batch_id, processing_status);
CREATE INDEX idx_stg_prefets_identity
    ON stg_prefets(nom, prenom, birth_year);


CREATE TABLE stg_government_members (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_government_members_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    role_type         TEXT,
    position          TEXT,
    start_date        TEXT,
    end_date          TEXT,
    government_name   TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_government_members_processing
    ON stg_government_members(batch_id, processing_status);
CREATE INDEX idx_stg_government_members_identity
    ON stg_government_members(nom, prenom, birth_year);


CREATE TABLE stg_mdh_fafl (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_mdh_fafl_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_mdh_fafl_processing
    ON stg_mdh_fafl(batch_id, processing_status);
CREATE INDEX idx_stg_mdh_fafl_identity
    ON stg_mdh_fafl(nom, prenom, birth_year);


CREATE TABLE stg_mdh_deportes (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_mdh_deportes_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_mdh_deportes_processing
    ON stg_mdh_deportes(batch_id, processing_status);
CREATE INDEX idx_stg_mdh_deportes_identity
    ON stg_mdh_deportes(nom, prenom, birth_year);


CREATE TABLE stg_mdh_medailles (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_mdh_medailles_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_mdh_medailles_processing
    ON stg_mdh_medailles(batch_id, processing_status);
CREATE INDEX idx_stg_mdh_medailles_identity
    ON stg_mdh_medailles(nom, prenom, birth_year);


CREATE TABLE stg_mdh_homologations (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_mdh_homologations_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    movement_family   TEXT,
    movement_name     TEXT,
    network_name      TEXT,
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_mdh_homologations_processing
    ON stg_mdh_homologations(batch_id, processing_status);
CREATE INDEX idx_stg_mdh_homologations_identity
    ON stg_mdh_homologations(nom, prenom, birth_year);
CREATE INDEX idx_stg_mdh_homologations_movement
    ON stg_mdh_homologations(movement_family, movement_name);


CREATE TABLE stg_wikidata_matches (
    staging_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id          TEXT NOT NULL REFERENCES source_import_batches(batch_id),
    source_record_id  TEXT NOT NULL,
    nom               TEXT,
    prenom            TEXT,
    birth_date        TEXT,
    birth_year        TEXT,
    birth_place       TEXT,
    death_date        TEXT,
    external_id       TEXT,
    raw_record        JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending'
                      CONSTRAINT ck_stg_wikidata_matches_processing_status
                      CHECK (processing_status IN (
                          'pending','normalized','matched','needs_review',
                          'promoted','skipped','error'
                      )),
    processing_error  TEXT,
    query             TEXT,
    candidate_qid     TEXT,
    score             NUMERIC(4,3) CHECK (score IS NULL OR score BETWEEN 0 AND 1),
    decision          TEXT
                      CONSTRAINT ck_stg_wikidata_matches_decision
                      CHECK (
                          decision IS NULL
                          OR decision IN ('auto_link','needs_review','no_match','rejected')
                      ),
    UNIQUE (batch_id, source_record_id)
);

CREATE INDEX idx_stg_wikidata_matches_processing
    ON stg_wikidata_matches(batch_id, processing_status);
CREATE INDEX idx_stg_wikidata_matches_identity
    ON stg_wikidata_matches(nom, prenom, birth_year);
CREATE INDEX idx_stg_wikidata_matches_candidate
    ON stg_wikidata_matches(candidate_qid);

COMMIT;
