# Generated by Django 5.2.1 on 2025-05-30 12:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weather_app', '0002_remove_searchhistory_weather_app_session_ac6cda_idx_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SearchHistory',
        ),
    ]
