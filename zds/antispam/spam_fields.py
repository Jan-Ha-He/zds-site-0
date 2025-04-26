from zds.forum.models import Comment
from zds.member.models import Profile

spam_fields = [
    {
        "model": Profile,
        "field": "biography",
        "scope": "PROFILE",
        "get_instance_info": lambda instance: f"Profile of user '{instance.user.username}'",
    },
    {
        "model": Comment,
        "field": "text",
        "scope": "FORUM",
        "get_instance_info": lambda instance: f"Comment by '{instance.author.username}'",
    },
]
