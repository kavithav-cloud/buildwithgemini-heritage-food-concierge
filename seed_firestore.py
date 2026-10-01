"""Seed script for populating Firestore with cultural destinations and food tours."""

import subprocess
import google.auth
from google.cloud import firestore
from google.oauth2.credentials import Credentials

# IMPORTANT: Hardcoded Project ID string (do NOT use GOOGLE_CLOUD_PROJECT env var or google.auth.default for project ID)
FIRESTORE_PROJECT = "qwiklabs-gcp-01-a4a0918623fd"
COLLECTION_NAME = "cultural_destinations"

DESTINATIONS = [
    {
        "id": "colosseum-rome",
        "name": "The Colosseum & Roman Forum",
        "city": "Rome",
        "category": "historic_landmark",
        "historical_era": "Ancient Rome",
        "description": "Flavian amphitheatre built in 70 AD, the iconic center of ancient Roman gladiatorial contests and public spectacles.",
        "recommended_duration_hours": 3.5,
        "avg_cost_usd": 28.0,
        "rating": 4.8,
        "tags": ["architecture", "ancient_history", "monument"],
    },
    {
        "id": "louvre-paris",
        "name": "Musée du Louvre",
        "city": "Paris",
        "category": "museum",
        "historical_era": "Renaissance / 18th Century",
        "description": "World's largest art museum housing the Mona Lisa, Venus de Milo, and royal French art treasures.",
        "recommended_duration_hours": 4.0,
        "avg_cost_usd": 24.0,
        "rating": 4.9,
        "tags": ["art", "monuments", "royal_history"],
    },
    {
        "id": "tsukiji-food-tour-tokyo",
        "name": "Tsukiji Outer Market Culinary & Cultural Tour",
        "city": "Tokyo",
        "category": "food_tour",
        "historical_era": "Edo & Modern Japan",
        "description": "Immersive street food tasting tour through historic market stalls, sampling fresh tamagoyaki, tamari-glazed seafood, and matcha.",
        "recommended_duration_hours": 2.5,
        "avg_cost_usd": 65.0,
        "rating": 4.7,
        "tags": ["street_food", "seafood", "guided_tour", "culinary"],
    },
    {
        "id": "mercado-san-juan-cdmx",
        "name": "Mercado de San Juan & Historic Center Gourmet Walk",
        "city": "Mexico City",
        "category": "culinary_market",
        "historical_era": "Pre-Hispanic & Colonial",
        "description": "Explore Mexico City's premier exotic food market, sampling artisanal cheeses, mole, traditional mezcal, and pre-Hispanic delicacies.",
        "recommended_duration_hours": 3.0,
        "avg_cost_usd": 45.0,
        "rating": 4.8,
        "tags": ["gastronomy", "local_markets", "tasting"],
    },
    {
        "id": "acropolis-athens",
        "name": "The Acropolis & Parthenon",
        "city": "Athens",
        "category": "historic_landmark",
        "historical_era": "Classical Antiquity",
        "description": "Ancient citadel perched above Athens containing the Parthenon and masterpieces of Classical Greek architecture.",
        "recommended_duration_hours": 3.0,
        "avg_cost_usd": 22.0,
        "rating": 4.9,
        "tags": ["greece", "antiquity", "temple", "unesco"],
    },
    {
        "id": "trastevere-food-walk-rome",
        "name": "Trastevere Historic Neighborhood & Wine Tasting",
        "city": "Rome",
        "category": "food_tour",
        "historical_era": "Medieval & Renaissance Rome",
        "description": "Evening culinary walk through cobblestone alleys in Trastevere, featuring authentic Roman pastas (Cacio e Pepe, Carbonara) and regional Lazio wines.",
        "recommended_duration_hours": 3.5,
        "avg_cost_usd": 85.0,
        "rating": 4.9,
        "tags": ["wine", "pasta", "night_tour", "trastevere"],
    },
]


def _get_db():
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], stderr=subprocess.DEVNULL).decode().strip()
        if token:
            creds = Credentials(token)
            return firestore.Client(project=FIRESTORE_PROJECT, credentials=creds)
    except Exception:
        pass

    credentials, _ = google.auth.default()
    return firestore.Client(project=FIRESTORE_PROJECT, credentials=credentials)


def seed_database():
    db = _get_db()
    print(f"Connecting to Firestore project '{FIRESTORE_PROJECT}'...")
    collection_ref = db.collection(COLLECTION_NAME)

    for item in DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        print(f"  - Seeded item: {doc_id} ({item['name']})")

    print(f"Successfully seeded {len(DESTINATIONS)} items into collection '{COLLECTION_NAME}'!")


if __name__ == "__main__":
    seed_database()
