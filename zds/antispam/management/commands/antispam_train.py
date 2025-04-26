from django.core.management.base import BaseCommand

from zds.antispam.spam_model_manager import SpamModelManager


class Command(BaseCommand):
    help = "Retrain the spam filter model and save it to a file."

    def handle(self, *args, **options):
        self.stdout.write("Starting retraining of the spam filter model...")
        model_manager = SpamModelManager()
        model_manager.train()
        self.stdout.write("Retraining completed successfully.")
