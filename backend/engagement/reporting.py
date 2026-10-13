from collections import defaultdict
from datetime import timedelta
from django.db.models import Count, Sum, Q
from django.utils import timezone
from learning.models import QuizAttempt
from .models import Like, EngagementEvent
from .services import PILOT_ZONE


def aggregate_report(days=7):
    if not 1 <= days <= 90:
        raise ValueError("Choose between 1 and 90 days.")
    today = timezone.localdate(timezone=PILOT_ZONE)
    start = today - timedelta(days=days - 1)
    groups = {}
    active_days = defaultdict(set)
    events = EngagementEvent.objects.filter(day__gte=start, day__lte=today).select_related("unit")
    for event in events.iterator():
        key = (event.unit.key, str(event.card_identity), tuple(sorted(event.context.items())))
        if key not in groups:
            groups[key] = {"unit_key": event.unit.key, "card_identity": str(event.card_identity), **event.context,
                           "daily_views": 0, "viewers": set(), "dare_shown": 0, "dare_accepted": 0}
        group = groups[key]
        active_days[event.day.isoformat()].add(event.user_id)
        if event.kind == "view":
            group["daily_views"] += 1
            group["viewers"].add(event.user_id)
        else:
            group[event.kind] += 1
    active_like_users = defaultdict(set)
    for unit_key, identity, user_id in Like.objects.filter(is_active=True).values_list("unit__key", "card_identity", "user_id").iterator():
        active_like_users[(unit_key, str(identity))].add(user_id)
    content = []
    for group in groups.values():
        viewers = group.pop("viewers")
        group["unique_viewers"] = len(viewers)
        group["viewers_with_active_like"] = len(viewers & active_like_users[(group["unit_key"], group["card_identity"])])
        content.append(group)
    visits = defaultdict(int)
    for users in active_days.values():
        for user in users:
            visits[user] += 1
    likes = [{"unit_key": key[0], "card_identity": key[1], "active_likes": len(users)}
             for key, users in sorted(active_like_users.items()) if users]
    # Date boundaries are Lagos days, including quizzes completed around UTC midnight.
    from datetime import datetime, time
    begin = timezone.make_aware(datetime.combine(start, time.min), PILOT_ZONE)
    end = timezone.make_aware(datetime.combine(today + timedelta(days=1), time.min), PILOT_ZONE)
    quizzes = []
    for row in QuizAttempt.objects.filter(completed_at__gte=begin, completed_at__lt=end).values("unit__key", "version_id").annotate(
            attempts=Count("id"), candidates=Count("user_id", distinct=True), first_attempts=Count("id", filter=Q(number=1)),
            first_correct=Sum("score", filter=Q(number=1)), first_questions=Sum("total", filter=Q(number=1))):
        quizzes.append({"unit_key": row["unit__key"], "version": row["version_id"], "attempts": row["attempts"],
                        "unique_candidates": row["candidates"], "first_attempts": row["first_attempts"],
                        "first_correct": row["first_correct"] or 0, "first_questions": row["first_questions"] or 0,
                        "practice_attempts": row["attempts"] - row["first_attempts"]})
    return {"generated_at": timezone.now().isoformat(), "timezone": "Africa/Lagos", "from": start.isoformat(), "through": today.isoformat(),
            "content": content, "active_likes_as_of_now": likes, "quiz_summary": quizzes,
            "daily_active_candidates": [{"day": day, "candidates": len(users)} for day, users in sorted(active_days.items())],
            "candidates_active_on_multiple_days": sum(count > 1 for count in visits.values())}
