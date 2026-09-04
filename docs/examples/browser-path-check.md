# Judge-local browser path check

- Date: 2026-09-04
- Image: `vericlose:dev`
- Build metadata: `local`
- Model credential: absent; deterministic fallback active

Observed from a clean in-app browser session against the production container:

1. The compiled UI loaded on the same origin as the API.
2. **Restore demo** created a fresh seed-42 run with one proved case and two exceptions.
3. The missing-ERP case exposed exact gateway and bank rows plus every deterministic proof check.
4. The bounded investigator returned an explicitly labelled deterministic fallback.
5. Run-scoped Q&A answered only after an exact case ID was supplied.
6. The proposed journal balanced: ₹2,000.00 debits and ₹2,000.00 credits.
7. Approval was required before export, and export exposed a downloadable artifact.
8. Applying the approved mock journal created a new run and moved the selected case from
   `SUPPORTED` to `PROVED`.
9. The corrected run showed two proved cases and retained one unrelated unresolved
   `MISSING_BANK_RECEIPT` case at ₹1,464.60.
10. The prior run's Q&A input and answer were cleared after the run changed.

This is a product-path check on seeded synthetic data, not a practitioner validation or audit.
