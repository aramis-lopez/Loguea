from django.views.generic import TemplateView


class AppView(TemplateView):
    """SPA ligera para login y gestión de productos (consume la API JWT)."""

    template_name = "web/app.html"
