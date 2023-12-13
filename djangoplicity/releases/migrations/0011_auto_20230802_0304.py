# Generated by Django 3.1 on 2023-08-02 03:04

from django.db import migrations, models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0012_remove_program_type'),
        ('releases', '0010_auto_20220912_1022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='programs',
            field=djangoplicity.translation.fields.TranslationManyToManyField(blank=True, limit_choices_to=models.Q(types__name='Releases'), to='metadata.Program'),
        ),
    ]