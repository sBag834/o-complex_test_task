from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json


class WeatherViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.autocomplete_url = reverse('autocomplete')

        # Мок-данные для API
        self.mock_geo_data = {
            'name': 'Москва',
            'latitude': 55.7522,
            'longitude': 37.6156
        }
        self.mock_weather_data = {
            'hourly': {
                'time': ['2025-05-30T18:00', '2025-05-30T19:00'],
                'temperature_2m': [24.2, 23.7],
                'weathercode': [3, 2]
            }
        }

    def test_index_view_get(self):
        """Тест GET-запроса к главной странице"""
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Прогноз погоды')
        self.assertIsNone(response.context.get('weather'))
        self.assertIsNone(response.context.get('error'))

    @patch('weather_app.views.geocode_city')
    @patch('weather_app.views.get_weather')
    def test_index_view_post_valid_city(self, mock_get_weather, mock_geocode_city):
        """Тест POST-запроса с валидным городом"""
        # Настраиваем моки
        mock_geocode_city.return_value = self.mock_geo_data
        mock_get_weather.return_value = self.mock_weather_data

        # Выполняем запрос
        response = self.client.post(self.index_url, {'city': 'Москва'})

        # Проверяем результаты
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['weather'])
        self.assertEqual(response.context['weather']['city'], 'Москва')
        self.assertEqual(len(response.context['weather']['hourly']), 2)
        self.assertContains(response, 'Москва')

        # Проверяем сохранение в сессии
        session = self.client.session
        self.assertIn('search_history', session)
        self.assertEqual(session['search_history'], ['Москва'])

    @patch('weather_app.views.geocode_city')
    def test_index_view_post_invalid_city(self, mock_geocode_city):
        """Тест POST-запроса с невалидным городом"""
        # Настраиваем мок
        mock_geocode_city.return_value = None

        # Выполняем запрос
        response = self.client.post(self.index_url, {'city': 'бебебе'})

        # Проверяем результаты
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['error'])
        self.assertEqual(response.context['error'], "Город не найден")
        self.assertContains(response, "Город не найден")

        # Проверяем, что история не сохранилась
        session = self.client.session
        self.assertNotIn('search_history', session)

    @patch('weather_app.views.geocode_city')
    @patch('weather_app.views.get_weather')
    def test_search_history_functionality(self, mock_get_weather, mock_geocode_city):
        """Тест функционала истории поиска"""
        # Настраиваем моки
        mock_geocode_city.return_value = self.mock_geo_data
        mock_get_weather.return_value = self.mock_weather_data

        # Первый поиск
        self.client.post(self.index_url, {'city': 'Москва'})
        session = self.client.session
        self.assertEqual(session['search_history'], ['Москва'])

        # Второй поиск
        self.client.post(self.index_url, {'city': 'Санкт-Петербург'})
        session = self.client.session
        self.assertEqual(session['search_history'], ['Санкт-Петербург', 'Москва'])

        # Третий поиск
        self.client.post(self.index_url, {'city': 'Казань'})
        session = self.client.session
        self.assertEqual(session['search_history'], ['Казань', 'Санкт-Петербург', 'Москва'])

        # Четвертый поиск (должен вытеснить первый)
        self.client.post(self.index_url, {'city': 'Новосибирск'})
        session = self.client.session
        self.assertEqual(session['search_history'], ['Новосибирск', 'Казань', 'Санкт-Петербург'])

        # Повторный поиск существующего города (должен переместить его в начало)
        self.client.post(self.index_url, {'city': 'Казань'})
        session = self.client.session
        self.assertEqual(session['search_history'], ['Казань', 'Новосибирск', 'Санкт-Петербург'])

    @patch('weather_app.views.geocode_city')
    @patch('weather_app.views.get_weather')
    def test_history_display_in_template(self, mock_get_weather, mock_geocode_city):
        """Тест отображения истории в шаблоне"""
        # Настраиваем моки
        mock_geocode_city.return_value = self.mock_geo_data
        mock_get_weather.return_value = self.mock_weather_data

        # Выполняем несколько поисков
        self.client.post(self.index_url, {'city': 'Москва'})
        self.client.post(self.index_url, {'city': 'Санкт-Петербург'})
        self.client.post(self.index_url, {'city': 'Казань'})

        # Проверяем отображение истории
        response = self.client.get(self.index_url)
        self.assertContains(response, 'Вы ранее искали:')
        self.assertContains(response, 'Москва')
        self.assertContains(response, 'Санкт-Петербург')
        self.assertContains(response, 'Казань')

        # Проверяем, что история содержит кнопки
        self.assertContains(response, 'data-city="Москва"')
        self.assertContains(response, 'data-city="Санкт-Петербург"')
        self.assertContains(response, 'data-city="Казань"')

    @patch('weather_app.views.geocode_city')
    @patch('weather_app.views.get_weather')
    def test_history_button_functionality(self, mock_get_weather, mock_geocode_city):
        """Тест работы кнопок истории"""
        # Настраиваем моки
        mock_geocode_city.return_value = self.mock_geo_data
        mock_get_weather.return_value = self.mock_weather_data

        # Добавляем город в историю
        self.client.post(self.index_url, {'city': 'Москва'})

        # Эмулируем клик по кнопке истории
        response = self.client.post(self.index_url, {'city': 'Москва'}, follow=True)

        # Проверяем, что город был найден
        self.assertContains(response, 'Москва')

        # Проверяем обновление истории
        session = self.client.session
        self.assertEqual(session['search_history'], ['Москва'])

    @patch('weather_app.views.requests.get')
    def test_autocomplete_view(self, mock_requests_get):
        """Тест view автодополнения"""
        # Настраиваем мок API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {'name': 'Самара'},
                {'name': 'Саратов'},
                {'name': 'Санкт-Петербург'}
            ]
        }
        mock_requests_get.return_value = mock_response

        # Выполняем запрос
        response = self.client.get(self.autocomplete_url, {'term': 'са'})

        # Проверяем результаты
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, ['Самара', 'Саратов', 'Санкт-Петербург'])

    def test_autocomplete_view_no_term(self):
        """Тест автодополнения без параметра term"""
        response = self.client.get(self.autocomplete_url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        self.assertEqual(content, [])