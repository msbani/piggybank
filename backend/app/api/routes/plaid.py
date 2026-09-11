from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import (
    LinkTokenCreateRequestUser,
)
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

from app.services.plaid_service import get_plaid_client

from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.transactions_sync_request import (
    TransactionsSyncRequest,
)

from plaid.model.accounts_get_request import AccountsGetRequest
from app.core.encryption import encrypt_value
from app.db.database import get_db
from app.models.linked_account import LinkedAccount
from app.models.transaction import Transaction
from app.schemas.plaid import PublicTokenExchangeRequest

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter(
    prefix="/plaid",
    tags=["Plaid"],
)

@router.post("/create_link_token")
async def create_link_token(
    current_user: User = Depends(get_current_user),
):
    client = get_plaid_client()

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(
            client_user_id=str(current_user.id),
        ),
        client_name="PiggyBank",
        products=[
            Products('transactions'),
        ],
        country_codes=[
            CountryCode("US"),
        ],
        language="en",
    )

    response = client.link_token_create(request)

    return {
        "link_token": response.link_token,
    }

@router.post("/exchange_public_token")
async def exchange_public_token(
    data: PublicTokenExchangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = get_plaid_client()

    request = ItemPublicTokenExchangeRequest(
        public_token=data.public_token,
    )

    response = client.item_public_token_exchange(
        request
    )

    access_token = response.access_token
    item_id = response.item_id

    encrypted_access_token = encrypt_value(
        access_token
    )

    accounts_response = client.accounts_get(
        AccountsGetRequest(
            access_token=access_token
        )
    )

    accounts = accounts_response.accounts

    accounts_by_plaid_id: dict[str, LinkedAccount] = {}

    for account in accounts:
        linked_account = LinkedAccount(
            user_id=current_user.id,
            institution_name="Plaid Sandbox",
            account_name=account.name,
            account_type=str(account.type),
            last_four=account.mask,
            plaid_item_id=item_id,
            plaid_account_id=account.account_id,
            access_token_encrypted=encrypted_access_token,
        )

        db.add(linked_account)
        accounts_by_plaid_id[account.account_id] = linked_account

    # Flush (without committing) so the linked accounts get real primary
    # keys we can use as Transaction.account_id below.
    await db.flush()

    sync_response = client.transactions_sync(
        TransactionsSyncRequest(
            access_token=access_token,
        )
    )

    transactions_synced = 0

    for added_transaction in sync_response.added:
        linked_account = accounts_by_plaid_id.get(
            added_transaction.account_id
        )

        if linked_account is None:
            continue

        transaction = Transaction(
            account_id=linked_account.id,
            amount=added_transaction.amount,
            transaction_type=(
                "debit" if added_transaction.amount > 0 else "credit"
            ),
            description=added_transaction.name,
            merchant=(
                added_transaction.merchant_name
                or added_transaction.name
            ),
            category=(
                ", ".join(added_transaction.category)
                if added_transaction.category
                else None
            ),
            transaction_date=datetime.combine(
                added_transaction.date,
                datetime.min.time(),
            ),
            plaid_transaction_id=added_transaction.transaction_id,
        )

        db.add(transaction)
        transactions_synced += 1

    await db.commit()

    return {
        "accounts_synced": len(accounts),
        "transactions_synced": transactions_synced,
    }