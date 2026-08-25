from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    ContactDetail,
    Event,
    MemberProfile,
    MemberRequest,
    MinistryGroup,
    RequestReply,
    Sermon,
)


class WebsitePageTests(TestCase):
    def test_all_primary_pages_return_success(self):
        url_names = ["home", "about", "sermons", "events", "contact"]
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_homepage_contains_english_service_content(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "English Service")
        self.assertContains(response, "Every Sunday, 7:00 AM to 9:00 AM")
        self.assertContains(response, "2026 Theme")
        self.assertContains(response, "Transform Society")
        self.assertContains(response, "/static/website/pentecost-logo.png")
        self.assertContains(response, "Sunday Reactions")
        self.assertContains(response, "Preparing your worship experience")

    def test_contact_page_contains_map_link(self):
        response = self.client.get(reverse("contact"))
        self.assertContains(response, "Open Coordinates in Maps")
        self.assertContains(response, "6.762667,-1.639806")

    def test_contact_page_contains_coordinates(self):
        response = self.client.get(reverse("contact"))
        body = response.content.decode()
        self.assertIn("6°45", body)
        self.assertIn("1°38", body)
        self.assertContains(response, "6.762667, -1.639806")

    def test_contact_page_contains_instagram_link(self):
        response = self.client.get(reverse("contact"))
        self.assertContains(response, "@cop.englishassembly__media")
        self.assertContains(response, "instagram.com/cop.englishassembly__media")

    def test_static_css_path_is_absolute(self):
        response = self.client.get(reverse("about"))
        self.assertContains(response, 'href="/static/website/site.css')

    def test_favicon_link_is_present(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'rel="icon"')
        self.assertContains(response, 'href="/static/website/pentecost-logo.png"')

    def test_public_pages_keep_fallback_content_without_database_records(self):
        response = self.client.get(reverse("events"))
        self.assertContains(response, "Sunday English Service")
        response = self.client.get(reverse("sermons"))
        self.assertContains(response, "Walking in Faith Through Every Season")

    def test_public_pages_use_database_content_when_available(self):
        Event.objects.create(
            title="Youth Sunday",
            time_text="Next Sunday, 7:00 AM",
            description="A special English Service youth gathering.",
        )
        Sermon.objects.create(
            title="Grace for Today",
            speaker="Elder Mensah",
            scripture="Ephesians 2:8",
            description="A message on grace.",
        )
        ContactDetail.objects.create(label="Church Phone", detail="+233 000 000 000")

        self.assertContains(self.client.get(reverse("events")), "Youth Sunday")
        self.assertContains(self.client.get(reverse("sermons")), "Grace for Today")
        self.assertContains(self.client.get(reverse("contact")), "Church Phone")

    def test_public_pages_do_not_render_html_comments(self):
        for url_name in ["home", "about", "sermons", "events", "contact"]:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertNotContains(response, "<!--", html=False)


class AccountPortalDashboardTests(TestCase):
    def test_open_signup_creates_non_staff_unverified_user(self):
        group = MinistryGroup.objects.create(name="Youth Ministry")
        response = self.client.post(
            reverse("account_signup"),
            {
                "full_name": "Ama Boateng",
                "email": "ama@example.com",
                "phone": "0240000000",
                "group_interest": group.pk,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "website": "",
            },
        )

        self.assertRedirects(response, reverse("account_verification_sent"))
        user = User.objects.get(email="ama@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.member_profile.is_verified)
        self.assertEqual(user.member_profile.group_interest, group)

    def test_email_verification_activates_member_portal_access(self):
        user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="StrongPass123!",
            is_active=False,
        )
        profile = MemberProfile.objects.create(user=user)

        response = self.client.get(reverse("account_verify", kwargs={"token": profile.verification_token}))

        self.assertRedirects(response, reverse("account_login"))
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(profile.is_verified)
        self.assertIsNone(profile.verification_token)
        self.assertFalse("_auth_user_id" in self.client.session)

    def test_email_verification_link_is_single_use(self):
        user = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="StrongPass123!",
            is_active=False,
        )
        profile = MemberProfile.objects.create(user=user)
        token = profile.verification_token

        self.assertEqual(
            self.client.get(reverse("account_verify", kwargs={"token": token})).status_code,
            302,
        )
        self.assertEqual(
            self.client.get(reverse("account_verify", kwargs={"token": token})).status_code,
            404,
        )
    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response["Location"])

    def test_normal_member_cannot_access_dashboard(self):
        user = User.objects.create_user(username="member@example.com", email="member@example.com", password="x")
        MemberProfile.objects.create(user=user, is_verified=True)
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard_home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response["Location"])

    def test_staff_can_create_event_from_dashboard(self):
        staff = User.objects.create_user(
            username="editor@example.com",
            email="editor@example.com",
            password="x",
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("dashboard_section_create", kwargs={"section": "events"}),
            {
                "title": "Prayer Night",
                "time_text": "Friday, 6:00 PM",
                "location": "Church auditorium",
                "description": "A focused prayer gathering.",
                "is_published": "on",
            },
        )

        self.assertRedirects(response, reverse("dashboard_section", kwargs={"section": "events"}))
        self.assertTrue(Event.objects.filter(title="Prayer Night").exists())
        self.assertContains(self.client.get(reverse("events")), "Prayer Night")

    def test_member_requests_are_private_to_the_owner(self):
        owner_user = User.objects.create_user(username="owner@example.com", email="owner@example.com", password="x")
        other_user = User.objects.create_user(username="other@example.com", email="other@example.com", password="x")
        owner = MemberProfile.objects.create(user=owner_user, is_verified=True)
        other = MemberProfile.objects.create(user=other_user, is_verified=True)
        owner_request = MemberRequest.objects.create(
            member=owner,
            request_type=MemberRequest.TYPE_PRAYER,
            subject="Please pray",
            message="Prayer request.",
        )
        other_request = MemberRequest.objects.create(
            member=other,
            request_type=MemberRequest.TYPE_CONTACT,
            subject="Other request",
            message="Another request.",
        )
        self.client.force_login(owner_user)

        self.assertEqual(self.client.get(reverse("portal_request_detail", kwargs={"pk": owner_request.pk})).status_code, 200)
        self.assertEqual(self.client.get(reverse("portal_request_detail", kwargs={"pk": other_request.pk})).status_code, 404)

    def test_staff_can_reply_to_member_request(self):
        staff = User.objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password="x",
            is_staff=True,
        )
        member_user = User.objects.create_user(username="member@example.com", email="member@example.com", password="x")
        member = MemberProfile.objects.create(user=member_user, is_verified=True)
        member_request = MemberRequest.objects.create(
            member=member,
            request_type=MemberRequest.TYPE_GENERAL,
            subject="Question",
            message="I have a question.",
        )
        self.client.force_login(staff)

        response = self.client.post(
            reverse("dashboard_request_detail", kwargs={"pk": member_request.pk}),
            {
                "action": "reply",
                "message": "Thanks for reaching out.",
            },
        )

        self.assertRedirects(response, reverse("dashboard_request_detail", kwargs={"pk": member_request.pk}))
        self.assertTrue(RequestReply.objects.filter(request=member_request, message="Thanks for reaching out.").exists())
        member_request.refresh_from_db()
        self.assertEqual(member_request.status, MemberRequest.STATUS_PROGRESS)
