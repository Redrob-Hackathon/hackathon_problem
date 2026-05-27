"""
Local Submission Validator (for participants)
=============================================

Checks your submission.csv against the format spec BEFORE you upload it.
Catches all the errors that would cause auto-rejection on the server.

USAGE
-----
    python validate_submission.py submission.csv
    python validate_submission.py submission.csv --candidates candidates.jsonl

If you provide --candidates, it will also verify that every candidate_id in
your submission exists in the released candidate pool.
"""

import argparse
import csv
import gzip
import json
import sys
from pathlib import Path


EXPECTED_ROWS = 100
REQUIRED_COLUMNS = ["candidate_id", "rank", "score"]


class ValidationError(Exception):
    pass


def validate(submission_path, candidates_path=None):
    errors = []
    warnings = []

    # Load submission
    try:
        with open(submission_path, newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValidationError("CSV is empty or missing header row.")
            missing_cols = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing_cols:
                raise ValidationError(
                    f"Missing required columns: {missing_cols}. "
                    f"Found columns: {reader.fieldnames}"
                )
            rows = list(reader)
    except FileNotFoundError:
        raise ValidationError(f"File not found: {submission_path}")

    # Row count
    if len(rows) != EXPECTED_ROWS:
        errors.append(f"Expected exactly {EXPECTED_ROWS} rows, got {len(rows)}.")

    # Parse rows
    parsed = []
    for i, row in enumerate(rows, start=1):
        try:
            rank = int(row["rank"])
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'rank' is not a valid integer: {row['rank']!r}")
            continue
        try:
            score = float(row["score"])
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'score' is not a valid float: {row['score']!r}")
            continue
        cid = str(row["candidate_id"]).strip()
        if not cid:
            errors.append(f"Row {i}: empty candidate_id.")
            continue
        parsed.append({"rank": rank, "score": score, "candidate_id": cid, "row_idx": i})

    if errors:
        return errors, warnings  # stop early if rows are malformed

    # Ranks must be 1..N unique
    ranks = sorted([p["rank"] for p in parsed])
    if ranks != list(range(1, EXPECTED_ROWS + 1)):
        # Be specific
        dupes = set([r for r in ranks if ranks.count(r) > 1])
        gaps = set(range(1, EXPECTED_ROWS + 1)) - set(ranks)
        out_of_range = [r for r in ranks if r < 1 or r > EXPECTED_ROWS]
        if dupes:
            errors.append(f"Duplicate ranks found: {sorted(dupes)[:10]}")
        if gaps:
            errors.append(f"Missing ranks: {sorted(gaps)[:10]}")
        if out_of_range:
            errors.append(f"Ranks out of 1-{EXPECTED_ROWS} range: {out_of_range[:10]}")

    # Sort by rank
    parsed.sort(key=lambda p: p["rank"])

    # Candidate IDs unique
    ids = [p["candidate_id"] for p in parsed]
    seen = set()
    duped_ids = []
    for cid in ids:
        if cid in seen:
            duped_ids.append(cid)
        seen.add(cid)
    if duped_ids:
        errors.append(f"Duplicate candidate_id values: {duped_ids[:5]}")

    # Candidate ID format
    bad_format = [cid for cid in ids if not (cid.startswith("CAND_") and len(cid) == 12 and cid[5:].isdigit())]
    if bad_format:
        warnings.append(
            f"{len(bad_format)} candidate_id values don't match expected format CAND_XXXXXXX. "
            f"First 3: {bad_format[:3]}"
        )

    # Monotonic non-increasing scores
    scores = [p["score"] for p in parsed]
    monotonic_violations = 0
    for i in range(1, len(scores)):
        if scores[i] > scores[i - 1]:
            monotonic_violations += 1
    if monotonic_violations:
        warnings.append(
            f"Scores are not monotonically non-increasing — {monotonic_violations} "
            f"position(s) where score increased as rank increased. "
            f"Submission will be accepted but tie-breaks may be affected."
        )

    # All identical scores
    if len(set(scores)) == 1:
        warnings.append("All scores are identical — your model isn't differentiating between candidates.")

    # Reasoning column (optional)
    has_reasoning = rows and "reasoning" in rows[0].keys()
    if has_reasoning:
        reasonings = [str(row.get("reasoning", "")).strip() for row in rows]
        empty = sum(1 for r in reasonings if not r)
        short = sum(1 for r in reasonings if 0 < len(r) < 20)
        if empty > 0:
            warnings.append(
                f"{empty}/{EXPECTED_ROWS} rows have an empty 'reasoning' field. "
                f"Reasoning is OPTIONAL but recommended — top submissions are evaluated "
                f"partly on reasoning quality at Stage 4 (manual review)."
            )
        if short > EXPECTED_ROWS * 0.3:
            warnings.append(
                f"{short} reasonings are under 20 characters. Reasonings should be 1-2 "
                f"substantive sentences explaining why this candidate is ranked here."
            )
        # All identical reasoning strings = templated/lazy
        if len(set(r for r in reasonings if r)) <= 3 and len(reasonings) >= 50:
            warnings.append(
                "Reasoning field appears to use very few unique templates. "
                "Consider tailoring reasoning to each candidate's specific profile."
            )
    else:
        warnings.append(
            "No 'reasoning' column in submission. This is OPTIONAL but recommended — "
            "the top 50 submissions will be evaluated partly on reasoning quality at "
            "Stage 4 (manual review). Add a 4th column 'reasoning' to your CSV."
        )

    # If candidates.jsonl(.gz) provided, check IDs exist
    if candidates_path:
        valid_ids = set()
        opener = gzip.open if str(candidates_path).endswith(".gz") else open
        with opener(candidates_path, "rt") as f:
            for line in f:
                if line.strip():
                    valid_ids.add(json.loads(line)["candidate_id"])
        missing = [cid for cid in ids if cid not in valid_ids]
        if missing:
            errors.append(
                f"{len(missing)} candidate_id(s) not found in candidates.jsonl. "
                f"First 5: {missing[:5]}"
            )

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("submission", help="Path to submission.csv")
    parser.add_argument("--candidates", help="Path to candidates.jsonl (optional, enables ID existence check)")
    args = parser.parse_args()

    print(f"Validating: {args.submission}")
    if args.candidates:
        print(f"Against candidate pool: {args.candidates}")
    print()

    try:
        errors, warnings = validate(args.submission, args.candidates)
    except ValidationError as e:
        print(f"❌ FATAL: {e}")
        sys.exit(1)

    if errors:
        print(f"❌ INVALID — {len(errors)} error(s):")
        for e in errors:
            print(f"  • {e}")
        if warnings:
            print(f"\n⚠  Also {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  • {w}")
        print("\nFix the errors and re-run.")
        sys.exit(1)

    if warnings:
        print(f"✓ Format valid — but {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  • {w}")
        print("\nSubmission will be accepted but consider addressing the warnings.")
    else:
        print("✓ Submission is valid. You're ready to upload.")

    sys.exit(0)


if __name__ == "__main__":
    main()
