from django.conf import settings
from django.urls import path, re_path

from feedback_bot.views import BuildAssetView, MiniAppView

urlpatterns = []

if not settings.DEBUG:
    urlpatterns += [
        path(
            'favicon.ico',
            BuildAssetView.as_view(asset_name='favicon.ico', content_type='image/x-icon'),
            name='mini_app_favicon_ico',
        ),
        path(
            'favicon.svg',
            BuildAssetView.as_view(asset_name='favicon.svg', content_type='image/svg+xml'),
            name='mini_app_favicon_svg',
        ),
        path(
            'robots.txt',
            BuildAssetView.as_view(asset_name='robots.txt', content_type='text/plain'),
            name='mini_app_robots',
        ),
        path(
            'screenshots/<path:asset>',
            BuildAssetView.as_view(asset_name='screenshots', content_type='image/png'),
            name='screenshots',
        ),
        path('', MiniAppView.as_view(), name='landing'),
        re_path(r'^app(?:/.*)?$', MiniAppView.as_view(), name='mini_app'),
    ]
