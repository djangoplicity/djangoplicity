# Generated by Django 3.1 on 2022-09-12 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menus', '0004_merge_20191007_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menuitem',
            name='level',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='lft',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='rght',
            field=models.PositiveIntegerField(editable=False),
        ),
    ]