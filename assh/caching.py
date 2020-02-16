import datetime
import json
import os

from assh.exceptions import TooManyResultsException, NoResultsException
from assh.instance import Instance, get_instances as _get_fresh_instances


def get_instances(cache_dir):
    if not cache_dir.exists():
        os.makedirs(cache_dir)

    region_suffix = "default"
    cache_path = cache_dir / f"instances-{region_suffix}.json"
    cached_response = {}
    instances = []

    if cache_path.exists():
        with open(cache_path) as cache_file:
            cached_response = json.load(cache_file)

    cache_updated = datetime.datetime.utcfromtimestamp(
        cached_response.get("fetched_at", 0)
    )
    now = datetime.datetime.utcnow()

    if cache_updated < (now - datetime.timedelta(minutes=1)):
        instances = _get_fresh_instances()

        with open(cache_path, "w+") as cache_file:
            json.dump(
                {
                    "fetched_at": now.timestamp(),
                    "instances": [instance.to_dict() for instance in instances],
                },
                cache_file,
            )
    else:
        instances = [
            Instance.from_dict(instance) for instance in cached_response["instances"]
        ]

    return instances


def get_instance(cache_dir, query):
    instances = get_instances(cache_dir)
    matched = [
        instance
        for instance in instances
        if (query in instance.id or query.lower() in instance.name.lower())
    ]

    if len(matched) > 1:
        raise TooManyResultsException(
            f"Query was too vague, {len(matched)} results were returned"
        )

    if len(matched) == 0:
        raise NoResultsException(f"No results could be found with query term '{query}'")

    return matched[0]
