from django.urls import path

from inference import views


app_name = "inference"


urlpatterns = [
    path("", views.home, name="home"),
    path("api/infer/", views.infer_image, name="infer_image"),
]
