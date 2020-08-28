import json
import uuid
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import requests
from django.shortcuts import redirect
from slugify import slugify

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.manager import get_plugins_manager
from saleor.plugins.models import PluginConfiguration
from saleor.product.models import Product, AssignedProductAttribute, \
    AttributeValue, ProductImage, ProductVariant


@dataclass
class AllegroConfiguration:
    redirect_url: str
    callback_url: str
    token_value: str
    client_id: str
    client_secret: str
    refresh_token: str
    saleor_redirect_url: str
    token_access: str
    auth_env: str
    env: str


class AllegroPlugin(BasePlugin):
    PLUGIN_ID = "allegro"
    PLUGIN_NAME = "Allegro"
    PLUGIN_NAME_2 = "Allegro"
    META_CODE_KEY = "AllegroPlugin.code"
    META_DESCRIPTION_KEY = "AllegroPlugin.description"
    DEFAULT_CONFIGURATION = [{"name": "redirect_url", "value": "https://allegro.pl.allegrosandbox.pl/auth/oauth"},
                             {"name": "callback_url", "value": "http://localhost:8000/allegro"},
                             {"name": "saleor_redirect_url", "value": "http://localhost:9000"},
                             {"name": "token_value", "value": None},
                             {"name": "client_id", "value": None},
                             {"name": "client_secret", "value": None},
                             {"name": "refresh_token", "value": None},
                             {"name": "token_access", "value": None},
                             {"name": "auth_env", "value":  "https://allegro.pl.allegrosandbox.pl"},
                             {"name": "env", "value":  "https://api.allegro.pl.allegrosandbox.pl"},]
    CONFIG_STRUCTURE = {
        "redirect_url": {
            "type": ConfigurationTypeField.STRING,
            "label": "Redirect URL np: https://allegro.pl.allegrosandbox.pl/auth/oauth",
        },
        "callback_url": {
            "type": ConfigurationTypeField.STRING,
            "label": "Callback URL:",
            "help_text": "Callback URL ustalany przy tworzeniu aplikacji po stronie allegro.",
        },
        "saleor_redirect_url": {
            "type": ConfigurationTypeField.STRING,
            "label": "Redirect URL saleora po autoryzacji:",
            "help_text": "URL saleora na ktory przekierowac po autoryzacji.",
        },
        "token_value": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Wartośc tokena:",
            "label": "Wartość tokena.",
        },
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "ID klienta allegro generowany przez allegro.",
            "label": "ID klienta allegro:",
        },
        "client_secret": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Wartość skeretnego klucza generowanego przez allegro.",
            "label": "Wartość sekretnego klucza:",
        },
        "refresh_token": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Wartośc refresh tokena.",
            "label": "Refresh token.",
        },
        "token_access": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Data uzupełni się automatycznie.",
            "label": "Data ważności tokena:",
        },
        "auth_env": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Adres do środowiska.",
            "label": "Adres do środowiska:",
        },
        "env": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Adres do środowiska.",
            "label": "Adres do środowiska:",
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = AllegroConfiguration(redirect_url=configuration["redirect_url"],
                                           callback_url=configuration["callback_url"],
                                           saleor_redirect_url=configuration["saleor_redirect_url"],
                                           token_access=configuration["token_access"],
                                           token_value=configuration["token_value"],
                                           client_id=configuration["client_id"],
                                           client_secret=configuration["client_secret"],
                                           refresh_token=configuration["refresh_token"],
                                           auth_env=configuration["auth_env"],
                                           env=configuration["env"])

        HOURS_LESS_THAN_WE_REFRESH_TOKEN = 6

        if self.config.token_access and self.calculate_hours_to_token_expire() < HOURS_LESS_THAN_WE_REFRESH_TOKEN:
            access_token, refresh_token, expires_in = AllegroAPI(self.config.token_access).refresh_token(self.config.refresh_token, self.config.client_id, self.config.client_secret, self.config.saleor_redirect_url) or (None, None, None)
            if access_token and refresh_token and expires_in is not None:
                AllegroAuth.save_token_in_plugin_configuration(AllegroAuth, access_token, refresh_token, expires_in)


    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        access_key = configuration.get("Access key")

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

        configuration = {item["name"]: item["value"] for item in
                         plugin_configuration.configuration}

        if (plugin_configuration.active == True and not configuration[
            'token_value'] and bool(configuration['client_id']) and bool(
            configuration['client_secret'])):
            allegro_auth = AllegroAuth()
            allegro_auth.get_access_code(configuration['client_id'],
                                         configuration['client_secret'],
                                         configuration['callback_url'],
                                         configuration['redirect_url'])

        return plugin_configuration

    def product_created(self, product: "Product", previous_value: Any) -> Any:

        if product.is_published == True:
            allegro_api = AllegroAPI(self.config.token_value)
            allegro_api.product_publish(saleor_product=product)

    def calculate_hours_to_token_expire(self):
        token_expire = datetime.strptime(self.config.token_access, '%d/%m/%Y %H:%M:%S')
        duration = token_expire - datetime.now()
        return divmod(duration.total_seconds(), 3600)[0]

class AllegroAuth:

    def get_access_code(self, client_id, api_key, redirect_uri,
                        oauth_url):
        # zmienna auth_url zawierać będzie zbudowany na podstawie podanych parametrów URL do zdobycia kodu
        auth_url = '{}/authorize' \
                   '?response_type=code' \
                   '&client_id={}' \
                   '&api-key={}' \
                   '&redirect_uri={}&prompt=none'.format(oauth_url, client_id,
                                                           api_key,
                                                           redirect_uri)

        webbrowser.open(auth_url)

        return True

    def sign_in(self, client_id, client_secret, access_code, redirect_uri, oauth_url):

        token_url = oauth_url + '/token'

        access_token_data = {'grant_type': 'authorization_code',
                             'code': access_code,
                             'redirect_uri': redirect_uri}

        response = requests.post(url=token_url,
                                 auth=requests.auth.HTTPBasicAuth(client_id,
                                                                  client_secret),
                                 data=access_token_data)

        access_token = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        expires_in = response.json()['expires_in']

        self.save_token_in_plugin_configuration(access_token, refresh_token, expires_in)


        return response.json()


    def save_token_in_plugin_configuration(self, access_token, refresh_token, expires_in):
        cleaned_data = {
            "configuration": [{"name": "token_value", "value": access_token},
                              {"name": "token_access", "value": (datetime.now() + timedelta(
                                  seconds=expires_in)).strftime("%d/%m/%Y %H:%M:%S")},
                              {"name": "refresh_token", "value": refresh_token}]
        }

        AllegroPlugin.save_plugin_configuration(
            plugin_configuration=PluginConfiguration.objects.get(
                identifier=AllegroPlugin.PLUGIN_ID), cleaned_data=cleaned_data, )

    def resolve_auth(request):
        manager = get_plugins_manager()
        plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
        allegro_auth = AllegroAuth()

        access_code = request.GET["code"]

        CLIENT_ID = plugin.config.client_id
        CLIENT_SECRET = plugin.config.client_secret
        CALLBACK_URL = plugin.config.callback_url
        DEFAULT_REDIRECT_URI = plugin.config.redirect_url

        allegro_auth.sign_in(CLIENT_ID, CLIENT_SECRET, access_code,
                             CALLBACK_URL, DEFAULT_REDIRECT_URI)

        return redirect(plugin.config.saleor_redirect_url)


class AllegroAPI:

    token = None

    def __init__(self, token):
        self.token = token


    def refresh_token(self, refresh_token, client_id, client_secret, saleor_redirect_url):

        endpoint = 'auth/oauth/token?grant_type=refresh_token&refresh_token=' + refresh_token + '&redirect_uri=' + str(saleor_redirect_url)

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri': str(saleor_redirect_url),
        }

        response = self.auth_request(endpoint=endpoint, data=data, client_id=client_id,
                                     client_secret=client_secret)

        if response.status_code is 200:
            return json.loads(response.text)['access_token'], json.loads(response.text)['refresh_token'], json.loads(response.text)['expires_in']
        else:
            return None

    def product_publish(self, saleor_product):

        config = self.get_plugin_configuration()
        env = config.get('auth_env')

        if saleor_product.private_metadata.get('publish.status') is None and saleor_product.is_published is True:

            categoryId = saleor_product.product_type.metadata[
                'allegro.mapping.categoryId']

            require_parameters = self.get_require_parameters(categoryId)

            parameters_mapper = ParametersMapperFactory().getMapper()

            parameters = parameters_mapper.set_product(
                saleor_product).set_require_parameters(require_parameters).run_mapper()

            product_mapper = ProductMapperFactory().getMapper()

            product = product_mapper.set_saleor_product(saleor_product) \
                .set_saleor_images(self.upload_images(saleor_product)) \
                .set_saleor_parameters(parameters) \
                .set_category(categoryId).run_mapper()

            offer = self.publish_to_allegro(allegro_product=product)

            if 'errors' in offer:
                print('Wystąpił bład z zapisem', offer['errors'])
                return None
            else:
                if offer['validation'].get('errors') is not None:
                    if len(offer['validation'].get('errors')) > 0:
                        print(offer['validation'].get('errors')[0]['message'], 'dla ogłoszenia: ', env + '/offer/' +  offer['id'] + '/restore')
                        self.update_status_and_publish_data_in_private_metadata(saleor_product, offer['id'], 'moderated', False)
                    else:
                        offer_publication = self.offer_publication(offer['id'])
                        self.update_status_and_publish_data_in_private_metadata(
                            saleor_product, offer['id'], 'published', True)

                return offer['id']

        if saleor_product.private_metadata.get('publish.status') == 'moderated' and saleor_product.is_published is True:

            offerId = saleor_product.private_metadata.get('publish.allegroId')
            offer = self.valid_offer(offerId)

            if offer['validation'].get('errors') is not None:
                if len(offer['validation'].get('errors')) > 0:
                    print(offer['validation'].get('errors')[0]['message'],
                          'dla ogłoszenia: ',
                          env + '/offer/' + offer[
                              'id'] + '/restore')
                    self.update_status_and_publish_data_in_private_metadata(
                        saleor_product, offer['id'], 'moderated', False)
                else:
                    self.offer_publication(
                        saleor_product.private_metadata.get('publish.allegroId'))

                    self.update_status_and_publish_data_in_private_metadata(
                        saleor_product, offer['id'], 'published', True)


    def get_plugin_configuration(self):
        manager = get_plugins_manager()
        plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
        configuration = {item["name"]: item["value"] for item in plugin.configuration}
        return configuration

    def publish_to_allegro(self, allegro_product):

        endpoint = 'sale/offers'
        response = self.post_request(endpoint=endpoint, data=allegro_product)
        return json.loads(response.text)

    def post_request(self, endpoint, data):

        config = self.get_plugin_configuration()
        env = config.get('env')
        url = env + '/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        return response

    def get_request(self, endpoint):

        config = self.get_plugin_configuration()
        env = config.get('env')
        url = env + '/' + endpoint

        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.get(url, headers=headers)

        return response

    def put_request(self, endpoint, data):

        config = self.get_plugin_configuration()
        env = config.get('env')
        url = env + '/' + endpoint

        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.put(url, data=json.dumps(data), headers=headers)

        return response

    def auth_request(self, endpoint, data, client_id, client_secret):

        config = self.get_plugin_configuration()
        env = config.get('auth_env')
        url = env + '/' + endpoint

        response = requests.post(url, auth=requests.auth.HTTPBasicAuth(client_id,
                                                                       client_secret),
                                 data=json.dumps(data))

        return response

    def valid_offer(self, offer_id):
        endpoint = 'sale/offers/' + offer_id

        response = self.get_request(endpoint)

        return json.loads(response.text)

    def get_require_parameters(self, category_id):

        endpoint = 'sale/categories/' + category_id + '/parameters'
        response = self.get_request(endpoint)
        requireParams = [param for param in json.loads(response.text)['parameters'] if
                         param['required'] == True]

        return requireParams

    def upload_images(self, saleor_product):

        images_url = ['https://saleor-test-media.s3.amazonaws.com' + pi.image.url.replace('/media', '') for pi in ProductImage.objects.filter(product=saleor_product)]

        return [self.upload_image(image_url) for image_url in images_url]

    def upload_image(self, url):
        endpoint = 'sale/images'

        data = {
            "url": url
        }

        response = self.post_request(endpoint=endpoint, data=data)
        return json.loads(response.text)['location']

    def update_status_and_publish_data_in_private_metadata(self, product, allegro_offer_id, status, is_published):
        product.store_value_in_private_metadata({'publish.status': status})
        product.store_value_in_private_metadata(
            {'publish.date': datetime.today().strftime('%Y-%m-%d-%H:%M:%S')})
        product.store_value_in_private_metadata({'publish.allegroId': str(allegro_offer_id)})
        product.is_published = is_published
        product.save(update_fields=["private_metadata", "is_published"])

    def get_detailed_offer_publication(self, offer_id):
        endpoint = 'sale/offer-publication-commands/' + str(offer_id) + '/tasks'
        response = self.get_request(endpoint=endpoint)

        return json.loads(response.text)

    def offer_publication(self, offer_id):

        endpoint = 'sale/offer-publication-commands/' + str(uuid.uuid1())
        data = {
            "publication": {
                "action": "ACTIVATE"
            },
            "offerCriteria": [
                {
                    "offers": [
                        {
                            "id": offer_id
                        }
                    ],
                    "type": "CONTAINS_OFFERS"
                }
            ]
        }
        response = self.put_request(endpoint=endpoint, data=data)

        return json.loads(response.text)


class ParametersMapper:

    def __init__(self, mapper):
        self.mapper = mapper

    def mapper(self):
        return self.mapper.map()


class BaseParametersMapper():

    def __init__(self):
        self.mapped_parameters = []

    def map(self):
        return self

    def parse_parameters_name(self, parameters):
        return parameters.lower().replace(' ', '-')

    def set_product(self, product):
        self.product = product
        return self

    def set_product_attributes(self, product_attributes):
        self.product_attributes = product_attributes
        return self

    def set_require_parameters(self, require_parameters):
        self.require_parameters = require_parameters
        return self

    def get_product_attributes(self):

        assigned_product_attributes = AssignedProductAttribute.objects.filter(
            product=self.product)

        attributes = {}

        for assigned_product_attribute in assigned_product_attributes:
            try:
                attributes[slugify(str(assigned_product_attribute.assignment.attribute.slug))] = \
                    str(AttributeValue.objects.get(assignedproductattribute=assigned_product_attribute))

            except AttributeValue.DoesNotExist:
                pass


        attributes_name = attributes.keys()

        return attributes, attributes_name

    # TODO: rebuild, too much if conditionals, and add case when dictionary is empty like for bluzki dzieciece
    def create_allegro_parameter(self, mapped_parameter_key, mapped_parameter_value):


        key = self.get_allegro_key(mapped_parameter_key)

        if key.get('dictionary') is None:
            value = self.set_allegro_typed_value(key, mapped_parameter_value)
            return value
        else:
            value = self.set_allegro_value(key, mapped_parameter_value)
            return value

    def get_allegro_key(self, key):
        param = next((param for param in self.require_parameters if
                      slugify(param["name"]) == key), None)
        return param

    def set_allegro_value(self, param, mapped_value):
        if mapped_value is not None:
            value = next((value for value in param['dictionary'] if
                      value["value"].lower() == mapped_value.lower()), None)
            if value is not None:
                return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                    "rangeValue": None}

    def set_allegro_fuzzy_value(self, param, mapped_value):
        value = next((value for value in param['dictionary'] if
                      mapped_value.lower() in value["value"].lower()), None)
        if value is not None:
            return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                "rangeValue": None}

    def set_allegro_typed_value(self, param, value):
        if param.get('dictionary') is None and value is not None:
            return {'id': param['id'], 'valuesIds': [],
                    "values": [value], "rangeValue": None}

    # TODO: rebuild, too much if conditionals
    def create_allegro_fuzzy_parameter(self, mapped_parameter_key, mapped_parameter_value):
        key = self.get_allegro_key(mapped_parameter_key)
        if key is not None:
            value = self.set_allegro_fuzzy_value(key, mapped_parameter_value)

        return value

class AllegroParametersMapper(BaseParametersMapper):

    def map(self):
        return self

    def run_mapper(self):

        attributes, attributes_name = self.get_product_attributes()

        self.set_product_attributes(attributes)

        for require_parameter in self.require_parameters:
            self.mapped_parameters.append(self.get_allegro_parameter(require_parameter['name']))

        return self.mapped_parameters

    def get_specyfic_parameter_key(self, parameter):

        if parameter == 'Materiał dominujący':
            return 'Materiał'

        map = self.product.product_type.metadata.get('allegro.mapping.attributes')
        if map is not None:
            map = [m for m in map if '*' not in m]
            if bool(map):
                return self.parse_list_to_map(map).get(parameter)


    def get_global_parameter_key(self, parameter):
        config = self.get_plugin_configuration()
        map = config.get('allegro.mapping.' + self.parse_parameters_name(parameter))
        if map is not None:
            if bool(map):
                if isinstance(map, str):
                    return self.parse_list_to_map(json.loads(map.replace('\'', '\"'))).get(parameter)
                else:
                    if isinstance(map, list):
                        return self.parse_list_to_map((map)).get(parameter)
                    else:
                        return self.parse_list_to_map(json.loads(map)).get(parameter)

    def get_global_parameter_map(self, parameter):
        config = self.get_plugin_configuration()
        map = config.get('allegro.mapping.' + parameter)
        if map is not None:
            if isinstance(map, str):
                return self.parse_list_to_map(json.loads(map.replace('\'', '\"')))
            else:
                return self.parse_list_to_map((map))

    def parse_list_to_map(self, list):
        if len(list) > 0 and len(list[0]) == 2:
            return {item[0]: item[1] for item in list}
        elif len(list) > 0 and len(list[0]) == 3:
            return {item[0]: item[2] for item in list}

    def get_plugin_configuration(self):
        manager = get_plugins_manager()
        plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
        configuration = {item["name"]: item["value"] for item in plugin.configuration}
        return configuration

    def get_mapped_parameter_value(self, parameter):
        mapped_parameter_map = self.get_global_parameter_map(parameter)
        if mapped_parameter_map is not None and mapped_parameter_map.get(self.product_attributes.get(parameter)) is not None:
            return mapped_parameter_map.get(self.product_attributes.get(parameter))

        return self.product_attributes.get(parameter)

    def get_mapped_parameter_key_and_value(self, parameter):

        mapped_parameter_key =  self.get_specyfic_parameter_key(parameter) or self.get_global_parameter_key(parameter) or parameter
        mapped_parameter_value = self.get_parameter_out_of_saleor_specyfic(str(mapped_parameter_key)) # or self.get_parameter_out_of_saleor_global(str(mapped_parameter_key))

        if mapped_parameter_value is not None:
            return mapped_parameter_key, mapped_parameter_value
        mapped_parameter_value = self.product_attributes.get(slugify(str(mapped_parameter_key)))

        return mapped_parameter_key, mapped_parameter_value

    def get_parameter_out_of_saleor_specyfic(self, parameter):
        map = self.product.product_type.metadata.get('allegro.mapping.attributes')
        if map is not None:
            map = [m for m in map if '*' in m]
            if bool(map):
                return self.parse_list_to_map(map).get(parameter)

    def get_parameter_out_of_saleor_global(self, parameter):
        mapped_parameter_map = self.get_global_parameter_map(slugify(parameter))
        if mapped_parameter_map is not None:
            return mapped_parameter_map.get("*")

    def get_value_one_to_one_global(self, parameter, value):
        mapped_parameter_map = self.get_global_parameter_map(slugify(parameter))
        if mapped_parameter_map is not None:
            return mapped_parameter_map.get(value)

    def get_universal_value_parameter(self, parameter):
        mapped_parameter_map = self.get_global_parameter_map(parameter)
        if mapped_parameter_map is not None:
            return mapped_parameter_map.get("!")

    def get_allegro_parameter(self, parameter):
        mapped_parameter_key, mapped_parameter_value = self.get_mapped_parameter_key_and_value(parameter)
        allegro_parameter = self.create_allegro_parameter(slugify(parameter), mapped_parameter_value)

        # print('get_allegro_parameter 1: ', parameter, mapped_parameter_key, mapped_parameter_value, allegro_parameter)

        if allegro_parameter is None:
            mapped_parameter_value = self.get_value_one_to_one_global(mapped_parameter_key, mapped_parameter_value)
            allegro_parameter = self.create_allegro_parameter(slugify(parameter), mapped_parameter_value)

        # print('get_allegro_parameter 2: ', parameter, mapped_parameter_key, mapped_parameter_value, allegro_parameter)

        if allegro_parameter is None:
            mapped_parameter_value = self.get_parameter_out_of_saleor_global(mapped_parameter_key)
            allegro_parameter = self.create_allegro_parameter(slugify(parameter), mapped_parameter_value)

        # print('get_allegro_parameter 3: ', parameter, mapped_parameter_key, mapped_parameter_value, allegro_parameter)

        if allegro_parameter is None:
            mapped_parameter_value = self.get_universal_value_parameter(slugify(mapped_parameter_key))
            allegro_parameter = self.create_allegro_parameter(slugify(parameter), mapped_parameter_value)

        # print('get_allegro_parameter 4: ', parameter, mapped_parameter_key, mapped_parameter_value, allegro_parameter)

        if allegro_parameter is None:
            if mapped_parameter_value is None:
                mapped_parameter_value = self.get_parameter_out_of_saleor_global(mapped_parameter_key) or self.product_attributes.get(slugify(str(mapped_parameter_key)))
            allegro_parameter = self.create_allegro_fuzzy_parameter(slugify(parameter), str(mapped_parameter_value))

        # print('get_allegro_parameter 5: ', parameter, mapped_parameter_key, mapped_parameter_value, allegro_parameter)

        return allegro_parameter


class ParametersMapperFactory:

    def getMapper(self):

        mapper = ParametersMapper(AllegroParametersMapper).mapper()
        return mapper


class ProductMapper:

    def __init__(self, mapper):
        self.mapper = mapper

    def mapper(self):
        return self.mapper.map()


class ProductMapperFactory:

    def getMapper(self):
        mapper = ProductMapper(AllegroProductMapper).mapper()
        return mapper


class AllegroProductMapper:

    def __init__(self):
        nested_dict = lambda: defaultdict(nested_dict)
        nest = nested_dict()
        self.product = nest

    def map(self):
        return self

    def set_saleor_product(self, saleor_product):
        self.saleor_product = saleor_product
        return self

    def set_implied_warranty(self, implied_warranty):
        self.product['afterSalesServices']['impliedWarranty']['id'] = implied_warranty
        return self

    def set_return_policy(self, return_policy):
        self.product['afterSalesServices']['returnPolicy']['id'] = return_policy
        return self

    def set_warranty(self, warranty):
        self.product['afterSalesServices']['warranty']['id'] = warranty
        return self

    def set_category(self, category):
        self.product['category']['id'] = category
        return self

    def set_delivery_additional_info(self, delivery_additional_info):
        self.product['delivery']['additionalInfo'] = delivery_additional_info
        return self

    def set_delivery_handling_time(self, delivery_handling_time):
        self.product['delivery']['handlingTime'] = delivery_handling_time
        return self

    def set_delivery_shipment_date(self, delivery_shipment_date):
        self.product['delivery']['shipmentDate'] = delivery_shipment_date
        return self

    def set_delivery_shipping_rates(self, delivery_shipping_rates):
        self.product['delivery']['shippingRates']['id'] = delivery_shipping_rates
        return self

    def set_location_country_code(self, location_country_code):
        self.product['location']['countryCode'] = location_country_code
        return self

    def set_location_province(self, location_province):
        self.product['location']['province'] = location_province
        return self

    def set_location_city(self, location_city):
        self.product['location']['city'] = 'Poznań'
        return self

    def set_location_post_code(self, location_post_code):
        self.product['location']['postCode'] = location_post_code
        return self

    def set_invoice(self, invoice):
        self.product['payments']['invoice'] = invoice
        return self

    def set_format(self, format):
        self.product['sellingMode']['format'] = format
        return self

    def set_starting_price_amount(self, starting_price_amount):
        self.product['sellingMode']['startingPrice']['amount'] = starting_price_amount
        return self

    def set_starting_price_currency(self, starting_price_currency):
        self.product['sellingMode']['startingPrice']['currency'] = starting_price_currency
        return self

    def set_name(self, name):
        self.product['name'] = name
        return self

    def set_saleor_images(self, saleor_images):
        self.saleor_images = saleor_images
        return self

    def set_images(self, images):

        self.product['images'] = [{'url': image} for image in images]
        return self

    def set_description(self, id):
        product_sections = []
        product_items = []

        product_items.append({
            'type': 'TEXT',
            'content': '<h1>' + id.replace('&', '&amp;') + '</h1>'
        })

        product_sections.append({'items': product_items})

        self.product['description']['sections'] = product_sections

        return self

    def set_stock_available(self, stock_available):
        self.product['stock']['available'] = stock_available
        return self

    def set_stock_unit(self, stock_unit):
        self.product['stock']['unit'] = stock_unit
        return self

    def set_publication_duration(self, publication_duration):
        self.product['publication']['duration'] = publication_duration
        return self

    def set_publication_ending_at(self, publication_ending_at):
        self.product['publication']['endingAt'] = publication_ending_at
        return self

    def set_publication_starting_at(self, publication_starting_at):
        self.product['publication']['startingAt'] = publication_starting_at
        return self

    def set_publication_status(self, publication_status):
        self.product['publication']['status'] = publication_status
        return self

    def set_publication_ended_by(self, publication_ended_by):
        self.product['publication']['endedBy'] = publication_ended_by
        return self

    def set_publication_republish(self, publication_republish):
        self.product['publication']['republish'] = publication_republish
        return self

    def set_saleor_parameters(self, saleor_parameters):
        self.saleor_parameters = saleor_parameters
        return self

    def set_parameters(self, parameters):
        self.product['parameters'] = parameters
        return self

    def set_external(self, sku):
        self.product['external']['id'] = sku
        return self

    def run_mapper(self):
        self.set_implied_warranty('59f8273f-6dff-4242-a6c2-60dd385e9525')
        self.set_return_policy('8b0ecc6b-8812-4b0f-b8a4-a0b56585c403')
        self.set_warranty('d3605a54-3cfb-4cce-8e1b-1c1adafb498c')

        self.set_delivery_additional_info('test')
        self.set_delivery_handling_time('PT72H')
        self.set_delivery_shipment_date('2020-07-25T08:03:59Z')
        self.set_delivery_shipping_rates('9d7f48de-87a3-449f-9028-d83512a17003')

        self.set_location_country_code('PL')
        self.set_location_province('WIELKOPOLSKIE')
        self.set_location_city('Pozna\u0144')
        self.set_location_post_code('60-122')

        self.set_invoice('NO_INVOICE')

        self.set_format('AUCTION')

        # TODO: zmienic na product_variant_stock.product_variant.price_amount
        self.set_starting_price_amount(
            str(self.saleor_product.minimal_variant_price_amount))

        # TODO: zmienic na product_variant_stock.product_variant.currency
        self.set_starting_price_currency('PLN')
        self.set_name(self.saleor_product.name)
        self.set_images(self.saleor_images)

        self.set_description(self.saleor_product.plain_text_description)

        # FIXME: po sprzedaniu przedmiotu na tym parametrze update?
        self.set_stock_available('1')

        self.set_stock_unit('SET')
        self.set_publication_duration('PT72H')
        self.set_publication_ending_at('')
        # self.set_publication_starting_at('2020-07-25T08:03:59Z')
        self.set_publication_status('INACTIVE')
        self.set_publication_ended_by('USER')
        self.set_publication_republish('False')

        self.set_parameters(self.saleor_parameters)
        self.set_external(str(ProductVariant.objects.filter(product=self.saleor_product).first()))
        return self.product
