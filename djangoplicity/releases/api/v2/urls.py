from django.urls import path, include
from rest_framework import routers
from .views import ReleaseListView, ReleaseDetailView

api_router = routers.DefaultRouter()
api_router.register('', ReleaseListView)
api_router.register('', ReleaseDetailView)

urlpatterns = [
    path('', include(api_router.urls))
]
