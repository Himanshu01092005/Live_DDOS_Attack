import asyncio
import httpx
import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

ABUSEIPDB_KEY = os.getenv("AbuseIPDB")
IPINFO_TOKEN = os.getenv("ipToken")

# Cache to store coordinates so we don't call ipinfo for the same IP twice
geo_cache = {}

async def get_coords(ip, client):
    """Fetches Lat/Lng from ipinfo.io"""
    if ip in geo_cache:
        return geo_cache[ip]
    
    try:
        url = f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}"
        resp = await client.get(url)
        data = resp.json()
        if "loc" in data:
            lat, lng = map(float, data["loc"].split(","))
            geo_cache[ip] = (lat, lng)
            return lat, lng
    except Exception as e:
        print(f"GeoIP Error for {ip}: {e}")
    return 0, 0

async def get_real_ddos_data(client):
    """Fetches the latest bad IPs and geolocates them"""
    url = 'https://api.abuseipdb.com/api/v2/blacklist'
    headers = {'Accept': 'application/json', 'Key': ABUSEIPDB_KEY}
    params = {'confidenceMinimum': '90', 'limit': '5'}

    try:
        response = await client.get(url, headers=headers, params=params)
        data = response.json()
        
        attacks = []
        for entry in data.get('data', []):
            ip = entry['ipAddress']
            lat, lng = await get_coords(ip, client)
            
            attacks.append({
                "ip": ip,
                "score": entry['abuseConfidenceScore'],
                "country": entry['countryCode'],
                "startLat": lat,
                "startLng": lng,
                "endLat": 28.61, # Targeting New Delhi
                "endLng": 77.20,
                "color": "red" if entry['abuseConfidenceScore'] > 95 else "orange"
            })
        return attacks
    except Exception as e:
        print(f"AbuseIPDB Error: {e}")
        return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with httpx.AsyncClient() as client:
        while True:
            # Fetch new batch of attacks
            attacks = await get_real_ddos_data(client)
            for attack in attacks:
                await websocket.send_json(attack)
                await asyncio.sleep(1) # Send one arc every second for smooth visuals
            await asyncio.sleep(1) # Wait before refreshing the blacklist