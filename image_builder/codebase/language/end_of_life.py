import json
from datetime import date

import requests


class EndOfLifeError(Exception):
    pass


class EndOfLifeNoProductError(EndOfLifeError):
    pass


def get_versions(product: str):
    response = requests.get(f"https://endoflife.date/api/{product}.json")
    if response.status_code != 200:
        raise EndOfLifeNoProductError
    versions = json.loads(response.content.decode())
    return versions


def get_latest_version_for(product: str, lts: bool = True, version: str = None) -> str:
    versions = get_versions(product)

    # Filter non-lts versions out
    if lts:
        lts_filtered_versions = []
        for v in versions:
            if lts and v["lts"] is False:
                continue
            lts_filtered_versions.append(v)
        versions = lts_filtered_versions

    # Filter non-matching versions out
    if version:
        version_filtered_versions = []
        version_segments = version.split(".")
        for v in versions:
            if v["cycle"] == version or v["cycle"] == version_segments[0]:
                version_filtered_versions.append(v)
        versions = version_filtered_versions

    versions.sort(key=lambda x: [int(s) for s in x["cycle"].split(".")], reverse=True)

    version = versions[0]["latest"]
    return ".".join(version.split(".")[0:2])


def is_end_of_life(product: str, version: str) -> bool:
    versions = get_versions(product)
    filtered_versions = [v for v in versions if v["cycle"] == version]

    if len(filtered_versions) == 0:
        version = version.split(".")[0]
        filtered_versions = [v for v in versions if v["cycle"] == version]

    this_version = filtered_versions[0]

    end_of_life = this_version["eol"]

    if end_of_life.__class__.__name__ == "bool":
        return end_of_life
    else:
        end_of_life = date.fromisoformat(end_of_life)
        return end_of_life < date.today()
