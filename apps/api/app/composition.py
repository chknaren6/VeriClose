from dataclasses import dataclass

from apps.api.app.settings import AppSettings, get_settings


@dataclass(frozen=True, slots=True)
class AppContainer:
    """Composition root for concrete application dependencies.

    The skeleton contains settings only. Repositories, adapters, the verification
    kernel, and application services will be added here as their milestones land.
    """

    settings: AppSettings


def build_container(settings: AppSettings | None = None) -> AppContainer:
    return AppContainer(settings=settings or get_settings())
