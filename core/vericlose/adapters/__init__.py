"""Source-format adapter implementations."""

from core.vericlose.adapters.bank import BankAdapter
from core.vericlose.adapters.erp_gl import ErpGlAdapter
from core.vericlose.adapters.gateway import GatewayAdapter
from core.vericlose.adapters.registry import AdapterRegistry

__all__ = ["AdapterRegistry", "BankAdapter", "ErpGlAdapter", "GatewayAdapter"]
