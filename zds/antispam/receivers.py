# zds/antispam/receivers.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from zds.antispam.spam_detector import SpamDetector
from zds.antispam.spam_fields import spam_fields


@receiver(post_save)
def analyze_record(sender, instance, **kwargs):
    """
    Signal handler to detect spam in configured fields.
    """
    for field_config in spam_fields:
        if isinstance(instance, field_config["model"]):
            field_value = getattr(instance, field_config["field"], None)
            if field_value:
                detector = SpamDetector()
                if detector.check_text(field_value):
                    detector.send_alert(instance, field_config["field"])
