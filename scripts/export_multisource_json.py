from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "v3"
NULL_SENTINEL = "__JSON_EXPORT_NULL__"
ELITE_ID_RE = re.compile(r"^FR_ELITE_[0-9]{6}$")
SOURCE_ID_RE = re.compile(r"^SRC_[A-Z0-9_]+$")
ORG_ID_RE = re.compile(r"^ORG_[A-Z0-9_]+$")


QUERIES = {
    "identity_master": """-- export: identity_master
SELECT elite_id, fingerprint_id, nom, prenom, nom_complet, sexe,
       birth_date, birth_year, birth_place, death_date,
       father_name, father_job, mother_name, mother_job,
       candidate_count, review_status, match_confidence,
       created_at, updated_at, extensions
FROM identity_master
ORDER BY elite_id""",
    "identity_links": """-- export: identity_links
SELECT elite_id, source_system, source_file, source_record_id, source_url,
       match_rule, match_confidence, created_at, extensions
FROM identity_links
ORDER BY elite_id, source_system, source_record_id""",
    "person_memberships": """-- export: person_memberships
SELECT pm.elite_id, pm.rule_id, mr.description AS rule_description,
       pm.status, pm.confidence, pm.evidence_source_id,
       pm.evidence_record_id, pm.org_id, pm.valid_from, pm.valid_to,
       pm.rationale, pm.reviewed_by, pm.reviewed_at
FROM person_memberships pm
JOIN membership_rules mr ON mr.rule_id = pm.rule_id
ORDER BY pm.elite_id, pm.rule_id, pm.evidence_source_id, pm.evidence_record_id""",
    "person_external_ids": """-- export: person_external_ids
SELECT elite_id, id_system, external_id, source_id, match_confidence,
       verification_status, url
FROM person_external_ids
ORDER BY elite_id, id_system, external_id""",
    "career_entries": """-- export: career_entries
SELECT career_id, elite_id, source_system, source_record_id, position,
       regime, legislature, mandat_debut, mandat_fin, departement,
       circonscription, groupe, groupe_abrev, is_gaulliste, status,
       suppleant_de, a_eu_suppleant, source_url, extensions
FROM career_entries
ORDER BY elite_id, career_id""",
    "career_organizations": """-- export: career_organizations
SELECT career_org_id, elite_id, org_id, source_id, source_record_id,
       position, start_date, end_date, details
FROM career_organizations
ORDER BY elite_id, career_org_id""",
    "network_edges": """-- export: network_edges
SELECT edge_id, elite_id_a, elite_id_b, relation_type, relation_category,
       strength, context, source_system, source_url, extensions
FROM network_edges
ORDER BY edge_id""",
    "sources": """-- export: sources
SELECT source_id, source_system, source_file, title, publisher, url, lang,
       access_date, reliability_tier, extraction_date, extracted_by,
       notes, extensions
FROM sources
ORDER BY source_id""",
    "source_import_batches": """-- export: source_import_batches
SELECT batch_id, source_id, source_file, imported_at, row_count,
       success_count, error_count, mapping_version, status
FROM source_import_batches
ORDER BY source_id, imported_at, batch_id""",
    "organizations": """-- export: organizations
SELECT org_id, nom_officiel, nom_court, org_type, org_level, country,
       parent_org_id, is_gaulliste_marker, start_date, end_date, notes,
       extensions
FROM organizations
ORDER BY org_id""",
    "organization_aliases": """-- export: organization_aliases
SELECT org_id, alias, alias_type, source_id
FROM organization_aliases
ORDER BY org_id, alias""",
}


def find_psql() -> str:
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidate = Path(program_files) / "PostgreSQL" / "18" / "bin" / "psql.exe"
    if candidate.exists():
        return str(candidate)
    return shutil.which("psql.exe") or shutil.which("psql") or "psql.exe"


class PsqlRunner:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 55432,
        database: str = "gaullist_db",
        user: str = "postgres",
        *,
        executable: str | None = None,
        run_process: Callable[..., object] = subprocess.run,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.executable = executable or find_psql()
        self.run_process = run_process

    def __call__(self, sql: str) -> str:
        command = [
            self.executable,
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--dbname",
            self.database,
            "--username",
            self.user,
            "--no-psqlrc",
            "--csv",
            f"--pset=null={NULL_SENTINEL}",
            "--set=ON_ERROR_STOP=1",
            "-c",
            sql,
        ]
        env = os.environ.copy()
        env["PGCLIENTENCODING"] = "UTF8"
        result = self.run_process(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        return str(result.stdout)


def parse_csv(text: str) -> list[dict[str, str | None]]:
    if not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text, newline=""))
    return [
        {
            key: None if value == NULL_SENTINEL else value
            for key, value in row.items()
        }
        for row in reader
    ]


def as_json(value: str | None, default=None):
    if value is None or value == "":
        return {} if default is None else default
    parsed = json.loads(value)
    return parsed


def as_int(value: str | None) -> int | None:
    return None if value is None or value == "" else int(value)


def as_float(value: str | None) -> float | None:
    return None if value is None or value == "" else float(value)


def as_bool(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "t", "1", "yes", "y", "oui"}:
        return True
    if normalized in {"false", "f", "0", "no", "n", "non"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def has_textual_history(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    normalized = value.strip().lower()
    if normalized in {"false", "f", "0", "no", "n", "non"}:
        return False
    return True


def sorted_group(rows: Iterable[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def source_indexes(source_rows: list[dict]) -> tuple[dict[tuple, list[str]], dict[str, list[str]]]:
    by_file: dict[tuple, list[str]] = defaultdict(list)
    by_system: dict[str, list[str]] = defaultdict(list)
    for row in source_rows:
        source_id = row["source_id"]
        system = row["source_system"]
        by_system[system].append(source_id)
        by_file[(system, row.get("source_file"))].append(source_id)
    return by_file, by_system


def matching_source_ids(
    row: dict,
    by_file: dict[tuple, list[str]],
    by_system: dict[str, list[str]],
) -> list[str]:
    system = row.get("source_system")
    source_file = row.get("source_file")
    exact = by_file.get((system, source_file), []) if source_file else []
    return sorted(exact or by_system.get(system, []))


def canonical_value(value: str | None, source_ids: list[str]) -> dict:
    return {
        "canonical": value,
        "reported_values": [
            {"source_id": source_id, "value": value}
            for source_id in source_ids
            if value is not None
        ],
    }


def build_documents(datasets: dict[str, list[dict]]) -> dict[str, dict[str, dict]]:
    source_rows = datasets["sources"]
    by_file, by_system = source_indexes(source_rows)
    links_by_person = sorted_group(datasets["identity_links"], "elite_id")
    memberships_by_person = sorted_group(datasets["person_memberships"], "elite_id")
    external_by_person = sorted_group(datasets["person_external_ids"], "elite_id")
    legacy_careers_by_person = sorted_group(datasets["career_entries"], "elite_id")
    org_careers_by_person = sorted_group(datasets["career_organizations"], "elite_id")
    aliases_by_org = sorted_group(datasets["organization_aliases"], "org_id")
    batches_by_source = sorted_group(datasets["source_import_batches"], "source_id")

    people: dict[str, dict] = {}
    for row in datasets["identity_master"]:
        elite_id = row["elite_id"]
        links = links_by_person.get(elite_id, [])
        identity_source_ids = sorted(
            {
                source_id
                for link in links
                for source_id in matching_source_ids(link, by_file, by_system)
            }
        )
        extensions = as_json(row.get("extensions"), {})
        aliases = [
            {
                "value": alias,
                "type": "other",
                "period": None,
                "source_ref": identity_source_ids,
            }
            for alias in sorted(extensions.get("aliases", []))
        ]
        memberships = [
            {
                "rule_id": item["rule_id"],
                "rule_description": item.get("rule_description"),
                "status": item["status"],
                "confidence": as_float(item["confidence"]),
                "evidence": {
                    "source_id": item["evidence_source_id"],
                    "record_id": item["evidence_record_id"],
                },
                "org_id": item.get("org_id"),
                "valid_from": item.get("valid_from"),
                "valid_to": item.get("valid_to"),
                "rationale": item["rationale"],
                "review": {
                    "reviewed_by": item.get("reviewed_by"),
                    "reviewed_at": item.get("reviewed_at"),
                },
            }
            for item in memberships_by_person.get(elite_id, [])
        ]
        external_ids = [
            {
                "system": item["id_system"],
                "value": item["external_id"],
                "source_id": item.get("source_id"),
                "status": item["verification_status"],
                "confidence": as_float(item.get("match_confidence")),
                "url": item.get("url"),
            }
            for item in external_by_person.get(elite_id, [])
        ]
        identity_links = [
            {
                "source_system": item["source_system"],
                "source_file": item.get("source_file"),
                "source_record_id": item["source_record_id"],
                "source_url": item.get("source_url"),
                "match_rule": item.get("match_rule"),
                "match_confidence": as_float(item.get("match_confidence")),
                "created_at": item.get("created_at"),
                "extensions": as_json(item.get("extensions"), {}),
            }
            for item in links
        ]

        career_path = []
        for item in legacy_careers_by_person.get(elite_id, []):
            career_extensions = as_json(item.get("extensions"), {})
            org_id = career_extensions.get("org_id")
            if not org_id and (
                item.get("legislature")
                or item.get("mandat_debut")
                or item.get("mandat_fin")
            ):
                org_id = "ORG_AN"
            source_ids = matching_source_ids(item, by_file, by_system)
            suppleant_history = item.get("a_eu_suppleant")
            career_path.append(
                {
                    "career_id": f"{elite_id}-CAR-L{int(item['career_id']):06d}",
                    "kind": "career_entry",
                    "org_id": org_id,
                    "position": item.get("position"),
                    "source_system": item["source_system"],
                    "source_record_id": item["source_record_id"],
                    "start_date": item.get("mandat_debut"),
                    "end_date": item.get("mandat_fin"),
                    "mandate_details": {
                        "regime": item.get("regime"),
                        "legislature": item.get("legislature"),
                        "departement": item.get("departement"),
                        "circonscription": item.get("circonscription"),
                        "groupe": item.get("groupe"),
                        "groupe_abrev": item.get("groupe_abrev"),
                        "status": item.get("status"),
                        "suppleant_de": item.get("suppleant_de"),
                        "a_eu_suppleant": suppleant_history,
                        "has_suppleant_history": has_textual_history(
                            suppleant_history
                        ),
                        "is_gaulliste": as_bool(item.get("is_gaulliste")),
                    },
                    "details": career_extensions,
                    "source_ref": source_ids,
                }
            )
        for item in org_careers_by_person.get(elite_id, []):
            source_row = next(
                source
                for source in source_rows
                if source["source_id"] == item["source_id"]
            )
            career_path.append(
                {
                    "career_id": f"{elite_id}-CAR-O{int(item['career_org_id']):06d}",
                    "kind": "organization_membership",
                    "org_id": item["org_id"],
                    "position": item.get("position"),
                    "source_system": source_row["source_system"],
                    "source_record_id": item["source_record_id"],
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "mandate_details": None,
                    "details": as_json(item.get("details"), {}),
                    "source_ref": [item["source_id"]],
                }
            )
        career_path.sort(key=lambda item: item["career_id"])

        network_groups = {"proven": [], "potential": []}
        for edge in datasets["network_edges"]:
            if elite_id not in {edge["elite_id_a"], edge["elite_id_b"]}:
                continue
            target = (
                edge["elite_id_b"]
                if edge["elite_id_a"] == elite_id
                else edge["elite_id_a"]
            )
            refs = matching_source_ids(edge, by_file, by_system)
            network_groups[edge["relation_category"]].append(
                {
                    "target_elite_id": target,
                    "relation_type": edge["relation_type"],
                    "relation_category": edge["relation_category"],
                    "strength": edge.get("strength"),
                    "context": edge.get("context"),
                    "source_url": edge.get("source_url"),
                    "source_ref": refs,
                    "extensions": as_json(edge.get("extensions"), {}),
                }
            )
        for items in network_groups.values():
            items.sort(key=lambda item: (item["target_elite_id"], item["relation_type"]))

        source_ids = set(identity_source_ids)
        source_ids.update(item["evidence"]["source_id"] for item in memberships)
        source_ids.update(
            item["source_id"] for item in external_ids if item["source_id"] is not None
        )
        source_ids.update(
            source_id for item in career_path for source_id in item["source_ref"]
        )
        source_ids.update(
            source_id
            for items in network_groups.values()
            for item in items
            for source_id in item["source_ref"]
        )
        people[elite_id] = {
            "elite_id": elite_id,
            "fingerprint_id": row.get("fingerprint_id"),
            "schema_version": "3.0",
            "record_version": 1,
            "metadata": {
                "created_at": row.get("created_at"),
                "last_updated": row.get("updated_at"),
                "lang_primary": "fr",
                "review_status": row["review_status"],
                "match_confidence": as_float(row.get("match_confidence")),
                "candidate_count": as_int(row.get("candidate_count")),
            },
            "identity": {
                "nom": row.get("nom"),
                "prenom": row.get("prenom"),
                "nom_complet": row.get("nom_complet"),
                "sexe": row.get("sexe") or "Unknown",
                "aliases": aliases,
                "birth": {
                    "date": canonical_value(row.get("birth_date"), identity_source_ids),
                    "place": canonical_value(row.get("birth_place"), identity_source_ids),
                },
                "death": {
                    "date": canonical_value(row.get("death_date"), identity_source_ids),
                    "place": canonical_value(None, []),
                },
            },
            "social_mobility": {
                "father": {
                    "name": row.get("father_name"),
                    "job": row.get("father_job"),
                    "pcs_code": None,
                    "source_ref": identity_source_ids,
                },
                "mother": {
                    "name": row.get("mother_name"),
                    "job": row.get("mother_job"),
                    "pcs_code": None,
                    "source_ref": identity_source_ids,
                },
                "education": [],
                "derived": {
                    "family_class": None,
                    "mobility_type": None,
                    "computed_at": None,
                },
                "data_gaps": [],
            },
            "memberships": memberships,
            "external_ids": external_ids,
            "identity_links": identity_links,
            "career_path": career_path,
            "networks": {
                "proven_links": network_groups["proven"],
                "potential_links": network_groups["potential"],
            },
            "sources_used": sorted(source_ids),
        }

    contribution_maps: dict[str, dict[str, dict]] = {
        row["source_id"]: {} for row in source_rows
    }

    def add_contribution(
        source_id: str,
        elite_id: str,
        record_id: str | None,
        field_name: str,
        *,
        match_rule: str | None = None,
        confidence: float | None = None,
    ) -> None:
        item = contribution_maps[source_id].setdefault(
            elite_id,
            {
                "elite_id": elite_id,
                "source_record_ids": set(),
                "fields_supplied": set(),
                "match_rules": set(),
                "match_confidence": None,
            },
        )
        if record_id:
            item["source_record_ids"].add(record_id)
        item["fields_supplied"].add(field_name)
        if match_rule:
            item["match_rules"].add(match_rule)
        if confidence is not None:
            current = item["match_confidence"]
            item["match_confidence"] = confidence if current is None else max(current, confidence)

    for item in datasets["identity_links"]:
        for source_id in matching_source_ids(item, by_file, by_system):
            add_contribution(
                source_id,
                item["elite_id"],
                item.get("source_record_id"),
                "identity_links",
                match_rule=item.get("match_rule"),
                confidence=as_float(item.get("match_confidence")),
            )
    for item in datasets["person_memberships"]:
        add_contribution(
            item["evidence_source_id"],
            item["elite_id"],
            item.get("evidence_record_id"),
            "memberships",
            confidence=as_float(item.get("confidence")),
        )
    for item in datasets["person_external_ids"]:
        if item.get("source_id"):
            add_contribution(
                item["source_id"],
                item["elite_id"],
                item.get("external_id"),
                "external_ids",
                confidence=as_float(item.get("match_confidence")),
            )

    sources: dict[str, dict] = {}
    for row in source_rows:
        source_id = row["source_id"]
        contributions = []
        for elite_id, item in sorted(contribution_maps[source_id].items()):
            contributions.append(
                {
                    "elite_id": elite_id,
                    "source_record_ids": sorted(item["source_record_ids"]),
                    "fields_supplied": sorted(item["fields_supplied"]),
                    "match_rules": sorted(item["match_rules"]),
                    "match_confidence": item["match_confidence"],
                }
            )
        sources[source_id] = {
            "source_id": source_id,
            "schema_version": "3.0",
            "record_version": 1,
            "metadata": {
                "source_system": row["source_system"],
                "source_file": row.get("source_file"),
                "extraction_date": row.get("extraction_date"),
                "extracted_by": row.get("extracted_by"),
                "extensions": as_json(row.get("extensions"), {}),
            },
            "bibliography": {
                "type": "Online_Database_Entry",
                "title": row.get("title") or source_id,
                "publisher": row.get("publisher"),
                "url": row.get("url"),
                "lang": row.get("lang") or "fr",
                "access_date": row.get("access_date"),
                "reliability_tier": row.get("reliability_tier"),
                "reliability_note": row.get("notes"),
            },
            "import_batches": [
                {
                    "batch_id": item["batch_id"],
                    "source_file": item["source_file"],
                    "imported_at": item["imported_at"],
                    "row_count": as_int(item["row_count"]),
                    "success_count": as_int(item["success_count"]),
                    "error_count": as_int(item["error_count"]),
                    "mapping_version": item["mapping_version"],
                    "status": item["status"],
                }
                for item in batches_by_source.get(source_id, [])
            ],
            "contributions": contributions,
        }

    children_by_parent: dict[str, list[str]] = defaultdict(list)
    for row in datasets["organizations"]:
        if row.get("parent_org_id"):
            children_by_parent[row["parent_org_id"]].append(row["org_id"])
    organizations: dict[str, dict] = {}
    for row in datasets["organizations"]:
        org_id = row["org_id"]
        aliases = [
            {
                "value": item["alias"],
                "type": item.get("alias_type"),
                "source_id": item.get("source_id"),
            }
            for item in aliases_by_org.get(org_id, [])
        ]
        org_memberships = [
            {
                "elite_id": item["elite_id"],
                "rule_id": item["rule_id"],
                "status": item["status"],
                "confidence": as_float(item["confidence"]),
                "evidence": {
                    "source_id": item["evidence_source_id"],
                    "record_id": item["evidence_record_id"],
                },
                "valid_from": item.get("valid_from"),
                "valid_to": item.get("valid_to"),
            }
            for item in datasets["person_memberships"]
            if item.get("org_id") == org_id
        ]
        career_members = []
        for item in datasets["career_entries"]:
            extensions = as_json(item.get("extensions"), {})
            legacy_org_id = extensions.get("org_id")
            if not legacy_org_id and (
                item.get("legislature")
                or item.get("mandat_debut")
                or item.get("mandat_fin")
            ):
                legacy_org_id = "ORG_AN"
            if legacy_org_id != org_id:
                continue
            career_members.append(
                {
                    "elite_id": item["elite_id"],
                    "career_id": f"{item['elite_id']}-CAR-L{int(item['career_id']):06d}",
                    "position": item.get("position"),
                    "start_date": item.get("mandat_debut"),
                    "end_date": item.get("mandat_fin"),
                    "source_ids": matching_source_ids(item, by_file, by_system),
                }
            )
        for item in datasets["career_organizations"]:
            if item["org_id"] != org_id:
                continue
            career_members.append(
                {
                    "elite_id": item["elite_id"],
                    "career_id": f"{item['elite_id']}-CAR-O{int(item['career_org_id']):06d}",
                    "position": item.get("position"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "source_ids": [item["source_id"]],
                }
            )
        career_members.sort(key=lambda item: (item["elite_id"], item["career_id"]))
        sources_used = {
            item["source_id"] for item in aliases if item["source_id"] is not None
        }
        sources_used.update(
            item["evidence"]["source_id"] for item in org_memberships
        )
        sources_used.update(
            source_id
            for item in career_members
            for source_id in item["source_ids"]
        )
        organizations[org_id] = {
            "org_id": org_id,
            "schema_version": "3.0",
            "record_version": 1,
            "identity": {
                "nom_officiel": row["nom_officiel"],
                "nom_court": row.get("nom_court"),
                "org_type": row.get("org_type"),
                "org_level": row.get("org_level"),
                "country": row.get("country") or "FR",
            },
            "aliases": aliases,
            "lifespan": {
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "note": row.get("notes"),
            },
            "parent_org_id": row.get("parent_org_id"),
            "child_org_ids": sorted(children_by_parent.get(org_id, [])),
            "is_gaulliste_marker": as_bool(row.get("is_gaulliste_marker")) or False,
            "extensions": as_json(row.get("extensions"), {}),
            "memberships": org_memberships,
            "career_members": career_members,
            "sources_used": sorted(sources_used),
        }

    return {
        "persons": people,
        "sources": sources,
        "organizations": organizations,
    }


def validate_documents(documents: dict[str, dict[str, dict]]) -> None:
    people = documents["persons"]
    sources = documents["sources"]
    organizations = documents["organizations"]
    qids: dict[str, str] = {}

    for elite_id, person in people.items():
        if not ELITE_ID_RE.fullmatch(elite_id):
            raise ValueError(f"invalid elite_id: {elite_id}")
        for membership in person["memberships"]:
            source_id = membership["evidence"]["source_id"]
            org_id = membership.get("org_id")
            if source_id not in sources:
                raise ValueError(f"{elite_id}: unknown membership source {source_id}")
            if org_id is not None and org_id not in organizations:
                raise ValueError(f"{elite_id}: unknown membership organization {org_id}")
        for external_id in person["external_ids"]:
            system = external_id["system"]
            value = external_id["value"]
            if not system or not value:
                raise ValueError(f"{elite_id}: external system/value must be non-empty")
            if external_id.get("source_id") not in {None, *sources}:
                raise ValueError(
                    f"{elite_id}: unknown external source {external_id['source_id']}"
                )
            if system.upper() == "WIKIDATA" and re.fullmatch(r"Q[1-9][0-9]*", value):
                previous = qids.get(value)
                if previous is not None and previous != elite_id:
                    raise ValueError(f"duplicate QID {value}: {previous}, {elite_id}")
                qids[value] = elite_id
        for career in person["career_path"]:
            if career.get("org_id") is not None and career["org_id"] not in organizations:
                raise ValueError(f"{elite_id}: unknown career organization {career['org_id']}")
            for source_id in career["source_ref"]:
                if source_id not in sources:
                    raise ValueError(f"{elite_id}: unknown career source {source_id}")
        for category in ("proven_links", "potential_links"):
            for link in person["networks"][category]:
                if link["target_elite_id"] not in people:
                    raise ValueError(
                        f"{elite_id}: unknown network person {link['target_elite_id']}"
                    )
        for source_id in person["sources_used"]:
            if source_id not in sources:
                raise ValueError(f"{elite_id}: unknown source {source_id}")

    for source_id, source in sources.items():
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise ValueError(f"invalid source_id: {source_id}")
        contributed = [item["elite_id"] for item in source["contributions"]]
        if len(contributed) != len(set(contributed)):
            raise ValueError(f"{source_id}: duplicate contribution elite_id")
        for elite_id in contributed:
            if elite_id not in people:
                raise ValueError(f"{source_id}: unknown contribution person {elite_id}")

    for org_id, organization in organizations.items():
        if not ORG_ID_RE.fullmatch(org_id):
            raise ValueError(f"invalid org_id: {org_id}")
        if (
            organization["parent_org_id"] is not None
            and organization["parent_org_id"] not in organizations
        ):
            raise ValueError(f"{org_id}: unknown parent organization")
        for item in organization["memberships"] + organization["career_members"]:
            if item["elite_id"] not in people:
                raise ValueError(f"{org_id}: unknown member {item['elite_id']}")


def atomic_write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (
        json.dumps(
            document,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    handle, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def write_documents(output: Path, documents: dict[str, dict[str, dict]]) -> dict[str, int]:
    counts = {}
    id_fields = {
        "persons": "elite_id",
        "sources": "source_id",
        "organizations": "org_id",
    }
    for directory, records in documents.items():
        target_dir = output / directory
        target_dir.mkdir(parents=True, exist_ok=True)
        expected_names = set()
        for record_id, document in sorted(records.items()):
            if document[id_fields[directory]] != record_id:
                raise ValueError(f"{directory}: inconsistent record id {record_id}")
            file_name = f"{record_id}.json"
            expected_names.add(file_name)
            atomic_write_json(target_dir / file_name, document)
        for old_path in target_dir.glob("*.json"):
            if old_path.name not in expected_names:
                old_path.unlink()
        counts[directory] = len(records)
    return counts


def export_all(
    output: Path | str,
    runner: Callable[[str], str],
) -> dict[str, int]:
    datasets = {
        name: parse_csv(runner(sql))
        for name, sql in QUERIES.items()
    }
    documents = build_documents(datasets)
    validate_documents(documents)
    return write_documents(Path(output), documents)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export gaullist_db JSON v3 records")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55432)
    parser.add_argument("--database", default="gaullist_db")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = PsqlRunner(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
    )
    counts = export_all(args.output, runner)
    print(
        "Exported "
        + ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
        + f" to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
