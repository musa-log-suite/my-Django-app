import requests
from django.conf import settings

MONNIFY_BASE_URL = "https://api.monnify.com/api/v1"
API_KEY = settings.MONNIFY_API_KEY
CONTRACT_CODE = settings.MONNIFY_CONTRACT_CODE

def create_virtual_account(user):
    url = f"{MONNIFY_BASE_URL}/reserved-accounts"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "accountReference": f"user-{user.id}",
        "accountName": user.get_full_name(),
        "currencyCode": "NGN",
        "contractCode": CONTRACT_CODE,
        "customerEmail": user.email,
        "customerName": user.get_full_name()
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if response.status_code == 200:
        return {
            "account_number": data['responseBody']['accountNumber'],
            "bank_name": data['responseBody']['bankName']
        }
    else:
        raise Exception(f"Monnify error: {data}")