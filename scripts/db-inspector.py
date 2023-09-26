"""
Download all data from a MongoDB collection and save it as .csv for inspection.
"""
import argparse
import csv
import os
import sys

from pymongo import MongoClient


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="test", help="MongoDB database.")
    parser.add_argument("--collection", help="MongoDB collection.", required=True)
    parser.add_argument("--output", default="data.csv", help="Output file.")
    parser.add_argument(
        "--limit",
        default=0,
        type=int,
        help="Limit the number of documents to export.",
    )
    args = parser.parse_args()
    return args


def flatten(document: dict) -> dict:
    """
    Flatten a nested dictionary.

    >>> flatten({'a': {'b': 1, 'c': 2}})
    {'a.b': 1, 'a.c': 2}
    """
    flattened = {}
    for key, value in document.items():
        if isinstance(value, dict):
            for subkey, subvalue in flatten(value).items():
                flattened[f"{key}.{subkey}"] = subvalue
        else:
            flattened[key] = value
    return flattened


def main():
    args = get_args()
    client = MongoClient(args.host, args.port)
    db = client[args.db]
    collection = db[args.collection]
    cursor = collection.find()
    if args.limit > 0:
        cursor = cursor.limit(args.limit)
    first = collection.find({}).limit(1)[0]
    with open(args.output, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=flatten(first).keys())
        writer.writeheader()
        for document in cursor:
            writer.writerow(flatten(document))


if __name__ == "__main__":
    main()
