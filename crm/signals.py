"""ثبت خودکار تاریخچه فعالیت‌ها (Timeline) برای هر مشتری."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (Activity, Customer, CustomerSoftware, Payment, Request, Task)


def log(customer, text, user=None):
    Activity.objects.create(customer=customer, text=text, user=user)


@receiver(post_save, sender=Customer)
def customer_saved(sender, instance, created, **kw):
    if created:
        log(instance, "مشتری ثبت شد.", instance.owner)


@receiver(post_save, sender=CustomerSoftware)
def software_saved(sender, instance, created, **kw):
    if created:
        log(instance.customer, f"نرم‌افزار «{instance.software}» به مشتری اضافه شد.")


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, created, **kw):
    if created:
        log(instance.customer, f"پرداخت {instance.amount:,} ثبت شد.", instance.created_by)


@receiver(post_save, sender=Request)
def request_saved(sender, instance, created, **kw):
    if created:
        log(instance.customer, f"درخواست «{instance.subject}» ثبت شد.", instance.created_by)


@receiver(pre_save, sender=Task)
def task_remember_old_status(sender, instance, **kw):
    old = Task.objects.filter(pk=instance.pk).values_list("status", flat=True).first() \
        if instance.pk else None
    instance._old_status = old


@receiver(post_save, sender=Task)
def task_saved(sender, instance, created, **kw):
    who = instance.assignee.get_full_name() or instance.assignee.get_username() \
        if instance.assignee else "بدون مسئول"
    if created:
        log(instance.customer, f"کار «{instance.title}» برای {who} ایجاد شد.", instance.created_by)
    elif getattr(instance, "_old_status", None) != instance.status:
        text = f"وضعیت کار «{instance.title}» به «{instance.get_status_display()}» تغییر کرد."
        if instance.result:
            text += f" نتیجه: {instance.result}"
        log(instance.customer, text, instance.assignee)
