# -*- coding: utf-8 -*-
# accounts.py

from typing import List, Dict
from bingads.service_client import ServiceClient
from bingads.authorization import AuthorizationData


def list_user_accounts(authorization_data: AuthorizationData) -> List[Dict]:
    """
    Returns a list of dicts:
      { 'account_id': int, 'account_name': str, 'parent_customer_id': int, 'number': str }
    """
    if authorization_data.authentication is None:
        raise ValueError("authorization_data.authentication cannot be None")
    env = authorization_data.authentication.environment
    customer_service = ServiceClient(
        service='CustomerManagementService',
        version=13,
        authorization_data=authorization_data,
        environment=env
    )

    # get user (for their Id)
    user = customer_service.GetUser(UserId=None).User

    # list
    predicate = customer_service.factory.create('ns5:Predicate')
    predicate.Field = "UserId"
    predicate.Operator = "Equals"
    predicate.Value = str(user.Id)

    paging = customer_service.factory.create('ns5:Paging')
    paging.Index = 0
    paging.Size = 1000

    result = customer_service.SearchAccounts(
        Predicates={'Predicate': [predicate]},
        Ordering=None,
        PageInfo=paging
    )

    accounts = []
    # this handles both older and newer SDK return structs
    items = []
    if hasattr(result, "Accounts") and hasattr(result.Accounts, "AdvertiserAccount"):
        items = result.Accounts.AdvertiserAccount
    elif hasattr(result, "AdvertiserAccount"):
        items = result.AdvertiserAccount

    for acct in items or []:
        accounts.append({
            "account_id": int(acct.Id),
            "account_name": acct.Name,
            "parent_customer_id": int(acct.ParentCustomerId),
            "number": getattr(acct, "Number", "")
        })

    return accounts
