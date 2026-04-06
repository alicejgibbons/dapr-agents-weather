#
# Copyright 2026 The Dapr Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from pymongo import MongoClient

CITIES = [
    {"name": "London", "country": "United Kingdom", "latitude": 51.5074, "longitude": -0.1278},
    {"name": "New York", "country": "United States", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503},
    {"name": "Paris", "country": "France", "latitude": 48.8566, "longitude": 2.3522},
    {"name": "Sydney", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093},
    {"name": "São Paulo", "country": "Brazil", "latitude": -23.5505, "longitude": -46.6333},
    {"name": "Cairo", "country": "Egypt", "latitude": 30.0444, "longitude": 31.2357},
    {"name": "Mumbai", "country": "India", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Seattle", "country": "United States", "latitude": 47.6062, "longitude": -122.3321},
]


def main() -> None:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["weatherdb"]
    collection = db["cities"]

    collection.drop()
    result = collection.insert_many(CITIES)
    print(f"Inserted {len(result.inserted_ids)} cities into weatherdb.cities")
    client.close()


if __name__ == "__main__":
    main()
