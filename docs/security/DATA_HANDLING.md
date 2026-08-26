# Data Handling

VeriClose’s hackathon build is for synthetic data only.

- Do not upload real client exports.
- Do not commit uploads, local databases, generated truth outputs, API keys or company mappings.
- Store uploaded files beneath a generated identifier, never the supplied filename.
- Keep model keys server-side.
- Hosted-demo mode must limit file size and retention and display a synthetic-data warning.
- Production claims require authentication, tenant isolation, encryption, retention controls and security review that are outside the MVP.
