from django.apps import AppConfig


class DocusignintegrationConfig(AppConfig):
    name = 'DocuSignIntegration'

    def ready(self):
        import DocuSignIntegration.processor  # noqa: F401
