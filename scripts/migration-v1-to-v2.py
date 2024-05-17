"""
Migration script to convert data from v1 to v2.
"""

import argparse

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from tauth.entities.models import EntityDAO, EntityRef
from tauth.entities.schemas import EntityIntermediate
from tauth.schemas import Creator, Infostar


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


def conditional_action(action, inaction, dry_run: bool):
    if not dry_run:
        action()
    else:
        inaction()


def conditional_insert(collection: Collection, document: dict, dry_run: bool):
    if not dry_run:
        collection.insert_one(document)
    else:
        print(f"Would insert: '{document}' into '{collection.name}'.")


def migrate_entities(db: Database, dry_run: bool):
    entity_col = db[EntityDAO.collection_name()]
    ## Organizations
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
    ## services
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


def main():
    args = get_args()
    client = MongoClient(args.host, args.port)
    db = client[args.in_db]

    ## Users
    #  Query 'tokens' collection for all (client_name, user_email) pairs
    #  For each pair
    #    Extract the organization (e.g., `/teialabs/athena` -> `/teialabs`)
    #    Create user entity as child of organization
    #    Register melt_key_client usage in user entity

    # Authproviders
    #  For each organization entity
    #    Add `melt-key` authprovider
    #    Register melt_key_client usage in authprovider entity

    # Tokens (melt_key)
    #  Migrate `tokens` collection to `melt_keys` collection


def get_clients(db: MongoClient) -> list[str]:
    return db["clients"].distinct("name")


if __name__ == "__main__":
    main()
