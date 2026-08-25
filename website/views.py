from functools import wraps
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .content import (
    CHURCH_INFO,
    CONTACT_ITEMS,
    EVENT_ITEMS,
    HOME_HIGHLIGHTS,
    NAVIGATION,
    REACTION_ITEMS,
    SERMON_FORMATS,
    SERMON_SAMPLES,
    SERVICE_PILLARS,
    THEME_2026,
    VISITOR_EXPECTATIONS,
)
from .forms import (
    AnnouncementForm,
    ContactDetailForm,
    EventForm,
    GalleryItemForm,
    LeaderForm,
    MemberProfileForm,
    MemberRequestForm,
    MinistryGroupForm,
    RequestReplyForm,
    RequestStatusForm,
    SermonForm,
    SignUpForm,
)
from .models import (
    Announcement,
    ContactDetail,
    Event,
    GalleryItem,
    Leader,
    MemberProfile,
    MemberRequest,
    MinistryGroup,
    Sermon,
)


DASHBOARD_SECTIONS = {
    "sermons": {
        "title": "Sermons",
        "model": Sermon,
        "form": SermonForm,
        "description": "Manage video, audio, notes, speakers, and scripture references.",
        "search": ("title", "speaker", "scripture"),
    },
    "events": {
        "title": "Events",
        "model": Event,
        "form": EventForm,
        "description": "Manage Sunday service details, programs, and upcoming gatherings.",
        "search": ("title", "location", "description"),
    },
    "gallery": {
        "title": "Gallery",
        "model": GalleryItem,
        "form": GalleryItemForm,
        "description": "Upload visual recaps and church moments.",
        "search": ("title", "caption"),
    },
    "leaders": {
        "title": "Leaders",
        "model": Leader,
        "form": LeaderForm,
        "description": "Add pastor and service leader profiles.",
        "search": ("name", "role", "bio"),
    },
    "contacts": {
        "title": "Contact Details",
        "model": ContactDetail,
        "form": ContactDetailForm,
        "description": "Manage phone, email, social, and prayer connection details.",
        "search": ("label", "detail"),
    },
    "announcements": {
        "title": "Announcements",
        "model": Announcement,
        "form": AnnouncementForm,
        "description": "Publish public updates for everyone who visits the site.",
        "search": ("title", "body"),
    },
    "groups": {
        "title": "Groups",
        "model": MinistryGroup,
        "form": MinistryGroupForm,
        "description": "Organize ministry groups and member interests.",
        "search": ("name", "leader_name", "description"),
    },
}


def build_base_context():
    base_context = dict(CHURCH_INFO)
    base_context["navigation"] = NAVIGATION
    base_context["theme_2026"] = THEME_2026
    base_context["maps_search_url"] = (
        "https://www.google.com/maps/search/?api=1&query="
        f"{CHURCH_INFO['latitude']},{CHURCH_INFO['longitude']}"
    )
    return base_context


def render_page(request, template_name, extra_context=None):
    context = build_base_context()
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)


def active_announcements():
    today = timezone.localdate()
    return Announcement.objects.filter(is_public=True, start_date__lte=today).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )


def public_events():
    events = list(Event.published.all())
    if events:
        return [
            {
                "title": event.title,
                "time": event.public_time,
                "description": event.description,
            }
            for event in events
        ]
    return EVENT_ITEMS


def public_sermons():
    sermons = list(Sermon.published.all()[:6])
    if sermons:
        return [
            {
                "title": sermon.title,
                "format": sermon.get_format_display(),
                "scripture": sermon.scripture,
                "status": sermon.public_status,
                "media_url": sermon.media_url,
                "description": sermon.description,
            }
            for sermon in sermons
        ]
    return SERMON_SAMPLES


def public_contacts():
    contacts = list(ContactDetail.objects.filter(is_public=True))
    if contacts:
        return [
            {
                "title": contact.label,
                "detail": contact.detail,
                "url": contact.url,
                "label": contact.link_label or contact.url,
            }
            for contact in contacts
        ]
    return CONTACT_ITEMS


def public_leaders():
    return Leader.objects.filter(is_active=True)


def home(request):
    return render_page(
        request,
        "website/home.html",
        {
            "page_title": CHURCH_INFO["full_name"],
            "meta_description": CHURCH_INFO["summary"],
            "home_highlights": HOME_HIGHLIGHTS,
            "reaction_items": REACTION_ITEMS,
            "event_items": public_events(),
            "sermon_formats": SERMON_FORMATS,
            "theme_2026": THEME_2026,
            "announcements": active_announcements()[:3],
        },
    )


def about(request):
    return render_page(
        request,
        "website/about.html",
        {
            "page_title": f"About | {CHURCH_INFO['full_name']}",
            "meta_description": (
                "Learn about the vision and worship culture of the English "
                "Service at Church of Pentecost, New Kyekyere District."
            ),
            "service_pillars": SERVICE_PILLARS,
            "visitor_expectations": VISITOR_EXPECTATIONS,
            "leaders": public_leaders(),
        },
    )


def sermons(request):
    return render_page(
        request,
        "website/sermons.html",
        {
            "page_title": f"Sermons | {CHURCH_INFO['full_name']}",
            "meta_description": (
                "Explore the sermon page for video, audio, and teaching notes "
                "from the English Service."
            ),
            "sermon_formats": SERMON_FORMATS,
            "sermon_samples": public_sermons(),
        },
    )


def events(request):
    return render_page(
        request,
        "website/events.html",
        {
            "page_title": f"Events | {CHURCH_INFO['full_name']}",
            "meta_description": (
                "See service schedules, program announcements, and upcoming "
                "church moments for the English Service."
            ),
            "event_items": public_events(),
            "announcements": active_announcements(),
        },
    )


def contact(request):
    return render_page(
        request,
        "website/contact.html",
        {
            "page_title": f"Contact | {CHURCH_INFO['full_name']}",
            "meta_description": (
                "Plan your visit to the English Service and find location, "
                "service time, and future contact channels."
            ),
            "contact_items": public_contacts(),
        },
    )


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def signup_is_limited(request):
    key = f"signup-attempts:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= 5:
        return True
    cache.set(key, count + 1, 600)
    return False


def send_verification_email(request, user):
    profile = user.member_profile
    verify_url = request.build_absolute_uri(
        reverse("account_verify", kwargs={"token": profile.verification_token})
    )
    send_mail(
        "Verify your English Service account",
        (
            f"Hello {profile.display_name},\n\n"
            "Please verify your account using this link:\n"
            f"{verify_url}\n\n"
            "Church of Pentecost, New Kyekyere District English Service"
        ),
        None,
        [user.email],
        fail_silently=False,
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("portal")
    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if not settings.ACCOUNT_SIGNUP_ENABLED:
            form.add_error(None, "Account registration is temporarily unavailable. Please contact the church team.")
        elif signup_is_limited(request):
            form.add_error(None, "Too many sign-up attempts. Please try again later.")
        elif form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            return redirect("account_verification_sent")
    return render_page(
        request,
        "website/accounts/signup.html",
        {
            "page_title": "Create Account | " + CHURCH_INFO["full_name"],
            "meta_description": "Create an English Service member account.",
            "form": form,
        },
    )


def verification_sent(request):
    return render_page(
        request,
        "website/accounts/verification_sent.html",
        {
            "page_title": "Verify Account | " + CHURCH_INFO["full_name"],
            "meta_description": "Check your email to verify your English Service account.",
        },
    )


def verify_account(request, token):
    with transaction.atomic():
        profile = get_object_or_404(
            MemberProfile.objects.select_for_update(),
            verification_token=token,
            is_verified=False,
        )
        if profile.verification_sent_at < timezone.now() - timedelta(hours=24):
            raise Http404("This verification link has expired.")
        profile.verify()
    messages.success(request, "Your account is verified. Please log in to open the member portal.")
    return redirect("account_login")


def verified_member_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return redirect("dashboard_home")
        profile = getattr(request.user, "member_profile", None)
        if not profile or not profile.is_verified:
            messages.warning(request, "Please verify your account before opening the portal.")
            return redirect("account_login")
        return view_func(request, *args, **kwargs)

    return wrapper


@verified_member_required
def portal(request):
    profile = request.user.member_profile
    profile_form = MemberProfileForm(instance=profile)
    request_form = MemberRequestForm()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = MemberProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("portal")
        elif action == "request":
            request_form = MemberRequestForm(request.POST)
            if request_form.is_valid():
                member_request = request_form.save(commit=False)
                member_request.member = profile
                member_request.save()
                messages.success(request, "Your request has been sent.")
                return redirect("portal")
    return render_page(
        request,
        "website/portal.html",
        {
            "page_title": "Member Portal | " + CHURCH_INFO["full_name"],
            "meta_description": "Manage your English Service member profile and requests.",
            "profile": profile,
            "profile_form": profile_form,
            "request_form": request_form,
            "member_requests": profile.requests.prefetch_related("replies")[:8],
        },
    )


@verified_member_required
def portal_request_detail(request, pk):
    member_request = get_object_or_404(
        MemberRequest.objects.prefetch_related("replies"),
        pk=pk,
        member=request.user.member_profile,
    )
    return render_page(
        request,
        "website/portal_request_detail.html",
        {
            "page_title": member_request.subject + " | Member Portal",
            "meta_description": "View your English Service request and replies.",
            "member_request": member_request,
        },
    )


def staff_check(user):
    return user.is_authenticated and user.is_staff


staff_required = user_passes_test(staff_check, login_url="account_login")


def dashboard_context(extra=None):
    context = {
        "dashboard_sections": DASHBOARD_SECTIONS,
    }
    if extra:
        context.update(extra)
    return context


def section_config(section):
    config = DASHBOARD_SECTIONS.get(section)
    if not config:
        raise Http404("Dashboard section not found.")
    return config


def search_queryset(queryset, fields, query):
    if not query:
        return queryset
    filters = Q()
    for field in fields:
        filters |= Q(**{f"{field}__icontains": query})
    return queryset.filter(filters)


def dashboard_row(item):
    if isinstance(item, Sermon):
        return {
            "title": item.title,
            "subtitle": item.speaker or item.scripture or "Sermon details",
            "badge": item.get_format_display(),
            "is_live": item.is_published,
        }
    if isinstance(item, Event):
        return {
            "title": item.title,
            "subtitle": item.public_time,
            "badge": "Published" if item.is_published else "Draft",
            "is_live": item.is_published,
        }
    if isinstance(item, GalleryItem):
        return {
            "title": item.title,
            "subtitle": item.caption or "Gallery item",
            "badge": "Published" if item.is_published else "Draft",
            "is_live": item.is_published,
        }
    if isinstance(item, Leader):
        return {
            "title": item.name,
            "subtitle": item.role,
            "badge": "Active" if item.is_active else "Hidden",
            "is_live": item.is_active,
        }
    if isinstance(item, ContactDetail):
        return {
            "title": item.label,
            "subtitle": item.detail,
            "badge": "Public" if item.is_public else "Hidden",
            "is_live": item.is_public,
        }
    if isinstance(item, Announcement):
        return {
            "title": item.title,
            "subtitle": item.body,
            "badge": "Public" if item.is_public else "Hidden",
            "is_live": item.is_public,
        }
    if isinstance(item, MinistryGroup):
        return {
            "title": item.name,
            "subtitle": item.description or item.meeting_info or "Group",
            "badge": "Active" if item.is_active else "Hidden",
            "is_live": item.is_active,
        }
    return {"title": str(item), "subtitle": "", "badge": "", "is_live": True}


@staff_required
def dashboard_home(request):
    overview_cards = [
        ("Sermons", Sermon.objects.count()),
        ("Events", Event.objects.count()),
        ("Gallery", GalleryItem.objects.count()),
        ("Members", MemberProfile.objects.count()),
        ("Open Requests", MemberRequest.objects.filter(status=MemberRequest.STATUS_OPEN).count()),
        ("Announcements", Announcement.objects.count()),
    ]
    return render_page(
        request,
        "website/dashboard/overview.html",
        dashboard_context(
            {
                "page_title": "Dashboard | " + CHURCH_INFO["full_name"],
                "meta_description": "Staff dashboard for the English Service website.",
                "overview_cards": overview_cards,
                "latest_requests": MemberRequest.objects.select_related("member__user")[:6],
            }
        ),
    )


@staff_required
def dashboard_section_list(request, section):
    config = section_config(section)
    query = request.GET.get("q", "").strip()
    queryset = search_queryset(config["model"].objects.all(), config["search"], query)
    rows = [(item, dashboard_row(item)) for item in queryset[:80]]
    return render_page(
        request,
        "website/dashboard/section_list.html",
        dashboard_context(
            {
                "page_title": config["title"] + " | Dashboard",
                "meta_description": config["description"],
                "section": section,
                "section_title": config["title"],
                "section_description": config["description"],
                "rows": rows,
                "query": query,
            }
        ),
    )


@staff_required
def dashboard_section_create(request, section):
    config = section_config(section)
    form_class = config["form"]
    form = form_class(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, config["title"] + " item saved.")
        return redirect("dashboard_section", section=section)
    return render_page(
        request,
        "website/dashboard/section_form.html",
        dashboard_context(
            {
                "page_title": "Add " + config["title"] + " | Dashboard",
                "meta_description": "Add dashboard content.",
                "section": section,
                "section_title": config["title"],
                "form": form,
                "form_title": "Add " + config["title"],
            }
        ),
    )


@staff_required
def dashboard_section_edit(request, section, pk):
    config = section_config(section)
    instance = get_object_or_404(config["model"], pk=pk)
    form_class = config["form"]
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, config["title"] + " item updated.")
        return redirect("dashboard_section", section=section)
    return render_page(
        request,
        "website/dashboard/section_form.html",
        dashboard_context(
            {
                "page_title": "Edit " + config["title"] + " | Dashboard",
                "meta_description": "Edit dashboard content.",
                "section": section,
                "section_title": config["title"],
                "form": form,
                "form_title": "Edit " + str(instance),
            }
        ),
    )


@staff_required
def dashboard_section_delete(request, section, pk):
    config = section_config(section)
    instance = get_object_or_404(config["model"], pk=pk)
    if request.method == "POST":
        instance.delete()
        messages.success(request, config["title"] + " item deleted.")
        return redirect("dashboard_section", section=section)
    return render_page(
        request,
        "website/dashboard/confirm_delete.html",
        dashboard_context(
            {
                "page_title": "Delete " + config["title"] + " | Dashboard",
                "meta_description": "Delete dashboard content.",
                "section": section,
                "section_title": config["title"],
                "object": instance,
            }
        ),
    )


@staff_required
def dashboard_requests(request):
    status = request.GET.get("status", "")
    requests = MemberRequest.objects.select_related("member__user", "member__group_interest")
    if status:
        requests = requests.filter(status=status)
    return render_page(
        request,
        "website/dashboard/requests.html",
        dashboard_context(
            {
                "page_title": "Member Requests | Dashboard",
                "meta_description": "Review English Service member requests.",
                "member_requests": requests[:100],
                "status": status,
                "status_choices": MemberRequest.STATUS_CHOICES,
            }
        ),
    )


@staff_required
def dashboard_request_detail(request, pk):
    member_request = get_object_or_404(
        MemberRequest.objects.select_related("member__user").prefetch_related("replies"),
        pk=pk,
    )
    status_form = RequestStatusForm(instance=member_request)
    reply_form = RequestReplyForm()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "status":
            status_form = RequestStatusForm(request.POST, instance=member_request)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Request status updated.")
                return redirect("dashboard_request_detail", pk=member_request.pk)
        elif action == "reply":
            reply_form = RequestReplyForm(request.POST)
            if reply_form.is_valid():
                reply = reply_form.save(commit=False)
                reply.request = member_request
                reply.staff = request.user
                reply.save()
                if member_request.status == MemberRequest.STATUS_OPEN:
                    member_request.status = MemberRequest.STATUS_PROGRESS
                    member_request.save(update_fields=["status", "updated_at"])
                messages.success(request, "Reply sent.")
                return redirect("dashboard_request_detail", pk=member_request.pk)
    return render_page(
        request,
        "website/dashboard/request_detail.html",
        dashboard_context(
            {
                "page_title": member_request.subject + " | Dashboard",
                "meta_description": "Reply to a member request.",
                "member_request": member_request,
                "status_form": status_form,
                "reply_form": reply_form,
            }
        ),
    )
