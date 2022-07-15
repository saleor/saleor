import requests
import json
import pandas as pd

query = products(first: 50, channel: "default-channel") {
    edges {
      node {
        id: isAvailableForPurchase
        name
        description
        chargeTaxes
        availableForPurchaseAt
        created
        rating
        updatedAt
        __typename
      }
    }
  }

url = 'https://demo.saleor.io/graphql/'
r = requests.post(url, json={'query': query})
print(r.status_code)
print(r.text)

json_data = json.loads(r.text)

df_data = json_data[‘data’][‘characters’][‘results’]
df = pd.DataFrame(df_data)

