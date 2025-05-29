import requests

def geocode_city(name):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": name, "count": 1}
    )
    results = response.json().get('results', [])
    return results[0] if results else None

def get_weather(lat, lon):
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "timezone": "auto"
            }
        )
        return response.json()
    except Exception as e:
        return {'error': True, 'reason': str(e)}