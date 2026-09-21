import json

import requests


url = (
    "https://siwar.ksaa.gov.sa/"
    "api/screens/public/get-lexicon-search-screen-data/"
    "Riyadh?languageCode="
)

payload = {
    "preferences": {
        "first": 0,
        # Only five records while inspecting the response.
        "rows": 5,
        "filters": {
            "languageCode": [
                {
                    "value": "ar",
                    "matchMode": "equals",
                    "operator": "and",
                }
            ]
        },
        "multisortmeta": [],
    }
}

response = requests.post(
    url,
    json=payload,
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://siwar.ksaa.gov.sa",
        "Referer": "https://siwar.ksaa.gov.sa/",
    },
    timeout=30,
)

print("Status:", response.status_code)
print("Content-Type:", response.headers.get("content-type"))

response.raise_for_status()

data = response.json()

print("Type:", type(data).__name__)

if isinstance(data, dict):
    print("Top-level keys:", list(data.keys()))

print(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )[:8000]
)