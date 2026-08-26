export type ReadyResponse = {
  status: "ready";
  checks: Record<string, string>;
};

export type MetaResponse = {
  app: string;
  environment: string;
  build_commit: string;
  rule_version: string;
  policy_version: string;
  demo_mode: boolean;
  model_enabled: boolean;
};

export type RuntimeStatus = {
  ready: ReadyResponse;
  meta: MetaResponse;
};
