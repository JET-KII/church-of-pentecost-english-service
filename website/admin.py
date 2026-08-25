from django.contrib import admin

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


@admin.register(Sermon)
class SermonAdmin(admin.ModelAdmin):
    list_display = ("title", "speaker", "format", "service_date", "is_published")
    list_filter = ("format", "is_published", "is_featured")
    search_fields = ("title", "speaker", "scripture")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "time_text", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "location", "description")


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "date_taken", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "caption")


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "role")


@admin.register(ContactDetail)
class ContactDetailAdmin(admin.ModelAdmin):
    list_display = ("label", "is_public", "sort_order")
    list_filter = ("is_public",)
    search_fields = ("label", "detail")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_public")
    list_filter = ("is_public",)
    search_fields = ("title", "body")


@admin.register(MinistryGroup)
class MinistryGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "leader_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "leader_name", "description")


class RequestReplyInline(admin.TabularInline):
    model = RequestReply
    extra = 0


@admin.register(MemberRequest)
class MemberRequestAdmin(admin.ModelAdmin):
    list_display = ("subject", "member", "request_type", "status", "created_at")
    list_filter = ("request_type", "status")
    search_fields = ("subject", "message", "member__user__email")
    inlines = [RequestReplyInline]


@admin.register(MemberProfile)
class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "phone", "group_interest", "is_verified")
    list_filter = ("is_verified", "group_interest")
    search_fields = ("user__first_name", "user__last_name", "user__email", "phone")
