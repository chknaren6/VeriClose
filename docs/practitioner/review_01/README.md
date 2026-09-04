# Practitioner Review 01

This directory is the synthetic-only, blinded review pack for VeriClose's 65% domain review.

## Session order

1. Read `WALKTHROUGH.md`; do not explain the system's decisions.
2. Use `OBSERVATION_NOTES.md` while the practitioner opens five cases without coaching.
3. Let the practitioner independently label all cases in `CASES.md` using `labels.csv`.
4. Record workflow requests in `feature_priorities.csv` only after observation and labelling.
5. Open `.data/practitioner/review_01/private/LEAST_CERTAIN.md` and the answer key only during the reveal stage.
6. Classify every disagreement in `resolutions.csv`; accepted corrections require task IDs.
7. Run `make review-analyze` after every required label and feature row is complete.

The analyzer intentionally fails on incomplete labels. It will not manufacture agreement, findings,
accepted changes, or a completed domain-review report.

## Privacy

Every case is seeded synthetic data. Do not paste client exports, company identifiers, screenshots,
credentials, or proprietary mappings into these files.
