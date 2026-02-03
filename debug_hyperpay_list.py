
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.plugins.manager import get_plugins_manager

print("--- Listing All Detected Plugins ---")
try:
    manager = get_plugins_manager(allow_replica=True)
    # manager.all_plugins is a list of plugin instances
    # But wait, manager might be a LazyObject or similar, or just the Manager instance.
    # In Saleor 3.x, get_plugins_manager returns the manager *instance* usually, 
    # but the plugins themselves are often accessed via methods.
    # Actually, PluginsManager init loads the plugins.
    
    # Let's inspect 'plugins' attribute or similar if accessible, 
    # or iterate via a method if possible.
    # Looking at manager.py code is best, but let's try to access 'plugins'
    # BasePlugin classes are stored in 'plugins' usually.
    
    # In recent Saleor versions, manager has a 'plugins' attribute (list of instances).
    
    found = False
    if hasattr(manager, 'plugins'):
        print(f"Total plugins found: {len(manager.plugins)}")
        for p in manager.plugins:
            # p is an instance
            name = getattr(p, 'PLUGIN_NAME', str(p))
            pid = getattr(p, 'PLUGIN_ID', 'N/A')
            print(f" - {name} (ID: {pid})")
            if pid == "saleor.payments.hyperpay":
                found = True
    else:
        # Fallback inspection
        print("Manager does not have 'plugins' attribute visible.")
        print(dir(manager))
        
    if found:
        print("\nSUCCESS: HyperPay plugin is loaded by PluginsManager!")
    else:
        print("\nFAILURE: HyperPay plugin NOT found in PluginsManager list.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
