from common import events

from . import services


@events.subscribe(events.FRIENDSHIP_CHANGED)
def refresh_feed_on_friendship(payload):
    services.invalidate_feed(payload.get("user_ids", []))


@events.subscribe(events.POST_CREATED)
def refresh_feed_on_new_post(payload):
    if not payload.get("group_id"):
        services._invalidate_author_audience(payload["author_id"])


@events.subscribe(events.GROUP_DELETED)
def remove_group_posts(payload):
    services.soft_delete_group_posts(payload["group_id"])
