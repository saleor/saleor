Extensions
==========
Saleor has implemented extensions architecture.
It includes hooks for most basic operations like calculation of prices in the checkout or
calling some actions when an order has been created.


Plugin
------
Saleor has some plugins implemented by default. These plugins are located in ``saleor.extensions.plugins``.
The ExtensionManager needs to receive a list of enabled plugins. It can be done by including the Python plugin path in the
``settings.PLUGINS`` list.

Writing Your Own Plugin
^^^^^^^^^^^^^^^^^^^^^^^
A custom plugin has to inherit from the BasePlugin class. It should overwrite base methods. The plugin needs to be added
to the ``settings.PLUGINS``
Your own plugin can be written as a class which has callable instances, like this:


``custom/plugin.py``

.. code-block:: python


    from django.conf import settings
    from urllib.parse import urljoin

    from ...base_plugin import BasePlugin
    from .tasks import api_post_request_task

    class CustomPlugin(BasePlugin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._enabled = bool(settings.CUSTOM_PLUGIN_KEYS)


        def postprocess_order_creation(self, order: "Order", previous_value: Any):
            if not self._enabled:
                return
            data = {}

            transaction_url = urljoin(settings.CUSTOM_API_URL, "transactions/createoradjust")
            api_post_request_task.delay(transaction_url, data)


.. note::
   There is no need to implement all base methods. ``ExtensionManager`` will use default values for methods that are not implemented.

Activating Plugin
^^^^^^^^^^^^^^^^^
To activate the plugin, add it to the ``PLUGINS`` list in your Django settings:


``settings.py``

.. code-block:: python

    PLUGINS = ["saleor.extensions.plugins.custom.CustomPlugin", ]


Configuring Plugins
^^^^^^^^^^^^^^^^^^^
Saleor allows you to change a configuration of the given plugin over API.
Plugin owner needs to overwrite a method to create a structure of default configuration ``_get_default_configuration``
and ``CONFIG_STRUCTURE`` .
It requires an expected structure as in the following example:

.. code-block:: python


        from django.utils.translation import pgettext_lazy

        from saleor.extensions import ConfigurationTypeField

        CONFIG_STRUCTURE = {
            "Username or account": {
                "type": ConfigurationTypeField.STRING,
                "help_text": pgettext_lazy(
                    "Plugin help text", "Provide user or account details"
                ),
                "label": pgettext_lazy("Plugin label", "Username or account"),
            },
            "Password or license": {
                "type": ConfigurationTypeField.STRING,
                "help_text": pgettext_lazy(
                    "Plugin help text", "Provide password or license details"
                ),
                "label": pgettext_lazy("Plugin label", "Password or license"),
            }
        }

        @classmethod
        def _get_default_configuration(cls):
            defaults = {
                "name": cls.PLUGIN_NAME,
                "description": "",
                "active": False,
                "configuration": [
                    {
                        "name": "Username or account",
                        "value": "",
                    },
                    {
                        "name": "Password or license",
                        "value": "",
                    },
                ]
            }
            return defaults


``ExtensionManager`` will use this data to create default configuration in DB which will be served by API.

By using GraphQL queries -  ``pluginConfigurations`` and ``pluginConfiguration`` user will be able to list all enabled plugins.
Mutation ``pluginConfigurationUpdate`` will allow the user to active/disable and update configuration fields like ``API keys``
for a  given plugin.

API serves response with the given fields:


+------------------+-----------------------------------------------------------------------------+
| Name             |  Description                                                                |
+==================+=============================================================================+
| id               | Id of the plugin                                                            |
+------------------+-----------------------------------------------------------------------------+
| name             | Name of the plugin                                                          |
+------------------+-----------------------------------------------------------------------------+
| active           | Indicate if the plugin is activated or not                                  |
+------------------+-----------------------------------------------------------------------------+
| description      | Description of the plugin                                                   |
+------------------+-----------------------------------------------------------------------------+
| configuration    | It stores all configuration fields as a list that can be changed by a user  |
+------------------+-----------------------------------------------------------------------------+

Configuration fields:

+----------+-----------------------------------------------------------------+
| Name     |  Description                                                    |
+==========+=================================================================+
| name     | Name of the field                                               |
+----------+-----------------------------------------------------------------+
| value    | Current value of the field                                      |
+----------+-----------------------------------------------------------------+
| type     | Type of the field. Saleor supports - ``String`` and ``Boolean`` |
+----------+-----------------------------------------------------------------+
| helpText | Description of the field                                        |
+----------+-----------------------------------------------------------------+
| label    | Label for the field                                             |
+----------+-----------------------------------------------------------------+


ExtensionsManager
-----------------
``ExtensionsManager`` is located in ``saleor.extensions.base_plugin``.
It is a class responsible for handling all declared plugins and serving a response from them.
It serves a default response in case of a non-declared plugin.  There is a possibility to overwrite an ExtensionsManager
class by implementing it on its own. Saleor will discover the manager class by taking the declared path from
``settings.EXTENSIONS_MANAGER``.
Each Django request object has its own manager included as the ``extensions`` field. It is attached in the Saleor middleware.


BasePlugin
----------
``BasePlugin`` is located in ``saleor.extensions.base_plugin``. It is an abstract class for storing all methods
available for any plugin. All methods take the ``previous_value`` parameter. This contains a value
calculated by the previous plugin in the queue. If the plugin is first in line, it will use the default value calculated by
the manager.


Celery Tasks
------------
Some plugin operations should be done asynchronously. If Saleor has Celery enabled, it will discover all tasks
declared in ``tasks.py`` in the plugin directories.


``plugin.py``


.. code-block:: python

    def postprocess_order_creation(self, order: "Order", previous_value: Any):
        if not self._enabled:
            return
        data = {}
        transaction_url = urljoin(get_api_url(), "transactions/createoradjust")

        api_post_request_task.delay(transaction_url, data)


``tasks.py``

.. code-block:: python

    import json
    from celery import shared_task
    from typing import Any, Dict

    import requests
    from requests.auth import HTTPBasicAuth
    from django.conf import settings


    @shared_task
    def api_post_request(
        url: str,
        data: Dict[str, Any],
    ):
        try:
            username = "username"
            password = "password"
            auth = HTTPBasicAuth(username, password)
            requests.post(url, auth=auth, data=json.dumps(data), timeout=settings.TIMEOUT)
        except requests.exceptions.RequestException:
            return
