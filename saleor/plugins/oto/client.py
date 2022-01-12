import requests
from sympy.core.singleton import Singleton


class OTOApiClient(metaclass=Singleton):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.api_key),
            }
        )

    @staticmethod
    def get_oto_url(path):
        return f"https://api.tryoto.com/rest/v2/{path}"

    def get_oto_token(self):
        return

    def create_oto_order(self, order_data):
        url = self.get_oto_url("createOrder")
        return self.session.post(url, json=order_data).json()
