from dataclasses import dataclass
from datetime import datetime
from typing import Any
from saleor.product.models import Product, AssignedProductAttribute, \
    AttributeValue
from saleor.plugins.models import PluginConfiguration
from django.shortcuts import redirect
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
import requests
import webbrowser
import csv
import json


@dataclass
class AllegroConfiguration:
    is_connected: str
    token_access: str
    token_value: str

class AllegroPlugin(BasePlugin):

    PLUGIN_ID = "allegro"
    PLUGIN_NAME = "Allegro"
    PLUGIN_NAME_2 = "Allegro"
    META_CODE_KEY = "AllegroPlugin.code"
    META_DESCRIPTION_KEY = "AllegroPlugin.description"
    DEFAULT_CONFIGURATION = [{"name": "is_connected", "value": None}, {"name": "token_access", "value": None}, {"name": "token_value", "value": None}]
    CONFIG_STRUCTURE = {
        "is_connected": {
            "type": ConfigurationTypeField.SECRET,
            "label": "Czy jest powiązdanie z Allegro?",
        },
        "token_access": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Pokazuje XXX:XXX.",
            "label": "Ważność tokena do:",
        },
        "token_value": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Access token.",
            "label": "Wartość tokena.",
        }

    }

    DEFAULT_REDIRECT_URI = 'https://allegro.pl.allegrosandbox.pl/auth/oauth'

    CLIENT_ID = '55ad2cda731c4160a001fb195bd47b2d'
    CLIENT_SECRET = '71Uv6BqXFwVnhgw828COleU1swy5ZPG0TOb0dtTcfOzj5u0EvWrapeKly4N5fMnB'
    CALLBACK_URL = 'http://localhost:8000/allegro'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = AllegroConfiguration(is_connected=configuration["is_connected"], token_access=configuration["token_access"], token_value=configuration["token_value"])

        if(configuration['token_value'] == None):
            self.get_access_code(self.CLIENT_ID, self.CLIENT_SECRET, self.CALLBACK_URL, self.DEFAULT_REDIRECT_URI)

        self._cached_taxes = {}

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
        return plugin_configuration

    def product_created(self, product: "Product", previous_value: Any) -> Any:


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


    def sign_in(self, client_id, client_secret, access_code,
                redirect_uri, oauth_url):


        token_url = oauth_url + '/token'

        access_token_data = {'grant_type': 'authorization_code',
                             'code': access_code,
                             'redirect_uri': redirect_uri}

        response = requests.post(url=token_url,
                                 auth=requests.auth.HTTPBasicAuth(client_id, client_secret), data=access_token_data)
        access_token = response.json()['access_token']

        print('accessToken: ' + access_token)

        cleaned_data = {
            "configuration": [{"name": "token_value", "value": access_token}]}

        self.save_plugin_configuration(plugin_configuration=PluginConfiguration.objects.get(
            identifier=AllegroPlugin.PLUGIN_ID), cleaned_data=cleaned_data, )




        return response.json()


    def resolve_auth(request):

        access_code = request.GET["code"]

        CLIENT_ID = '55ad2cda731c4160a001fb195bd47b2d'
        CLIENT_SECRET = '71Uv6BqXFwVnhgw828COleU1swy5ZPG0TOb0dtTcfOzj5u0EvWrapeKly4N5fMnB'
        CALLBACK_URL = 'http://localhost:8000/allegro'
        DEFAULT_REDIRECT_URI = 'https://allegro.pl.allegrosandbox.pl/auth/oauth'

        AllegroPlugin.sign_in(AllegroPlugin, CLIENT_ID,
                              CLIENT_SECRET, access_code,
                              CALLBACK_URL, DEFAULT_REDIRECT_URI)


        return redirect('http://localhost:9000')


class AllegroAPI:

    def get_allegro_dictionary(self, slug):

        PATH = '/Users/patryk/data_with_slug.csv'

        input_file = csv.DictReader(open(PATH))
        for row in input_file:
            if row['slug'] == slug:
                return row

    def search_category_in_allegro_dictionary(self, slug):
        self.get_allegro_dictionary()


    def product_created(self, product: "Product", previous_value: Any) -> Any:

        product = Product.objects.get(name=product)

        # print('Is published ', ['http://localhost:8000' + pi.image.url for pi in ProductImage.objects.filter(product=product)])

        if product.private_metadata.get('publish.target') and product.private_metadata.get('publish.target') == 'allegro'\
                and product.private_metadata.get('publish.status') == 'unpublished':

            slug = '-'.join(product.product_type.slug.split('-')[0:-1])

            category_id = self.get_allegro_dictionary(slug)['index']

            attributes, attributes_name = self.get_product_attributes(product=product)
            require_params = self.get_apriopriate_paremeters_for_category(category_id)
            missing_parameters = self.assign_missing_categories(require_params, attributes_name)
            parameters = self.assign_parameter_to_allegro_parameter(attributes=attributes, require_params=require_params)
            parameters = self.append_missing_categories(parameters, missing_parameters)
            allegro_product = self.create_allegro_api_product(product=product, parameters=parameters, category_id=category_id)
            offer = self.publish_product(allegro_product=allegro_product)


            if 'errors' in offer:
                print('Wystąpił bład z zapisem', offer['errors'])
            else:
                self.update_status_and_publish_data_in_private_metadata(product)
                offer_publication = self.offer_publication(offer['id'])
        else:
            self.set_allegro_private_metadata(product)



    def publish_product(self, allegro_product):

        test_api_url_test = 'https://api.allegro.pl.allegrosandbox.pl/sale/offers'

        api_call_headers = {'Authorization': 'Bearer ' + self.config.token_value,
                            'Accept': 'application/vnd.allegro.public.v1+json',
                            'Content-Type': 'application/vnd.allegro.public.v1+json'}

        api_call_response_test = requests.post(test_api_url_test,
                                               data=json.dumps(allegro_product),
                                               headers=api_call_headers)

        return json.loads(api_call_response_test.text)



    def get_allegro_category_id(self):
        pass

    def assign_parameter_to_allegro_parameter(self, attributes, require_params):

        params = []

        for atr in attributes:
            param = next((param for param in require_params if
                          param["name"].split(' ')[0] ==
                          str(atr.get('name')).split(' ')[0]), False)
            value = next((value for value in param['dictionary'] if
                          value["value"] == str(atr.get('value'))), False)
            params.append({'id': param['id'], 'valuesIds': [value['id']], "values": [],
                           "rangeValue": None})


        return params



    def append_missing_categories(self, parameters, missing_parameters):

        for missing_parameter in missing_parameters:
            parameters.append(missing_parameter)

        return parameters

    def get_apriopriate_paremeters_for_category(self, category_id):

        test_api_url = 'https://api.allegro.pl.allegrosandbox.pl/sale/categories/' + category_id + '/parameters'

        api_call_headers = {'Authorization': 'Bearer ' + self.config.token_value,
                            'Accept': 'application/vnd.allegro.public.v1+json',
                            'Content-Type': 'application/vnd.allegro.public.v1+json'}

        api_call_response = requests.get(test_api_url, headers=api_call_headers)

        requireParams = [param for param in json.loads(api_call_response.text)['parameters'] if param['required'] == True]

        return requireParams

    def assign_missing_categories(self, require_params, attributes_name):


        params = []

        for rp in require_params:
            if rp['name'] not in attributes_name:
                if(rp['name'] == 'Materiał dominujący'):
                    pass
                else:
                    params.append({"id": rp['id'], "valuesIds": [rp['dictionary'][0]['id']], "values": [], "rangeValue": None})

        return params

    def create_allegro_api_product(self, product, parameters, category_id):

        allegro_product = {}

        allegro_product['afterSalesServices'] = {}
        allegro_product['afterSalesServices']['impliedWarranty'] = {"id": "59f8273f-6dff-4242-a6c2-60dd385e9525"}
        allegro_product['afterSalesServices']['returnPolicy'] = {"id": "8b0ecc6b-8812-4b0f-b8a4-a0b56585c403"}
        allegro_product['afterSalesServices']['warranty'] = {"id": "d3605a54-3cfb-4cce-8e1b-1c1adafb498c"}
        allegro_product['category'] = {}
        allegro_product['delivery'] = {}
        allegro_product['delivery']['additionalInfo'] = 'test'
        allegro_product['delivery']['handlingTime'] = 'PT72H'
        allegro_product['delivery']['shipmentDate'] = '2020-07-20T08:03:59Z'
        allegro_product['delivery']['shippingRates'] = { "id": "9d7f48de-87a3-449f-9028-d83512a17003" }
        allegro_product['location'] = {}
        allegro_product['location']['countryCode'] = 'PL'
        allegro_product['location']['province'] = 'WIELKOPOLSKIE'
        allegro_product['location']['city'] = 'Poznań'
        allegro_product['location']['postCode'] = '60-122'
        allegro_product['payments']= {}
        allegro_product['payments']['invoice'] = 'NO_INVOICE'
        allegro_product['sellingMode'] = {}
        allegro_product['sellingMode']['format'] = 'AUCTION'
        allegro_product['sellingMode']['startingPrice'] = {}
        allegro_product['sellingMode']['startingPrice']['amount'] = str(product.minimal_variant_price_amount)
        allegro_product['sellingMode']['startingPrice']['currency'] = 'PLN'
        allegro_product['name'] = product.name


        allegro_product['images'] = [
                {
                    "url": self.upload_images()
                }]

        allegro_product['description'] = {}

        product_sections = []
        product_items = []


        product_items.append({
            'type': 'TEXT',
            'content': '<h1>' + product.plain_text_description + '</h1>'
        })

        product_sections.append({'items': product_items})

        allegro_product['description']['sections'] = product_sections


        allegro_product['stock'] = {}
        allegro_product['stock']['available'] = 1
        allegro_product['stock']['unit'] = 'SET'

        allegro_product['publication'] = {}
        allegro_product['publication']['duration'] = 'PT72H'
        allegro_product['publication']['endingAt'] = ''
        allegro_product['publication']['startingAt'] = '2020-07-20T08:03:59Z'
        allegro_product['publication']['status'] = 'INACTIVE'
        allegro_product['publication']['endedBy'] = 'USER'
        allegro_product['publication']['republish'] = 'False'
        allegro_product['parameters'] = []
        allegro_product['parameters'] = parameters
        allegro_product['category'] = {'id': category_id}

        print(allegro_product)
        return allegro_product

    def get_product_attributes(self, product):

        assigned_product_attributes = AssignedProductAttribute.objects.filter(
            product=product)

        attributes = []

        for assigned_product_attribute in assigned_product_attributes:
            try:
                attributes.append({'name': assigned_product_attribute.assignment.attribute,
                               'value': AttributeValue.objects.get(
                                   assignedproductattribute=assigned_product_attribute)})
            except AttributeValue.DoesNotExist:
                pass


        attributes_name = [str(attribute['name']).split(' ')[0] for attribute in attributes]

        return attributes, attributes_name

    def upload_images(self):

        url = 'https://api.allegro.pl.allegrosandbox.pl/sale/images'

        headers = {'Authorization': 'Bearer ' + self.config.token_value,
                            'Accept': 'application/vnd.allegro.public.v1+json',
                            'Content-Type': 'application/vnd.allegro.public.v1+json'}

        data = {
             "url": "https://cdn.shoplo.com/0986/products/th2048/bca3/197520-eleganckie-body-z-dekoltem-v.jpg"
        }


        api_call_response = requests.post(url, data=json.dumps(data), headers=headers)

        return json.loads(api_call_response.text)['location']

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

        test_api_url = 'https://api.allegro.pl.allegrosandbox.pl/sale/offer-publication-commands/' + offer_id

        api_call_headers = {'Authorization': 'Bearer ' + self.config.token_value,
                            'Accept': 'application/vnd.allegro.public.v1+json',
                            'Content-Type': 'application/vnd.allegro.public.v1+json'}

        api_call_response = requests.get(test_api_url, headers=api_call_headers)

        return json.loads(api_call_response.text)
