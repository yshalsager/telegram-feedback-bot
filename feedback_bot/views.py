from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views import View


class MiniAppView(View):
    def get(self, request, *args, **kwargs):
        index_path = settings.SVELTEKIT_BUILD_DIR / 'index.html'
        if not index_path.is_file():
            raise Http404('Mini app build not found')
        return HttpResponse(index_path.read_bytes(), content_type='text/html')


class BuildAssetView(View):
    asset_name: str = ''
    content_type: str = 'application/octet-stream'

    def get(self, request, *args, **kwargs):
        if not self.asset_name:
            raise Http404('Asset not specified')
        file_path = settings.SVELTEKIT_BUILD_DIR / self.asset_name
        if not file_path.is_file():
            raise Http404('Asset not found')
        response = FileResponse(file_path, content_type=self.content_type)
        return response
