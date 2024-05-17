"""
Migration script to convert data from v1 to v2.
"""

import argparse

from pymongo import MongoClient


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


def main():
    args = get_args()
    client = MongoClient(args.host, args.port)
    db = client[args.in_db]

    # Entities
    ## Organizations
    #  Create root organization entity for '/' token
    #  Query 'tokens' collection for all client names
    #  For each client name
    #    Extract the root organization (e.g., `/teialabs/athena` -> `/teialabs`)
    #    Create organization entity based on client name
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
