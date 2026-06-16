from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "inputs"
OUTPUT_DIR = ROOT / "outputs"

FREE_FRANCE_PATH = INPUT_DIR / "Personnalites_Gaullistes_Merged_career.xlsx"
SYCOMORE_PATH = INPUT_DIR / "gaullistes_sycomore.csv"
MANUAL_RESOLUTIONS_PATH = INPUT_DIR / "manual_identity_resolutions.csv"

MASTER_OUT = OUTPUT_DIR / "identity_master.csv"
LINKS_OUT = OUTPUT_DIR / "identity_links.csv"
CAREER_OUT = OUTPUT_DIR / "career_entries.csv"
AMBIGUOUS_OUT = OUTPUT_DIR / "ambiguous_matches_pending.csv"
REGISTRY_OUT = OUTPUT_DIR / "id_registry.csv"
REVIEWED_OUT = OUTPUT_DIR / "reviewed_identity_resolutions.csv"


FRENCH_MONTHS = {
    "janvier": "01",
    "fevrier": "02",
    "février": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "aout": "08",
    "août": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "decembre": "12",
    "décembre": "12",
}


def clean_value(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def normalize_text(value: object) -> str:
    text = clean_value(value)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_place(value: object) -> str:
    text = clean_value(value)
    text = re.sub(r"[（(].*?[）)]", "", text)
    text = text.replace("，", ",")
    if "," in text:
        text = text.split(",", 1)[0]
    return normalize_text(text)


def parse_date(value: object) -> str:
    text = clean_value(value)
    if not text:
        return ""

    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    norm = normalize_text(text).lower()
    match = re.match(r"^(\d{1,2})\s+([a-zéûôîàèùç]+)\s+(\d{4})$", text.lower())
    if match:
        day, month_name, year = match.groups()
        month = FRENCH_MONTHS.get(month_name)
        if month:
            return f"{year}-{month}-{int(day):02d}"

    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", norm)
    return match.group(1) if match else text


def birth_year(date_value: object) -> str:
    parsed = parse_date(date_value)
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", parsed)
    return match.group(1) if match else ""


def fingerprint(nom: object, prenom: object, year: object, place: object) -> str:
    parts = [
        normalize_text(nom),
        normalize_text(prenom),
        clean_value(year),
        normalize_place(place),
    ]
    if not parts[0] or not parts[1]:
        return ""
    raw = "|".join(parts)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest().upper()[:12]
    return f"FP_{digest}"


def split_sycomore_name(nom_complet: object) -> tuple[str, str]:
    text = clean_value(nom_complet)
    if not text:
        return "", ""
    tokens = text.replace(",", " ").split()
    if len(tokens) == 1:
        return tokens[0], ""
    nom = tokens[-1]
    prenom = " ".join(tokens[:-1])
    return nom, prenom


def first_nonempty(values: list[object]) -> str:
    for value in values:
        text = clean_value(value)
        if text:
            return text
    return ""


def build_free_france_candidates() -> tuple[list[dict], list[dict]]:
    df = pd.read_excel(FREE_FRANCE_PATH, dtype=str).fillna("")
    candidates: list[dict] = []
    links: list[dict] = []

    for idx, row in df.iterrows():
        nom = clean_value(row.get("Nom"))
        prenom = clean_value(row.get("Prénom"))
        birth_date = parse_date(row.get("Date de naissance"))
        year = birth_year(row.get("Date de naissance"))
        birth_place = first_nonempty([
            row.get("Commune de naissance"),
            row.get("Lieu de naissance"),
        ])
        death_date = parse_date(row.get("Date de décès"))
        source_record_id = f"FREE_FRANCE_ROW_{idx + 1:05d}"
        source_url = clean_value(row.get("Sources"))
        fp = fingerprint(nom, prenom, year, birth_place)

        candidates.append({
            "candidate_id": source_record_id,
            "source_system": "FREE_FRANCE_WIKI",
            "source_file": FREE_FRANCE_PATH.name,
            "source_record_id": source_record_id,
            "nom": nom,
            "prenom": prenom,
            "nom_complet": " ".join(x for x in [prenom, nom] if x),
            "sexe": clean_value(row.get("Sexe")),
            "birth_date": birth_date,
            "birth_year": year,
            "birth_place": birth_place,
            "death_date": death_date,
            "fingerprint_id": fp,
            "sycomore_id": "",
            "sycomore_url": "",
            "source_url": source_url,
            "source_groups": clean_value(row.get("Organisations d'appartenance")),
            "father_name": " ".join(x for x in [
                clean_value(row.get("Prénom(s) du père")),
                clean_value(row.get("Nom du père")),
            ] if x),
            "father_job": clean_value(row.get("Profession(s) du père")),
            "mother_name": " ".join(x for x in [
                clean_value(row.get("Prénom(s) de la mère")),
                clean_value(row.get("Nom de la mère")),
            ] if x),
            "mother_job": clean_value(row.get("Profession(s) de la mère")),
            "match_priority": 2,
        })

        links.append({
            "candidate_id": source_record_id,
            "source_system": "FREE_FRANCE_WIKI",
            "source_file": FREE_FRANCE_PATH.name,
            "source_record_id": source_record_id,
            "source_url": source_url,
            "match_rule": "source_row",
            "match_confidence": 1.0,
        })

    return candidates, links


def build_sycomore_candidates() -> tuple[list[dict], list[dict], list[dict]]:
    df = pd.read_csv(SYCOMORE_PATH, dtype=str).fillna("")
    candidates: list[dict] = []
    links: list[dict] = []
    career_rows: list[dict] = []

    for fiche_id, group in df.groupby("fiche_id", sort=True):
        first = group.iloc[0]
        nom, prenom = split_sycomore_name(first.get("nom_complet"))
        birth_date = parse_date(first.get("naissance_date"))
        year = birth_year(first.get("naissance_date"))
        birth_place = clean_value(first.get("naissance_commune"))
        death_date = parse_date(first.get("deces_date"))
        source_record_id = f"SYCOMORE_{fiche_id}"
        source_url = clean_value(first.get("url"))
        fp = fingerprint(nom, prenom, year, birth_place)

        candidates.append({
            "candidate_id": source_record_id,
            "source_system": "SYCOMORE",
            "source_file": SYCOMORE_PATH.name,
            "source_record_id": fiche_id,
            "nom": nom,
            "prenom": prenom,
            "nom_complet": clean_value(first.get("nom_complet")),
            "sexe": "",
            "birth_date": birth_date,
            "birth_year": year,
            "birth_place": birth_place,
            "death_date": death_date,
            "fingerprint_id": fp,
            "sycomore_id": fiche_id,
            "sycomore_url": source_url,
            "source_url": source_url,
            "source_groups": "Sycomore; groupe parlementaire gaulliste",
            "father_name": "",
            "father_job": "",
            "mother_name": "",
            "mother_job": "",
            "match_priority": 1,
        })

        links.append({
            "candidate_id": source_record_id,
            "source_system": "SYCOMORE",
            "source_file": SYCOMORE_PATH.name,
            "source_record_id": fiche_id,
            "source_url": source_url,
            "match_rule": "exact_sycomore_fiche_id",
            "match_confidence": 1.0,
        })

        for mandate_idx, row in group.reset_index(drop=True).iterrows():
            career_rows.append({
                "candidate_id": source_record_id,
                "source_system": "SYCOMORE",
                "source_record_id": fiche_id,
                "career_source_row": mandate_idx + 1,
                "position": "Député",
                "regime": clean_value(row.get("regime")),
                "legislature": clean_value(row.get("legislature")),
                "mandat_debut": parse_date(row.get("mandat_debut")),
                "mandat_fin": parse_date(row.get("mandat_fin")),
                "departement": clean_value(row.get("departement")),
                "circonscription": clean_value(row.get("circonscription")),
                "groupe": clean_value(row.get("groupe")),
                "groupe_abrev": clean_value(row.get("groupe_abrev")),
                "is_gaulliste": clean_value(row.get("est_gaulliste")),
                "status": "suppléant" if clean_value(row.get("suppleant_de")) else "député",
                "suppleant_de": clean_value(row.get("suppleant_de")),
                "a_eu_suppleant": clean_value(row.get("a_eu_suppleant")),
                "source_url": clean_value(row.get("url")),
            })

    return candidates, links, career_rows


def load_existing_ids() -> tuple[dict[str, str], int]:
    if not MASTER_OUT.exists():
        return {}, 1

    existing = pd.read_csv(MASTER_OUT, dtype=str).fillna("")
    mapping = {
        row["fingerprint_id"]: row["elite_id"]
        for _, row in existing.iterrows()
        if clean_value(row.get("fingerprint_id")) and clean_value(row.get("elite_id"))
    }
    max_seq = 0
    for elite_id in existing.get("elite_id", []):
        match = re.match(r"^FR_ELITE_(\d{6})$", clean_value(elite_id))
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return mapping, max_seq + 1


def load_manual_resolutions() -> tuple[dict[str, str], set[frozenset[str]], pd.DataFrame]:
    if not MANUAL_RESOLUTIONS_PATH.exists():
        return {}, set(), pd.DataFrame()

    resolutions = pd.read_csv(MANUAL_RESOLUTIONS_PATH, dtype=str).fillna("")
    merge_groups: dict[str, str] = {}
    reviewed_sets: set[frozenset[str]] = set()

    for _, row in resolutions.iterrows():
        candidate_ids = [
            candidate_id.strip()
            for candidate_id in row["candidate_ids"].split(";")
            if candidate_id.strip()
        ]
        reviewed_sets.add(frozenset(candidate_ids))
        if row["review_decision"] == "same_person":
            for candidate_id in candidate_ids:
                merge_groups[candidate_id] = row["resolution_id"]

    return merge_groups, reviewed_sets, resolutions


def assign_elite_ids(candidates: list[dict]) -> tuple[pd.DataFrame, dict[str, str], pd.DataFrame]:
    df = pd.DataFrame(candidates)
    df["name_key"] = df["nom"].map(normalize_text) + "|" + df["prenom"].map(normalize_text)
    df["place_key"] = df["birth_place"].map(normalize_place)
    df["identity_key"] = (
        df["name_key"] + "|" + df["birth_year"].fillna("") + "|" + df["place_key"].fillna("")
    )

    candidate_to_elite: dict[str, str] = {}
    master_rows: list[dict] = []
    ambiguous_rows: list[dict] = []
    manual_merge_groups, reviewed_sets, _ = load_manual_resolutions()

    grouped: dict[str, list[int]] = {}
    for idx, row in df.iterrows():
        manual_group = manual_merge_groups.get(row["candidate_id"])
        key = (
            f"MANUAL|{manual_group}"
            if manual_group
            else clean_value(row["fingerprint_id"]) or f"NOFP|{row['candidate_id']}"
        )
        grouped.setdefault(key, []).append(idx)

    existing_ids, elite_seq = load_existing_ids()
    for _, indexes in sorted(grouped.items(), key=lambda item: item[0]):
        rows = df.loc[indexes].sort_values(["match_priority", "candidate_id"])
        existing_elite_ids = [
            existing_ids[fp]
            for fp in rows["fingerprint_id"].tolist()
            if clean_value(fp) and fp in existing_ids
        ]
        if existing_elite_ids:
            elite_id = sorted(set(existing_elite_ids))[0]
        else:
            elite_id = f"FR_ELITE_{elite_seq:06d}"
            elite_seq += 1

        for candidate_id in rows["candidate_id"]:
            candidate_to_elite[candidate_id] = elite_id

        sources = sorted(set(rows["source_system"]))
        sycomore_ids = [x for x in rows["sycomore_id"].tolist() if clean_value(x)]
        sycomore_urls = [x for x in rows["sycomore_url"].tolist() if clean_value(x)]

        is_manual_merge = any(
            candidate_id in manual_merge_groups
            for candidate_id in rows["candidate_id"]
        )
        review_status = "verified" if len(rows) == 1 or is_manual_merge else "auto_merged"
        match_confidence = 1.0 if len(rows) == 1 or is_manual_merge else 0.95

        master_rows.append({
            "elite_id": elite_id,
            "fingerprint_id": first_nonempty(rows["fingerprint_id"].tolist()),
            "nom": first_nonempty(rows["nom"].tolist()),
            "prenom": first_nonempty(rows["prenom"].tolist()),
            "nom_complet": first_nonempty(rows["nom_complet"].tolist()),
            "sexe": first_nonempty(rows["sexe"].tolist()),
            "birth_date": first_nonempty(rows["birth_date"].tolist()),
            "birth_year": first_nonempty(rows["birth_year"].tolist()),
            "birth_place": first_nonempty(rows["birth_place"].tolist()),
            "death_date": first_nonempty(rows["death_date"].tolist()),
            "source_groups": " | ".join(sorted(set(x for x in rows["source_groups"] if clean_value(x)))),
            "sycomore_id": ";".join(sorted(set(sycomore_ids))),
            "sycomore_url": ";".join(sorted(set(sycomore_urls))),
            "father_name": first_nonempty(rows["father_name"].tolist()),
            "father_job": first_nonempty(rows["father_job"].tolist()),
            "mother_name": first_nonempty(rows["mother_name"].tolist()),
            "mother_job": first_nonempty(rows["mother_job"].tolist()),
            "source_systems": ";".join(sources),
            "candidate_count": len(rows),
            "review_status": review_status,
            "match_confidence": match_confidence,
            "identity_key": first_nonempty(rows["identity_key"].tolist()),
        })

    # Same name but multiple birth/place combinations: useful manual review queue.
    for name_key, rows in df.groupby("name_key"):
        if not clean_value(name_key):
            continue
        fps = sorted(set(x for x in rows["fingerprint_id"] if clean_value(x)))
        candidate_set = frozenset(rows["candidate_id"].tolist())
        if len(rows) > 1 and len(fps) > 1 and candidate_set not in reviewed_sets:
            ambiguous_rows.append({
                "name_key": name_key,
                "candidate_ids": ";".join(rows["candidate_id"].tolist()),
                "fingerprint_ids": ";".join(fps),
                "birth_years": ";".join(sorted(set(x for x in rows["birth_year"] if clean_value(x)))),
                "birth_places": ";".join(sorted(set(x for x in rows["birth_place"] if clean_value(x)))),
                "note": "同名但身份指纹不同，需人工确认是否同一人或同名异人",
            })

    ambiguous_columns = [
        "name_key",
        "candidate_ids",
        "fingerprint_ids",
        "birth_years",
        "birth_places",
        "note",
    ]
    return (
        pd.DataFrame(master_rows),
        candidate_to_elite,
        pd.DataFrame(ambiguous_rows, columns=ambiguous_columns),
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    free_candidates, free_links = build_free_france_candidates()
    syc_candidates, syc_links, syc_careers = build_sycomore_candidates()

    candidates = free_candidates + syc_candidates
    links = free_links + syc_links
    master_df, candidate_to_elite, ambiguous_df = assign_elite_ids(candidates)
    _, _, reviewed_df = load_manual_resolutions()

    links_df = pd.DataFrame(links)
    links_df.insert(0, "elite_id", links_df["candidate_id"].map(candidate_to_elite))
    links_df = links_df.drop(columns=["candidate_id"])

    career_df = pd.DataFrame(syc_careers)
    career_df.insert(0, "elite_id", career_df["candidate_id"].map(candidate_to_elite))
    career_df = career_df.drop(columns=["candidate_id"])

    master_df = master_df.sort_values("elite_id")
    links_df = links_df.sort_values(["elite_id", "source_system", "source_record_id"])
    career_df = career_df.sort_values(["elite_id", "mandat_debut", "legislature"])
    registry_df = master_df[[
        "elite_id",
        "fingerprint_id",
        "nom",
        "prenom",
        "birth_year",
        "birth_place",
        "source_systems",
        "candidate_count",
        "review_status",
        "match_confidence",
    ]].copy()

    master_df.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    links_df.to_csv(LINKS_OUT, index=False, encoding="utf-8-sig")
    career_df.to_csv(CAREER_OUT, index=False, encoding="utf-8-sig")
    ambiguous_df.to_csv(AMBIGUOUS_OUT, index=False, encoding="utf-8-sig")
    registry_df.to_csv(REGISTRY_OUT, index=False, encoding="utf-8-sig")
    reviewed_df.to_csv(REVIEWED_OUT, index=False, encoding="utf-8-sig")

    print(f"identity_master: {len(master_df)} rows -> {MASTER_OUT}")
    print(f"identity_links:  {len(links_df)} rows -> {LINKS_OUT}")
    print(f"career_entries:  {len(career_df)} rows -> {CAREER_OUT}")
    print(f"ambiguous:       {len(ambiguous_df)} rows -> {AMBIGUOUS_OUT}")
    print(f"id_registry:     {len(registry_df)} rows -> {REGISTRY_OUT}")
    print(f"reviewed:        {len(reviewed_df)} rows -> {REVIEWED_OUT}")
    print(f"source systems:  {master_df['source_systems'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
