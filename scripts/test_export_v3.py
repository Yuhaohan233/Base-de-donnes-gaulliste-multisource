from __future__ import annotations

import csv
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "export_multisource_json.py"
SCHEMA_DIR = ROOT / "schema"
NULL = "__JSON_EXPORT_NULL__"


def csv_text(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: NULL if value is None else value
                for key, value in row.items()
            }
        )
    return stream.getvalue()


def load_exporter():
    spec = importlib.util.spec_from_file_location("export_multisource_json", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load exporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, datasets: dict[str, list[dict[str, object]]]):
        self.datasets = datasets
        self.queries: list[str] = []

    def __call__(self, sql: str) -> str:
        self.queries.append(sql)
        marker = sql.splitlines()[0].removeprefix("-- export:").strip()
        return csv_text(self.datasets.get(marker, []))


def fixture_datasets() -> dict[str, list[dict[str, object]]]:
    return {
        "identity_master": [
            {
                "elite_id": "FR_ELITE_000001",
                "fingerprint_id": "FP_ABCDEF123456",
                "nom": "Durand",
                "prenom": "Alice",
                "nom_complet": "Alice Durand",
                "sexe": "F",
                "birth_date": "1920-01-02",
                "birth_year": "1920",
                "birth_place": "Paris",
                "death_date": None,
                "father_name": None,
                "father_job": "Teacher",
                "mother_name": None,
                "mother_job": None,
                "candidate_count": "1",
                "review_status": "verified",
                "match_confidence": "0.975",
                "created_at": "2026-06-01",
                "updated_at": "2026-06-02",
                "extensions": '{"aliases": ["A. Durand"]}',
            }
        ],
        "identity_links": [
            {
                "elite_id": "FR_ELITE_000001",
                "source_system": "SYCOMORE",
                "source_file": "sycomore.csv",
                "source_record_id": "42",
                "source_url": "https://example.test/person/42",
                "match_rule": "exact_id",
                "match_confidence": "1.000",
                "created_at": "2026-06-01",
                "extensions": "{}",
            }
        ],
        "person_memberships": [
            {
                "elite_id": "FR_ELITE_000001",
                "rule_id": "RULE_01",
                "rule_description": "Gaullist parliamentary group",
                "status": "Verified",
                "confidence": "1.000",
                "evidence_source_id": "SRC_SYCOMORE",
                "evidence_record_id": "42",
                "org_id": "ORG_AN",
                "valid_from": "1958-12-09",
                "valid_to": "1962-10-09",
                "rationale": "Official parliamentary record",
                "reviewed_by": "reviewer",
                "reviewed_at": "2026-06-03 10:30:00+00",
            }
        ],
        "person_external_ids": [
            {
                "elite_id": "FR_ELITE_000001",
                "id_system": "WIKIDATA",
                "external_id": "Q123",
                "source_id": "SRC_WIKIDATA",
                "match_confidence": "0.990",
                "verification_status": "verified",
                "url": "https://www.wikidata.org/wiki/Q123",
            }
        ],
        "career_entries": [
            {
                "career_id": "7",
                "elite_id": "FR_ELITE_000001",
                "source_system": "SYCOMORE",
                "source_record_id": "42",
                "position": "Députée",
                "regime": "Cinquième République",
                "legislature": "Ire législature",
                "mandat_debut": "1958-12-09",
                "mandat_fin": "1962-10-09",
                "departement": "Paris",
                "circonscription": "1",
                "groupe": "UNR",
                "groupe_abrev": "UNR",
                "is_gaulliste": "true",
                "status": "titulaire",
                "suppleant_de": None,
                "a_eu_suppleant": "Patrick Ollier; Jacques Gautier",
                "source_url": "https://example.test/person/42",
                "extensions": '{"org_id": "ORG_AN"}',
            }
        ],
        "career_organizations": [
            {
                "career_org_id": "3",
                "elite_id": "FR_ELITE_000001",
                "org_id": "ORG_PARTY",
                "source_id": "SRC_SYCOMORE",
                "source_record_id": "42-party",
                "position": "Member",
                "start_date": "1960-01-01",
                "end_date": None,
                "details": '{"committee": "executive, national"}',
            }
        ],
        "network_edges": [],
        "sources": [
            {
                "source_id": "SRC_SYCOMORE",
                "source_system": "SYCOMORE",
                "source_file": "sycomore.csv",
                "title": "Assemblée source",
                "publisher": "Assemblée nationale",
                "url": "https://example.test/source",
                "lang": "fr",
                "access_date": "2026-06-01",
                "reliability_tier": "A",
                "extraction_date": "2026-06-01",
                "extracted_by": "fixture",
                "notes": None,
                "extensions": "{}",
            },
            {
                "source_id": "SRC_WIKIDATA",
                "source_system": "WIKIDATA",
                "source_file": "wikidata.csv",
                "title": "Wikidata",
                "publisher": "Wikimedia",
                "url": "https://www.wikidata.org",
                "lang": "en",
                "access_date": "2026-06-01",
                "reliability_tier": "B",
                "extraction_date": "2026-06-01",
                "extracted_by": "fixture",
                "notes": "",
                "extensions": '{"kind": "knowledge-base"}',
            },
        ],
        "source_import_batches": [
            {
                "batch_id": "BATCH_001",
                "source_id": "SRC_SYCOMORE",
                "source_file": "sycomore.csv",
                "imported_at": "2026-06-01 12:00:00+00",
                "row_count": "1",
                "success_count": "1",
                "error_count": "0",
                "mapping_version": "3.0",
                "status": "loaded",
            }
        ],
        "organizations": [
            {
                "org_id": "ORG_AN",
                "nom_officiel": "Assemblée nationale",
                "nom_court": "AN",
                "org_type": "Legislative",
                "org_level": "National",
                "country": "FR",
                "parent_org_id": None,
                "is_gaulliste_marker": "false",
                "start_date": "1958-10-04",
                "end_date": None,
                "notes": "Lower chamber",
                "extensions": "{}",
            },
            {
                "org_id": "ORG_PARTY",
                "nom_officiel": "Union",
                "nom_court": "UNR",
                "org_type": "Political_Party",
                "org_level": "National",
                "country": "FR",
                "parent_org_id": None,
                "is_gaulliste_marker": "true",
                "start_date": "1958-01-01",
                "end_date": None,
                "notes": None,
                "extensions": "{}",
            },
        ],
        "organization_aliases": [
            {
                "org_id": "ORG_AN",
                "alias": "Palais Bourbon",
                "alias_type": "common",
                "source_id": "SRC_SYCOMORE",
            }
        ],
    }


class ExportV3Tests(unittest.TestCase):
    def setUp(self):
        self.exporter = load_exporter()

    def read_tree(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*.json"))
        }

    def test_export_builds_valid_deterministic_cross_referenced_v3(self):
        runner = FakeRunner(fixture_datasets())
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            stale = output / "persons" / "FR_ELITE_999999.json"
            stale.parent.mkdir(parents=True)
            stale.write_text("{}", encoding="utf-8")
            unrelated = output / "keep.txt"
            unrelated.write_text("keep", encoding="utf-8")

            counts = self.exporter.export_all(output, runner)
            first_tree = self.read_tree(output)
            self.exporter.export_all(output, FakeRunner(fixture_datasets()))
            second_tree = self.read_tree(output)

            self.assertEqual(
                {"persons": 1, "sources": 2, "organizations": 2},
                counts,
            )
            self.assertEqual(first_tree, second_tree)
            self.assertFalse(stale.exists())
            self.assertEqual("keep", unrelated.read_text(encoding="utf-8"))
            self.assertFalse(list(output.rglob("*.tmp")))

            person = json.loads(
                (output / "persons" / "FR_ELITE_000001.json").read_text("utf-8")
            )
            source = json.loads(
                (output / "sources" / "SRC_SYCOMORE.json").read_text("utf-8")
            )
            organization = json.loads(
                (output / "organizations" / "ORG_AN.json").read_text("utf-8")
            )

            self.assertEqual("3.0", person["schema_version"])
            self.assertIsNone(person["identity"]["death"]["date"]["canonical"])
            self.assertEqual("Teacher", person["social_mobility"]["father"]["job"])
            self.assertEqual("SRC_SYCOMORE", person["memberships"][0]["evidence"]["source_id"])
            self.assertEqual("ORG_AN", person["memberships"][0]["org_id"])
            self.assertEqual("WIKIDATA", person["external_ids"][0]["system"])
            self.assertEqual("Q123", person["external_ids"][0]["value"])
            self.assertTrue(
                any(
                    item.get("mandate_details", {}).get("legislature")
                    == "Ire législature"
                    for item in person["career_path"]
                )
            )
            legacy_career = next(
                item
                for item in person["career_path"]
                if item["kind"] == "career_entry"
            )
            self.assertEqual(
                "Patrick Ollier; Jacques Gautier",
                legacy_career["mandate_details"]["a_eu_suppleant"],
            )
            self.assertTrue(
                legacy_career["mandate_details"]["has_suppleant_history"]
            )
            self.assertEqual(
                ["FR_ELITE_000001"],
                [item["elite_id"] for item in source["contributions"]],
            )
            self.assertEqual("BATCH_001", source["import_batches"][0]["batch_id"])
            self.assertEqual("Palais Bourbon", organization["aliases"][0]["value"])
            self.assertEqual("FR_ELITE_000001", organization["memberships"][0]["elite_id"])
            self.assertEqual("FR_ELITE_000001", organization["career_members"][0]["elite_id"])

            schemas = {
                "persons": "person_v3.schema.json",
                "sources": "source_v3.schema.json",
                "organizations": "organization_v3.schema.json",
            }
            for directory, schema_name in schemas.items():
                schema = json.loads((SCHEMA_DIR / schema_name).read_text("utf-8"))
                validator = Draft7Validator(schema)
                for path in sorted((output / directory).glob("*.json")):
                    errors = list(validator.iter_errors(json.loads(path.read_text("utf-8"))))
                    self.assertEqual([], errors, f"{path}: {errors}")

            person_ids = {
                json.loads(path.read_text("utf-8"))["elite_id"]
                for path in (output / "persons").glob("*.json")
            }
            source_ids = {
                json.loads(path.read_text("utf-8"))["source_id"]
                for path in (output / "sources").glob("*.json")
            }
            org_ids = {
                json.loads(path.read_text("utf-8"))["org_id"]
                for path in (output / "organizations").glob("*.json")
            }
            self.assertTrue(all(self.exporter.ELITE_ID_RE.fullmatch(item) for item in person_ids))
            self.assertTrue(
                all(
                    membership["evidence"]["source_id"] in source_ids
                    and membership["org_id"] in org_ids
                    for membership in person["memberships"]
                )
            )
            self.assertTrue(
                all(
                    contribution["elite_id"] in person_ids
                    for contribution in source["contributions"]
                )
            )

    def test_rejects_duplicate_qid_globally(self):
        datasets = fixture_datasets()
        second_person = dict(datasets["identity_master"][0])
        second_person["elite_id"] = "FR_ELITE_000002"
        second_person["fingerprint_id"] = "FP_123456ABCDEF"
        datasets["identity_master"].append(second_person)
        duplicate = dict(datasets["person_external_ids"][0])
        duplicate["elite_id"] = "FR_ELITE_000002"
        datasets["person_external_ids"].append(duplicate)

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "QID.*Q123"):
                self.exporter.export_all(Path(temp_dir), FakeRunner(datasets))

    def test_csv_json_null_and_scalar_conversion_are_explicit(self):
        parsed = self.exporter.parse_csv(
            csv_text(
                [
                    {
                        "nullable": None,
                        "empty": "",
                        "details": '{"text": "a,b"}',
                        "integer": "7",
                        "decimal": "0.750",
                        "boolean": "false",
                    }
                ]
            )
        )[0]
        self.assertIsNone(parsed["nullable"])
        self.assertEqual("", parsed["empty"])
        self.assertEqual({"text": "a,b"}, self.exporter.as_json(parsed["details"]))
        self.assertEqual(7, self.exporter.as_int(parsed["integer"]))
        self.assertEqual(0.75, self.exporter.as_float(parsed["decimal"]))
        self.assertIs(False, self.exporter.as_bool(parsed["boolean"]))

    def test_psql_runner_uses_postgresql_connection_defaults_and_csv(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))

            class Result:
                stdout = "elite_id\r\nFR_ELITE_000001\r\n"

            return Result()

        runner = self.exporter.PsqlRunner(run_process=fake_run, executable="psql.exe")
        result = runner("SELECT elite_id FROM identity_master")

        self.assertIn("FR_ELITE_000001", result)
        command, kwargs = calls[0]
        self.assertEqual("psql.exe", command[0])
        self.assertEqual("127.0.0.1", command[command.index("--host") + 1])
        self.assertEqual("55432", command[command.index("--port") + 1])
        self.assertEqual("gaullist_db", command[command.index("--dbname") + 1])
        self.assertEqual("postgres", command[command.index("--username") + 1])
        self.assertIn("--csv", command)
        self.assertEqual("SELECT elite_id FROM identity_master", command[-1])
        self.assertTrue(kwargs["check"])

    def test_find_psql_prefers_postgresql_18_installation(self):
        with (
            patch.dict(
                self.exporter.os.environ,
                {"ProgramFiles": r"C:\Program Files"},
                clear=False,
            ),
            patch.object(
                self.exporter.shutil,
                "which",
                return_value=r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
            ),
            patch.object(self.exporter.Path, "exists", return_value=True),
        ):
            self.assertEqual(
                r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
                self.exporter.find_psql(),
            )


if __name__ == "__main__":
    unittest.main()
