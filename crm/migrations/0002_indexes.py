from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(fields=["status"], name="crm_customer_status_idx"),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(fields=["status", "due_date"], name="crm_task_status_due_idx"),
        ),
    ]
