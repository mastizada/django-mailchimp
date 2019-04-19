# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mailchimp', '0002_auto_20161017_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queue',
            name='segment_options_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='reciever',
            name='campaign',
            field=models.ForeignKey(related_name='receivers', to='mailchimp.Campaign', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
