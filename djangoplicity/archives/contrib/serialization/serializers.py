from builtins import str
from past.builtins import basestring
from builtins import object
from datetime import datetime
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_text
from functools import partial

from djangoplicity.utils.datetimes import timezone


class SerializationError( Exception ):
    pass


class Serializer( object ):
    def serialize( self, obj ):
        raise NotImplementedError


class SimpleSerializer( Serializer ):
    fields = []
    related_fields = []
    related_cache = []

    def __init__( self, *args, **kwargs ):
        self._cached_objects = {}
        super( SimpleSerializer, self ).__init__( *args, **kwargs )

    def serialize_list( self, objects ):
        """
        Serialize list of image objects, but making some
        query optimizations.
        """
        datalist = []

        if self.related_cache:
            pks = [obj.pk for obj in objects]
            if pks:
                self._prime_cache( obj.__class__, pks )

        for obj in objects:
            datalist.append( self.serialize( obj ).data )
        return Serialization( datalist )

    def serialize( self, obj ):
        """ Serialize one object
        """
        data = {}

        for f in self.fields:
            data.update( **self._serialize_field( obj, f ) )

        for f_spec in self.related_fields:
            data.update( self._serialize_related( obj, f_spec ) )

        return Serialization( data )

    def _serialize_field( self, obj, field ):
        """
        Serialize a single field
        """
        if hasattr( self, "get_%s_value" % field ):
            func = getattr( self, "get_%s_value" % field )
        elif hasattr( obj, field ):
            func = lambda x: getattr( x, field )
        else:
            func = None

        if not func:
            raise ImproperlyConfigured( "%s has no method get_%s_value neither does %s have a field %s" % ( self.__class__.__name__, field, obj.__class__.__name__, field ) )

        value = func( obj )
        return { field: value if value is not None else value }

    def _serialize_related( self, obj, field_spec ):
        """
        Serialize related objects
        """
        fieldname = None
        if isinstance( field_spec, basestring ):
            field = field_spec
            serializercls = None
            filter = None
        elif len( field_spec ) == 2:
            field, serializercls = field_spec
            filter = None
        elif len( field_spec ) == 3:
            field, serializercls, filter = field_spec
        elif len( field_spec ) == 4:
            field, serializercls, filter, fieldname = field_spec
        else:
            raise ImproperlyConfigured( "Cannot serialize related objects - invalid field specification %s" % field_spec )

        # Get related objects
        func = None
        if hasattr( self, "get_%s_values" % field ):
            func = getattr( self, "get_%s_values" % field )
        elif hasattr( obj, field ):
            func = partial( self._get_related_objects, field=field )

        if not func:
            raise ImproperlyConfigured( "%s has no method get_%s_values neither does %s have a field %s" % ( self.__class__.__name__, field, obj.__class__.__name__, field ) )

        related_objects = func( obj, filter )

        # Serialize related objects (use serializer or just let the emitter turn the object into preferred type)
        values = []
        serializer = serializercls() if serializercls else None

        if related_objects:
            for relobj in related_objects:
                if serializer:
                    val = serializer.serialize( relobj )
                    if val is not None:
                        values.append( val.data )
                else:
                    if relobj is not None:
                        values.append( relobj )

        fieldname = fieldname if fieldname else field
        return { fieldname: values }

    def _get_related_objects( self, obj, filter_spec, field=None ):
        """
        Helper function to get all related objects
        """
        if field in self.related_cache:
            return self._get_cached_objects( obj, field, filter_spec )

        if filter_spec:
            return getattr( obj, field ).filter( **filter_spec )
        else:
            return getattr( obj, field ).all()

    def _get_cached_objects( self, obj, field, filter_spec ):
        """
        Get cached related objects for this pk
        """
        if self._cached_objects:  # We only cache objects for list serializations
            return [relobj for ( pk, relobj ) in self._cached_objects[field] if pk == obj.pk]

    def _prime_cache( self, model, pks ):
        """
        Prime cache with all related objects
        """
        for field, _val in list(self.related_cache.items()):
            reldescriptor = getattr( model, field )

            through_model_fieldname = reldescriptor.field.related.m2m_reverse_field_name()
            through_relatedmodel_fieldname = reldescriptor.field.related.m2m_field_name()

            filter_spec = { "%s__in" % through_model_fieldname: pks }

            self._cached_objects[field] = [
                ( getattr( x, "%s_id" % through_model_fieldname ), getattr( x, through_relatedmodel_fieldname ) )
                for x in reldescriptor.through.objects.filter( **filter_spec ).select_related( through_relatedmodel_fieldname )
            ]

    def append_timezone( self, date ):
        """
        Append the local timezone (as defined in settings.py) to
        a date if it doesn't have any timezone information.
        """
        if not isinstance( date, datetime ):
            raise Exception( "%s is not a datetime instance" % type( date ) )
        return timezone( date, tz=settings.TIME_ZONE )


class Serialization( object ):
    data = None

    def __init__( self, data ):
        self.data = data


class Emitter( object ):
    def emit( self, serialization ):
        raise NotImplementedError

    def response( self, response ):
        return response


class XMPEmitter( Emitter ):
    """
    """
    name = "xmp"
    content_type = "text/plain"

    def __init__( self ):
        pass

    def emit( self, serialization, type='str' ):
        import sys

        try:
            from libavm import AVMMeta
            avm = AVMMeta()
            avm_enabled = True
        except ImportError:
            avm = {}
            avm_enabled = False

        datadict = serialization.data
        if not isinstance( datadict, dict ):
            raise SerializationError( "XMP emitter expected a dictionary but got a %s." % type( datadict ) )

        for k, v in list(datadict.items()):
            try:
                if sys.version_info[0] >= 3:
                    if isinstance(v, bytes):
                        v = v.decode()
                avm[k] = v
            except KeyError:
                # Skip custom fields in serializer not defined in AVM
                continue

        if avm_enabled:
            if avm:
                if type == 'XMPMeta':
                    return avm.xmp
                elif type == 'AVMMeta':
                    return avm
                else:
                    return avm.xmp.serialize_to_unicode()
            else:
                return ""
        else:
            return u"Error:libavm could not load. Try running 'from libavm import AVMMeta' from a python prompt."


class JSONEmitter( Emitter ):
    name = "json"
    content_type = "text/plain"

    json_encoders = {
        datetime: lambda dt: dt.isoformat(),
    }

    def emit( self, serialization ):
        return json.dumps( serialization.data, default=self.default_encode )

    def default_encode( self, v ):
        if hasattr( v, 'as_json' ) and callable( v.as_json ):
            return v.as_json()

        t = type( v )
        if t in self.json_encoders:
            encoder = self.json_encoders[t]
            return encoder( v )

        try:
            return str( v )
        except:
            pass

        # Default return error
        return json.JSONEncoder.default( self, v )


class ICalEmitter( Emitter ):
    name = "ical"
    content_type = "text/calendar"

    def emit( self, serialization ):
        try:
            from icalendar import Calendar, Event
            from icalendar import vText
        except ImportError:
            raise SerializationError( "iCalendar module could not be loaded." )

        cal = Calendar()
        cal.add( 'prodid', '-//European Southern Observatory//Djangoplicity//EN' )
        cal.add( 'version', '2.0' )

        for e in serialization.data:
            event = Event()
            event.add( 'summary', smart_text( e['summary'] ) )
            event.add( 'description', smart_text( e['description'] ) )
            event.add( 'dtstart', e['dtstart'] )
            event.add( 'dtend', e['dtend'] )
            event.add( 'dtstamp', e['dtstamp'] )

            if 'location' in e:
                event['location'] = vText( smart_text( e['location'] ) )

            cal.add_component( event )

        return cal.to_ical()

    def response( self, response ):
        response['Content-Disposition'] = "attachment; filename=calendar.ics"
        return response
