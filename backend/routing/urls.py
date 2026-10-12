from django.urls import path

from .views import (
    health_check,
    geocode_search,
    calculate_routes,
)

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("geocode/", geocode_search, name="geocode-search"),
    path("routes/", calculate_routes, name="calculate-routes"),
]