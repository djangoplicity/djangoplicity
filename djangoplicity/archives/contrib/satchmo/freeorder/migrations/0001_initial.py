# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.contrib.satchmo.freeorder.models


class Migration(migrations.Migration):

    dependencies = [
        ('l10n', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='FreeOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, verbose_name=b'Full Name')),
                ('email', models.EmailField(max_length=250, verbose_name=b'Email Address')),
                ('justification', models.TextField(help_text=b'Please tell us a few words about yourself/your organisation and provide a short justification explaining how you intend to use the products.', verbose_name=b'Justification')),
                ('accepted', models.NullBooleanField(verbose_name=b'Accepted')),
                ('amount', models.FloatField(default=100.0, verbose_name=b'Discount percentage offered', validators=[djangoplicity.archives.contrib.satchmo.freeorder.models.validate_percentage])),
                ('discount_code', models.CharField(default=b'', help_text=b'Created automatically.', max_length=20, blank=True)),
                ('reject_reason', models.CharField(blank=True, max_length=255, choices=[(b'NOSTOCK', b'The product(s) is/are not available on stock.'), (b'UNQUALIFIED', b'You did not qualify for receiving free orders at this occasion.'), (b'INSUFFICIENT', b'Your justification is not sufficient to evaluate the request.'), (b'AMOUNT', b'Your order was above our maximum of 180 EUR.'), (b'OLDCUSTOMER', b'You already received a free order during the last six months'), (b'ESONONLY', b'Unfortunately we no longer ship free orders outside ESON countries: http://www.eso.org/public/outreach/eson/'), (b'EUROONLY', b'Unfortunately we no longer ship free orders outside Europe.')])),
                ('submitted', models.DateTimeField()),
                ('reviewed', models.DateTimeField(help_text=b'Updated automatically.', null=True, blank=True)),
                ('country', models.ForeignKey(verbose_name=b'Country of delivery', to='l10n.Country')),
            ],
            options={
                'verbose_name': 'free order application',
            },
            bases=(models.Model,),
        ),
    ]
