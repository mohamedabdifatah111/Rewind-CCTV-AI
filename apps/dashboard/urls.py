from django.urls import path
from .views import StatsView
urlpatterns = [path("dashboard/stats/", StatsView.as_view())]
