from django.contrib.auth import get_user_model

from common import events

from .models import Profile


@events.subscribe(events.USER_REGISTERED)
def create_profile(payload):
    user = get_user_model().objects.filter(id=payload["user_id"]).first()
    if not user:
        return
    profile, _ = Profile.objects.get_or_create(user=user)
    if payload.get("birth_date") and not profile.birth_date:
        profile.birth_date = payload["birth_date"]
        profile.save(update_fields=["birth_date"])
