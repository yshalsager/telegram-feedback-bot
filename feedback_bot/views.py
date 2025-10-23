from django.conf import settings
from django.http import Http404, HttpResponse
from django.views import View


class MiniAppView(View):
    def get(self, request, *args, **kwargs):
        index_path = settings.SVELTEKIT_BUILD_DIR / 'index.html'
        if not index_path.is_file():
            raise Http404('Mini app build not found')
        return HttpResponse(index_path.read_bytes(), content_type='text/html')
