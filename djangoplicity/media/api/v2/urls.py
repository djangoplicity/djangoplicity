from django.urls import path, include
from rest_framework import routers
from .views import ImageListView, ImageDetailView, VideoListView, VideoDetailView

api_router = routers.DefaultRouter()
api_router.register('images', ImageListView)
api_router.register('images', ImageDetailView)
api_router.register('videos', VideoListView)
api_router.register('videos', VideoDetailView)

urlpatterns = [
    path('', include(api_router.urls))
]
