"""Field-level audit of human writes (C79/V81).

Only the human entry points call this: `MemberSerializer`, `MemberFileSerializer`
and `MemberLinkViewSet`. `members/utils.py::get_members_all` is the hourly sync
and never imports this module, which is what makes V81's "sync adds zero rows"
hold by construction rather than by a flag.
"""

from .models import SiteChangeLog


def _stringify(value):
    """File fields -> stored relative path; lookups -> name; M2M -> pks."""
    if value is None:
        return None
    if not isinstance(value, (str, bytes)):
        if hasattr(value, "all"):
            return ",".join(str(pk) for pk in value.all().values_list("pk", flat=True))
        if hasattr(value, "name"):
            return str(value.name) or None
    return str(value)


def snapshot(instance, fields):
    return {field: _stringify(getattr(instance, field, None)) for field in fields}


def log_changes(instance, user, action, before, batch_id=None, clear=False):
    """Append one row per field whose stored value actually changed."""
    after = {field: None for field in before} if clear else snapshot(instance, before)
    member = getattr(instance, "member", instance)
    rows = [
        SiteChangeLog(
            member=member,
            user=user,
            batch_id=batch_id,
            action=action,
            field=field,
            old_value=old,
            new_value=after.get(field),
        )
        for field, old in before.items()
        if old != after.get(field)
    ]
    if rows:
        SiteChangeLog.objects.bulk_create(rows)
    return len(rows)


def audit(instance, context, action, before, clear=False):
    """`log_changes` bound to the serializer/request context (C79)."""
    request = context.get("request")
    user = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        user = None
    return log_changes(
        instance,
        user,
        context.get("changelog_action", action),
        before,
        context.get("changelog_batch"),
        clear,
    )
