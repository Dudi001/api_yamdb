# Generated by Django 3.0.5 on 2021-03-26 05:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yamdb', '0004_category_comment_genre_review_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='title',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', to='yamdb.Category'),
        ),
    ]
