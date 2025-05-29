import requests
from django.shortcuts import render, redirect
from django.contrib.sessions.backends.db import SessionStore
from .utils import geocode_city, get_weather
from .models import SearchHistory
from django.http import JsonResponse
from django.db.models import Count


def index(request):
    # Проверяем последний город в сессии
    last_city = request.session.get('last_city', None)
    weather_data = None
    error = None

    if request.method == 'POST':
        city_name = request.POST.get('city')
        if city_name:
            # Сохраняем в историю
            if request.session.session_key:
                SearchHistory.objects.create(
                    city=city_name,
                    session_key=request.session.session_key
                )

            # Получаем координаты
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
                        'city': city_name,
                        'temperature': weather['current_weather']['temperature'],
                        'windspeed': weather['current_weather']['windspeed'],
                        'weathercode': weather['current_weather']['weathercode'],
                    }
                    # Сохраняем последний город
                    request.session['last_city'] = city_name
                    request.session.modified = True

    return render(request, 'index.html', {
        'last_city': last_city,
        'weather': weather_data,
        'error': error
    })


def search_history_api(request):
    if not request.session.session_key:
        return JsonResponse([], safe=False)

    # Статистика по городам
    stats = SearchHistory.objects.filter(
        session_key=request.session.session_key
    ).values('city').annotate(
        count=Count('id')
    ).order_by('-count')

    return JsonResponse(list(stats), safe=False)

def autocomplete_cities(request):
    term = request.GET.get('term', '')
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": term, "count": 5}
    )
    results = response.json().get('results', [])
    cities = [city['name'] for city in results]
    return JsonResponse(cities, safe=False)


def search_history_view(request):
    if not request.session.session_key:
        return render(request, 'history.html', {'history': []})

    history = SearchHistory.objects.filter(
        session_key=request.session.session_key
    ).order_by('-timestamp')[:10]

    return render(request, 'history.html', {'history': history})