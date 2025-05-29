from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('autocomplete/', views.autocomplete_cities, name='autocomplete'),
    path('history/', views.search_history_view, name='history'),
    path('api/history/', views.search_history_api, name='api_history'),
]