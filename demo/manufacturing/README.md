# Manufacturing demo datasets

These three packs are deterministic, INR-only, synthetic datasets using the existing VeriClose
gateway, bank, and ERP schemas. They contain no client data and no hidden evaluation truth.

| Company | Legal entity ID | Gateway | Bank | ERP | Primary scenarios |
|---|---|---:|---:|---:|---|
| Aether Precision Components Private Limited | `le_aether_precision_in` | 102 | 14 | 56 | many-to-one settlements; fee/GST mismatches |
| Nexus Industrial Tools Private Limited | `le_nexus_tools_in` | 104 | 13 | 56 | partial receipts; date shifts; missing bank receipts |
| Vanguard Specialty Chemicals Private Limited | `le_vanguard_chemicals_in` | 102 | 15 | 64 | refunds; duplicate postings; unbalanced journal; orphan credit |

Each company directory contains:

```text
inputs/gateway.csv
inputs/bank.csv
inputs/erp_gl.csv
manifest.json
```

The manifest carries the legal-entity name and ID, seed, scenario mix, row counts, and SHA-256
checksums. The CSVs can be selected directly in VeriClose's three upload slots.

## Regenerate exactly

```bash
make manufacturing-demos
```

## Use a pack with Restore demo

Choose one fixture directory before starting the app:

```bash
VERICLOSE_DEMO_FIXTURE_DIR=demo/manufacturing/aether-precision-components/inputs \
VERICLOSE_DETERMINISTIC_SEED=1042 \
make demo
```

Then select **Restore seed-42**. The label refers to the reset control's historical name; the
runtime uses the configured fixture directory and seed. Restart VeriClose to switch packs.

For an entity-specific CLI reconciliation, pass the manifest's legal entity ID explicitly:

```bash
uv run python -m scripts.reconcile \
  --gateway demo/manufacturing/aether-precision-components/inputs/gateway.csv \
  --bank demo/manufacturing/aether-precision-components/inputs/bank.csv \
  --erp demo/manufacturing/aether-precision-components/inputs/erp_gl.csv \
  --legal-entity le_aether_precision_in \
  --seed 1042 \
  --run-id aether-demo-v1
```

The same command shape works for Nexus and Vanguard using their manifest values. Runtime code
never reads scenario labels or hidden truth; decisions still come entirely from the existing
deterministic reconciliation kernel.
