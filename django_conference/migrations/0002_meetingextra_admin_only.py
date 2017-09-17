# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_conference', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='meetingextra',
            name='admin_only',
            field=models.BooleanField(default=False, help_text=b'If checked, this extra will only be available when registering through the admin interface.'),
        ),
    ]
