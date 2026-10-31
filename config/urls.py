from django.urls import include, path
urlpatterns = [path("api/", include("apps.videos.urls")), path("api/", include("apps.processing.urls")),
               path("api/", include("apps.search.urls")), path("api/", include("apps.dashboard.urls"))]
