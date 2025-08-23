from django.conf import settings
from django.urls import path

from feedback_bot.views import MiniAppView

urlpatterns = []

if not settings.DEBUG:
    urlpatterns += [
        path('app/', MiniAppView.as_view(), name='mini_app'),
    ]
