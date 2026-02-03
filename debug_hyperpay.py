
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

print("--- Debugging HyperPay Plugin ---")

# 1. Verify Settings
print("\n1. Checking settings.BUILTIN_PLUGINS...")
plugin_path = "saleor.payment.gateways.hyperpay.plugin.HyperPayGatewayPlugin"
if plugin_path in settings.BUILTIN_PLUGINS:
    print(f"PASS: {plugin_path} found in settings.")
else:
    print(f"FAIL: {plugin_path} NOT found in settings.")
    print("Listing all BUILTIN_PLUGINS:")
    for p in settings.BUILTIN_PLUGINS:
        print(f" - {p}")

# 2. Verify Import
print("\n2. Trying to import HyperPayGatewayPlugin...")
try:
    from saleor.payment.gateways.hyperpay.plugin import HyperPayGatewayPlugin
    print(f"PASS: Imported {HyperPayGatewayPlugin}")
    print(f"PLUGIN_ID: {HyperPayGatewayPlugin.PLUGIN_ID}")
    print(f"PLUGIN_NAME: {HyperPayGatewayPlugin.PLUGIN_NAME}")
except ImportError as e:
    print(f"FAIL: ImportError: {e}")
except Exception as e:
    print(f"FAIL: Exception during import: {e}")

# 3. Verify Dependencies
print("\n3. Checking imports in __init__.py...")
try:
    from saleor.payment import ChargeStatus, TransactionKind
    print("PASS: Imported ChargeStatus, TransactionKind from saleor.payment")
except ImportError as e:
    print(f"FAIL: Could not import core payment types: {e}")

# 4. Try Instantiation
print("\n4. Trying to instantiate HyperPayGatewayPlugin...")
try:
    # Mock configuration
    config = [
        {"name": "Entity ID", "value": "test"},
        {"name": "Access Token", "value": "test"},
        {"name": "Test mode", "value": True},
        {"name": "Payment brands", "value": "VISA"},
        {"name": "Automatic payment capture", "value": True},
    ]
    
    # Instantiate
    plugin = HyperPayGatewayPlugin(
        configuration=config,
        active=True,
        channel=None,
        requestor_getter=None,
        db_config=None,
        allow_replica=True
    )
    print("PASS: Plugin instantiated successfully.")
    print(f"Active: {plugin.active}")
    print(f"Config: {plugin.config}")
except TypeError as e:
    print(f"FAIL: TypeError during instantiation: {e}")
    import inspect
    print("Inspect __init__ signature:")
    print(inspect.signature(HyperPayGatewayPlugin.__init__))
except Exception as e:
    print(f"FAIL: Unexpected error during instantiation: {e}")
    import traceback
    traceback.print_exc()

print("\n--- End Debug ---")
