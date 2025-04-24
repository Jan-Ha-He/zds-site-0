import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

logger = logging.getLogger(__name__)

# arguments: instance, user, by_email
ping = Signal()

# arguments: instance, user
unping = Signal()


def get_profile_model():
    return apps.get_model("member", "Profile")


@receiver(post_save)
def check_profile_spam(sender, instance, created, **kwargs):
    from zds.antispam.spam_detector import SpamDetector

    """
    Signal handler to detect spam profiles, triggered upon creation or update of biography.
    """
    if sender == get_profile_model():
        logger.info(f"Profile signal received for: {instance.user.username} (created={created})")

        if not instance.biography:
            logger.info(f"No bio for {instance.user.username} - skip")
            return

        logger.info(f"Spam check started for {instance.user.username}")
        detector = SpamDetector()
        detector.check_profile(instance)
        logger.info(f"Spam check finished for {instance.user.username}")
