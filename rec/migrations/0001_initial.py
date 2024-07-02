# Generated by Django 5.0 on 2024-02-26 07:45

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Facerec",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("person", models.CharField(max_length=100)),
                ("event", models.CharField(max_length=100)),
                ("time", models.DateTimeField(null=True)),
            ],
        ),
    ]