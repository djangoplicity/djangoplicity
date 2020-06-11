import pytest
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from djangoplicity.media.models import Image
from djangoplicity.metadata.models import TaggingStatus
from djangoplicity.releases.models import Release, ReleaseType, \
    ReleaseContact, ReleaseTranslationContact, ReleaseImage


# To run:
# ./bin/py.test src/djangoplicity/src/djangoplicity/translation/tests/translation.py


@pytest.fixture
def release_type():
    release_type = ReleaseType(name='Release Type')
    release_type.save()
    return release_type

@pytest.mark.django_db
def test_source_objects_api(release_type):
    pass
    # Create a translatable object
    # t1 = Release(release_type=release_type, title='Science Release', id='eso1501')
    # t1.save()
    # assert t1.lang == settings.LANGUAGE_CODE
    # assert t1.source is None
    # assert Release.objects.all().count() == 1

    # # Create a translatable object in the primary language
    # t2 = Release(release_type=typ, title='Organisation Release', lang=settings.LANGUAGE_CODE, id='eso1502')
    # t2.save()
    # assert t2.lang == settings.LANGUAGE_CODE
    # assert t2.source is None
    # assert Release.objects.all().count() == 2

    # # Create a translatable object in a secondary language
    # t3 = Release(release_type=typ, title='Pressemeddelelse', lang='da', id='eso1502da')
    # t3.save()
    # assert t3.lang == 'da'
    # assert t3.source is None

    # # Retrieving all primary releases using the TranslationManager
    # assert Release.objects.all().count() == 3
    # assert Release.objects.language(settings.LANGUAGE_CODE).count() == 2
    # assert Release.objects.language('da').count() == 1
    # assert Release.objects.fallback('fr').count() == 3

    # assert Release.objects.fallback(settings.LANGUAGE_CODE).count() == 3

    # Release.Translation.non_default_languages_in_fallback = False
    # assert Release.objects.fallback(settings.LANGUAGE_CODE).count() == 2
    # assert Release.objects.fallback('fr').count() == 2

    # # Revert non_default_languages_in_fallback so it doesn't affect further tests
    # Release.Translation.non_default_languages_in_fallback = True


# @pytest.mark.django_db
# def test_translated_objects_api(typ):
#     # Create a source object
#     t1 = Release(release_type=typ, title='Science Release', published=True, release_date=datetime(2010, 3, 5, 12, 36), id='eso1501')
#     t1.save()
#     assert t1.published is True
#     assert t1.release_date == datetime(2010, 3, 5, 12, 36)
#     assert t1.is_source() is True
#     assert t1.is_translation() is False

#     # Create a translation of the source object
#     assert settings.LANGUAGE_CODE == 'en'
#     t2 = Release(title='Pressemeddelelse', lang='da', source=t1, published=False, id='eso1502da')
#     t2.save()
#     assert t2.lang == 'da'
#     assert t2.source == t1
#     assert t2.is_translation() is True
#     assert t2.is_source() is False
#     assert Release.objects.all().count() == 1
#     assert Release.objects.language('da').count() == 1
#     assert Release.objects.fallback('fr').count() == 1

#     # Retrieving the source/translated object
#     # Source object
#     t1_new = Release.objects.get(pk=t1.pk)
#     assert t1.title == t1_new.title
#     assert t1.published == t1_new.published
#     assert t1.release_date == t1_new.release_date

#     # Translated object
#     t2_new = Release.objects.language('da').get(pk=t1.pk)
#     assert t2.title == t2_new.title  # translated property
#     assert t1.published != t2_new.published  # non-inherited property
#     assert t1.release_date == t2_new.release_date  # non-inherited property

#     # Retrieving the source object using Q objects
#     # Source object
#     t1_new = None
#     t1_new = Release.objects.get(Q(pk=t1.pk))
#     assert t1.title == t1_new.title
#     assert t1.published == t1_new.published
#     assert t1.release_date == t1_new.release_date

#     # Translated object
#     t2_new = None
#     t2_new = Release.objects.language('da').get(Q(pk=t1.pk))
#     assert t2.title == t2_new.title
#     assert t1.published != t2_new.published
#     assert t1.release_date == t2_new.release_date


# @pytest.mark.django_db
# def test_translation_objects_filters(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Science Release', published=False, id='eso1501')
#     t2 = Release(release_type=typ, title='Photo Release', published=True, id='eso1502')
#     t3 = Release(release_type=typ, title='Organisation Release', published=True, id='eso1503')
#     t4 = Release(release_type=typ, title='Hallo', published=True, lang='da', id='eso1504')
#     _ = [x.save() for x in [t1, t2, t3, t4]]
#     t1_da = Release(release_type=typ, title='Pressemeddelelse (Videnskabelig)', published=True, source=t1, lang='da', id='eso1501da')
#     t2_da = Release(release_type=typ, title='Pressemeddelelse (Billed)', published=False, source=t2, lang='da', id='eso1502da')
#     t3_da = Release(release_type=typ, title='Pressemeddelelse (Organisation)', published=False, source=t3, lang='da', id='eso1503da')
#     t4_en = Release(release_type=typ, title='Hello', published=False, source=t4, lang='en', id='eso1504en')
#     _ = [x.save() for x in [t1_da, t2_da, t3_da, t4_en]]

#     # Source releases filtering
#     assert Release.objects.all().count() == 4
#     assert Release.objects.filter(title__endswith='Release', published=True).count() == 2
#     assert Release.objects.filter(title__startswith='Pressemeddelelse').count() == 0
#     assert Release.objects.filter(title='Hallo').count() == 1

#     # Translated releases filtering
#     assert Release.objects.language('da').count() == 4
#     assert Release.objects.language('da').filter(title__endswith='Release').count() == 0
#     assert Release.objects.language('da').filter(title__startswith='Pressemeddelelse', published=False).count() == 2
#     assert Release.objects.language('fr').count() == 0
#     assert Release.objects.fallback('da').count() == 4

#     assert Release.objects.language('da').exclude(id__in=[t4.pk, t2.pk], title__startswith='Ha').exclude(pk__in=[t1.pk, t3.pk], title__contains='Organisation').count() == 3
#     assert Release.objects.language('da').filter(Q(id__in=[t4.pk, t2.pk], title__startswith='Ha') | Q(pk__in=[t1.pk, t3.pk], title__contains='Organisation')).count() == 2
#     assert Release.objects.language('da').filter(Q(published=True), (Q(id__in=[t4.pk, t2.pk], title__startswith='Ha') | Q(pk__in=[t1.pk, t3.pk], title__contains='Organisation'))).count() == 1
#     assert Release.objects.language('da').exclude(Q(published=True), (Q(id__in=[t4.pk, t2.pk], title__startswith='Ha') | Q(pk__in=[t1.pk, t3.pk], title__contains='Organisation'))).count() == 3

#     # Query Set methods
#     assert [x['title'] for x in Release.objects.order_by('title').values()] == \
#     [u'Hallo', u'Organisation Release', u'Photo Release', u'Science Release']
#     assert [x['title'] for x in Release.objects.language('da').order_by('title').values()] == \
#     [u'Hallo', u'Pressemeddelelse (Billed)', u'Pressemeddelelse (Organisation)', u'Pressemeddelelse (Videnskabelig)']
#     assert len(Release.objects.values_list()) == 4
#     assert Release.objects.language('da').defer('title').all().count() == 4
#     assert Release.objects.language('da').none().count() == 0
#     assert [x['title'] for x in Release.objects.language('da').order_by('-title').values()] == \
#     [u'Pressemeddelelse (Videnskabelig)', u'Pressemeddelelse (Organisation)', u'Pressemeddelelse (Billed)', u'Hallo']

#     # Delete
#     Release.objects.language('da').filter(Q(id__in=[t4.pk, t2.pk], title__startswith='Ha') | Q(pk__in=[t1.pk, t3.pk], title__contains='Organisation')).delete()
#     assert Release.objects.language('da').all().count() == 2


# @pytest.mark.django_db
# def test_translations(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Press Release', published=True, id='eso1501')
#     t2 = Release(release_type=typ, title='Test 1', published=True, id='eso1502')
#     t3 = Release(release_type=typ, title='Test 2', published=True, lang='da', id='eso1503')
#     _ = [x.save() for x in [t1, t2, t3]]
#     t1_da = Release(release_type=typ, title='Pressemeddelelse', published=True, source=t1, lang='da', id='eso1501da')
#     t1_de = Release(release_type=typ, title='Pressemitteilung', published=True, source=t1, lang='de', id='eso1501de')
#     _ = [x.save() for x in [t1_da, t1_de]]

#     assert Release.objects.all().count() == 3

#     # Getting all the translations for a specific source release
#     t1 = Release.objects.get(pk=t1.pk)
#     assert t1.translations.all().count() == 2

#     # Delete
#     t1.delete()
#     assert Release._base_manager.all().count() == 2


# @pytest.mark.django_db
# def test_source_updates(typ):
#     t1 = Release(release_type=typ, title='Press Release', published=True, release_date=datetime(2010, 3, 5, 12, 00), id='eso1501')
#     t2 = Release(release_type=typ, title='Test 1', published=True, release_date=datetime(2010, 4, 5, 12, 00), id='eso1502')
#     t1.save()
#     t2.save()

#     t1_da = Release(published=True, title='Pressemeddelese', source=t1, lang='da', id='eso1501da')
#     t1_de = Release(published=True, title='Pressemitteilung', source=t1, lang='de', id='eso1501de')
#     t2_da = Release(published=True, title='Test Da', source=t2, lang='da', id='eso1502da')
#     t2_de = Release(published=True, title='Test De', source=t2, lang='de', id='eso1502de')
#     _ = [x.save() for x in [t1_da, t1_de, t2_da, t2_de]]

#     # Update inherited property in source
#     t1.release_date = datetime(2011, 3, 5, 12, 00)
#     t1.save()
#     assert t1.release_date == datetime(2011, 3, 5, 12, 00)
#     assert Release._base_manager.filter(source__isnull=False, release_date=t1.release_date).count() == 2

#     # Update non-inherited property in source
#     t1.published = False
#     t1.save()
#     assert [x.published for x in Release._base_manager.filter(source=t1)] == [True, True]


# @pytest.mark.django_db
# def test_related_translations(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Item 1', id='eso1501')
#     t2 = Release(release_type=typ, title='Item 2', id='eso1502')
#     t3 = Release(release_type=typ, title='Item 3', id='eso1503')
#     _ = [x.save() for x in [t1, t2, t3]]
#     t1_da = Release(title='Item 1da', source=t1, lang='da', id='eso1501da')
#     t1_de = Release(title='Item 1de', source=t1, lang='de', id='eso1501de')
#     _ = [x.save() for x in [t1_da, t1_de]]

#     t2_da = Release(title='Item 2da', source=t2, lang='da', id='eso1502da')
#     t2_da.save()

#     # Ensure that everythin is correctly setup
#     t1_da = Release.objects.language('da').get(pk=t1.pk)
#     t1_de = Release.objects.language('de').get(pk=t1.pk)
#     t2_da = Release.objects.language('da').get(pk=t2.pk)
#     assert [t1_da.source, t1_de.source, t2_da.source] == [t1, t1, t2]

#     # Accessing all translations from a source
#     t1 = Release.objects.get(pk=t1.pk)
#     t2 = Release.objects.get(pk=t2.pk)
#     t3 = Release.objects.get(pk=t3.pk)
#     assert [x.source for x in [t1, t2, t3]] == [None, None, None]
#     assert [x.pk for x in t1.translations.all().order_by('title')] == ['eso1501da', 'eso1501de']
#     assert [x.pk for x in t2.translations.all()] == ['eso1502da']
#     assert [x.pk for x in t3.translations.all()] == []


# @pytest.mark.django_db
# def test_foreign_keys(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Release 1', id='eso1501')
#     t2 = Release(release_type=typ, title='Release 2', id='eso1502')
#     rc1 = ReleaseContact(name='RC1', release=t1)
#     rc2 = ReleaseContact(name='RC2', release=t2)
#     rc3 = ReleaseContact(name='RC3', release=t2)
#     rtc1 = ReleaseTranslationContact(name='RTC1', release=t1)
#     rtc2 = ReleaseTranslationContact(name='RTC2', release=t2)
#     _ = [x.save() for x in [t1, t2, rc1, rc2, rc3, rtc1, rtc2]]

#     t1_da = Release(title='Release 1da', source=t1, lang='da', id='eso1501da')
#     t1_de = Release(title='Release 1de', source=t1, lang='de', id='eso1501de')
#     t1_da.save()
#     t1_de.save()

#     rtc3da = ReleaseTranslationContact(name='RTC1da', release=t1_da)
#     rtc3da.save()

#     t1 = Release.objects.get(pk=t1.pk)
#     assert [x.pk for x in t1.translations.all().order_by('pk')] == ['eso1501da', 'eso1501de']
#     assert [x.pk for x in t2.translations.all().order_by('pk')] == []

#     # Accessing foreign keys defined in translated model
#     assert t1.release_type == t1_da.release_type

#     # Updating foreign key
#     type_2 = ReleaseType(name='Other type')
#     type_2.save()
#     t1.release_type = type_2
#     t1.save()
#     t1_da = Release.objects.language('da').get(pk=t1.pk)
#     t1_de = Release.objects.language('de').get(pk=t1.pk)
#     assert t1_da.release_type == type_2
#     assert t1_de.release_type == type_2

#     # Revert changes
#     t1.release_type = typ
#     t1.save()

#     # Reverse relations managers for inherited/non-inherited
#     # foreign keys defined on model
#     assert list(t1.releasecontact_set.all()) == [rc1]  # inherited
#     assert list(t2.releasecontact_set.all()) == [rc2, rc3]  # inherited
#     assert list(t1.releasetranslationcontact_set.all()) == [rtc1]  # non-inherited
#     assert list(t2.releasetranslationcontact_set.all()) == [rtc2]  # non-inherited
#     assert list(t1_da.releasetranslationcontact_set.all()) == [rtc3da]  # non-inherited
#     assert list(t1_de.releasetranslationcontact_set.all()) == []  # non-inherited

#     # Delete reverse fk
#     rc2.delete()
#     rc3.delete()
#     rtc1.delete()
#     assert list(t2.releasecontact_set.all()) == []  # inherited
#     assert list(t1.releasetranslationcontact_set.all()) == []  # non-inherited
#     assert list(t1_da.releasetranslationcontact_set.all()) == [rtc3da]  # non-inherited


# @pytest.mark.django_db
# def test_many_to_many(typ):
#     # Setup
#     i1 = Image(title='Image 1', priority=10, pk='eso1501a')
#     i2 = Image(title='Image 2', priority=10, pk='eso1502a')
#     i3 = Image(title='Image 3', priority=10, pk='eso1503a')
#     i4 = Image(title='Image 4', priority=10, pk='eso1504a')
#     ts1 = TaggingStatus(slug='ts1', name='TS1')
#     ts2 = TaggingStatus(slug='ts2', name='TS2')
#     ts3 = TaggingStatus(slug='ts3', name='TS3')
#     ts4 = TaggingStatus(slug='ts4', name='TS4')
#     _ = [x.save() for x in [i1, i2, i3, i4, ts1, ts2, ts3, ts4]]

#     # Forward empty relations
#     assert not i1.tagging_status.all().exists()
#     assert not i2.tagging_status.all().exists()
#     assert not i3.tagging_status.all().exists()
#     assert not i4.tagging_status.all().exists()

#     # Reverse empty relations
#     assert not ts1.image_set.all().exists()
#     assert not ts2.image_set.all().exists()
#     assert not ts3.image_set.all().exists()
#     assert not ts4.image_set.all().exists()

#     # Setup relations
#     i1.tagging_status.add(ts1, ts2, ts3)
#     i2.tagging_status.add(ts2, ts3)
#     i3.tagging_status.add(ts4)

#     # Forward relations
#     assert list(i1.tagging_status.all()) == [ts1, ts2, ts3]
#     assert list(i2.tagging_status.all()) == [ts2, ts3]
#     assert list(i3.tagging_status.all()) == [ts4]
#     assert not i4.tagging_status.all().exists()

#     # Reverse solutions
#     assert list(ts1.image_set.all()) == [i1]
#     assert list(ts2.image_set.all()) == [i1, i2]
#     assert list(ts3.image_set.all()) == [i1, i2]
#     assert list(ts4.image_set.all()) == [i3]

#     # Adding to relation via translation object
#     i1da = Image(title='Image 1da', source=i1, pk='eso1501ada')
#     i1de = Image(title='Image 1de', source=i1, pk='eso1501ade')
#     i4da = Image(title='Image 4da', source=i4, pk='eso1504ada')
#     _ = [x.save() for x in [i1da, i1de, i4da]]
#     i1da.tagging_status.add(ts4)
#     i4da.tagging_status.add(ts1)
#     assert list(i1.tagging_status.all()) == [ts1, ts2, ts3, ts4]
#     assert list(i1da.tagging_status.all()) == [ts1, ts2, ts3, ts4]
#     assert list(i1de.tagging_status.all()) == [ts1, ts2, ts3, ts4]
#     assert list(i4.tagging_status.all()) == [ts1]
#     assert list(i4da.tagging_status.all()) == [ts1]
#     ts4.image_set.add(i4)
#     assert list(i4.tagging_status.all()) == [ts1, ts4]
#     assert list(i4da.tagging_status.all()) == [ts1, ts4]

#     # Removing relation via translation object
#     i1.tagging_status.remove(ts3, ts4)
#     assert list(i1.tagging_status.all()) == [ts1, ts2]
#     assert list(i1da.tagging_status.all()) == [ts1, ts2]
#     assert list(i1de.tagging_status.all()) == [ts1, ts2]
#     ts2.image_set.remove(i1de)
#     assert list(i1.tagging_status.all()) == [ts1]
#     assert list(i1da.tagging_status.all()) == [ts1]
#     assert list(i1de.tagging_status.all()) == [ts1]

#     # Clear relations
#     i4.tagging_status.clear()
#     assert not i4.tagging_status.all().exists()
#     assert list(ts4.image_set.all()) == [i3]

#     # Through relations
#     t1 = Release(release_type=typ, title='Release 1', id='eso1501')
#     t2 = Release(release_type=typ, title='Release 2', id='eso1502')
#     t1_da = Release(title='Release 1da', source=t1, lang='da', id='eso1501da')
#     t1_de = Release(title='Release 1de', source=t1, lang='de', id='eso1501de')
#     _ = [x.save() for x in [t1, t2, t1_da, t1_de]]
#     ri1 = ReleaseImage(archive_item=i1, release=t1)
#     ri2 = ReleaseImage(archive_item=i2, release=t1)
#     ri3 = ReleaseImage(archive_item=i3, release=t1)
#     ri4 = ReleaseImage(archive_item=i4, release=t2)
#     _ = [x.save() for x in [t1, t2, t1_da, t1_de, ri1, ri2, ri3, ri4]]
#     assert list(t1.related_images.all()) == [i1, i2, i3]
#     assert list(t1_da.related_images.all()) == [i1, i2, i3]
#     assert list(t1_de.related_images.all()) == [i1, i2, i3]
#     assert list(t2.related_images.all()) == [i4]
#     assert list(i1.releaseimage_set.all()) == [ri1]
#     assert list(i1da.releaseimage_set.all()) == [ri1]
#     assert list(i1de.releaseimage_set.all()) == [ri1]
#     assert list(i4.releaseimage_set.all()) == [ri4]
#     t2.related_images.clear()
#     assert list(i4.releaseimage_set.all()) == []


# @pytest.mark.django_db
# def test_filter_api(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Release 1', id='eso1501')
#     t2 = Release(release_type=typ, title='Release 2', id='eso1502')
#     t1_da = Release(title='Release 1da', source=t1, lang='da', id='eso1501da')
#     t2_da = Release(title='Release 2da', source=t2, lang='da', id='eso1502da')
#     _ = [x.save() for x in [t1, t2, t1_da, t2_da]]

#     # Filter involving primary key
#     assert list(Release.objects.filter(pk__icontains='eso150').order_by('pk')) == [t1, t2]
#     assert list(Release.objects.language('da').filter(pk__icontains='eso150').order_by('pk')) == [t1_da, t2_da]


# @pytest.mark.django_db
# def test_non_en_source(typ):
#     # Setup
#     t1 = Release(release_type=typ, title='Pressemitteilung', published=True, lang='de', id='eso1501de', created=datetime.now())
#     t1_en = Release(release_type=typ, title='Press Release', published=True, source=t1, lang='en', id='eso1501de-en', created=datetime.now())

#     _ = [x.save() for x in [t1, t1_en]]

#     assert Release.objects.all().count() == 1

#     assert Release.objects.language('de').count() == 1
#     assert Release.objects.fallback('en').count() == 1
#     assert Release.objects.fallback('fr').count() == 1
#     assert Release.objects.fallback('da').count() == 1
