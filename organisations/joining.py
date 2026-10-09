"""✨ The join link a visitor holds in their session while they sign up and consent on the way to joining."""

from organisations.models import Group

_HELD_TOKEN = "organisations.join_token"


def hold(session, group):
    session[_HELD_TOKEN] = group.join_token


def release(session):
    session.pop(_HELD_TOKEN, None)


def holds_a_working_join_link(session):
    """✨ Whether the session holds a join link some group still has. A replaced one no longer counts."""
    token = session.get(_HELD_TOKEN)
    return token is not None and Group.objects.filter(join_token=token).exists()
