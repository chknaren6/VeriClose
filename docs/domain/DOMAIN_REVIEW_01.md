# Domain Review 01

**Status:** awaiting real practitioner session

The blinded 25-case review pack, observation protocol, structured label form, feature-priority form,
private reveal key and reserved holdout are prepared. Findings, agreement numbers, disagreements and
accepted rule changes are intentionally absent until an experienced ERP reconciliation practitioner
completes the independent review.

Run:

```bash
make review-pack
# conduct the session and complete the CSV forms
make review-analyze
```

`make review-analyze` refuses incomplete labels and accepted feature requests without task IDs.
When the review is complete it replaces this placeholder with a proportional report that explicitly
states it represents one practitioner and is not an audit or certification.

## Privacy constraints

Only seeded synthetic data may be used. No client artifact, identifier, credential or proprietary
mapping may enter the repository.

