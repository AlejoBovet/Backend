from django.apps import AppConfig


class ApirestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apirest'

    def ready(self):
        import apirest.signals  # Importar las señales para registrarlas
