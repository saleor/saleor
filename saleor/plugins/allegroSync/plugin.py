import json
import logging
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from saleor.product.models import ProductVariant
from saleor.plugins.manager import PluginsManager
from saleor.plugins.allegro.plugin import AllegroPlugin, AllegroAPI
from saleor.plugins.base_plugin import BasePlugin
from saleor.plugins.models import PluginConfiguration
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


@dataclass
class AllegroSyncConfiguration:
    pass

class AllegroSyncPlugin(BasePlugin):
    PLUGIN_ID = "allegroSync"
    PLUGIN_NAME = "AllegroSync"
    PLUGIN_NAME_2 = "AllegroSync"
    META_CODE_KEY = "AllegroSyncPlugin.code"
    META_DESCRIPTION_KEY = "AllegroSyncPlugin.description"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration",
                                  cleaned_data):

        current_config = plugin_configuration.configuration

        configuration_to_update = cleaned_data.get("configuration")

        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)
        if "active" in cleaned_data:
            plugin_configuration.active = cleaned_data["active"]
        cls.validate_plugin_configuration(plugin_configuration)
        plugin_configuration.save()
        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)

        return plugin_configuration

    @staticmethod
    def valid_product(product):
        errors = []

        if not product.is_published:
            errors.append('flaga is_published jest ustawiona na false')
        if product.private_metadata.get('publish.allegro.status') != 'published':
            errors.append('publish.allegro.status != published')

        return errors

    def synchronize_allegro_offers(self):
        manage = PluginsManager(plugins=["saleor.plugins.allegro.plugin.AllegroPlugin"])
        plugin_configs = manage.get_plugin(AllegroPlugin.PLUGIN_ID)
        conf = {item["name"]: item["value"] for item in plugin_configs.configuration}
        token = conf.get('token_value')
        allegro_api = AllegroAPI(token)
        params = {'publication.status': [str(self.type)], 'limit': '1',
                  'offset': 0}
        response = allegro_api.get_request('sale/offers', params)
        totalCount = json.loads(response.text).get('totalCount')

        limit = 1000
        errors = []

        for i in range(int(int(totalCount) / limit) + 1):
            offset = i * limit

            params = {'publication.status': [str(self.type)], 'limit': limit,
                      'offset': offset}
            response = allegro_api.get_request('sale/offers', params)
            offers = json.loads(response.text).get('offers')
            if offers:
                skus = [offer.get('external').get('id') for offer in offers]
                product_variants = list(ProductVariant.objects.filter(sku__in=skus))
                for offer in offers:
                    product_errors = []
                    sku = offer.get('external').get('id')
                    id = offer.get('id')
                    variant = next((x for x in product_variants if x.sku == sku), None)
                    if variant:
                        product = variant.product
                        product_errors = AllegroSyncPlugin.valid_product(product)
                        if len(product_errors) == 0:
                            if product.private_metadata.get('publish.allegro.id') != id:
                                product.store_value_in_private_metadata({
                                    'publish.allegro.id': id})
                                product.save(update_fields=["private_metadata"])
                    else:
                        product_errors.append('nie znaleziono produktu o podanym SKU')

                    errors.append({'sku': sku, 'errors': product_errors})
        html_errors_list = plugin_configs.create_table(errors)
        return self.send_mail(html_errors_list)

    def send_mail(self, html_errors_list):
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('noreply.salingo@gmail.com', self.password)

        msg = MIMEMultipart('alternative')

        html = MIMEText(html_errors_list, 'html')

        msg.attach(html)
        msg['Subject'] = 'Logi z synchronizacji ofert'
        msg['From'] = 'sync+noreply.salingo@gmail.com'
        msg['To'] = 'sync+noreply.salingo@gmail.com'

        server.sendmail('noreply.salingo@gmail.com', 'noreply.salingo@gmail.com', msg.as_string())
