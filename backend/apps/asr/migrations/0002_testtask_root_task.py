from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("asr", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="testtask",
            name="root_task",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="derived_runs",
                to="asr.testtask",
                verbose_name="所属运行组根任务",
            ),
        ),
    ]
