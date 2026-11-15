from common import events

from .models import Report
from .services import create_auto_report


@events.subscribe(events.POST_FLAGGED)
def on_post_flagged(p):
    create_auto_report(Report.TargetType.POST, p["post_id"], p["author_id"], p.get("words", []))


@events.subscribe(events.COMMENT_FLAGGED)
def on_comment_flagged(p):
    create_auto_report(Report.TargetType.COMMENT, p["comment_id"], p["author_id"], p.get("words", []))
