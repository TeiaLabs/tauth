"""
Migration script to convert data from v1 to v2.
"""

import argparse
from collections import defaultdict
from collections.abc import Callable
from typing import Literal

from loguru import logger
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from pymongo.database import Database
from redbaby.pyobjectid import PyObjectId
from tqdm import tqdm

from tauth.authproviders.models import AuthProviderDAO
from tauth.entities.models import EntityDAO, EntityRef, OrganizationRef, ServiceRef
from tauth.legacy.tokens import TokenDAO
from tauth.schemas import Infostar
from tauth.schemas.attribute import Attribute

OID = PyObjectId()
MY_IP = "127.0.0.1"
MY_EMAIL = "sysadmin@teialabs.com"

SYSTEM_INFOSTAR = Infostar(
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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        default="mongodb://localhost:27017",
        help="MongoDB host.",
    )
    parser.add_argument("--port", type=int, default="27017", help="MongoDB port.")
    parser.add_argument(
        "--in-db", type=str, default="tauth", help="MongoDB input database."
    )
    parser.add_argument(
        "--out-db", type=str, default="tauth-v2", help="MongoDB output database."
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
        return self.func(*self.args, **self.kwargs, **kwargs)

    def __repr__(self) -> str:
        return f"Partial({self.func!r}, {self.args!r}, {self.kwargs!r})"

    def __str__(self) -> str:
        return f"Partial<{self.func}({self.args}, {self.kwargs})>"


def conditional_action(
    action: Partial, dry_run: bool, inaction: Callable[[Partial], None] = logger.info
):
    if not dry_run:
        logger.debug(f"Executing action: {action}")
        action()
    else:
        logger.debug(f"Would execute: {action}")
        inaction(action)


def conditional_insert(collection: Collection, document: dict, dry_run: bool):
    if not dry_run:
        logger.info(f"Inserting document into {collection.name}: {document}")
        collection.insert_one(document)
    else:
        logger.info(f"Would insert: '{document}' into '{collection.name}'.")


def migrate_orgs(
    client: MongoClient, old_db_name: str, new_db_name: str, dry_run: bool
):
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    new_entity_col = new_db[EntityDAO.collection_name()]
    new_entity_col.create_indexes(EntityDAO.indexes())
    # Create root organization entity for '/' token
    root_org = EntityDAO(
        created_by=SYSTEM_INFOSTAR,
        handle="/",
        owner_ref=None,
        type="organization",
    )
    try:
        conditional_insert(new_entity_col, root_org.bson(), dry_run)
    except errors.DuplicateKeyError:
        pass
    obj = new_entity_col.find_one({"handle": "/"})
    if obj:
        root_org_ref = EntityDAO(**obj).to_ref()
    else:
        root_org_ref = EntityRef(handle="/", type="organization", owner_handle=None)
    # Query 'tokens' collection for all client names
    client_names = old_db["tokens"].distinct("client_name")
    for client_name in client_names:
        logger.debug(f"Creating organization entity for '{client_name}'")
        # Extract the root organization (e.g., `/teialabs/athena` -> `teialabs`)
        root_org_handle = client_name.split("/")[1]
        # Create organization entity based on client name
        org = EntityDAO(
            created_by=SYSTEM_INFOSTAR,
            handle=f"/{root_org_handle}",
            owner_ref=root_org_ref,
            type="organization",
        )
        try:
            conditional_insert(new_entity_col, org.bson(), dry_run)
        except errors.DuplicateKeyError:
            logger.warning(f"Organization entity '{org.handle}' already exists.")
    # query 'organizations' collection for all auth0 org-ids (/teialabs--auth0-org-id)
    orgs = old_db["organizations"].find()
    for org in orgs:
        conditional_action(
            Partial(
                new_entity_col.update_one,
                {"handle": org["name"]},
                {"$set": {"external_ids": org["external_ids"]}},
            ),
            dry_run,
        )


def migrate_services(
    client: MongoClient, old_db_name: str, new_db_name: str, dry_run: bool
):
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    entity_col_new = new_db[EntityDAO.collection_name()]
    client_names = old_db["tokens"].distinct("client_name")
    # extract the service names (/teialabs/athena -> [athena], /osf/allai/code -> [allai, code]
    print(client_names)
    service_names = defaultdict(list)
    for client_name in client_names:
        org_name, *service_name = client_name.split("/")[1:]
        if service_name:
            service_names[f"/{org_name}"].append(service_name)
    for org_name, service_names in service_names.items():
        for serv_name in service_names:
            logger.debug(f"Creating service entity for '{org_name}' and '{serv_name}'")
            org = entity_col_new.find_one({"handle": org_name})
            if not org:
                raise ValueError(f"Organization entity '{org_name}' not found.")
            org_ref = EntityDAO(**org).to_ref()
            # create service entities based on service names
            service = EntityDAO(
                created_by=SYSTEM_INFOSTAR,
                handle=f"{'--'.join(serv_name)}",
                owner_ref=org_ref,
                type="service",
            )
            try:
                conditional_insert(entity_col_new, service.bson(), dry_run)
            except errors.DuplicateKeyError:
                pass


def migrate_users(
    client: MongoClient, old_db_name: str, new_db_name: str, dry_run: bool
):
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    entity_col_new = new_db[EntityDAO.collection_name()]
    users = old_db["users"].find()
    for user in users:
        if "email" not in user:
            continue
        org_name = user["client_name"].split("/")[1]
        org = entity_col_new.find_one({"handle": f"/{org_name}"})
        if not org:
            raise ValueError(f"Organization entity '{org_name}' not found.")
        org_ref = EntityDAO(**org).to_ref()
        user_entity = EntityDAO(
            handle=user["email"],
            owner_ref=org_ref,
            type="user",
            extra=[
                Attribute(name="melt_key_client", value=user["client_name"]),
                Attribute(name="melt_key_client_first_login", value=user["created_at"]),
            ],
            created_by=Infostar(
                request_id=OID,
                apikey_name=user["created_by"]["token_name"],
                authprovider_org=org["handle"],
                authprovider_type="melt-key",
                extra={},
                service_handle="tauth",
                user_handle=user["created_by"]["user_email"],
                user_owner_handle=org["handle"],
                original=SYSTEM_INFOSTAR,
                client_ip=user["created_by"].get("user_ip", "127.0.0.1"),
            ),
        )
        try:
            conditional_action(
                Partial(entity_col_new.insert_one, user_entity.bson()), dry_run
            )
        except errors.DuplicateKeyError:
            logger.warning(f"User entity '{user_entity.handle}' already exists.")


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


def migrate_melt_keys(
    client: MongoClient, old_db_name: str, new_db_name: str, dry_run: bool
):
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    melt_keys = new_db[TokenDAO.collection_name()]
    tokens = list(old_db["tokens"].find())
    for t in tqdm(tokens):
        logger.debug(f"Creating melt-key for '{t['client_name']}'")
        org = get_entity_ref_from_client_name(new_db, t["client_name"], "organization")
        try:
            service_handle = get_entity_ref_from_client_name(
                new_db, t["client_name"], "service"
            ).handle
        except ValueError:
            service_handle = "tauth--api"
        key = TokenDAO(
            client_name=t["client_name"],
            name=t["name"],
            value=t["value"],
            created_by=Infostar(
                request_id=OID,
                apikey_name=t["created_by"]["token_name"],
                authprovider_org=org.handle,
                authprovider_type="melt-key",
                extra={},
                service_handle=service_handle,
                user_handle=t["created_by"]["user_email"],
                user_owner_handle=org.handle,
                original=SYSTEM_INFOSTAR,
                client_ip=t["created_by"].get("user_ip", "127.0.0.1"),
            ),
        )
        try:
            conditional_insert(melt_keys, key.bson(), dry_run)
        except errors.DuplicateKeyError:
            logger.warning(f"Melt-key '{key.name}' already exists.")


def migrate_authproviders(
    client: MongoClient, old_db_name: str, new_db_name: str, dry_run: bool
):
    old_db = client[old_db_name]
    new_db = client[new_db_name]
    authproviders = new_db[AuthProviderDAO.collection_name()]
    clients = old_db["clients"].distinct("name")
    orgs = [f"/{c.split('/')[1]}" for c in clients] + ["/"]
    for org in orgs:
        authprovider = AuthProviderDAO(
            created_by=SYSTEM_INFOSTAR,
            organization_ref=OrganizationRef(handle=org),
            service_ref=None,
            type="melt-key",
        )
        conditional_insert(authproviders, authprovider.bson(), dry_run)
    authproviders_data = [
        {
            "created_by": SYSTEM_INFOSTAR,
            "external_ids": [
                Attribute(
                    name="issuer", value="https://dev-z60iog20x0slfn0a.us.auth0.com"
                ),
                Attribute(name="audience", value="api://allai.chat.webui"),
                Attribute(name="client-id", value="4FdEO3ncOVFuROab8wf3c0GLyEMWi4f4"),
            ],
            "organization_ref": OrganizationRef(handle="/teialabs"),
            "service_ref": ServiceRef(handle="athena--chat"),
            "type": "auth0",
        },
        {
            "created_by": SYSTEM_INFOSTAR,
            "external_ids": [
                Attribute(name="issuer", value="https://osfdigital.eu.auth0.com"),
                Attribute(
                    name="audience", value="api://d4f7a0b5-2a6d-476f-b251-c468a25acdef"
                ),
                Attribute(name="client-id", value="My4fjEfyByLfRPWzxlkP7rTDSFroklNW"),
            ],
            "organization_ref": OrganizationRef(handle="/osf"),
            "service_ref": ServiceRef(handle="allai--chat"),
            "type": "auth0",
        },
        {
            "created_by": SYSTEM_INFOSTAR,
            "external_ids": [
                Attribute(name="issuer", value="https://osfdigital.eu.auth0.com"),
                Attribute(
                    name="audience", value="api://27a058b1-2f69-475b-b126-5d816b037cbe"
                ),
            ],
            "organization_ref": OrganizationRef(handle="/osf"),
            "service_ref": ServiceRef(handle="allai--code"),
            "type": "auth0",
        },
    ]
    for authprovider_data in authproviders_data:
        authprovider = AuthProviderDAO(**authprovider_data)
        conditional_insert(authproviders, authprovider.bson(), dry_run)


def main():
    args = get_args()
    logger.add("migration.log", level="INFO")
    logger.info("Starting migration script")
    client = MongoClient(args.host, args.port)
    # migrate_orgs(client, args.in_db, args.out_db, args.dry_run)
    # migrate_services(client, args.in_db, args.out_db, args.dry_run)
    # migrate_users(client, args.in_db, args.out_db, args.dry_run)
    migrate_melt_keys(client, args.in_db, args.out_db, args.dry_run)
    migrate_authproviders(client, args.in_db, args.out_db, args.dry_run)
    logger.info("Migration script completed")


if __name__ == "__main__":
    main()
