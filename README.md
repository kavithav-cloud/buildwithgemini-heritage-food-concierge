# 🏛️ Cultural Heritage & Food Tour Concierge

An intelligent AI travel concierge agent built with Google's **Agent Development Kit (ADK)** and **Gemini 2.5 Flash**, designed to help travelers discover authentic heritage destinations, historic landmarks, museum treasures, and culinary food tours around the world.

![Heritage & Food Tour Concierge Demo](./demo.gif)

---

## 🌟 Key Features & Capabilities

Based on the implemented toolset in `app/tools.py` and `app/agent.py`:

- **🍷 Culinary & Food Tour Discovery**: Searches curated food walks, local tasting tours, street food markets, and regional dish recommendations.
- **🖼️ Metropolitan Museum Artworks & Artifacts**: Queries real historical artifacts, paintings, and sculptures directly from the Metropolitan Museum of Art Open Access API.
- **🌦️ Live Destination Weather & Packing Tips**: Fetches real-time local weather conditions and tailored packing suggestions via the Open-Meteo API.
- **📍 Google Maps Geocoding & Nearby Places**: Converts addresses into spatial coordinates and searches nearby restaurants, basilicas, and historic sites via Google Maps APIs.
- **🎨 AI Visual Postcard Generation**: Generates custom destination postcard artwork using Google's `gemini-3.1-flash-lite-image` model in the global region.
- **🎥 AI Omni Video Generation**: Produces short cinematic cultural videos using Google's `gemini-omni-flash-preview` model, saving artifacts to the ADK Playground and streaming directly to Cloud Storage.
- **🧠 Cross-Session Memory & Allergy Intelligence**: Automatically extracts and remembers user dietary restrictions, food allergies, and travel preferences across conversations using Vertex AI Memory Bank.
- **📱 Rich A2UI Card Surfaces & Lightbox**: Emits structured A2UI visual cards (Card, Column, Row, Text, Image) rendered natively in the dark-themed web frontend with an interactive full-screen image Lightbox modal.
- **🐍 Python Sandbox Code Execution**: Evaluates mathematical calculations and data processing scripts securely via `AgentEngineSandboxCodeExecutor`.

---

## ☁️ Google Cloud & Tech Stack Integration

| Technology / Service | Implementation & Role |
| :--- | :--- |
| **Agent Development Kit (ADK)** | Core framework (`google.adk.agents.Agent`, `App`) managing prompt instructions, tool routing, and callbacks |
| **Gemini 2.5 Flash** | Primary reasoning LLM (`gemini-2.5-flash`) for multi-step intent routing and response generation |
| **Gemini Omni & Imagen Models** | `gemini-omni-flash-preview` for video generation; `gemini-3.1-flash-lite-image` for visual postcards |
| **Vertex AI Memory Bank** | Long-term memory persistence using `PreloadMemoryTool` and `add_session_to_memory` callbacks |
| **Google Cloud Firestore** | Database storage for curated cultural destinations and local food tour itineraries |
| **Google Cloud Storage (GCS)** | Public asset hosting for generated postcard images and video MP4 files |
| **A2UI Protocol** | Standardized UI surface rendering (`A2uiSchemaManager`, `BasicCatalog`, `a2ui_callback`) |
| **FastAPI & Cloud Run** | A2A-compliant proxy server and dark-themed web frontend deployed on Google Cloud Run |

---

## 🏗️ Project Architecture

```
heritage-food-concierge/
├── app/
│   ├── agent.py            # ADK root agent configuration, A2UI prompts, and memory callbacks
│   ├── tools.py            # Tool implementations (Firestore, GCS, Maps, Weather, Met Museum, Omni Video)
│   └── a2ui_utils.py       # A2UI stream interceptor and surface generator callback
├── frontend/
│   ├── main.py             # FastAPI proxy server translating browser HTTP to Agent Engine A2A stream
│   └── static/
│       └── index.html      # Dark-themed UI with category filter chips, prompt pills, and Lightbox modal
├── agents-cli-manifest.yaml # Deployment specification for Vertex AI Agent Engine & Cloud Run
├── pyproject.toml          # Project dependencies (google-adk, google-genai, google-cloud-storage, etc.)
└── demo.gif                # Interactive demonstration recording
```

---

## 🚀 Local Development & Setup

### Prerequisites

- Python 3.11+
- Google Cloud SDK (`gcloud`) authenticated to your GCP project
- Active GCP Project with Firestore, Vertex AI, and Cloud Storage APIs enabled

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/heritage-food-concierge.git
cd heritage-food-concierge
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Environment Variables

Create a `.env` file in the project root:

```ini
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_REGION=us-east1
GOOGLE_GENAI_USE_VERTEXAI=1
GCS_BUCKET_NAME=your-gcs-assets-bucket
```

### 3. Seed Firestore Database

Initialize the Firestore destination database with sample food tours:

```bash
python seed_firestore.py
```

### 4. Deploying & Running

Deploy the reasoning engine to Vertex AI Agent Engine using `agents-cli`:

```bash
agents-cli deploy --project $GOOGLE_CLOUD_PROJECT --region $GOOGLE_CLOUD_REGION
```

Run the local FastAPI proxy server and web interface:

```bash
python -m uvicorn frontend.main:app --reload --port 8080
```

Access the web interface by navigating to `localhost:8080` in your web browser.

---

## 📋 Feature Status Matrix

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **Food Tour & Destination Discovery** | ✅ Implemented | Backed by Firestore database queries |
| **Met Museum Artifact Search** | ✅ Implemented | Queries Met Museum Open Access REST API |
| **Weather & Packing Suggestions** | ✅ Implemented | Live Open-Meteo API integration |
| **Google Maps Geocoding & Nearby** | ✅ Implemented | Geocoding & Google Places API |
| **AI Visual Postcard Generation** | ✅ Implemented | `gemini-3.1-flash-lite-image` model |
| **AI Omni Video Generation** | ✅ Implemented | `gemini-omni-flash-preview` model + GCS upload |
| **Vertex AI Memory Bank Persistence** | ✅ Implemented | Durable memory for dietary allergies & preferences |
| **A2UI Surface Cards & Lightbox UI** | ✅ Implemented | Native dark mode renderer with image zoom modal |
| **Real-Time Audio Translation** | ⏳ Planned | Future roadmap feature for multilingual audio tours |

---

## 📄 License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.
