from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointment_app'

    def ready(self):
        import appointment_app.signals  # Import signals to activate them