from django.urls import path, include
from rest_framework import routers
from .views import ImageListView, ImageDetailView

api_router = routers.DefaultRouter()
api_router.register('images', ImageListView)
api_router.register('images', ImageDetailView)

urlpatterns = [
    path('', include(api_router.urls))
]
