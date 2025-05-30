from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime


def index(request):
    weather_data = None
    error = None

    # Получаем историю поиска из сессии
    search_history = request.session.get('search_history', [])

    if request.method == 'POST':
        city_name = request.POST.get('city')
        if city_name:
            # Обновляем историю поиска
            if city_name in search_history:
                search_history.remove(city_name)  # Удаляем если уже есть
            search_history.insert(0, city_name)  # Добавляем в начало
            search_history = search_history[:3]  # Оставляем только 3 последних

            # Сохраняем в сессию
            request.session['search_history'] = search_history

            # Получаем координаты города
            geo_data = geocode_city(city_name)
            if not geo_data:
                error = "Город не найден"
            else:
                # Получаем погоду
                weather = get_weather(
                    geo_data['latitude'],
                    geo_data['longitude']
                )
                if 'error' in weather:
                    error = weather['reason']
                else:
                    weather_data = {
                        'city': geo_data['name'],
                        'hourly': process_hourly_data(weather['hourly'])
                    }

    return render(request, 'index.html', {
        'weather': weather_data,
        'error': error,
        'search_history': search_history  # Передаем историю в шаблон
    })


def autocomplete(request):
    term = request.GET.get('term')
    if term:
        # Выполняем запрос к API геокодинга
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": term, "count": 5, "language": "ru"}
        )
        results = response.json().get('results', [])
        cities = [result['name'] for result in results]
        return JsonResponse(cities, safe=False)
    return JsonResponse([], safe=False)


def geocode_city(name):
    try:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": name, "count": 1, "language": "ru"}
        )
        data = response.json()
        if 'results' in data and data['results']:
            return data['results'][0]
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None


def get_weather(lat, lon):
    try:
        # Получаем прогноз на 24 часа
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,weathercode",
                "forecast_days": 1,
                "timezone": "auto"
            }
        )
        return response.json()
    except Exception as e:
        return {'error': True, 'reason': str(e)}


def process_hourly_data(hourly):
    """Обрабатываем данные о погоде по часам"""
    processed = []
    now = datetime.now()
    current_hour = now.hour

    for i in range(len(hourly['time'])):
        hour_time = datetime.fromisoformat(hourly['time'][i])
        # Показываем только будущие часы
        if hour_time.hour >= current_hour:
            processed.append({
                'time': hour_time.strftime("%H:%M"),
                'temperature': hourly['temperature_2m'][i],
                'weathercode': hourly['weathercode'][i]
            })

    return processed