import hashlib
import secrets

from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Func, Value
from django.utils import timezone


class PathwayVersion(models.Model):
    """✨ An immutable snapshot of a pathway document. The database refuses any update to a stored row."""

    document = models.JSONField()
    content_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pathway version {self.pk} ({self.content_hash[:12]})"


class Publication(models.Model):
    """✨ A record that a pathway version became the published one. The latest publication is current.

    Publishing is appended rather than flagged, because a pathway version can never be updated.
    """

    version = models.ForeignKey(PathwayVersion, on_delete=models.PROTECT, related_name="publications")
    published_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def current_version(cls):
        latest = cls.objects.select_related("version").order_by("-pk").first()
        return latest.version if latest else None


class Response(models.Model):
    """✨ A participant's answers to one pathway version, keyed by block identifier.

    A participant stays on the version their response was started against, even after a later one is
    published. Whether a response is test or seed data is decided here on the server, never by a client.
    """

    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="responses")
    version = models.ForeignKey(PathwayVersion, on_delete=models.PROTECT, related_name="responses")
    answers = models.JSONField(default=dict)
    # ✨ When the participant said each section was finished. Completing is their own act, so it is recorded
    # rather than derived: an answer changed afterwards does not quietly undo it.
    completed_sections = models.JSONField(default=dict)
    # ✨ When each answer an author marked `fixed_once_complete` became fixed. Recorded, like completion, so that
    # reopening the section afterwards does not quietly make it changeable again.
    fixed_answers = models.JSONField(default=dict)
    # ✨ When the participant moved past each page of a section with "Continue →", keyed "<section>/<page>". Recorded
    # rather than worked out from the answers, since a page that needs nothing (the coach page) would otherwise hold
    # nobody back.
    pages_moved_past = models.JSONField(default=dict)
    is_test_data = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["participant", "version"], name="one_response_per_participant_per_version"),
        ]

    @classmethod
    def in_progress(cls, participant):
        return cls.objects.select_related("version").filter(participant=participant).order_by("-pk").first()

    def save_answer(self, block_id, value):
        """✨ Store one block's answer in a single UPDATE that merges it into the stored answers.

        The rest of the response is never re-serialised, so a save from a stale copy of this object
        cannot undo an answer saved to another block since. Nor can it change an answer fixed since: the
        same UPDATE skips a fixed answer, so a save that raced a completion writes nothing. Returns whether
        the answer was stored.
        """
        stored = (
            Response.objects.filter(pk=self.pk)
            .exclude(fixed_answers__has_key=block_id)
            .update(
                answers=_MergeJson(F("answers"), Value({block_id: value}, output_field=models.JSONField())),
                updated_at=timezone.now(),
            )
        )
        return stored == 1

    def submit_sort(self, block_id, sort, scores):
        """✨ Store a sort and the result scored from it together, or neither.

        A second sort for the same block raises IntegrityError from the database and changes nothing,
        since retake is not offered yet.
        """
        with transaction.atomic():
            Result.objects.create(response=self, block_id=block_id, scores=scores)
            self.save_answer(block_id, sort)

    def complete_section(self, section_id, fixed_block_ids=()):
        """✨ Record that the participant completed a section, and fix the answers to `fixed_block_ids`, in one UPDATE.

        The caller has already re-checked the section's gate. Completing twice is harmless: the second
        time replaces the completion timestamp and nothing else. An answer fixed before keeps the time it
        was first fixed, since the stored entries are kept over the new ones.
        """
        now = timezone.now()
        stamp = now.isoformat()
        Response.objects.filter(pk=self.pk).update(
            completed_sections=_MergeJson(
                F("completed_sections"), Value({section_id: stamp}, output_field=models.JSONField())
            ),
            fixed_answers=_MergeJson(
                Value({block_id: stamp for block_id in fixed_block_ids}, output_field=models.JSONField()), F("fixed_answers")
            ),
            updated_at=now,
        )

    def move_past_page(self, section_id, page):
        """✨ Record that the participant moved past one page of a section, in one UPDATE that merges it in.

        The caller has already re-checked that the page may be moved past. Pages already moved past are kept, so a tab left
        open on an earlier page never takes back the pages gone through since.
        """
        now = timezone.now()
        moved_past = Value({f"{section_id}/{page}": now.isoformat()}, output_field=models.JSONField())
        Response.objects.filter(pk=self.pk).update(
            pages_moved_past=_MergeJson(F("pages_moved_past"), moved_past),
            updated_at=now,
        )

    def moved_past_by_section(self):
        """✨ The pages moved past, as {section identifier: set of page numbers}, as the hub reads them."""
        moved_past = {}
        for key in self.pages_moved_past:
            section_id, _, page = key.rpartition("/")
            moved_past.setdefault(section_id, set()).add(int(page))
        return moved_past

    def reopen_section(self, section_id):
        """✨ Take back the participant's own act of completing a section, leaving every answer as it is.

        Only this section's record goes: what they completed before or after it is theirs, and reopening
        one section never discards another. Reopening one that was never complete does nothing.
        """
        Response.objects.filter(pk=self.pk).update(
            completed_sections=_WithoutKey(F("completed_sections"), Value(section_id)),
            updated_at=timezone.now(),
        )


    def replace_contacts(self, block_id, contacts, role):
        """✨ Keep exactly these people for one block, in order, in place of whoever it held before, and return them
        as kept, in that order.

        A person carrying the `id` of one this block already holds is that contact, edited in place, so their
        observer's link keeps working; any other id (someone else's, or one since deleted) is taken as a new
        person. Done together or not at all, so a list is never kept half-replaced. Someone taken off the list is
        deleted, not merely hidden: they are another person's details, kept only while the participant wants them,
        and their link goes with them.
        """
        with transaction.atomic():
            held = {str(contact.pk): contact for contact in self.contacts.filter(block_id=block_id)}
            # ✨ Out of the way of the positions about to be taken, which one_contact_per_row keeps one to a row.
            # Postgres checks that row by row as it updates, so the rows move past every position now held too.
            out_of_the_way = max([len(contacts), *(contact.position + 1 for contact in held.values())])
            kept = [held.pop(str(person.get("id") or ""), None) for person in contacts]
            Contact.objects.filter(pk__in=[contact.pk for contact in held.values()]).delete()
            self.contacts.filter(block_id=block_id).update(position=F("position") + out_of_the_way)
            for position, (person, contact) in enumerate(zip(contacts, kept)):
                if contact is None:
                    contact = Contact(response=self, block_id=block_id, role=role)
                contact.position, contact.name, contact.email = position, person["name"], person["email"]
                contact.save()
                kept[position] = contact
        Response.objects.filter(pk=self.pk).update(updated_at=timezone.now())
        return kept

    def answers_with_contacts(self):
        """✨ The stored answers, with each block's contacts read in as its answer, as the gate and progress read it.
        Each contact carries its id, which a contact list's rows send back so a save can tell them apart."""
        kept = {}
        for contact in self.contacts.order_by("block_id", "position"):
            person = {"name": contact.name, "email": contact.email, "id": contact.pk}
            kept.setdefault(contact.block_id, []).append(person)
        return {**self.answers, **kept}


class Contact(models.Model):
    """✨ Someone the participant named: a coach, or a person who knows them well. Kept apart from the answers,
    since these are other people's details, and later each becomes an invitation (ticket 13)."""

    class Role(models.TextChoices):
        COACH = "coach"
        CONTACT = "contact"

    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="contacts")
    block_id = models.CharField(max_length=64)
    role = models.CharField(max_length=16, choices=Role.choices)
    position = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["response", "block_id", "position"], name="one_contact_per_row"),
        ]


class Invitation(models.Model):
    """✨ The one live link a contact has to act as an observer (ADR 0005).

    The link's token is 32 random bytes, and only its hash is kept, so the link itself exists only in the page that
    issued it. Revoking deletes the record, so a revoked link is refused exactly as one that never existed.
    Reissuing replaces the record, which stops the previous link and whatever was claimed through it. Taking the
    contact off the list deletes it too.

    The participant holds a copy of the link, so the observer claims it on first use: claiming exchanges it for a
    secret of 32 random bytes of its own, again kept only as a hash, and the participant's copy is used up. The claimed
    secret lasts as long as the link would have.
    """

    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name="invitation")
    token_hash = models.CharField(max_length=64, unique=True)
    secret_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    claimed_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, contact, lifetime):
        """✨ Give the contact a new link, lasting `lifetime`, in place of any they had. Returns the token, once.

        A new record, not the old one with a new hash, so nothing bound to the old one (a claim, and later the answers
        written through it) is reachable through the new link.
        """
        token = secrets.token_urlsafe(32)
        now = timezone.now()
        with transaction.atomic():
            cls.objects.filter(contact=contact).delete()
            cls.objects.create(contact=contact, token_hash=_hash_of(token), issued_at=now, expires_at=now + lifetime)
        return token

    @classmethod
    def live(cls, token):
        """✨ The invitation a token belongs to, claimed or not, or None if it is wrong, expired or revoked. None
        says which."""
        return cls.objects.filter(token_hash=_hash_of(token), expires_at__gt=timezone.now()).first()

    @classmethod
    def claim(cls, token):
        """✨ Exchange an unclaimed, live token for the observer's own secret, returned once; None if the token is
        dead or already claimed. One UPDATE, so of two claims at once exactly one wins."""
        secret = secrets.token_urlsafe(32)
        now = timezone.now()
        claimed = cls.objects.filter(token_hash=_hash_of(token), expires_at__gt=now, claimed_at__isnull=True).update(
            secret_hash=_hash_of(secret), claimed_at=now
        )
        return secret if claimed else None

    @classmethod
    def claimed_by(cls, secret):
        """✨ The live invitation an observer's secret claimed, with its contact, or None, saying nothing of why."""
        if not secret:
            return None
        return (
            cls.objects.select_related("contact__response__participant", "contact__response__version")
            .filter(secret_hash=_hash_of(secret), expires_at__gt=timezone.now())
            .first()
        )


def _hash_of(token):
    # ✨ A plain SHA-256 is enough: 32 random bytes cannot be guessed, so a slow password hash would add nothing.
    return hashlib.sha256(token.encode()).hexdigest()


class Result(models.Model):
    """✨ The scores computed from one sort answer, kept against its response and so its pathway version.

    Computed once, when the sort is submitted, and never recomputed: a later version with different scoring
    leaves it alone. The scores carry the name of the method that produced them.
    """

    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="results")
    block_id = models.CharField(max_length=64)
    scores = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["response", "block_id"], name="one_result_per_sort_per_response"),
        ]


class _MergeJson(Func):
    """✨ PostgreSQL's jsonb `||`: the right-hand object's keys replace the left's, and every other key is kept."""

    arg_joiner = " || "
    template = "%(expressions)s"
    output_field = models.JSONField()


class _WithoutKey(Func):
    """✨ PostgreSQL's jsonb `-`: one key removed in a single UPDATE, every other key left as it was."""

    arg_joiner = " - "
    template = "%(expressions)s"
    output_field = models.JSONField()
