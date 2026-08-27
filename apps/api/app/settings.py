from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "judge-local", "hosted-demo", "benchmark", "test"]


class AppSettings(BaseSettings):
    """Typed runtime settings shared by local, judge, hosted, and test profiles."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VERICLOSE_",
        extra="ignore",
    )

    app_name: str = "VeriClose"
    environment: Environment = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Path(".data")
    database_path: Path = Path(".data/vericlose.duckdb")
    static_dir: Path = Path("apps/api/app/static")
    policy_path: Path = Path("config/policies/razorpay_inr_v1.yaml")
    upload_max_bytes: int = 10 * 1024 * 1024
    demo_mode: bool = True
    deterministic_seed: int = 42
    build_commit: str = "development"
    rule_version: str = "segment4-v1"
    policy_version: str = "razorpay_inr_v1@1.0.0"
    model_api_key: SecretStr | None = None

    @property
    def model_enabled(self) -> bool:
        return self.model_api_key is not None and bool(self.model_api_key.get_secret_value())

    def prepare_runtime_paths(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
