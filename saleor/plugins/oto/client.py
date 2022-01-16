import requests
from sympy.core.singleton import Singleton


class OTOApiClient(metaclass=Singleton):
    def __init__(self, access_token):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
        )

    @staticmethod
    def get_oto_url(path):
        return f"https://api.tryoto.com/rest/v2/{path}"

    def create_oto_order(self, order_data):
        url = self.get_oto_url("createOrder")
        return self.session.post(url, json=order_data).json()

    def cancel_oto_order(self, order_data):
        url = self.get_oto_url("cancelOrder")
        return self.session.post(url, json=order_data).json()

    def get_oto_order_return_link(self, order_data):
        url = self.get_oto_url("getReturnLink")
        return self.session.post(url, json=order_data).json()
