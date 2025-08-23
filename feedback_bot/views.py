from django.views.generic import TemplateView


class MiniAppView(TemplateView):
    template_name = 'index.html'
