import logging

import graphene
import requests
from tqdm import tqdm

from saleor.account.models import Address, User

logger = logging.getLogger(__name__)


class BaseMigration:
    @staticmethod
    def get_session(jwt_token):
        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"JWT {jwt_token}",
            }
        )
        return session

    def clear(self):
        raise NotImplementedError()

    def migrate(self, url, token):
        raise NotImplementedError()


USER_QUERY = """
query CUSTOMER {
  user(id: "user_id") {
    role
    phone
    gender
    birthday
    isFeatured
    permissionGender
        addresses {
      firstName
      lastName
      companyName
      streetAddress1
      streetAddress2
      city {
        name
      }
      postalCode
      country {
        code
      }
      countryArea
      phone
      cityArea
    }
  }
}
"""


class DataMigration(BaseMigration):
    def clear(self):
        pass

    def migrate(self, url, token):

        # Get all users from old database
        users = User.objects.using("datamigration").raw(
            """SELECT id, first_name, last_name avatar, is_staff, password,
            is_active, last_login, date_joined from account_user where email !=''"""
        )
        for user in tqdm(
            ascii=True,
            total=len(users),
            desc="User migrations",
            iterable=users.iterator(),
        ):
            created_user, created = User.objects.get_or_create(
                email=user.email,
                defaults={
                    "avatar": user.avatar,
                    "is_staff": user.is_staff,
                    "password": user.password,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "first_name": user.first_name,
                    "last_login": user.last_login,
                    "date_joined": user.date_joined,
                },
            )
            if created:
                user_global_id = graphene.Node.to_global_id("User", user.id)
                user_query = USER_QUERY.replace("user_id", user_global_id)
                response = (
                    self.get_session(jwt_token=token)
                    .post(url=url, json={"query": user_query})
                    .json()
                )
                user_data = response.get("data", {}).get("user")
                if not response.get("errors") and user_data:
                    created_user.store_value_in_private_metadata(items=user_data)
                    created_user.save(update_fields=["private_metadata"])
                    user_addresses = user_data.get("addresses", [])
                    if user_addresses:
                        for address_data in user_addresses:
                            address_data = {
                                "phone": address_data.get("phone", ""),
                                "city_area": address_data.get("cityArea", ""),
                                "last_name": address_data.get("lastName", ""),
                                "first_name": address_data.get("firstName", ""),
                                "city": address_data.get("city").get("name", ""),
                                "postal_code": address_data.get("postalCode", ""),
                                "country_area": address_data.get("countryArea", ""),
                                "company_name": address_data.get("companyName", ""),
                                "country": address_data.get("country").get("code", ""),
                                "street_address_1": address_data.get(
                                    "streetAddress1", ""
                                ),
                                "street_address_2": address_data.get(
                                    "streetAddress2", ""
                                ),
                            }
                            try:
                                address, _ = Address.objects.get_or_create(
                                    **address_data
                                )
                                created_user.addresses.add(address)
                            except Address.MultipleObjectsReturned:
                                addresses = Address.objects.filter(**address_data)
                                created_user.addresses.set(addresses)
