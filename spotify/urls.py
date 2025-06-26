from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login),
    path('callback/', views.callback),
    path('refresh_token/', views.refresh_token_view),
    path('status/', views.status_view),
    path('testing/', views.testing),
]