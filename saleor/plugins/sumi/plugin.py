import json
import logging
from datetime import datetime

from django.http import HttpResponse
from django.http.response import JsonResponse

from saleor.plugins.allegro.plugin import AllegroPlugin
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.manager import get_plugins_manager
from saleor.product.models import ProductVariant
from saleor.warehouse.models import Stock

logger = logging.getLogger(__name__)

class SumiConfiguration:
    token: str

class SumiPlugin(BasePlugin):
    PLUGIN_ID = "sumi"
    PLUGIN_NAME = "Sumi"
    PLUGIN_NAME_2 = "Sumi"
    META_CODE_KEY = "SumiPlugin.code"
    META_DESCRIPTION_KEY = "SumiPlugin.description"
    DEFAULT_CONFIGURATION = [{"name": "token", "value": "666"}]
    CONFIG_STRUCTURE = {
        "token": {
            "type": ConfigurationTypeField.STRING,
            "label": "Token do autoryzacji.",
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuration = {item["name"]: item["value"] for item in self.configuration}

    @staticmethod
    def get_configuration():
        manager = get_plugins_manager()
        plugin = manager.get_plugin(SumiPlugin.PLUGIN_ID)
        configuration = {item["name"]: item["value"] for item in plugin.configuration}
        return configuration



    @staticmethod
    def is_auth(token):
        configuration = SumiPlugin.get_configuration()
        return configuration.get('token') == token



    @staticmethod
    def create_reservation(request):
        logger.info('Request for create reservation')
        results = {"status": "ok", "data": [], "errors": []}
        # TODO: wynieś to do dekoratora
        if SumiPlugin.is_auth(request.headers.get('X-API-KEY')) and request.method == 'POST':
            products = json.loads(request.body.decode('utf-8'))['skus']
            for product in products:
                if ProductVariant.objects.filter(sku=product).exists():
                    product_variant = ProductVariant.objects.filter(sku=product).first()
                    if SumiPlugin.is_product_reserved(product_variant) == False:
                        if Stock.objects.filter(product_variant=product_variant).exists():
                            product_variant_stock = Stock.objects.filter(product_variant=product_variant).first()
                            result = SumiPlugin.reserve_product(product_variant_stock)
                            if isinstance(result, Stock):
                                results.get('data').append(str(result.product_variant))
                            else:
                                if result.get('error') is not None:
                                    results.get('errors').append(result.get('error'))
                                    results['status'] = 'error'
                        else:
                            results.get('errors').append('001: nie znaleziono produktu o kodzie ' + str(product))
                            results['status'] = 'error'
                    else:
                        pass
                else:
                    results.get('errors').append('001: nie znaleziono produktu o kodzie ' + str(product))
                    results['status'] = 'error'
            return JsonResponse(results)
        else:
            http_response = HttpResponse()
            http_response.status_code = 403
            return http_response

    @staticmethod
    def get_allegro_token(request):
        if SumiPlugin.is_auth(request.headers.get('X-API-KEY')) and request.method == 'GET':
            manager = get_plugins_manager()
            plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
            configuration = {item["name"]: item["value"] for item in
                             plugin.configuration}
            valid_till = datetime.strptime(configuration.get('token_access'), '%d/%m/%Y %H:%M:%S')
            return JsonResponse({"token": configuration.get('token_value'), "validTill": valid_till.strftime("%Y-%m-%dT%H:%M:%SZ")})
        else:
            http_response = HttpResponse()
            http_response.status_code = 403
            return http_response

    @staticmethod
    def reserve_product(product_variant_stock):
        try:
            SumiPlugin.update_reservation_status_in_metadata(product_variant_stock.product_variant, True)
            return product_variant_stock
        except:
            return {'error': '002: stan magazynowy produktu ' + str(product_variant_stock.product_variant) + ' wynosi 0'}

    @staticmethod
    def sell_product(product_variant_stock):
        try:
            product_variant_stock.decrease_stock(1)
            return {"sku": str(product_variant_stock.product_variant),
                    "name": str(product_variant_stock.product_variant.product),
                    "netPrice": str(round(float(product_variant_stock.product_variant.cost_price_amount) / 1.23, 2)),
                    "grossPrice": str(product_variant_stock.product_variant.cost_price_amount),
                    "vatRate": '23'
                    }
        except:
            return {'error': '002: stan magazynowy produktu ' + str(
                product_variant_stock.product_variant) + ' wynosi 0'}

    @staticmethod
    def update_reservation_status_in_metadata(product_variant, status):
        product_variant.store_value_in_metadata({'reserved': status})
        product_variant.save(update_fields=["metadata"])

    @staticmethod
    def is_product_reserved(product_variant):
        if product_variant.metadata.get('reserved') is not None:
            if product_variant.metadata.get('reserved') == True:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def cancel_product_reservation(product_variant_stock):
        try:
            SumiPlugin.update_reservation_status_in_metadata(product_variant_stock.product_variant, False)
            return product_variant_stock
        except:
            return {'error': '003: wystąpił błąd podczas przetwarzania produktu ' + str(
                product_variant_stock.product_variant)}

    @staticmethod
    def cancel_reservation(request):
        logger.info('Request for cancel reservation')
        results = {"status": "ok", "data": [], "errors": []}
        # TODO: wynieś to do dekoratora
        if SumiPlugin.is_auth(
                request.headers.get('X-API-KEY')) and request.method == 'POST':
            products = json.loads(request.body.decode('utf-8'))['skus']
            for product in products:
                if ProductVariant.objects.filter(sku=product).exists():
                    product_variant = ProductVariant.objects.filter(sku=product).first()
                    if SumiPlugin.is_product_reserved(product_variant) == True:
                        if Stock.objects.filter(product_variant=product_variant).exists():
                            product_variant_stock = Stock.objects.filter(
                                product_variant=product_variant).first()
                            result = SumiPlugin.cancel_product_reservation(product_variant_stock)
                            if isinstance(result, Stock):
                                results.get('data').append(str(result.product_variant))
                            else:
                                if result.get('error') is not None:
                                    results.get('errors').append(result.get('error'))
                                    results['status'] = 'error'
                    else:
                        pass

                else:
                    results.get('errors').append(
                        '001: nie znaleziono produktu o kodzie ' + str(product))
                    results['status'] = 'error'

            return JsonResponse(results)
        else:
            http_response = HttpResponse()
            http_response.status_code = 403
            return http_response

    @staticmethod
    def sell_products(request):
        logger.info('Request for sell product')
        results = {"status": "ok", "data": [], "errors": []}
        # TODO: wynieś to do dekoratora
        if SumiPlugin.is_auth(
                request.headers.get('X-API-KEY')) and request.method == 'POST':
            products = json.loads(request.body.decode('utf-8'))['skus']
            for product in products:
                if ProductVariant.objects.filter(sku=product).exists():
                    product_variant = ProductVariant.objects.filter(sku=product).first()
                    if Stock.objects.filter(
                            product_variant=product_variant).exists():
                        product_variant_stock = Stock.objects.filter(
                            product_variant=product_variant).first()
                        if product_variant_stock.quantity > 0:
                            result = SumiPlugin.sell_product(product_variant_stock)
                            results.get('data').append(result)
                        else:
                            results.get('errors').append('002: stan magazynowy produktu ' + str(
                product_variant_stock.product_variant) + ' wynosi 0')
                            results['status'] = 'error'
                    else:
                        results.get('errors').append(
                            '001: nie znaleziono produktu o kodzie ' + str(
                                product))
                        results['status'] = 'error'

                else:
                    results.get('errors').append(
                        '001: nie znaleziono produktu o kodzie ' + str(product))
                    results['status'] = 'error'

            return JsonResponse(results)
        else:
            http_response = HttpResponse()
            http_response.status_code = 403
            return http_response


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
            cls._append_config_structure(plugin_configuration.configuration)
        return plugin_configuration
