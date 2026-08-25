from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Announcement,
    ContactDetail,
    Event,
    GalleryItem,
    Leader,
    MemberProfile,
    MemberRequest,
    MinistryGroup,
    RequestReply,
    Sermon,
)


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )


class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=40, required=False)
    group_interest = forms.ModelChoiceField(
        queryset=MinistryGroup.objects.none(),
        required=False,
        empty_label="Choose a group later",
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "group_interest", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group_interest"].queryset = MinistryGroup.objects.filter(is_active=True)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Please try again.")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data["full_name"].strip()
        email = self.cleaned_data["email"]
        user.username = email
        user.email = email
        user.first_name = full_name
        user.is_active = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            MemberProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get("phone", ""),
                group_interest=self.cleaned_data.get("group_interest"),
            )
        return user


class MemberProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150)

    class Meta:
        model = MemberProfile
        fields = ("full_name", "phone", "group_interest")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].initial = self.instance.user.get_full_name()
        self.fields["group_interest"].queryset = MinistryGroup.objects.filter(is_active=True)

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data["full_name"].strip()
        if commit:
            profile.user.save(update_fields=["first_name"])
            profile.save()
        return profile


class MemberRequestForm(forms.ModelForm):
    class Meta:
        model = MemberRequest
        fields = ("request_type", "subject", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }


class RequestStatusForm(forms.ModelForm):
    class Meta:
        model = MemberRequest
        fields = ("status",)


class RequestReplyForm(forms.ModelForm):
    class Meta:
        model = RequestReply
        fields = ("message",)
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }


class SermonForm(forms.ModelForm):
    class Meta:
        model = Sermon
        fields = (
            "title",
            "speaker",
            "scripture",
            "format",
            "description",
            "media_url",
            "notes",
            "service_date",
            "is_featured",
            "is_published",
        )
        widgets = {
            "service_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ("title", "start_date", "end_date", "time_text", "location", "description", "is_published")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class GalleryItemForm(forms.ModelForm):
    class Meta:
        model = GalleryItem
        fields = ("title", "image", "caption", "date_taken", "is_published")
        widgets = {
            "date_taken": forms.DateInput(attrs={"type": "date"}),
            "caption": forms.Textarea(attrs={"rows": 4}),
        }

class LeaderForm(forms.ModelForm):
    class Meta:
        model = Leader
        fields = ("name", "role", "bio", "photo", "is_active", "sort_order")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }

class ContactDetailForm(forms.ModelForm):
    class Meta:
        model = ContactDetail
        fields = ("label", "detail", "url", "link_label", "is_public", "sort_order")
        widgets = {
            "detail": forms.Textarea(attrs={"rows": 4}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "body", "start_date", "end_date", "is_public")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "body": forms.Textarea(attrs={"rows": 5}),
        }


class MinistryGroupForm(forms.ModelForm):
    class Meta:
        model = MinistryGroup
        fields = ("name", "description", "leader_name", "meeting_info", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }
