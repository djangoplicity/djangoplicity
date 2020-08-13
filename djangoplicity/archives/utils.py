from __future__ import division
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from builtins import str
from builtins import range
from past.utils import old_div
from builtins import object
import hashlib
import logging
from math import ceil
from os.path import isfile
from time import sleep

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.utils.functional import curry

from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.resources import ResourceManager
from djangoplicity.translation.models import TranslationModel
from djangoplicity.utils.d2d import D2dDict


class FormatTokenGenerator( object ):
    """
    Token generator to be used to generate
    a token for a combination of id and format.

    Currently only used for media.Image to give
    access to an image without having login
    details (necessary for embargoed Newsletters).
    """
    @classmethod
    def create_token( cls, format, id ):
        m = hashlib.sha256()
        m.update( settings.SECRET_KEY )
        m.update( str( format ) )
        m.update( str( id ) )
        m.update( settings.SECRET_KEY )
        return m.hexdigest()

    @classmethod
    def check_token( cls, token, format, id ):
        return token == cls.create_token( format, id )


def wait_for_resource(archive, resource_name='original'):
    '''
    Returns the specified resource
    If the resource doesn't exist sleeps for 5 seconds and try again up to
    2 minutes total time in case the NFS share is slow to update
    '''
    for _t in range(0, 120, 5):
        resource = getattr(archive, 'resource_%s' % resource_name)

        if resource:
            return resource

        logging.warning('No %s format found for "%s", waiting 5s...',
            resource_name, archive.pk)

        # We clear the resource_cache to make sure we check again on the disk
        # for the next iteration
        archive.clear_resource_cache()

        sleep(5)

    return None


def is_internal( request ):
    """
    Check if a request is an internal request
    """
    if settings.DEBUG:
        # When developing assume internal unless ?external is passed
        return 'external' not in request.GET

    # If we use NGINX as proxy REMOTE_ADDR will be 127.0.0.1
    # so we use HTTP_X_REAL_IP if available, otherwise we default
    # to REMOTE_ADDR
    if 'HTTP_X_REAL_IP' in request.META:
        key = 'HTTP_X_REAL_IP'
    else:
        key = 'REMOTE_ADDR'

    return request and key in request.META and request.META[key] in settings.INTERNAL_IPS


#
# Retrieve related archive items (useful for releases and announcements).
#
def related_archive_item_fk( src_model_field, obj ):
    """
    Get a related archive item (use translation if exists, otherwise source language).
    """
    ( _src_class, src_attr, dest_class, _dest_attr ) = _extract_relation( src_model_field )

    # FKs are replicated on translation models, so just get the related object
    # and find any translation if exists.
    related_obj = getattr( obj, src_attr )
    lookup_lang = obj.lang if isinstance( obj, TranslationModel ) else settings.LANGUAGE_CODE

    if settings.USE_I18N and issubclass( dest_class, TranslationModel ):
        try:
            if related_obj.lang != lookup_lang:
                if related_obj.is_translation():
                    related_obj = related_obj.source
                related_obj = related_obj.translations.get( lang=lookup_lang )
        except dest_class.DoesNotExist:
            pass

        related_obj.in_original_language = ( related_obj.lang == lookup_lang )
    else:
        related_obj.in_original_language = ( settings.LANGUAGE_CODE == lookup_lang )

    return related_obj


def related_archive_items( src_model_field, obj, has_main_visual=True ):
    """
    Get all related archive items (use translation if exists,
    otherwise source language).

    class Release( ... ):
        related_images = ManyToManyField( through='ReleaseImage' )

    release = Release.objects.get( pk='...' )
    release = Release.objects.language('da').get( pk='...' )

    images = related_archive_items( Release.related_images, release )

    It's expected that ReleaseImage besides a ForeignKey to each of the
    related models, also contains the attributes:
        * order (anything that can be ordered by)
        * main_visual (boolean)
        * override_id (char field)
    """
    ( _src_class, _src_attr, dest_class, _dest_attr, through_class, through_src_name, through_dest_name ) = _extract_relation( src_model_field )

    # Use source object to query for related items.
    query_obj = obj
    if settings.USE_I18N:
        if isinstance( obj, TranslationModel ) and obj.is_translation():
            query_obj = obj.source

    ordering = ['-main_visual', 'order', '%s__id' % through_dest_name] if has_main_visual else ['order', '%s__id' % through_dest_name]
    related_qs = through_class.objects.select_related().filter( **{ through_src_name: query_obj } ).filter( **{ "%s__published" % through_dest_name: True } ).order_by( *ordering )

    # Get translated versions of objects if exists (and if obj is not a source object).
    trans_dict = {}
    if settings.USE_I18N and issubclass( dest_class, TranslationModel ):
        archive_item_ids = [getattr( x, through_dest_name ).id for x in related_qs]
        if archive_item_ids:  # Don't query unless we have something to query for
            trans_dict = dict( [( x.source.id, x ) for x in dest_class.objects.language( obj.lang ).filter( published=True, source__in=archive_item_ids )] )

    archive_items = []
    for i, rel_item in enumerate( related_qs ):
        archive_item = getattr( rel_item, through_dest_name )

        # Get translated object if exists
        if archive_item.id in trans_dict:
            archive_item = trans_dict[archive_item.id]

        # Set attribute to determine if related object is in the original language
        if settings.USE_I18N:
            if issubclass( dest_class, TranslationModel ):
                archive_item.in_original_language = obj.lang == archive_item.lang if isinstance( obj, TranslationModel ) else settings.LANGUAGE_CODE == archive_item.lang
            else:
                archive_item.in_original_language = obj.lang == settings.LANGUAGE_CODE if isinstance( obj, TranslationModel ) else True
        else:
            archive_item.in_original_language = True

        # Set main visual attribute (only the first item can be main visual due to ordering of query set)
        archive_item.is_main_visual = has_main_visual and rel_item.main_visual and i == 0

        # Set override if needed
        if rel_item.override_id:
            archive_item.override_id = rel_item.override_id

        # Set 'hide' attribute
        archive_item.hide = rel_item.hide

        archive_items.append( archive_item )

    return archive_items


def get_instance_archives(instance):
    '''
    Returns a list of all existing Archives for a given instance
    '''
    return [x for x in dir(instance.Archive) if
        isinstance(getattr(instance.Archive, x), ResourceManager ) and
        getattr(instance, 'resource_%s' % x) is not None]


def get_instance_resources(instance):
    '''
    Return D2D compatible resources list
    '''
    key = 'instance-resource-cache-{}-{}-{}'.format(instance._meta.app_label,
        instance._meta.model_name, instance.pk)

    result = cache.get(key)
    if result:
        return result

    if instance.__class__.__name__ == 'Image':
        formats = D2dDict([
            ('Original', ('original', 'Image')),
            ('Large', ('large', 'Image')),
            ('Small', ('screen', 'Image')),
            ('Thumbnail', ('potwmedium', 'Image')),
            ('Icon', ('newsmini', 'Image')),
        ])
    elif instance.__class__.__name__ == 'Video':
        formats = D2dDict()

        # Fulldome videos:
        for fmt in ['dome_8kmaster', 'dome_4kmaster', 'dome_2kmaster', 'dome_mov']:
            if getattr(instance, 'resource_%s' % fmt, None):
                if 'Original' not in formats:
                    formats['Original'] = (fmt, 'Video')
                else:
                    formats['Large'] = (fmt, 'Video')
            if 'Original' in formats and 'Large' in formats:
                break

        if getattr(instance, 'resource_dome_preview', None):
            formats['Preview'] = ('dome_preview', 'Video')

        # Normal videos
        for fmt in ['ultra_hd', 'hd_1080p25_screen', 'hd_1080_screen', 'ext_highres']:
            if getattr(instance, 'resource_%s' % fmt, None):
                formats['Original'] = (fmt, 'Video')
                break

        for fmt in ['hd_and_apple', 'ext_playback', 'medium_podcast', 'old_video']:
            if getattr(instance, 'resource_%s' % fmt, None):
                formats['Preview'] = (fmt, 'Video')
                break

        formats['Thumbnail'] = ('potwmedium', 'Image')
        formats['Icon'] = ('newsmini', 'Image')
    elif instance.__class__.__name__ == 'Music':
        formats = D2dDict([
            ('Original', ('wav', 'Audio')),
            ('Preview', ('aac', 'Audio')),
        ])
    elif instance.__class__.__name__ == 'Model3d':
        formats = D2dDict([
            ('Original', ('model_3d_c4d', 'Model')),
            ('Obj', ('model_3d_obj', 'Model')),
            ('Thumbnail', ('thumb', 'Image')),
        ])
    else:
        formats = D2dDict()

    resources = [
        get_instance_d2d_resource(instance, fmt, name, media_type)
        for (name, (fmt, media_type)) in list(formats.items())
    ]

    # Remove empty resources if any:
    result = [r for r in resources if r]

    cache.set(key, result, 60 * 10)

    return result


def get_instance_archives_urls(instance):
    '''
    Returns a list of all existing Archives URL for a given instance
    '''
    urls = {}
    for x in dir(instance.Archive):
        if not isinstance(getattr(instance.Archive, x), ResourceManager):
            continue

        resource = getattr(instance, 'resource_%s' % x)

        if not resource:
            continue

        urls[x] = resource.absolute_url
    return urls


def get_resource_dimension(instance, resource_name):
    '''
    Get the dimensions for a given resource if available
    '''
    typ = getattr(instance.__class__.Archive, resource_name).type

    try:
        width = typ.width
        height = typ.height
        instance_width = instance.width
        instance_height = instance.height
    except AttributeError:
        # The filetype or instance doesn't specify either width or height
        return [None, None]

    # Conver to float if we have values to avoid rounding errors:
    width = float(width) if width else None
    height = float(height) if height else None

    if width and height:
        return [width, height]

    if hasattr(typ, 'size') and typ.size:
        size = float(typ.size)
        # Resource has a max dimension (restricts maximum width or height)
        if instance_width > instance_height:
            # Landscape
            return [size, ceil(old_div(instance_height * size, instance_width))]
        else:
            # Portrait
            return [ceil(old_div(instance_width * size, instance_height)), size]

    if width and instance_width and instance_height:
        # Only width is defined
        return [width, ceil(old_div(instance_height * width, instance_width))]

    if height and instance_width and instance_height:
        # Only height is defined
        return [old_div(ceil(instance_width * height), instance_height), height]

    return [instance_width, instance_height]


def get_instance_d2d_resource(instance, resource_name, name, media_type):
    resource = getattr(instance, 'resource_%s' % resource_name)
    if hasattr(instance, 'web_category'):
        web_categories = [c.name for c in instance.web_category.all()]
    else:
        web_categories = []

    # Skip non-file resources (e.g. zoomable):
    if not resource or not isfile(resource.path):
        return {}

    if instance.__class__.__name__ == 'Image':
        # Figure out ProjectionType
        if hasattr(instance, 'type'):
            if instance.type == 'Observation':
                projection_type = 'Observation'
            elif instance.fov_x == 360:
                projection_type = 'Equirectangular'
            elif 'Fulldome' in web_categories:
                projection_type = 'Fulldome'
            else:
                projection_type = 'Tan'
        else:
            projection_type = 'Tan'

        if hasattr(instance, 'fov_x_l'):
            if instance.fov_x_l and instance.fov_x_r:
                fov_x = [instance.fov_x_l, instance.fov_x_r]
            else:
                fov_x = None
            if instance.fov_y_d and instance.fov_y_u:
                fov_y = [instance.fov_y_d, instance.fov_y_u]
            else:
                fov_y = None
        else:
            fov_x = None
            fov_y = None

    elif instance.__class__.__name__ == 'Video':
        fov_x = None
        fov_y = None
        if hasattr(instance, 'web_category'):
            if 'Fulldome' in web_categories:
                projection_type = 'Fulldome'
            else:
                projection_type = 'Tan'
        else:
            projection_type = 'Tan'
    else:
        fov_x = None
        fov_y = None
        projection_type = None

    return D2dDict([
        ('ResourceType', name),
        ('MediaType', media_type),
        ('URL', resource.absolute_url),
        ('FileSize', resource.size),
        ('Dimensions', get_resource_dimension(instance, resource_name)),
        ('HorizontalFOV', fov_x),
        ('VerticalFOV', fov_y),
        ('ProjectionType', projection_type),
        ('Checksum', get_instance_checksum(instance, resource_name)),
    ])


def get_instance_d2d_resources(instance):
    '''
    Returns a list of Data2Dome resources
    '''
    result = []
    for x in dir(instance.Archive):
        if not isinstance(getattr(instance.Archive, x), ResourceManager):
            continue

        resource = getattr(instance, 'resource_%s' % x)

        # Skip non-file resources (e.g. zoomable):
        if not resource or not isfile(resource.path):
            continue

        result.append(D2dDict([
            ('ResourceType', x),
            ('URL', resource.absolute_url),
            ('FileSize', resource.size),
        ]))

        # Checking the size apparently opens the file, we close it to prevent
        # IOError: [Errno 24] Too many open files:
        resource.close()

    return result


def get_instance_checksum(instance, resource_name):
    '''
    Return the checksum for the given resource name or None
    '''

    checksums = instance.checksums if hasattr(instance, 'checksums') and instance.checksums else {}

    try:
        return checksums[resource_name]
    except KeyError:
        return None


# ==============
# Helper methods
# ==============
def _extract_relation( src_model_field ):
    """
    Extract source/destination models and attributes from
    ManyToManyField definition (e.g Release.related_images)
    """
    try:
        field = src_model_field.field  # src_model_field equals e.g. Release.related_images or PictureOfTheWeek.image

        if isinstance( field, models.ManyToManyField ) or isinstance( field, models.ForeignKey ):
            src_class = field.remote_field.related_model
            src_attr = field.name
            dest_class = field.remote_field.model
            dest_attr = field.remote_field.get_accessor_name()

        if isinstance( field, models.ManyToManyField ):
            through_class = src_model_field.through
            through_src_name = field.m2m_field_name()
            through_dest_name = field.m2m_reverse_field_name()

            return ( src_class, src_attr, dest_class, dest_attr, through_class, through_src_name, through_dest_name )
        else:
            return ( src_class, src_attr, dest_class, dest_attr )

        return ()
    except AttributeError:
        raise ImproperlyConfigured( "propagate_m2m_release_date only works on ManyToManyFields" )


def _check_model( klass, with_owner=False ):
    """
    Check a model klass if it is an archive and has release dates fields specified.
    """
    # Check that model is an ArchiveModel
    if not issubclass( klass, ArchiveModel ):
        raise ImproperlyConfigured( "Model %s.%s must be a subclass of ArchiveModel." % ( klass._meta.app_label, klass._meta.model_name ) )

    # Check that archive has release and embargo dated
    if not klass.Archive.Meta.release_date or not klass.Archive.Meta.embargo_date or not klass.Archive.Meta.published:
        raise ImproperlyConfigured( "Model %s.%s is missing one or more of the fields: release date, embargo date and published." % ( klass._meta.app_label, klass._meta.model_name ) )

    if with_owner and not klass.Archive.Meta.release_date_owner:
        raise ImproperlyConfigured( "Model %s.%s is missing release_date_owner." % ( klass._meta.app_label, klass._meta.model_name ) )


# ========================
# Release date propagation
# ========================
#
# To ensure efficient and simple queries, release dates are propagated from one model to related
# models (e.g. from press releases to related images and videos)
#
# The propagation works over both ForeignKeys and ManyToManyFields.
#
# Testing
# -------
# Testing of the release date propagation is currently done in djangoplicity.releases.tests


# Concepts:
#
# The *release date* (meaning release date and embargo date) is defined in a *source archive*
# and must be propagated to one or more *destination archives*. The propagation of a release date
# from source archive to destination archives happens on the following actions:
#  * _creation of a relation_ between source object and a destination object
#  * _deletion of a relation_ between source object and a destination object
#  * _update of a relation_ between source object and a destination object
#  * _update of the release date_ in the source object
#
# The destination archives must have the following attributes:
#  * release date
#  * embargo date
#  * release date owner: object id of owner
#  * owner archive: archive wherein object id is located
#
#

def propagate_release_date( src_model_field ):
    """
    Setup propagation of release dates over a ForeignKey or ManyToManyField.

    It works by connecting a post-save and post-delete signals. If the release
    date in the source archive is updated then it's automatically propagated to the
    destination archives.
    """
    try:
        if isinstance( src_model_field.field, models.ForeignKey ):
            _propagate_fk_release_date( src_model_field )
        elif isinstance( src_model_field.field, models.ManyToManyField ):
            _propagate_m2m_release_date( src_model_field )
    except AttributeError:
        raise ImproperlyConfigured( "Expected ForeignKey or ManyToManyField" )


def _propagate_fk_release_date( src_model_field ):
    """
    Setup propagation of release dates over a ForeignKey.
    """
    # Get source/destination models
    ( src_class, src_attr, dest_class, dest_attr ) = _extract_relation( src_model_field )

    # Run checks on models
    _check_model( src_class )
    _check_model( dest_class, with_owner=True )

    # Partially evaluate signal handlers
    pre_source_updated_created = curry( fk_pre_source_updated_created_handler, src_attr )
    source_updated_created = curry( fk_source_updated_created_handler, src_attr, dest_attr )
    source_deleted = curry( fk_source_deleted_handler, src_attr, dest_class, dest_attr )

    # Connect signals
    pre_save.connect( pre_source_updated_created, sender=src_class, weak=False )
    post_save.connect( source_updated_created, sender=src_class, weak=False )
    post_delete.connect( source_deleted, sender=src_class, weak=False )


def _propagate_m2m_release_date( src_model_field ):
    """
    Setup propagation of release dates over a ManyToManyField.

    The primary difference from _propagate_fk_release_date is that
    update methods must be fired on different signals.
    """
    # Get source/destination models
    ( src_class, src_attr, dest_class, dest_attr, through_class, through_src_name, through_dest_name ) = _extract_relation( src_model_field )

    # Run checks on models
    _check_model( src_class )
    _check_model( dest_class, with_owner=True )

    # Partially evaluate signal handlers
    relation_created = curry( m2m_relation_created_handler, through_src_name, through_dest_name )
    relation_deleted = curry( m2m_relation_deleted_handler, src_class, through_src_name, through_dest_name, dest_attr )
    source_updated = curry( m2m_source_updated_handler, dest_class, src_attr )

    # Connect signals
    post_save.connect( relation_created, sender=through_class, weak=False )
    post_delete.connect( relation_deleted, sender=through_class, weak=False )
    post_save.connect( source_updated, sender=src_class, weak=False )


def _remove_release_date( dest_instance, source_instance_identifier, dest_attr ):
    """
    Remove a release date of a destination instance when a relation to
    a source instance has been removed.

    Either 1) set the release date to another related object or 2) leave
    release date but remove owner.
    """
    # Ensure this object owns the release date or the related item
    if dest_instance and dest_instance.release_date_owner == source_instance_identifier:
        try:
            # See if we have any other related item that we need to
            # add the release date from.

            related_sources_qs = getattr( dest_instance, dest_attr ).all().order_by( 'release_date' )

            # We take the earliest possible release date (qs is ordered with earliest first)
            obj = related_sources_qs[0]
            dest_instance.release_date_owner = obj.get_object_identifier()
            dest_instance.release_date = obj.release_date
            dest_instance.embargo_date = obj.embargo_date
            dest_instance.save()
        except IndexError:
            dest_instance.release_date_owner = ''
            # do not reset release date, since we want it to show correctly in feeds
            # related_object.release_date = None
            dest_instance.embargo_date = None
            dest_instance.save()


def _update_release_date( dest_instance, source_instance ):
    """
    Update the release date of a destination instance when a relation to
    a source instance has been created.
    """
    # Ensure this object owns the release date or the related item
    # does not have an release date owner.
    if hasattr( source_instance, 'release_date_owner' ) and source_instance.release_date_owner:
        owner = source_instance.release_date_owner
    else:
        owner = source_instance.get_object_identifier()

    #owner = source_instance.get_object_identifier()
    if dest_instance and ( dest_instance.release_date_owner == source_instance.get_object_identifier() or dest_instance.release_date_owner == owner or not dest_instance.release_date_owner ):
        dest_instance.release_date_owner = owner
        dest_instance.release_date = source_instance.release_date
        dest_instance.embargo_date = source_instance.embargo_date
        dest_instance.save()


# ================
# Signal handlers
# ================
# Note all signal handlers cannot be used without first partially evaluating (see django.utils.functional.curry)

def fk_pre_source_updated_created_handler( src_attr, sender, instance, raw=False, *args, **kwargs ):
    """
    Incases where a FK is set to null, it's hard in django to determine if
    the value of the FK have changed. This pre_save method will determine if
    an FK was changed, and if it was, it will make sure that the postsave method
    can reset release_date_owner of old related objects.
    """
    if raw:
        return

    # Check if FK has been set to null (ignore newly created source instance,
    # since if newly created, and FK is null, they couldn't have owned any
    # release dates
    dest_instance = getattr( instance, src_attr )
    if not hasattr( instance, '_release_date_owner_of' ):
        instance._release_date_owner_of = {}

    if not dest_instance and instance.pk:
        if not hasattr( instance, '_release_date_owner_old' ):
            try:
                instance._release_date_owner_old = sender.objects.get( pk=instance.pk )
            except ObjectDoesNotExist:
                instance._release_date_owner_old = None

        if hasattr( instance, '_release_date_owner_old' ) and instance._release_date_owner_old:
            instance._release_date_owner_of[src_attr] = getattr( instance._release_date_owner_old, src_attr )
        else:
            instance._release_date_owner_of[src_attr] = None
    else:
        instance._release_date_owner_of[src_attr] = None


def fk_source_updated_created_handler( src_attr, dest_attr, sender, instance, created, raw=False, *args, **kwargs ):
    """
    Post-save signal handler for propagating the release date in the source class
    to all destination classes.
    """

    if raw:
        return

    # Get related object.
    dest_instance = getattr( instance, src_attr )
    source_instance = instance

    if dest_instance:
        _update_release_date( dest_instance, source_instance )
    else:
        if hasattr( instance, '_release_date_owner_old' ):
            del instance._release_date_owner_old
        if hasattr( instance, '_release_date_owner_of' ) and src_attr in instance._release_date_owner_of and instance._release_date_owner_of[src_attr]:
            _remove_release_date( instance._release_date_owner_of[src_attr], source_instance.get_object_identifier(), dest_attr )


def fk_source_deleted_handler( src_attr, dest_class, dest_attr, sender, instance, raw=False, *args, **kwargs ):
    """
    Post-delete handler for removing the release date of a source class being deleted
    from all it's destination classes.
    """
    if raw:
        return

    # Get dest and src instances
    dest_instance = getattr( instance, src_attr )
    source_instance_identifier = instance.get_object_identifier()
    _remove_release_date( dest_instance, source_instance_identifier, dest_attr )


def m2m_relation_created_handler( through_src_name, through_dest_name, sender, instance, created, **kwargs ):
    """
    Signal handler invoked when a relationship is created between a
    destination instance and source instance.
    """
    if created:
        dest_instance = getattr( instance, through_dest_name )
        source_instance = getattr( instance, through_src_name )
        _update_release_date( dest_instance, source_instance )


def m2m_relation_deleted_handler( src_class, through_src_name, through_dest_name, dest_attr, sender, instance, **kwargs ):
    """
    Signal handler invoked when a relationship is removed between a
    source instance and destination instance.
    """

    # source object: the release date owner
    # destination object: the release date "owned"

    # Let's try to get the destination object. If we can't, that means the object being deleted
    # is not the release date owner, (e.g. we are deteting an Image that "belonged" to a Release).
    try:
        dest_instance = getattr( instance, through_dest_name )
    except AttributeError:
        dest_instance = None

    if dest_instance is not None:
        # Source object has been deleted at this point, so it's no longer available (hence we cannot
        # just call "getattr( instance, through_src_name ).get_object_identifier()" )
        source_instance_identifier = src_class.get_object_identifier_for_pk( pk=getattr( instance, "%s_id" % through_src_name ) )
        _remove_release_date( dest_instance, source_instance_identifier, dest_attr )


def m2m_source_updated_handler( dest_class, src_attr, sender, instance, **kwargs ):
    """
    Propagate release dates for source to destination

    Only already existing relationships to connections are going to be updated.
    The rest will be taken care of when creating the link.
    """
    # Be sure to evaluate qs, otherwise the update method in the bottom will have circular reference (selecting from the same table
    # you are updating is not allowed).
    related_object_set = list( dest_class.objects.filter( **{ 'release_date_owner': instance.get_object_identifier() } ).values_list( 'id', flat=True ) )
    if settings.USE_I18N and issubclass( dest_class, TranslationModel ):
        # We need to use base manager to have access to both source and translations.
        qs = dest_class._base_manager.filter( models.Q( id__in=related_object_set ) | models.Q( source__in=related_object_set ) )
    else:
        qs = dest_class.objects.filter( id__in=related_object_set )

    # We keep track of instances which have the embargo/release change so that
    # we can run set_embargo_date_task accordingly
    embargo_date_changed = list(qs.exclude(embargo_date=instance.embargo_date).values_list('pk', flat=True))
    release_date_changed = list(qs.exclude(release_date=instance.release_date).values_list('pk', flat=True))

    qs.update( **{ 'release_date': instance.release_date, 'embargo_date': instance.embargo_date } )

    # Run set_embargo_date_task() for all instances were embargo date has changed
    for instance in qs.filter(pk__in=embargo_date_changed):
        if settings.USE_I18N and isinstance(instance, TranslationModel) and instance.is_translation():
            continue
        instance.set_embargo_date_task()
        instance.save()

    # Run set_release_date_task() for all instances were release date has changed
    for instance in qs.filter(pk__in=release_date_changed):
        if settings.USE_I18N and isinstance(instance, TranslationModel) and instance.is_translation():
            continue
        instance.set_release_date_task()
        instance.save()


def release_date_change_check(sender, instance, signal, raw=False, *args, **kwargs):
    """
    Checks if the release or embargo date has changed and set a scheduled task
    to run embargo_release_date_task at the given time.
    """
    if raw:
        return

    # We only check for release/embargo date change for source objects
    # when translations are used
    if settings.USE_I18N and isinstance(instance, TranslationModel) and instance.is_translation():
        return

    embargo_date_has_changed = False
    release_date_has_changed = False
    try:
        obj = sender.objects.get(pk=instance.pk)

        if obj.embargo_date != instance.embargo_date:
            embargo_date_has_changed = True

        if obj.release_date != instance.release_date:
            release_date_has_changed = True
    except sender.DoesNotExist:
        # New object
        embargo_date_has_changed = True
        release_date_has_changed = True

    if embargo_date_has_changed:
        instance.set_embargo_date_task()

    if release_date_has_changed:
        instance.set_release_date_task()


def main_visual_translated(main_visual, related_items):
    for v in related_items:
        if v.source and main_visual and v.source == main_visual:
            main_visual = v
    return main_visual
