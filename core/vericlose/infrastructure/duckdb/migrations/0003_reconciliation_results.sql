CREATE TABLE IF NOT EXISTS reconciliation_runs (
    run_id VARCHAR PRIMARY KEY,
    policy_version VARCHAR NOT NULL,
    rule_version VARCHAR NOT NULL,
    decision_count BIGINT NOT NULL,
    auto_cleared_count BIGINT NOT NULL,
    exception_count BIGINT NOT NULL,
    amount_at_risk_minor BIGINT NOT NULL,
    stage_timings_json VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT current_timestamp
);
