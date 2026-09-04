CREATE TABLE IF NOT EXISTS investigations (
    run_id VARCHAR NOT NULL,
    case_id VARCHAR NOT NULL,
    investigation_id VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (run_id, investigation_id)
);

CREATE INDEX IF NOT EXISTS investigations_case_idx
ON investigations (run_id, case_id, created_at);
