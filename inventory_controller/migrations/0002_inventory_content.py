# Generated by Django 4.0.5 on 2022-06-14 18:07

from django.db import migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_controller', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='content',
            field=tinymce.models.HTMLField(default=''),
        ),
    ]
