from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from ninja import Router

router = Router()


@router.get('/csrf/', url_name='get_csrf_token')
@ensure_csrf_cookie
@csrf_exempt
async def get_csrf_token(request: HttpRequest) -> HttpResponse:
    return HttpResponse()


@router.get('/healthcheck', url_name='healthcheck')
@csrf_exempt
def healthcheck(request: HttpRequest) -> HttpResponse:
    return HttpResponse('Up and running', content_type='text/plain')
