"""
Migration script to convert data from v1 to v2.
"""

import argparse
from typing import Callable, Literal

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from redbaby.pyobjectid import PyObjectId
from tqdm import tqdm

from tauth.authproviders.models import AuthProviderDAO
from tauth.entities.models import EntityDAO, EntityRef
from tauth.entities.schemas import EntityIntermediate
from tauth.legacy.tokens import TokenDAO
from tauth.schemas import Creator, Infostar
from tauth.schemas.attribute import Attribute

OID = PyObjectId()
MY_IP = "127.0.0.1"
MY_EMAIL = "sysadmin@teialabs.com"


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, required=True, help="MongoDB host.")
    parser.add_argument("--port", type=int, default="27017", help="MongoDB port.")
    parser.add_argument(
        "--in_db", type=str, default="tauth", help="MongoDB input database."
    )
    parser.add_argument(
        "--out_db", type=str, default="tauth-v2", help="MongoDB output database."
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run.")
    args = parser.parse_args()
    return args


class Partial:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self.func(*self.args, *args, **self.kwargs, **kwargs)

    def __repr__(self) -> str:
        return f"Partial({self.func!r}, {self.args!r}, {self.kwargs!r})"

    def __str__(self) -> str:
        return f"Partial<{self.func}({self.args}, {self.kwargs})>"


def conditional_action(
    action: Partial, dry_run: bool, inaction: Callable[[Partial]] = print
):
    if not dry_run:
        action()
    else:
        inaction(action)


def conditional_insert(collection: Collection, document: dict, dry_run: bool):
    if not dry_run:
        collection.insert_one(document)
    else:
        print(f"Would insert: '{document}' into '{collection.name}'.")


def migrate_orgs(db: Database, dry_run: bool):
    entity_col = db[EntityDAO.collection_name()]
    # Create root organization entity for '/' token
    root_org = EntityIntermediate(
        handle="/",
        owner_ref=None,
        type="organization",
    )
    conditional_insert(entity_col, root_org.model_dump(), dry_run)
    obj = entity_col.find_one({"handle": "/"})
    if obj:
        root_org_ref = EntityDAO(**obj).to_ref()
    else:
        root_org_ref = EntityRef(handle="/", id="mock_id", type="organization")
    # Query 'tokens' collection for all client names
    client_names = db["tokens"].distinct("client_name")
    for client_name in client_names:
        # Extract the root organization (e.g., `/teialabs/athena` -> `teialabs`)
        root_org_handle = client_name.split("/")[1]
        # Create organization entity based on client name
        org = EntityIntermediate(
            handle=f"/{root_org_handle}",
            owner_ref=root_org_ref,
            type="organization",
        )
        conditional_insert(entity_col, org.model_dump(), dry_run)
    # query 'organizations' collection for all auth0 org-ids (/teialabs--auth0-org-id)
    orgs = db["organizations"].find()
    for org in orgs:
        conditional_action(
            Partial(
                entity_col.update_one,
                {"handle": org["name"]},
                {"$set": {"external_ids": org["external_ids"]}},
            ),
            dry_run,
        )


def migrate_services(db: Database, dry_run: bool):
    entity_col = db[EntityDAO.collection_name()]
    client_names = db["tokens"].distinct("client_name")
    # extract the service names (/teialabs/athena -> [athena], /osf/allai/code -> [allai, code])
    service_names = {
        client_name.split("/")[1:]: tuple(client_name.split("/")[2:])
        for client_name in client_names
    }
    for org_name, service_name in service_names:
        org = entity_col.find_one({"handle": org_name})
        if not org:
            raise ValueError(f"Organization entity '{org_name}' not found.")
        org_ref = EntityDAO(**org).to_ref()
        # create service entities based on service names
        service = EntityIntermediate(
            handle=f"{'--'.join(service_name)}",
            owner_ref=org_ref,
            type="service",
        )
        conditional_insert(entity_col, service.model_dump(), dry_run)


def migrate_users(db: Database, dry_run: bool):
    entity_col = db[EntityDAO.collection_name()]
    # query 'users' collection
    users = db["users"].find()
    for user in users:
        # extract the organization (e.g., `/teialabs/athena` -> `/teialabs`)
        # TODO: what if client_name == / ?
        org_name = user["client_name"].split("/")[1]
        org = entity_col.find_one({"handle": org_name})
        if not org:
            raise ValueError(f"Organization entity '{org_name}' not found.")
        org_ref = EntityDAO(**org).to_ref()
        # create user entity as child of organization
        user_entity = EntityDAO(
            handle=user["email"],
            owner_ref=org_ref,
            type="user",
            extra=[
                Attribute(name="melt_key_client", value=user["client_name"]),
                Attribute(name="melt_key_client_first_login", value=user["created_at"]),
                Attribute(name="client_ip", value=user["created_by"]["user_ip"]),
            ],
            created_by=Infostar(
                request_id=OID,
                apikey_name="migrations",
                authprovider_org="/",
                authprovider_type="melt-key",
                extra={},
                service_handle="tauth",
                user_handle=MY_EMAIL,
                user_owner_handle="/",
                original=None,
                client_ip=MY_IP,
            ),
        )
        conditional_action(
            Partial(entity_col.insert_one, user_entity.model_dump()), dry_run
        )


def get_entity_ref_from_client_name(
    db: Database, client_name: str, mode: Literal["service", "organization"]
) -> EntityRef:
    entity_col = db[EntityDAO.collection_name()]
    org_name, *service_name = client_name.split("/")[1:]
    if mode == "service":
        entity = entity_col.find_one({"handle": "--".join(service_name)})
    elif mode == "organization":
        entity = entity_col.find_one({"handle": f"/{org_name}"})
    else:
        raise ValueError(f"Invalid mode '{mode}'.")
    if not entity:
        raise ValueError(f"Entity '{entity}' not found.")
    return EntityDAO(**entity).to_ref()


def migrate_melt_keys(db: Database, dry_run: bool):
    melt_keys = db[TokenDAO.collection_name()]
    tokens = list(db["tokens"].find())
    for t in tqdm(tokens):
        org = get_entity_ref_from_client_name(db, t["client_name"], "organization")
        service = get_entity_ref_from_client_name(db, t["client_name"], "service")
        key = {
            "client_name": t["client_name"],
            "name": t["name"],
            "value": t["value"],
            "created_by": Infostar(
                request_id=OID,
                apikey_name=t["created_by"]["token_name"],
                authprovider_org="/",
                authprovider_type="melt-key",
                extra={},
                service_handle=service.handle,
                user_handle=t["email"],
                user_owner_handle=org.handle,
                original=None,
                client_ip=t["created_by"]["user_ip"],
            ),
        }
        conditional_insert(melt_keys, key, dry_run)


def migrate_authproviders(db: Database, dry_run: bool):
    authproviders = db[AuthProviderDAO.collection_name()]
    infostar = Infostar(
        request_id=OID,
        apikey_name="migrations",
        authprovider_org="/",
        authprovider_type="melt-key",
        extra={},
        service_handle="tauth",
        user_handle=MY_EMAIL,
        user_owner_handle="/",
        original=None,
        client_ip=MY_IP,
    )
    # create authproviders
    # melt-key
    clients = db["clients"].distinct("name")
    orgs = [f"/{c.split('/')[1]}" for c in clients] + ["/"]
    for org in orgs:
        authprovider = AuthProviderDAO(
            created_by=infostar,
            extra={},
            organization_ref=EntityRef(handle=org, type="organization"),
            service_ref=None,
            type="melt-key",
        )
        conditional_insert(authproviders, authprovider.model_dump(), dry_run)

    # teialabs auth0
    authprovider = AuthProviderDAO(
        created_by=infostar,
        external_ids=[
            Attribute(name="issuer", value="https://dev-z60iog20x0slfn0a.us.auth0.com"),
            Attribute(name="audience", value="api://allai.chat.webui"),
            Attribute(name="client-id", value="4FdEO3ncOVFuROab8wf3c0GLyEMWi4f4"),
        ],
        extra={},
        organization_ref=EntityRef(handle="/teialabs", type="organization"),
        service_ref=EntityRef(handle="athena--chat", type="service"),
        type="auth0",
    )
    # osf auth0 (chat)
    authprovider = AuthProviderDAO(
        created_by=infostar,
        external_ids=[
            Attribute(name="issuer", value="https://osfdigital.eu.auth0.com"),
            Attribute(name="audience", value="api://d4f7a0b5-2a6d-476f-b251-c468a25acdef"),
            Attribute(name="client-id", value="My4fjEfyByLfRPWzxlkP7rTDSFroklNW"),

        ],
        extra={},
        organization_ref=EntityRef(handle="/osf", type="organization"),
        service_ref=EntityRef(handle="allai--chat", type="service"),
        type="auth0",
    )
    # osf auth0 (code)
    authprovider = AuthProviderDAO(
        created_by=infostar,
        external_ids=[
            Attribute(name="issuer", value="https://osfdigital.eu.auth0.com"),
            Attribute(name="audience", value="???"),
        ],
        extra={},
        organization_ref=EntityRef(handle="/osf", type="organization"),
        service_ref=EntityRef(handle="allai--code", type="service"),
        type="auth0",
    )


def main():
    args = get_args()
    client = MongoClient(args.host, args.port)
    db = client[args.in_db]


if __name__ == "__main__":
    main()
