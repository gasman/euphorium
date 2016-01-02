# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-02 21:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('source_reference', models.CharField(max_length=255)),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_groups', to='forums.Site')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='forumgroup',
            unique_together=set([('site', 'source_reference')]),
        ),
    ]
