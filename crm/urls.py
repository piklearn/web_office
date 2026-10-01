from django.urls import path
from . import views

app_name = "crm"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/<int:pk>/result/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/status/", views.task_status, name="task_status"),
    path("reports/", views.reports, name="reports"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/new/", views.customer_form, name="customer_add"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_form, name="customer_edit"),
    path("customers/<int:pk>/contact/", views.contact_add, name="contact_add"),
    path("customers/<int:pk>/software/", views.software_add, name="software_add"),
    path("customers/<int:pk>/payment/", views.payment_add, name="payment_add"),
    path("customers/<int:pk>/request/", views.request_add, name="request_add"),
    path("customers/<int:pk>/task/", views.task_add, name="task_add"),
    path("customers/<int:pk>/request/<int:request_pk>/task/", views.task_add, name="task_add_for_request"),
    path("customers/<int:pk>/software/", views.software_add, name="software_add"),
    path("customers/<int:pk>/software/<int:spk>/edit/", views.software_edit, name="software_edit"),
    path("customers/<int:pk>/software/<int:spk>/delete/", views.software_delete, name="software_delete"),
    path("tasks/<int:pk>/claim/", views.task_claim, name="task_claim"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
]
