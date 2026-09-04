"""No-credential model adapter that deliberately activates deterministic fallback."""

from core.vericlose.ports.model_gateway import ModelRequest, ModelResponse, ModelUnavailableError


class DisabledModelGateway:
    def generate(self, request: ModelRequest) -> ModelResponse:
        del request
        raise ModelUnavailableError("model credentials are not configured")
