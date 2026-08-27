CREATE TABLE IF NOT EXISTS validation_issues (
    run_id VARCHAR NOT NULL,
    file_id VARCHAR NOT NULL,
    ordinal BIGINT NOT NULL,
    stage VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    code VARCHAR NOT NULL,
    row_number BIGINT,
    blocking BOOLEAN NOT NULL,
    payload_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, file_id, ordinal)
);

CREATE TABLE IF NOT EXISTS row_dispositions (
    run_id VARCHAR NOT NULL,
    file_id VARCHAR NOT NULL,
    row_number BIGINT NOT NULL,
    status VARCHAR NOT NULL,
    event_ids_json VARCHAR NOT NULL,
    issue_codes_json VARCHAR NOT NULL,
    PRIMARY KEY (run_id, file_id, row_number)
);

CREATE TABLE IF NOT EXISTS control_totals (
    run_id VARCHAR NOT NULL,
    file_id VARCHAR NOT NULL,
    component VARCHAR NOT NULL,
    currency VARCHAR NOT NULL,
    amount_minor BIGINT NOT NULL,
    record_count BIGINT NOT NULL,
    PRIMARY KEY (run_id, file_id, component)
);
