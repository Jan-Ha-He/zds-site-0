import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AntispamConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "zds.antispam"

    def ready(self):
        logger.info("Antispam app is ready. Importing receivers...")
        from . import receivers  # noqa
