# Generated by Django 2.0.5 on 2018-06-18 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0005_auto_20180507_0038'),
    ]

    operations = [
        migrations.AlterField(
            model_name='typeinfo',
            name='name',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
