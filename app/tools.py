"""Firestore function tools, public APIs, Google Maps, and Image Generation tools for Cultural Heritage & Food Tour Concierge."""

import base64
import os
import subprocess
import urllib.parse
import google.auth
import httpx
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types
from google.oauth2.credentials import Credentials

# IMPORTANT: Hardcoded Project ID and Bucket Name strings (do NOT read from GOOGLE_CLOUD_PROJECT env var)
FIRESTORE_PROJECT = "qwiklabs-gcp-01-a4a0918623fd"
COLLECTION_NAME = "cultural_destinations"
GCS_BUCKET_NAME = "heritage-food-concierge-assets-8623fd"


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


def _get_maps_api_key() -> str:
    """Retrieve the Google Maps API key from environment variable."""
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        try:
            from dotenv import load_dotenv

            load_dotenv()
            key = os.getenv("GOOGLE_MAPS_API_KEY")
        except Exception:
            pass
    return key or ""


async def generate_cultural_postcard_image(
    prompt: str,
    filename: str = "postcard.png",
    tool_context: ToolContext = None,
) -> dict:
    """Generate a visual postcard or cultural dish image using Gemini 3.1 Flash-Lite Image model in the global region.

    Saves the generated image as an artifact in ADK (Playground Artifacts panel) and uploads the bytes directly to a public Cloud Storage bucket.

    Args:
        prompt: Description of the scene, cultural landmark, heritage site, or culinary dish to generate.
        filename: Target filename for the image artifact and GCS object (default 'postcard.png').
        tool_context: ADK tool context injected automatically by the framework.

    Returns:
        A dictionary containing the status, prompt, filename, and public Cloud Storage image URL.
    """
    try:
        client = genai.Client(location="global")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        image_bytes = None
        mime_type = "image/png"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    break

        if not image_bytes:
            return {"error": "Failed to generate image bytes from Gemini model response."}

        # 1. Save artifact with tool_context so it shows up in Playground's Artifacts panel
        if tool_context:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public GCS bucket
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_image_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate and upload image: {str(e)}"}


async def generate_cultural_video(
    prompt: str,
    filename: str = "cultural_video.mp4",
    tool_context: ToolContext = None,
) -> dict:
    """Generate a short video for a cultural destination, landmark, heritage site, or culinary dish using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an artifact in ADK (Playground Artifacts panel) and uploads the bytes directly to a public Cloud Storage bucket.

    Args:
        prompt: Description of the scene, cultural landmark, heritage site, or culinary dish to generate video for.
        filename: Target filename for the video artifact and GCS object (default 'cultural_video.mp4').
        tool_context: ADK tool context injected automatically by the framework.

    Returns:
        A dictionary containing the status, prompt, filename, and public Cloud Storage video URL.
    """
    try:
        client = genai.Client(location="global")
        video_bytes = None
        mime_type = "video/mp4"

        # Try interactions API first (Gemini Omni Flash models)
        if hasattr(client, "interactions"):
            try:
                res = client.interactions.create(
                    model="gemini-omni-flash-preview",
                    input=prompt,
                )
                if hasattr(res, "output_video") and res.output_video and getattr(res.output_video, "data", None):
                    raw_data = res.output_video.data
                    if isinstance(raw_data, str):
                        video_bytes = base64.b64decode(raw_data)
                    else:
                        video_bytes = raw_data
            except Exception:
                pass

        # Fallback to generate_content API with response_modalities=["VIDEO"]
        if not video_bytes:
            try:
                res = client.models.generate_content(
                    model="gemini-omni-flash-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["VIDEO"]),
                )
                if res.candidates and res.candidates[0].content.parts:
                    for part in res.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            raw_data = part.inline_data.data
                            mime_type = part.inline_data.mime_type or "video/mp4"
                            if isinstance(raw_data, str):
                                video_bytes = base64.b64decode(raw_data)
                            else:
                                video_bytes = raw_data
                            break
            except Exception:
                pass

        # Fallback to generate_videos API if available
        if not video_bytes and hasattr(client.models, "generate_videos"):
            try:
                res = client.models.generate_videos(
                    model="gemini-omni-flash-preview",
                    prompt=prompt,
                )
                if hasattr(res, "generated_videos") and res.generated_videos:
                    video_obj = res.generated_videos[0].video
                    if hasattr(video_obj, "video_bytes") and video_obj.video_bytes:
                        video_bytes = video_obj.video_bytes
            except Exception:
                pass

        if not video_bytes:
            return {"error": "Failed to generate video bytes from gemini-omni-flash-preview model response."}

        # 1. Save artifact with tool_context so it shows up in Playground's Artifacts panel
        if tool_context:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to public GCS bucket (no local file writing)
        storage_client = storage.Client(project=FIRESTORE_PROJECT)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_video_url": public_url,
        }
    except Exception as e:
        return {"error": f"Failed to generate and upload video: {str(e)}"}



def geocode_address(address: str) -> dict:
    """Convert a human-readable address or landmark into geographic coordinates using Google Maps Geocoding API.

    Args:
        address: Human-readable location or landmark name (e.g. 'Piazza Navona, Rome' or 'Louvre Museum, Paris').

    Returns:
        A dictionary containing formatted_address, location coordinates (latitude, longitude), and place_id.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    encoded_addr = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

    try:
        response = httpx.get(url, timeout=10.0)
        data = response.json()
        status = data.get("status")

        if status == "OK" and data.get("results"):
            top = data["results"][0]
            loc = top["geometry"]["location"]
            return {
                "formatted_address": top.get("formatted_address"),
                "location": {"latitude": loc["lat"], "longitude": loc["lng"]},
                "place_id": top.get("place_id"),
            }
        return {"error": f"Geocoding failed with status: {status}"}
    except Exception as e:
        return [{"error": f"Failed to execute geocoding request: {str(e)}"}]


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: float = 1000.0,
) -> list[dict]:
    """Find nearby places (restaurants, cafes, museums, tourist attractions) around specific GPS coordinates using Google Maps Places API.

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Type of place to search for (e.g. 'restaurant', 'cafe', 'museum', 'tourist_attraction').
        radius_meters: Search radius in meters (default 1000m).

    Returns:
        A list of matching places with name, address, location coordinates, rating, and place types.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}]

    new_url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types,places.rating",
    }
    body = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }

    try:
        resp = httpx.post(new_url, headers=headers, json=body, timeout=10.0)
        data = resp.json()
        if resp.status_code == 200 and "places" in data:
            results = []
            for p in data["places"]:
                results.append(
                    {
                        "name": p.get("displayName", {}).get("text"),
                        "address": p.get("formattedAddress"),
                        "location": p.get("location"),
                        "rating": p.get("rating"),
                        "types": p.get("types"),
                    }
                )
            return results
    except Exception:
        pass

    legacy_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius_meters}&type={place_type}&key={api_key}"
    try:
        resp = httpx.get(legacy_url, timeout=10.0).json()
        status = resp.get("status")
        if status == "OK":
            results = []
            for p in resp.get("results", [])[:5]:
                loc = p.get("geometry", {}).get("location", {})
                results.append(
                    {
                        "name": p.get("name"),
                        "address": p.get("vicinity"),
                        "location": {"latitude": loc.get("lat"), "longitude": loc.get("lng")},
                        "rating": p.get("rating"),
                        "types": p.get("types"),
                    }
                )
            return results
        return [{"error": f"Places search failed with status: {status}"}]
    except Exception as e:
        return [{"error": f"Failed to search nearby places: {str(e)}"}]


def search_cultural_destinations(
    city: str | None = None,
    category: str | None = None,
    historical_era: str | None = None,
) -> list[dict]:
    """Search for cultural destinations, historic landmarks, museums, and food tours in Firestore.

    Args:
        city: Optional city filter (e.g. 'Rome', 'Paris', 'Tokyo', 'Mexico City', 'Athens').
        category: Optional category filter ('historic_landmark', 'museum', 'food_tour', 'culinary_market').
        historical_era: Optional historical era filter (e.g. 'Ancient Rome', 'Renaissance', 'Edo Period').

    Returns:
        A list of matching cultural destination items.
    """
    db = _get_db()
    query = db.collection(COLLECTION_NAME)

    docs = query.stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        if city and city.lower() not in data.get("city", "").lower():
            continue
        if category and category.lower() not in data.get("category", "").lower():
            continue
        if historical_era and historical_era.lower() not in data.get("historical_era", "").lower():
            continue
        results.append(data)

    return results


def add_cultural_destination(
    name: str,
    city: str,
    category: str,
    historical_era: str,
    description: str,
    recommended_duration_hours: float = 2.0,
    avg_cost_usd: float = 30.0,
    tags: list[str] | None = None,
) -> dict:
    """Add or save a new cultural destination or food tour into the Firestore database.

    Args:
        name: Name of the destination or tour.
        city: City where it is located.
        category: Category ('historic_landmark', 'museum', 'food_tour', 'culinary_market').
        historical_era: Era or historical period associated with the site.
        description: Summary of what visitors experience.
        recommended_duration_hours: Estimated duration in hours.
        avg_cost_usd: Average estimated cost per person in USD.
        tags: Relevant search tags (e.g. ['art', 'architecture']).

    Returns:
        A status dictionary with the saved destination details.
    """
    db = _get_db()
    doc_id = name.lower().replace(" ", "-").replace("'", "").replace("&", "and")
    item = {
        "id": doc_id,
        "name": name,
        "city": city,
        "category": category,
        "historical_era": historical_era,
        "description": description,
        "recommended_duration_hours": float(recommended_duration_hours),
        "avg_cost_usd": float(avg_cost_usd),
        "rating": 5.0,
        "tags": tags or [],
    }

    db.collection(COLLECTION_NAME).document(doc_id).set(item)
    return {"status": "success", "message": f"Successfully added '{name}' to {COLLECTION_NAME}.", "item": item}


def get_destination_weather_and_packing_tips(city: str) -> dict:
    """Get weather conditions and cultural packing recommendations for a target destination city.

    Args:
        city: Destination city name (e.g. 'Rome', 'Paris', 'Tokyo', 'Mexico City', 'Athens').

    Returns:
        A dictionary with weather conditions, temperature, and packing tips for heritage & food walks.
    """
    city_lower = city.lower()
    if "rome" in city_lower:
        return {
            "city": "Rome",
            "weather": "Warm and sunny",
            "temp_c": 24,
            "packing_tips": "Comfortable walking shoes for cobblestones, modest attire for basilicas/churches, sun hat, reusable water bottle.",
        }
    elif "paris" in city_lower:
        return {
            "city": "Paris",
            "weather": "Mild with light rain",
            "temp_c": 18,
            "packing_tips": "Compact umbrella, light jacket, stylish walkable sneakers for museum walks.",
        }
    elif "tokyo" in city_lower:
        return {
            "city": "Tokyo",
            "weather": "Clear and pleasant",
            "temp_c": 21,
            "packing_tips": "Easy slip-on shoes for temple entry, light layers, tote bag for street food markets.",
        }
    elif "mexico" in city_lower:
        return {
            "city": "Mexico City",
            "weather": "Sunny mornings with cool evenings",
            "temp_c": 22,
            "packing_tips": "Breathable layers, sunscreen for high altitude, comfortable shoes for market walking tours.",
        }
    elif "athens" in city_lower:
        return {
            "city": "Athens",
            "weather": "Hot and sunny",
            "temp_c": 28,
            "packing_tips": "Grip footwear for slippery marble at the Acropolis, sunglasses, high-SPF sunscreen.",
        }
    else:
        return {
            "city": city.capitalize(),
            "weather": "Pleasant and clear",
            "temp_c": 20,
            "packing_tips": "Comfortable walking shoes for historical sightseeing and food tasting tours.",
        }


def search_museum_artworks_and_artifacts(query: str, limit: int = 3) -> list[dict]:
    """Search for real historical artworks, artifacts, and cultural treasures from the Metropolitan Museum of Art collection API.

    Args:
        query: Search term for culture, location, artist, or historical era (e.g. 'Rome', 'Renaissance', 'Edo', 'Greek', 'Mexico').
        limit: Maximum number of detailed artifact items to return (default 3).

    Returns:
        A list of dictionaries containing title, culture, period, artist, image_url, and museum link.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q={encoded_query}&hasImages=true"

    try:
        response = httpx.get(search_url, headers=headers, timeout=10.0)
        if response.status_code != 200:
            return []

        data = response.json()
        object_ids = data.get("objectIDs") or []
        results = []

        for obj_id in object_ids[:limit]:
            detail_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
            detail_resp = httpx.get(detail_url, headers=headers, timeout=5.0)
            if detail_resp.status_code == 200:
                obj_data = detail_resp.json()
                results.append(
                    {
                        "title": obj_data.get("title", "Untitled"),
                        "culture": obj_data.get("culture") or obj_data.get("country") or "Historical Artifact",
                        "period": obj_data.get("period") or obj_data.get("objectDate") or "Historic",
                        "artist": obj_data.get("artistDisplayName") or "Unknown / Ancient Artisan",
                        "image_url": obj_data.get("primaryImageSmall") or obj_data.get("primaryImage") or "",
                        "museum_url": obj_data.get("objectURL") or "",
                    }
                )
        return results
    except Exception as e:
        return [{"error": f"Failed to fetch museum artifacts: {str(e)}"}]
