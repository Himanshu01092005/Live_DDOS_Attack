import asyncio
import httpx
import os
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

ABUSEIPDB_KEY = os.getenv("AbuseIPDB")
IPINFO_TOKEN = os.getenv("ipToken")

# Global variables to manage limits
blacklist_cache = []
geo_cache = {}

async def update_blacklist(client):
    """Fetches the blacklist only if we haven't exhausted our 5 daily calls."""
    global blacklist_cache
    url = 'https://api.abuseipdb.com/api/v2/blacklist'
    headers = {'Accept': 'application/json', 'Key': ABUSEIPDB_KEY}
    # We set a limit of 100 IPs so we have plenty of data to stream
    params = {'confidenceMinimum': '90', 'limit': '100'} 

    try:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            blacklist_cache = response.json().get('data', [])
            print(f"Successfully cached {len(blacklist_cache)} IPs from blacklist.")
        else:
            print(f"API Limit reached or error: {response.status_code}")
    except Exception as e:
        print(f"Fetch error: {e}")

async def get_coords(ip, client):
    if ip in geo_cache: return geo_cache[ip]
    try:
        url = f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}"
        resp = await client.get(url)
        data = resp.json()
        if "loc" in data:
            lat, lng = map(float, data["loc"].split(","))
            geo_cache[ip] = (lat, lng)
            return lat, lng
    except: pass
    return 0, 0

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with httpx.AsyncClient() as client:
        # Initial fetch on startup
        if not blacklist_cache:
            await update_blacklist(client)

        while True:
            if not blacklist_cache:
                await asyncio.sleep(60) # Wait if no data
                continue

            for entry in blacklist_cache:
                ip = entry['ipAddress']
                lat, lng = await get_coords(ip, client)
                
                payload = {
                    "ip": ip,
                    "score": entry['abuseConfidenceScore'],
                    "country": entry['countryCode'],
                    "startLat": lat, "startLng": lng,
                    "endLat": 28.61, "endLng": 77.20,
                    "color": "red" if entry['abuseConfidenceScore'] > 95 else "orange"
                }
                await websocket.send_json(payload)
                # Slower interval (3-5 seconds) keeps the UI moving 
                # without burning through your GeoIP (ipinfo) credits
                await asyncio.sleep(5)