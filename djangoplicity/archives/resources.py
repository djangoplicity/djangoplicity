# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from builtins import object
import logging
import os.path

from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.core.files.images import ImageFile
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.encoding import smart_text, smart_str
from django.utils.translation import ugettext_lazy as _, ugettext_noop

from djangoplicity.media.consts import MEDIA_CONTENT_SERVERS
from djangoplicity.contentserver.base import S3ContentServer
from djangoplicity.translation.models import TranslationModel

logger = logging.getLogger(__name__)

__all__ = (
    'FileType', 'ImageFileType', 'ResourceFile', 'ImageResourceFile',
    'ResourceManager', 'ImageResourceManager', 'get_instance_resource',
    'ResourceError'
)


class ResourceError( Exception ):
    pass


def _root_for_instance( instance, resource_name ):
    """ Return the root path for the resources managed by this ResourceManager """
    return os.path.join( instance.Archive.Meta.root, resource_name )


def _archive_instance_id( instance ):
    """ Return the archive id of this instance """
    try:
        # If translation, use source resources.
        if settings.USE_I18N and isinstance( instance, TranslationModel ) and instance.is_translation():
            instance = instance.source
        return getattr( instance, instance.Archive.Meta.idfield )
    except AttributeError:
        raise Exception( _('Instance has no archive id. This may be because the instance has not been saved yet.') )


def get_instance_resource( obj, resource_name ):
    """
    Get a resource
    """
    from djangoplicity.archives.base import ArchiveModel

    if not isinstance( obj, ArchiveModel ):
        raise ResourceError( "%s not an instance of ArchiveModel" % str( obj ) )

    resattr = "%s%s" % ( obj.__class__.Archive.Meta.resource_fields_prefix, resource_name )

    if not hasattr( obj, resattr ):
        raise ResourceError( "%s is not a valid resource for %s models" % ( resattr, obj.__class__.__name__ ) )

    return getattr( obj, resattr )


class FileType(object):
    """
    Metadata for a specific file type of a file resource. For an derived image
    resource like thumbnail this could e.g. be the image size, or for a specific
    video format it could be the encoding, framerate etc.
    """
    verbose_name = ugettext_noop( u'File' )
    field = models.FileField
    field_kwargs = {}
    exts = []
    help_text = u''


class ImageFileType( FileType ):
    """
    Metadata for image file types.
    """
    verbose_name = ugettext_noop( u'Image' )
    field = models.ImageField
    exts = ['jpg', 'tif', 'png', 'gif' ]
    size = None  # Max size in pixel (either height or width)
    width = None
    height = None
    unsharp = None  # Amount of unsharp in percent, e.g.: 70
    upscale = False  # Don't generate formats smaller than the original
    required = True  # Raise an error if the format is required but can't be generated


class ResourceFile( File ):
    """
    Similar to FieldFile, but is not required to be bound to a field and instance.
    """
    def __init__(self, path, storage, instance = None ):
        self.storage = storage
        self.name = path or u''
        self._closed = False
        self.instance = instance

    def _get_file(self):
        if not hasattr(self, '_file'):
            self._file = self.storage.open(self.name, 'rb')
        return self._file
    file = property(_get_file)

    def _get_path(self):
        return self.storage.path(self.name)
    path = property(_get_path)

    def _get_absolute_url(self):
        '''
        Return the absolute URL, use HTTPS if not protocol is specified in
        the URL
        '''
        url = self.storage.url(self.name)
        if url.startswith('http'):
            return url

        if url.startswith('//'):
            return 'https:' + url

        return 'https://%s%s' % (Site.objects.get_current().domain, url)
    absolute_url = property(_get_absolute_url)

    def _should_redirect_to_proxy(self):
        '''
        Return True if the file should be redirected to the proxy URL (AccessTag is Private).
        '''
        # 1. If doesnt exist USE_PROXY_FOR_PRIVATE_MEDIA, return False
        if not getattr(settings, 'USE_PROXY_FOR_PRIVATE_MEDIA', False):
            return False
            
        # 2. If not instance or not has access tag, return False
        if not self.instance or not hasattr(self.instance, 'get_access_tag'):
            return False
        
        # 3. If the instance is not a content server, return False
        if not getattr(self.instance, 'content_server', None):
            return False

        # 4. If content server is not s3, return False
        server = MEDIA_CONTENT_SERVERS.get(self.instance.content_server)
        if not isinstance(server, S3ContentServer):
            return False 

        # 5. Use proxy if access tag is private
        access_tag = self.instance.get_access_tag()
        return access_tag == 'Private'
    
    def _extract_resource_parts(self):
        # ./././<format>/<id.ext>
        parts = self.name.split('/')
        if len(parts) < 2:
            return None
        
        filename = parts[-1]        # <id.ext>
        format = parts[-2]          # <format>

        if '.' not in filename:
            return None
        
        id = filename.split('.')[0]
        ext = filename.split('.')[1]

        return format, id, ext

    def _get_url(self):
        # If not required to redirect to proxy, return the storage URL.
        if not self._should_redirect_to_proxy():
            return self.storage.url(self.name)
        
        # If the file is a zoomable image, return the storage URL.
        if 'zoomable' in self.name.split('/'):
            return self.storage.url(self.name)

        format, id, ext = self._extract_resource_parts()
        model_name = self.instance._meta.model_name 

        # If the format is always public, return the storage URL.
        if self.instance.get_access_tag_for_format(format) == 'Public':
            return self.storage.url(self.name)

        return reverse(
            'resource_proxy',
            kwargs={
                'model': model_name,
                'format': format,
                'id': id,
                'ext': ext,
            }
        )
    url = property(_get_url)

    def open(self, mode='rb'):
        return super(ResourceFile, self).open(mode)
    # open() doesn't alter the file's contents, but it does reset the pointer
    open.alters_data = True

    def save(self, name, content):
        self._name = self.storage.save(name, content)
        # Update the filesize cache
        self._size = len(content)
    save.alters_data = True

    def delete(self):
        self.close()
        self.storage.delete(self.name)

        self._name = None

        # Delete the filesize cache
        if hasattr(self, '_size'):
            del self._size
    delete.alters_data = True

    def __getstate__(self):
        # For ResourceFile the only necessary data to be pickled is the
        # file's name itself and the storage class.
        return {'name': self.name, '_closed': self._closed, 'storage': self.storage, 'instance': self.instance }


class ImageResourceFile( ResourceFile, ImageFile ):
    """
    """
    def delete(self):
        # Clear the image dimensions cache
        if hasattr(self, '_dimensions_cache'):
            del self._dimensions_cache
        super(ImageResourceFile, self).delete()


class ResourceManager(object):
    """
    """
    def __init__(self, verbose_name=None, derived=None, field=None,
            field_kwargs=None, exts=None, help_text=None, type=FileType,
            storage=None):
        """
        Note: self.name will be ingested into the ResourceManager by ArchiveBase class, which
        is creating ArchiveModel classes.
        """

        # Default settings from type
        if type is not None:
            if not issubclass(type, FileType):
                raise ImproperlyConfigured( _('Argument type for Resource must be FileType class or subclass thereof.') )

            self.type = type
            self.verbose_name = smart_text( type.verbose_name )
            self.field = type.field or None
            self.field_kwargs = type.field_kwargs or None
            self.exts = type.exts or []
            self.help_text = type.help_text or None
        else:
            self.type = None
            self.verbose_name = smart_text( ugettext_noop(u'Resource') )
            self.field = None
            self.field_kwargs = None
            self.exts = []
            self.help_text = None

        # Overwritten the file types values with user defined ones if they exists.
        if verbose_name is not None:
            self.verbose_name = smart_text( verbose_name )

        if field is not None:
            self.field = field or self.field

        if field_kwargs is not None:
            self.field_kwargs = field_kwargs

        if exts is not None:
            self.exts = exts

        if help_text is not None:
            self.help_text = help_text

        self.derived = derived

    def __str__(self):
        return smart_str(str(self.verbose_name) or '')

    def __unicode__(self):
        return smart_text(self.verbose_name or u'')

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self or "None")

    def get_resource_for_instance( self, instance, fileclass=ResourceFile, only_local_files=False ):
        """
        Hook for getting the file (resource) for a model instance (can be any model instance).
        only_local_files informs us if we need to check the local resources or not, this is useful for showing files that are ONLY in the content server like S3 and not locally
        """
        # Note 'name' has been ingested into the ResourceManager by ArchiveBase
        localbase = os.path.join( _root_for_instance( instance, self.name ), _archive_instance_id( instance ) )
        base = localbase
        storage = FileSystemStorage()
        resource = None

        # Identify the file extension if any
        ext = None
        name = base
        for e in self.exts:
            name = '%s.%s' % (base, e)
            localname = '%s.%s' % (localbase, e)
            if storage.exists(localname):
                ext = e
                resource = fileclass(name, storage, instance=instance)
                break
        else:
            if storage.exists(localbase):
                # No extension, but the file exists
                resource = fileclass(name, storage, instance=instance)

        # Check whether a content server is defined for this resource
        if (not only_local_files) and hasattr(instance, 'content_server') and instance.content_server and instance.content_server_ready:
            try:
                content_server = MEDIA_CONTENT_SERVERS[instance.content_server]
            except KeyError:
                logger.warning('Unknown content server: "%s" for %s: "%s"',
                    instance.content_server, instance.__class__.__name__, instance.id)
                content_server = None

            if content_server:
                # Try to get the extension from the existing records in the database ContentServerResource
                resource_record_found = False
                if hasattr(instance, 'get_source'):
                    # If it's a Translation model, get the original source which is linked to the resources
                    instance = instance.get_source()
                for resource_obj in instance.content_server_resources.all():
                    if resource_obj.format == self.name and resource_obj.is_active and resource_obj.content_server == instance.content_server:
                        ext = resource_obj.extension
                        resource_record_found = True
                        break

                if resource_record_found:
                    # The resource if found, then we can then use it
                    if ext:
                        # The extension is found either when the local files exists or when the ContentServerResource record is found
                        base += '.%s' % ext
                    resource = fileclass(base, storage, instance=instance)

                supports_all_formats = getattr(content_server, 'supports_all_formats', False)
                archive_formats = []
                if not supports_all_formats:
                    archive_class_name = '%s.%s' % (instance.__module__, instance.__class__.__name__)
                    try:
                        archive_formats = content_server.formats[archive_class_name]
                    except:
                        # No content server defined for this format
                        archive_formats = []
                
                if resource and (supports_all_formats or self.name in archive_formats):
                    new_location = os.path.join(storage.location, instance.Archive.Meta.root)
                    url = os.path.join(content_server.get_url(resource, self.name), instance.Archive.Meta.root)
                    storage = FileSystemStorage(base_url=url, location=new_location)
                    base = os.path.join(self.name, _archive_instance_id( instance ))

                    if ext:
                        # The extension is found either when the local files exists or when the ContentServerResource record is found
                        base += '.%s' % ext
                    # We updated the based and storage so we update the resource object:
                    resource = fileclass(base, storage, instance=instance)
                    if not content_server.requires_local_files:
                        resource.is_from_content_server = True

        return resource


class ImageResourceManager( ResourceManager ):
    """
    Image resource
    """
    def __init__(self, *args, **kwargs ):
        """ Constructor that ensures that"""

        if 'type' in kwargs:
            typ = kwargs['type']
        else:
            typ = ImageFileType

        if not issubclass( typ, ImageFileType ):
            raise ImproperlyConfigured( _('Argument type for ImageResourceManager must be ImageFileType class or subclass thereof. If not type is given, ImageFileType will be used.') )

        kwargs['type'] = typ

        super( ImageResourceManager, self ).__init__( *args, **kwargs )

    def get_resource_for_instance( self, instance, fileclass=ImageResourceFile, only_local_files=False ):
        """
        Hook for getting the file for this specific resource.
        """
        return super( ImageResourceManager, self ).get_resource_for_instance( instance, fileclass=ImageResourceFile, only_local_files=only_local_files )


class AudioResourceManager(ResourceManager):
    '''
    We subclass from ResourceFile to make it easier to identify audio
    resources when generating derivate formats.
    '''
    pass
