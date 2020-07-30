import json
import uuid
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import requests
from django.shortcuts import redirect

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from saleor.plugins.manager import get_plugins_manager
from saleor.plugins.models import PluginConfiguration
from saleor.product.models import Product, AssignedProductAttribute, \
    AttributeValue


@dataclass
class AllegroConfiguration:
    redirect_url: str
    callback_url: str
    token_access: str
    token_value: str
    client_id: str
    client_secret: str


class AllegroPlugin(BasePlugin):

    PLUGIN_ID = "allegro"
    PLUGIN_NAME = "Allegro"
    PLUGIN_NAME_2 = "Allegro"
    META_CODE_KEY = "AllegroPlugin.code"
    META_DESCRIPTION_KEY = "AllegroPlugin.description"
    DEFAULT_CONFIGURATION = [{"name": "redirect_url", "value": None}, {"name": "callback_url", "value": None}, {"name": "token_access", "value": None}, {"name": "token_value", "value": None},
                             {"name": "client_id", "value": None}, {"name": "client_secret", "value": None}]
    CONFIG_STRUCTURE = {
        "redirect_url": {
            "type": ConfigurationTypeField.STRING,
            "label": "Podaj redirect URL?",
        },
        "callback_url": {
            "type": ConfigurationTypeField.STRING,
            "label": "Podaj callback URL?",
        },
        "token_access": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Wartość uzupełni się automatycznie.",
            "label": "Ważność tokena do:",
        },
        "token_value": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Access token.",
            "label": "Wartość tokena.",
        },
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "Access token.",
            "label": "Wartość id klienta allegro.",
        },
        "client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Access token.",
            "label": "Wartość klucza.",
        }

    }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = AllegroConfiguration(redirect_url=configuration["redirect_url"], callback_url=configuration["callback_url"], token_access=configuration["token_access"], token_value=configuration["token_value"],
                                           client_id=configuration["client_id"], client_secret=configuration["client_secret"])


    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        access_key = configuration.get("Access key")

    @classmethod
    def save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration", cleaned_data):

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

        configuration = {item["name"]: item["value"] for item in plugin_configuration.configuration}

        if(plugin_configuration.active == True and not configuration['token_value'] and bool(configuration['client_id']) and bool(configuration['client_secret'])):
            allegro_auth = AllegroAuth()
            allegro_auth.get_access_code(configuration['client_id'], configuration['client_secret'], configuration['callback_url'], configuration['redirect_url'])

        return plugin_configuration



    def product_created(self, product: "Product", previous_value: Any) -> Any:

        allegro_api = AllegroAPI(self.config.token_value)
        allegro_api.product_publish(saleor_product=product)

class AllegroAuth:

    def get_access_code(self, client_id, api_key, redirect_uri,
                        oauth_url):
        # zmienna auth_url zawierać będzie zbudowany na podstawie podanych parametrów URL do zdobycia kodu
        auth_url = '{}/authorize' \
                   '?response_type=code' \
                   '&client_id={}' \
                   '&api-key={}' \
                   '&redirect_uri={}&prompt=confim'.format(oauth_url, client_id, api_key,
                                                         redirect_uri)

        webbrowser.open(auth_url)

        return True


    def sign_in(self, client_id, client_secret, access_code, redirect_uri, oauth_url):


        token_url = oauth_url + '/token'

        access_token_data = {'grant_type': 'authorization_code',
                             'code': access_code,
                             'redirect_uri': redirect_uri}

        response = requests.post(url=token_url,
                                 auth=requests.auth.HTTPBasicAuth(client_id, client_secret), data=access_token_data)
        access_token = response.json()['access_token']

        print('accessToken: ' + access_token)

        cleaned_data = {
            "configuration": [{"name": "token_value", "value": access_token}, {"name": "token_access", "value": (datetime.now() + timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")}]}

        AllegroPlugin.save_plugin_configuration(plugin_configuration=PluginConfiguration.objects.get(
            identifier=AllegroPlugin.PLUGIN_ID), cleaned_data=cleaned_data, )

        return response.json()


    def resolve_auth(request):


        manager = get_plugins_manager()
        plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
        allegro_auth = AllegroAuth()

        access_code = request.GET["code"]

        CLIENT_ID = plugin.config.client_id
        CLIENT_SECRET = plugin.config.client_secret
        CALLBACK_URL = plugin.config.callback_url
        DEFAULT_REDIRECT_URI = plugin.config.redirecturl


        allegro_auth.sign_in(CLIENT_ID, CLIENT_SECRET, access_code,
                              CALLBACK_URL, DEFAULT_REDIRECT_URI)


        return redirect('http://localhost:9000')


class AllegroAPI:

    token = None

    def __init__(self, token):
        self.token = token


    # def get_category(self, id):
    #
    #     path = '/Users/patryk/data_with_ids.csv'
    #
    #     dictionary_with_categories = csv.DictReader(open(path), delimiter=';')
    #     category = next(filter(lambda p: p['id'] == str(id), dictionary_with_categories), None)
    #
    #     return category


    def product_publish(self, saleor_product) :

        # print('Is published ', ['http://localhost:8000' + pi.image.url for pi in ProductImage.objects.filter(product=product)])

        if saleor_product.private_metadata.get('publish.target') and saleor_product.private_metadata.get('publish.target') == 'allegro'\
                and saleor_product.private_metadata.get('publish.status') == 'unpublished':

            categoryId = saleor_product.product_type.metadata['allegro.mapping.categoryId']

            require_parameters = self.get_require_parameters(categoryId)

            parameters_mapper = ParametersMapperFactory().getMapper(saleor_product.product_type)

            parameters = parameters_mapper.set_product(saleor_product).set_require_parameters(require_parameters).run_mapper()

            product_mapper = ProductMapperFactory().getMapper()

            product = product_mapper.set_saleor_product(saleor_product) \
                .set_saleor_images(self.upload_images())\
                .set_saleor_parameters(parameters)\
                .set_category(categoryId).run_mapper()



            offer = self.publish_to_allegro(allegro_product=product)

            if 'errors' in offer:
                print('Wystąpił bład z zapisem', offer['errors'])
            else:
                self.update_status_and_publish_data_in_private_metadata(saleor_product)
                offer_publication = self.offer_publication(offer['id'])
        else:
            self.set_allegro_private_metadata(saleor_product)



    def publish_to_allegro(self, allegro_product):

        endpoint = 'sale/offers'
        response = self.post_request(endpoint=endpoint, data=allegro_product)
        return json.loads(response.text)

    def post_request(self, endpoint, data):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        return response

    def get_request(self, endpoint):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.get(url, headers=headers)

        return response

    def put_request(self, endpoint, data):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.put(url, data=json.dumps(data), headers=headers)

        return response


    def get_require_parameters(self, category_id):

        endpoint = 'sale/categories/' + category_id + '/parameters'
        response = self.get_request(endpoint)
        requireParams = [param for param in json.loads(response.text)['parameters'] if param['required'] == True]

        return requireParams



    def upload_images(self):

        endpoint = 'sale/images'

        data = {
             "url": "https://cdn.shoplo.com/0986/products/th2048/bca3/197520-eleganckie-body-z-dekoltem-v.jpg"
        }

        response = self.post_request(endpoint=endpoint, data=data)

        return json.loads(response.text)['location']

    def update_status_and_publish_data_in_private_metadata(self, product):

        product.store_value_in_private_metadata({'publish.status': 'published'})
        product.store_value_in_private_metadata({'publish.date': datetime.today().strftime('%Y-%m-%d-%H:%M:%S')})
        product.save(update_fields=["private_metadata"])

    def set_allegro_private_metadata(self, product):

        product.store_value_in_private_metadata({'publish.target': 'allegro'})
        product.store_value_in_private_metadata({'publish.status': 'unpublished'})
        product.store_value_in_private_metadata({'publish.date': ''})
        product.save(update_fields=["private_metadata"])

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


class SimpleParametersMapper():

    def __init__(self):
        self.mapped_parameters = []

    def map(self):
        return self

    def set_product(self, product):
        self.product = product
        return self

    def set_product_attributes(self, product_attributes):
        self.product_attributes = product_attributes
        return self

    def set_require_parameters(self, require_parameters):
        self.require_parameters = require_parameters
        return self

    def map_state(self):

        PARAMETER_NAME = 'Stan'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_brand(self):

        PARAMETER_NAME = 'Marka'

        # ze względu na nazwy atrybutow Marka odzież damska, Marka odzież meska robimy splita do 'Marka'

        if PARAMETER_NAME in [attributes['name'].split(' ')[0] for attributes in self.product_attributes]:


            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"].split(' ')[0] == PARAMETER_NAME), False)

            attribute['name'] = attribute['name'].split(' ')[0]


            if(str(self.product.product_type) == 'Biustonosz' and attribute['value'] == 'inne'):
                attribute['value'] = 'Inna marka'
            if(str(self.product.product_type) == 'Bluza damska' and attribute['value'] == 'inne'):
                attribute['value'] = 'inna'
            if (str(self.product.product_type) == 'Bluzka damska' and attribute['value'] == 'inne'):
                attribute['value'] = 'inna'
            if (str(self.product.product_type) == 'Bluzka dziecięca' and attribute['value'] == 'inne'):
                attribute['value'] = 'Inna marka'
            if (str(self.product.product_type) == 'Bluza dziecięca' and attribute['value'] == 'inne'):
                attribute['value'] = 'Inna marka'

            if (attribute['value'] == 'Marks & Spencer'):
                attribute['value'] = 'Marks&Spencer'


            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_size(self):


        PARAMETER_NAME = 'Rozmiar'


        if str(self.product.product_type) == 'Bluzka dziecięca':
            return self.map_kids_size()

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            try:
                self.mapped_parameters.append(self.assign_parameter(attribute))
            except TypeError:
                attribute['value'] = self.product.product_type.metadata['allegro.mapping.size'][attribute['value']]
                self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_kids_size(self):

        SALEOR_PARAMETER_NAME = 'Rozmiar dzieci'

        PARAMETER_NAME = 'Rozmiar'


        if SALEOR_PARAMETER_NAME in [attributes['name'] for attributes in
                              self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == SALEOR_PARAMETER_NAME), False)

            attribute['value'] = json.loads(self.product.product_type.metadata['allegro.mapping.size'].replace('\'', "\""))[attribute['value']]

            attribute['name'] = PARAMETER_NAME

            self.mapped_parameters.append(self.assign_kids_size_parameter(attribute))

        return self

    def map_fashion(self):


        PARAMETER_NAME = 'Fason'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))

        else:
            if (str(self.product.product_type) == 'Bluzka damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny'))
            else:
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))


        return self


    def map_set(self):


        PARAMETER_NAME = 'Zestaw'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))

        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self


    def map_pattern(self):

        PARAMETER_NAME = 'Wzór dominujący'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value = 'inny wzór'))

        return self

    def map_color(self):

        PARAMETER_NAME = 'Kolor'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if attribute["name"] == PARAMETER_NAME), False)

            if attribute['value'] == 'brązowy' or attribute['value'] == 'beżowy':
                attribute['value'] = 'brązowy, beżowy'
            if attribute['value'] == 'żółty' or attribute['value'] == 'złoty':
                attribute['value'] = 'żółty, złoty'
            if attribute['value'] == 'szary' or attribute['value'] == 'srebrny':
                attribute['value'] = 'szary, srebrny'

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_material(self):

        PARAMETER_NAME = 'Materiał dominujący'
        SALEOR_PARAMETER_NAME = 'Materiał'

        if SALEOR_PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == SALEOR_PARAMETER_NAME), False)

            if(str(self.product.product_type) == 'Bluza damska'):
                attribute['name'] = PARAMETER_NAME
            if (str(self.product.product_type) == 'Bluzka damska'):
                attribute['name'] = PARAMETER_NAME
            if (str(self.product.product_type) == 'Bluzka dziecięca'):
                attribute['name'] = PARAMETER_NAME
            if (str(self.product.product_type) == 'Bluza dziecięca'):
                attribute['name'] = PARAMETER_NAME

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value = 'inny'))

        return self

    def map_clasp(self):

        PARAMETER_NAME = 'Zapięcie'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:


            if(str(self.product.product_type) == 'Biustonosz'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='zapięcie z tyłu'))
            elif(str(self.product.product_type) == 'Bluza damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inne'))
            elif (str(self.product.product_type) == 'Bluzka damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inne'))
            else:
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_type(self):

        PARAMETER_NAME = 'Rodzaj'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            if(str(self.product.product_type) == 'Biustonosz'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value = 'Inny typ'))
            elif (str(self.product.product_type) == 'Bluza damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny'))
            elif (str(self.product.product_type) == 'Bluzka damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny'))
            else:
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_features(self):

        PARAMETER_NAME = 'Cechy dodatkowe'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            if (str(self.product.product_type) == 'Bluza damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='brak'))
            elif (str(self.product.product_type) == 'Bluzka damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='brak'))
            else:
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_neckline(self):

        PARAMETER_NAME = 'Dekolt'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            if (str(self.product.product_type) == 'Bluza damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny'))
            elif (str(self.product.product_type) == 'Bluzka damska'):
                    self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny'))
            else:
                self.mapped_parameters.append(
                    self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_sleeve(self):

        PARAMETER_NAME = 'Rękaw'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            if (str(self.product.product_type) == 'Bluza damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny rękaw'))
            elif (str(self.product.product_type) == 'Bluzka damska'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='inny rękaw'))
            elif (str(self.product.product_type) == 'Bluzka dziecięca'):
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME, value='Inny'))
            else:
                self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_midsection(self):

        PARAMETER_NAME = 'Stan (wysokość w pasie)'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self


    def map_inseam(self):

        PARAMETER_NAME = 'Długość nogawki'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_length(self):

        PARAMETER_NAME = 'Długość'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_occasion(self):

        PARAMETER_NAME = 'Okazja'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_style(self):

        PARAMETER_NAME = 'Styl'

        if PARAMETER_NAME in [attributes['name'] for attributes in
                              self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self


    def get_product_attributes(self):

        assigned_product_attributes = AssignedProductAttribute.objects.filter(
            product=self.product)

        attributes = []

        for assigned_product_attribute in assigned_product_attributes:
            try:
                attributes.append(
                    {'name': str(assigned_product_attribute.assignment.attribute),
                     'value': str(AttributeValue.objects.get(
                         assignedproductattribute=assigned_product_attribute))})
            except AttributeValue.DoesNotExist:
                pass

        attributes_name = [str(attribute['name']).split(' ')[0] for attribute in
                           attributes]

        return attributes, attributes_name

    def run_mapper(self):

        product_attributes, product_attributes_name = self.get_product_attributes()

        self.set_product_attributes(product_attributes)

    def assign_parameter(self, atr):

        param = next((param for param in self.require_parameters if
                      param["name"] ==
                      str(atr.get('name'))), False)
        value = next((value for value in param['dictionary'] if
                      value["value"] == str(atr.get('value'))), False)

        return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                "rangeValue": None}

    def assign_kids_size_parameter(self, atr):

        param = next((param for param in self.require_parameters if
                      param["name"] ==
                      str(atr.get('name'))), False)

        return {'id': param['id'], 'valuesIds': [], "values": [atr['value']],
                "rangeValue": None}

    def assign_missing_parameter(self, name, *args, **kwargs):

        param = next((param for param in self.require_parameters if
                      param["name"] == name), False)

        if(kwargs.get('value', None)):
            value = next((value for value in param['dictionary'] if
                          value["value"] == kwargs.get('value', None)), False)
        else:
            value = param['dictionary'][0]

        return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                "rangeValue": None}

class ComplexParametersMapper(SimpleParametersMapper):

    def map(self):
        return self

    def run_mapper(self):

        attributes, attributes_name = self.get_product_attributes()

        self.set_product_attributes(attributes)

        for require_parameter in self.require_parameters:
            self.assign_mapper(require_parameter['name'])

        return self.mapped_parameters

    def append_missing_categories(self, parameters, missing_parameters):

        for missing_parameter in missing_parameters:
            parameters.append(missing_parameter)

        return parameters

    def assign_mapper(self, parameter):

        if parameter == 'Stan':
            self.map_state()

        if parameter == 'Marka':
            self.map_brand()

        if parameter == 'Rozmiar':
            self.map_size()

        if parameter == 'Kolor':
            self.map_color()

        if parameter == 'Fason':
            self.map_fashion()

        if parameter == 'Zestaw':
            self.map_set()

        if parameter == 'Wzór dominujący':
            self.map_pattern()

        if parameter == 'Materiał dominujący':
            self.map_material()

        if parameter == 'Cechy dodatkowe':
            self.map_features()

        if parameter == 'Zapięcie':
            self.map_clasp()

        if parameter == 'Rodzaj':
            self.map_type()

        if parameter == 'Dekolt':
            self.map_neckline()

        if parameter == 'Rękaw':
            self.map_sleeve()

        if parameter == 'Stan (wysokość w pasie)':
            self.map_midsection()

        if parameter == 'Długość nogawki':
            self.map_inseam()

        if parameter == 'Długość':
            self.map_length()

        if parameter == 'Okazja':
            self.map_occasion()

        if parameter == 'Styl':
            self.map_style()


class ParametersMapperFactory:

    def getMapper(self, category):

        if category == 'Body':
            mapper = ParametersMapper(SimpleParametersMapper).mapper()
            return mapper

        if category == 'Majtki':
            mapper = ParametersMapper(ComplexParametersMapper).mapper()
            return mapper

        else:
            mapper = ParametersMapper(ComplexParametersMapper).mapper()
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

    def set_implied_warranty(self, id):
        self.product['afterSalesServices']['impliedWarranty']['id'] = id
        return self

    def set_return_policy(self, id):
        self.product['afterSalesServices']['returnPolicy']['id'] = id
        return self

    def set_warranty(self, id):
        self.product['afterSalesServices']['warranty']['id'] = id
        return self

    def set_category(self, category):
        self.product['category']['id'] = category
        return self

    def set_delivery_additional_info(self, id):
        self.product['delivery']['additionalInfo'] = id
        return self

    def set_delivery_handling_time(self, id):
        self.product['delivery']['handlingTime'] = id
        return self

    def set_delivery_shipment_date(self, id):
        self.product['delivery']['shipmentDate'] = id
        return self

    def set_delivery_shipping_rates(self, id):
        self.product['delivery']['shippingRates']['id'] = id
        return self

    def set_location_country_code(self, id):
        self.product['location']['countryCode'] = id
        return self

    def set_location_province(self, id):
        self.product['location']['province'] = id
        return self

    def set_location_city(self, id):
        self.product['location']['city'] = 'Poznań'
        return self

    def set_location_post_code(self, id):
        self.product['location']['postCode'] = id
        return self

    def set_invoice(self, id):
        self.product['payments']['invoice'] = id
        return self

    def set_format(self, id):
        self.product['sellingMode']['format'] = id
        return self

    def set_starting_price_amount(self, id):
        self.product['sellingMode']['startingPrice']['amount'] = id
        return self

    def set_starting_price_currency(self, id):
        self.product['sellingMode']['startingPrice']['currency'] = id
        return self

    def set_name(self, id):
        self.product['name'] = id
        return self

    def set_saleor_images(self, id):
        self.saleor_images = id
        return self

    def set_images(self, id):

        self.product['images'] = [{'url': id}]
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

    def set_stock_available(self, id):
        self.product['stock']['available'] = id
        return self

    def set_stock_unit(self, id):
        self.product['stock']['unit'] = id
        return self

    def set_publication_duration(self, id):
        self.product['publication']['duration'] = id
        return self

    def set_publication_ending_at(self, id):
        self.product['publication']['endingAt'] = id
        return self

    def set_publication_starting_at(self, id):
        self.product['publication']['startingAt'] = id
        return self

    def set_publication_status(self, id):
        self.product['publication']['status'] = id
        return self

    def set_publication_ended_by(self, id):
        self.product['publication']['endedBy'] = id
        return self

    def set_publication_republish(self, id):
        self.product['publication']['republish'] = id
        return self

    def set_saleor_parameters(self, id):
        self.saleor_parameters = id
        return self

    def set_parameters(self, id):
        self.product['parameters'] = id
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

        self.set_starting_price_amount(str(self.saleor_product.minimal_variant_price_amount))
        self.set_starting_price_currency('PLN')
        self.set_name(self.saleor_product.name)
        self.set_images(self.saleor_images)

        self.set_description(self.saleor_product.plain_text_description)

        # FIXME: po sprzedaniu przedmiotu na tym parametrze update?
        self.set_stock_available('1')

        self.set_stock_unit('SET')
        self.set_publication_duration('PT72H')
        self.set_publication_ending_at('')
        self.set_publication_starting_at('2020-07-25T08:03:59Z')
        self.set_publication_status('INACTIVE')
        self.set_publication_ended_by('USER')
        self.set_publication_republish('False')

        self.set_parameters(self.saleor_parameters)

        return self.product
