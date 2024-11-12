#!/usr/bin/env python3
import base64
import json

from loguru import logger

paths = [
    "../republic-untangle/data/COM-entities.json",
    "../republic-untangle/data/HOE-entities.json",
    "../republic-untangle/data/LOC-entities.json",
    "../republic-untangle/data/ORG-entities.json",
    "../republic-untangle/data/PER-entities.json"
]

entity_browser_names = {
    "HOE": "hoedanigheid",
    "PERS": "persoon",
    "LOC": "locatie",
    "COM": "commissie",
    "ORG": "organisatie"
}

facet_names = {
    "HOE": "roleName",
    "PERS": "personName",
    "LOC": "locationName",
    "COM": "commissionName",
    "ORG": "organisationName"
}


def main():
    global b64
    for path in paths:
        print(f"<= {path}")
        with open(path) as f:
            entities = json.load(f)
        name_values = set()
        for e in entities:
            e_category = e["category"]
            e_id = e['id']
            eb_endpoint = entity_browser_names[e_category]
            eb_url = f"https://entiteiten.goetgevonden.nl/{eb_endpoint}/{e_id}"
            print(eb_url)
            facet_name = facet_names[e_category]
            e_name = e["name"]
            if e_name in name_values:
                logger.error(f"duplicate name {e_name} for {e_category}")
            name_values.add(e_name)
            query = '{"terms":{"' + facet_name + '":["' + e_name + '"]}}'
            # ic(query)
            print(f"query={query}")
            b64 = base64.b64encode(bytes(query, 'utf-8')).decode('utf-8')
            tav_url = f"https://app.goetgevonden.nl?query={b64}"
            print(tav_url)
            print()
        print()


if __name__ == '__main__':
    main()
