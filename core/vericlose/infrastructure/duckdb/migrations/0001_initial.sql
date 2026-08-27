CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR NOT NULL,
    snapshot_number BIGINT NOT NULL,
    state VARCHAR NOT NULL,
    policy_version VARCHAR NOT NULL,
    rule_version VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, snapshot_number)
);

CREATE TABLE IF NOT EXISTS source_files (
    run_id VARCHAR NOT NULL,
    file_id VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    sha256 VARCHAR NOT NULL,
    original_name VARCHAR NOT NULL,
    size_bytes BIGINT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    adapter_id VARCHAR NOT NULL,
    adapter_version VARCHAR NOT NULL,
    mapping_profile_version VARCHAR NOT NULL,
    relative_path VARCHAR NOT NULL,
    PRIMARY KEY (run_id, file_id),
    UNIQUE (run_id, sha256)
);

CREATE TABLE IF NOT EXISTS canonical_events (
    run_id VARCHAR NOT NULL,
    event_id VARCHAR NOT NULL,
    source_file_id VARCHAR NOT NULL,
    source_row_number BIGINT NOT NULL,
    file_sha256 VARCHAR NOT NULL,
    raw_row_hash VARCHAR NOT NULL,
    mapping_profile_version VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, event_id)
);

CREATE TABLE IF NOT EXISTS proof_checks (
    run_id VARCHAR NOT NULL,
    decision_id VARCHAR NOT NULL,
    ordinal BIGINT NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, decision_id, ordinal)
);

CREATE TABLE IF NOT EXISTS evidence_links (
    run_id VARCHAR NOT NULL,
    owner_type VARCHAR NOT NULL,
    owner_id VARCHAR NOT NULL,
    ordinal BIGINT NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, owner_type, owner_id, ordinal)
);

CREATE TABLE IF NOT EXISTS decisions (
    run_id VARCHAR NOT NULL,
    decision_id VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, decision_id)
);

CREATE TABLE IF NOT EXISTS exceptions (
    run_id VARCHAR NOT NULL,
    case_id VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, case_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    run_id VARCHAR NOT NULL,
    review_id VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, review_id)
);

CREATE TABLE IF NOT EXISTS actions (
    run_id VARCHAR NOT NULL,
    action_id VARCHAR NOT NULL,
    snapshot_number BIGINT NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, action_id, snapshot_number)
);

CREATE TABLE IF NOT EXISTS receipts (
    run_id VARCHAR NOT NULL,
    receipt_id VARCHAR NOT NULL,
    action_id VARCHAR NOT NULL,
    idempotency_key VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, receipt_id),
    UNIQUE (run_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS audit_events (
    run_id VARCHAR NOT NULL,
    audit_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, audit_id)
);
