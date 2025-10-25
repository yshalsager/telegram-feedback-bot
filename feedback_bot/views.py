from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import Http404, HttpResponse
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

    async def get(self, request, asset: str = '', *args, **kwargs) -> HttpResponse:
        asset = (asset or '').strip('/')
        name = (self.asset_name or '').strip('/')
        if asset:
            name = f'{name}/{asset}' if name else asset
        if not name:
            raise Http404('Asset not specified')

        base = settings.SVELTEKIT_BUILD_DIR.resolve()
        file_path = (base / name).resolve()
        if file_path != base and base not in file_path.parents:
            raise Http404('Asset not found')
        if not file_path.is_file():
            raise Http404('Asset not found')
        return HttpResponse(
            await sync_to_async(file_path.read_bytes)(), content_type=self.content_type
        )
