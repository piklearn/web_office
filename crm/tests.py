from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (Activity, Customer, EmployeeProfile, Payment, Role, Task, TaskStatus,
                     can_see_finance, get_role)

User = get_user_model()


def make_user(name, role=Role.EMPLOYEE, **kw):
    u = User.objects.create_user(name, password="x", **kw)
    EmployeeProfile.objects.create(user=u, role=role)
    return u


class RemainingAndRolesTests(TestCase):
    def test_remaining_is_total_minus_payments(self):
        c = Customer.objects.create(full_name="الف", total_amount=1000)
        Payment.objects.create(customer=c, amount=300)
        Payment.objects.create(customer=c, amount=200)
        self.assertEqual(c.paid_total, 500)
        self.assertEqual(c.remaining, 500)

    def test_roles(self):
        self.assertEqual(get_role(make_user("m", Role.MANAGER)), Role.MANAGER)
        self.assertTrue(can_see_finance(make_user("s", Role.SALES)))
        self.assertFalse(can_see_finance(make_user("e", Role.EMPLOYEE)))


class TimelineSignalTests(TestCase):
    def test_task_status_change_is_logged(self):
        u = make_user("u")
        c = Customer.objects.create(full_name="الف")
        t = Task.objects.create(customer=c, title="تماس", assignee=u)
        before = Activity.objects.filter(customer=c).count()
        t.status = TaskStatus.DONE
        t.save()
        self.assertEqual(Activity.objects.filter(customer=c).count(), before + 1)


class QuickStatusTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.other = make_user("other")
        self.c = Customer.objects.create(full_name="الف")
        self.t = Task.objects.create(customer=self.c, title="تماس", assignee=self.owner)

    def post(self, user, status, **extra):
        self.client.force_login(user)
        return self.client.post(reverse("crm:task_status", args=[self.t.pk]),
                                {"status": status, **extra}, HTTP_HX_REQUEST="true")

    def test_assignee_can_change_status(self):
        r = self.post(self.owner, TaskStatus.REVIEWING, mode="row")
        self.assertEqual(r.status_code, 200)
        self.t.refresh_from_db()
        self.assertEqual(self.t.status, TaskStatus.REVIEWING)

    def test_other_employee_is_forbidden(self):
        self.assertEqual(self.post(self.other, TaskStatus.DONE).status_code, 403)

    def test_invalid_status_rejected(self):
        self.assertEqual(self.post(self.owner, "nope").status_code, 400)


class ModalAndAccessTests(TestCase):
    def test_modal_save_refreshes_page(self):
        u = make_user("u")
        c = Customer.objects.create(full_name="الف")
        self.client.force_login(u)
        url = reverse("crm:contact_add", args=[c.pk])
        self.assertContains(self.client.get(url, HTTP_HX_REQUEST="true"), 'role="dialog"')
        r = self.client.post(url, {"name": "علی"}, HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r["HX-Refresh"], "true")
        self.assertEqual(c.contacts.count(), 1)

    def test_reports_only_for_finance_roles(self):
        self.client.force_login(make_user("e"))
        self.assertEqual(self.client.get(reverse("crm:reports")).status_code, 403)
        self.client.force_login(make_user("s", Role.SALES))
        self.assertEqual(self.client.get(reverse("crm:reports")).status_code, 200)

    def test_debtor_filter_and_customer_list(self):
        self.client.force_login(make_user("m", Role.MANAGER))
        a = Customer.objects.create(full_name="بدهکار", total_amount=1000)
        Payment.objects.create(customer=a, amount=400)
        b = Customer.objects.create(full_name="تسویه", total_amount=500)
        Payment.objects.create(customer=b, amount=500)
        r = self.client.get(reverse("crm:customer_list"), {"filter": "debtor"})
        self.assertEqual([c.pk for c in r.context["customers"]], [a.pk])

    def test_dashboard_and_overdue_badge_context(self):
        u = make_user("u")
        c = Customer.objects.create(full_name="الف")
        Task.objects.create(customer=c, title="دیرکرد", assignee=u,
                            due_date=timezone.localdate() - timedelta(days=2))
        self.client.force_login(u)
        r = self.client.get(reverse("crm:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["crm_overdue_count"], 1)
