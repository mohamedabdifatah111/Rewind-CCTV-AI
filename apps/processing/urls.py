from django.urls import path
from . import views
urlpatterns = [
    path("jobs/", views.JobListView.as_view()),
    path("videos/<int:pk>/frames/", views.VideoFramesView.as_view()),
    path("videos/<int:pk>/processing/", views.VideoProcessingView.as_view()),
]
