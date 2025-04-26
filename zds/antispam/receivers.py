import logging

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from zds.antispam.spam_detector import SpamDetector
from zds.member.models import Profile

logger = logging.getLogger(__name__)


def get_profile_model():
    return apps.get_model("member", "Profile")


@receiver(post_save, sender=Profile, weak=False)
def check_profile_spam(sender, instance, created, **kwargs):
    """
    Signal handler to detect spam profiles, triggered upon creation or update of biography.
    """
    logger.info(f"Profile signal received for: {instance.user.username} (created={created})")

    if not instance.biography:
        logger.info(f"No bio for {instance.user.username} - skip")
        return

    logger.info(f"Spam check started for {instance.user.username}")
    detector = SpamDetector()
    detector.check_profile(instance)
    logger.info(f"Spam check finished for {instance.user.username}")
