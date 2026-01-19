import json


def printJSON(data_json):
    print(json.dumps(data_json, sort_keys=True, indent=4))