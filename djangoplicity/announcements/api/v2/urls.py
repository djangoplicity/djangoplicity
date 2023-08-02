from django.urls import path, include
from rest_framework import routers
from .views import AnnouncementListView, AnnouncementDetailView

api_router = routers.DefaultRouter()
api_router.register('', AnnouncementListView)
api_router.register('', AnnouncementDetailView)

urlpatterns = [
    path('', include(api_router.urls))
]
