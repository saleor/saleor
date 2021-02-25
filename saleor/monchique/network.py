import urllib3
import json
import os

BASE_URL = os.environ.get("BASE_URL", "http://localhost:4003/api")
http = urllib3.PoolManager()


##Authentication
def create_user(name, email, username, password):
    data = {'name': name, 'email': email, 'username': username, 'password': password}

    response = http.request(
        'POST', 
        f'{BASE_URL}/register', 
        body=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    
    return response.status == 201

def custom_login(email, password):
    data = {'email': email, 'password': password}

    response = http.request(
        'POST', 
        f'{BASE_URL}/sign_in', 
        body=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )

    return response.headers.get('authorization')


##Payment

def payment_authorize(mcoins, token) -> bool:
    data = {'mcoins': int(mcoins)}

    response = http.request(
        'POST', 
        f'{BASE_URL}/v1/payment/authorize', 
        body=json.dumps(data),
        headers={
            'Content-Type': 'application/json',
            'Authorization': token
        }
    )

    return json_handler(response)

def payment_capture(mcoins, tx_id, token) -> bool:
    data = {
        'mcoins': int(mcoins),
        'tx_id': tx_id
    }

    response = http.request(
        'POST', 
        f'{BASE_URL}/v1/payment/capture', 
        body=json.dumps(data),
        headers={
            'Content-Type': 'application/json',
            'Authorization': token
        }
    )

    return json_handler(response)

def payment_refund(mcoins, tx_id, token) -> bool:
    data = {
        'mcoins': int(mcoins),
        'tx_id': tx_id
    }

    response = http.request(
        'POST', 
        f'{BASE_URL}/v1/payment/refund', 
        body=json.dumps(data),
        headers={
            'Content-Type': 'application/json',
            'Authorization': token
        }
    )

    return json_handler(response)

def json_handler(response):
    json_response = json.loads(response.data)

    if response.status == 201:
        return {'is_authorized': True, 'tx_id': json_response['tx_id']}
    elif response.status == 200:
        return {'is_authorized': True}
    elif response.status == 422:
        return {'is_authorized': False, 'error_code': json_response['error_code']}
    else:
        return {'is_authorized': False, 'error_code': "operation-failed"}