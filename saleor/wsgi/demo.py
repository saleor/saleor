from . import application as core_application
from .readonly_dashboard import readonly_dashboard

application = readonly_dashboard(core_application)
