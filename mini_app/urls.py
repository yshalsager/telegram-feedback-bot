from django.urls import path

from mini_app.views import app, validate_user

urlpatterns = [
    path('app/', app, name='app'),
    path('app/validate_user/', validate_user, name='validate_user'),
]
