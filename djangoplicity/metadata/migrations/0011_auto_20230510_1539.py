# Generated by Django 3.1 on 2023-05-10 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0010_auto_20220803_1204'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='program',
            options={'ordering': ('name',), 'verbose_name': 'Program', 'verbose_name_plural': 'Programs'},
        ),
        migrations.AddField(
            model_name='program',
            name='types',
            field=models.ManyToManyField(help_text='Defines to which types this program applies.', related_name='_program_types_+', to='metadata.CategoryType'),
        ),
        migrations.AlterUniqueTogether(
            name='program',
            unique_together={('url',)},
        ),
    ]