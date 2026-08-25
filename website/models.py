import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


def validate_image_size(upload):
    if upload.size > 5 * 1024 * 1024:
        raise ValidationError("Images must be 5 MB or smaller.")


image_validators = [
    FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
    validate_image_size,
]


class MinistryGroup(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    leader_name = models.CharField(max_length=120, blank=True)
    meeting_info = models.CharField(max_length=180, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sermon(models.Model):
    FORMAT_VIDEO = "video"
    FORMAT_AUDIO = "audio"
    FORMAT_NOTES = "notes"
    FORMAT_CHOICES = [
        (FORMAT_VIDEO, "Video"),
        (FORMAT_AUDIO, "Audio"),
        (FORMAT_NOTES, "Notes"),
    ]

    title = models.CharField(max_length=180)
    speaker = models.CharField(max_length=120, blank=True)
    scripture = models.CharField(max_length=160, blank=True)
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default=FORMAT_VIDEO)
    description = models.TextField(blank=True)
    media_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    service_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-service_date", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def public_status(self):
        if self.media_url:
            return "Open message"
        if self.speaker:
            return f"Speaker: {self.speaker}"
        return "Message details coming soon"


class Event(models.Model):
    title = models.CharField(max_length=180)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    time_text = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=180, blank=True)
    description = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["start_date", "title"]

    def __str__(self):
        return self.title

    @property
    def public_time(self):
        if self.time_text:
            return self.time_text
        if self.start_date:
            return self.start_date.strftime("%B %d, %Y").replace(" 0", " ")
        return "Coming soon"


class GalleryItem(models.Model):
    title = models.CharField(max_length=160)
    image = models.ImageField(upload_to="gallery/", blank=True, validators=image_validators)
    caption = models.TextField(blank=True)
    date_taken = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-date_taken", "-created_at"]

    def __str__(self):
        return self.title


class Leader(models.Model):
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="leaders/", blank=True, validators=image_validators)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} - {self.role}"


class ContactDetail(models.Model):
    label = models.CharField(max_length=120)
    detail = models.TextField()
    url = models.URLField(blank=True)
    link_label = models.CharField(max_length=120, blank=True)
    is_public = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "label"]

    def __str__(self):
        return self.label


class Announcement(models.Model):
    title = models.CharField(max_length=180)
    body = models.TextField()
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return self.title


class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member_profile")
    phone = models.CharField(max_length=40, blank=True)
    group_interest = models.ForeignKey(
        MinistryGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interested_members",
    )
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, null=True)
    verification_sent_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__email"]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    def verify(self):
        self.is_verified = True
        self.verified_at = timezone.now()
        self.verification_token = None
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.save(update_fields=["is_verified", "verification_token", "verified_at", "updated_at"])


class MemberRequest(models.Model):
    TYPE_PRAYER = "prayer"
    TYPE_CONTACT = "contact"
    TYPE_GROUP = "group"
    TYPE_GENERAL = "general"
    REQUEST_TYPE_CHOICES = [
        (TYPE_PRAYER, "Prayer request"),
        (TYPE_CONTACT, "Contact request"),
        (TYPE_GROUP, "Group/ministry request"),
        (TYPE_GENERAL, "General message"),
    ]

    STATUS_OPEN = "open"
    STATUS_PROGRESS = "in_progress"
    STATUS_HANDLED = "handled"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_PROGRESS, "In progress"),
        (STATUS_HANDLED, "Handled"),
    ]

    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE, related_name="requests")
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    subject = models.CharField(max_length=180)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject


class RequestReply(models.Model):
    request = models.ForeignKey(MemberRequest, on_delete=models.CASCADE, related_name="replies")
    staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply to {self.request.subject}"
