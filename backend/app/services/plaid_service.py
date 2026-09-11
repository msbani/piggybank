from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from app.core.config import settings

def get_plaid_client():
    configuration = Configuration(
        host="https://sandbox.plaid.com",
        api_key={
            "clientId": settings.PLAID_CLIENT_ID,
            "secret": settings.PLAID_SECRET,
        },
    )

    api_client = ApiClient(configuration)

    return plaid_api.PlaidApi(api_client)