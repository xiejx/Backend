# Generated by Django 2.0.5 on 2018-06-29 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0006_auto_20180618_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookinfo',
            name='cover',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='avatar',
            field=models.CharField(default='', max_length=255),
        ),
    ]