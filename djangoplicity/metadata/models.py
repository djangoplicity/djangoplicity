from builtins import str
from builtins import map
from builtins import range
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlencode
from six import python_2_unicode_compatible

from djangoplicity.metadata import consts


SIMBAD_URL = "https://simbad.u-strasbg.fr/simbad/sim-id"


if hasattr(settings, 'TELBIB'):
    TELBIB = settings.TELBIB
else:
    # ESO TELBIB
    TELBIB = "http://telbib.eso.org/detail.php?%(bibcode)s"

if settings.USE_I18N:
    from djangoplicity.translation.models import translation_reverse
    from django.utils import translation
    reverse_func = translation_reverse
    reverse_kwargs = lambda: { 'lang': translation.get_language() }
else:
    reverse_func = reverse
    reverse_kwargs = lambda: {}


@python_2_unicode_compatible
class Contact( models.Model):
    """
    Contact model for storing the following AVM tags:
       * Contact.Name
       * Contact.Email
       * Contact.Telephone


    Note, the remaining contact fields are not lists thus your model should
    provide the following tags itself:
       * Contact.Address
       * Contact.City
       * Contact.StateProvince
       * Contact.PostalCode
       * Contact.Country

    Note, see also the ExtendedContact model which contains above fields
    directly. The ExtendedContact models is however not AVM compliant as it
    changes the Address, City, StateProvience, PostalCode and Country from
    string format to string list format and add an Affiliation tag.

    Usage::
       class AVMModel( models.Model ):
           ...

       class AVMContact( Contact ):
           avm_model = models.ForeignKey( AVMModel, null=True, blank=True , on_delete=models.CASCADE)


    You can then include the AVMContact in the administration interface for AVMModel
    by making an inline administration interface.
    """
    name = models.CharField( max_length=255, blank=True )

    email = models.CharField( max_length=255, blank=True )

    telephone = models.CharField( max_length=255, blank=True )

    def __str__( self ):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']


class ExtendedContact( Contact ):
    """
    Extension of the standard AVM compliant contact model.

    Changes includes:
       * Changed format for Address, City, StateProvience, PostalCode and Country
         fields from string format to string list format
       * Add an Affiliation tag.
       * Add an Cellular tag.

    See Contact for usage example.

    TODO:: Ensure model can be converted to an AVM compliant model (with data-loss though).
    """
    cellular = models.CharField( max_length=255, blank=True )

    affiliation = models.CharField( max_length=255, blank=True )

    address = models.CharField( max_length=255, blank=True )

    city = models.CharField( max_length=255, blank=True )

    state_province = models.CharField( max_length=255, blank=True )

    postal_code = models.CharField( max_length=255, blank=True )

    country = models.CharField( max_length=255, blank=True )

    class Meta:
        abstract = True
        ordering = ['name']


@python_2_unicode_compatible
class TaxonomyHierarchy( models.Model ):
    """
    Model representation for AVM Image Taxonomy Hierarchy.

    Usage
    =====
    Make a many to many relationship to this model from your AVMModel

    """
    top_level = models.CharField( verbose_name=_( 'Top Level Hierarchy' ), max_length=1, null=False, blank=False, choices=consts.TOP_LEVEL_HIERARCHY, db_index=True )
    level1 = models.PositiveSmallIntegerField( null=True, blank=True )
    level2 = models.PositiveSmallIntegerField( null=True, blank=True )
    level3 = models.PositiveSmallIntegerField( null=True, blank=True )
    level4 = models.PositiveSmallIntegerField( null=True, blank=True )
    level5 = models.PositiveSmallIntegerField( null=True, blank=True )
    name = models.CharField( max_length=255, blank=False, unique=True )

    @staticmethod
    def simplify( taxonomy_list ):
        """
        Take a list of TaxonomyHierarchy instances and return a list of the
        instances with redundant entries removed.

        For instance the following list
           * Solar System : Planet
           * Solar System : Planet : Type : Terrestrial
           * Solar System : Planet : Feature : Surface

        can be simplified by removing "Solar System : Planet" since it is already
        implicit given by the two others.

        TODO:: Should also ensure that only one top level hierarchy can be selected
        """
        # Sort taxonomy_list by length
        # For t in taxonomy_list:
        #   for ts in taxonomy_list:
        #      if all ts begins with t then
        #        remove t
        return NotImplementedError()

    def __str__( self ):
        if self.top_level == 'X':
            return u'X - %s' % self.name
        return self.name

    def get_children(self):
        '''
        Returns a list of objects that match the current code
        E.g.: Returns A.6.1.2, A.6.1.1, A.6.1.3 and A.6.1 for object A.6.1
        '''
        kwargs = {'top_level': self.top_level}

        for i in range(1, 6):
            level = 'level%d' % i

            level_value = getattr(self, level)
            if level_value:
                kwargs[level] = level_value

        return TaxonomyHierarchy.objects.filter(**kwargs)

    @staticmethod
    def get_children_from_code(str):
        '''
        Returns a list of objects that match the giving code
        E.g.: Returns A.6.1.2, A.6.1.1, A.6.1.3 and A.6.1 for code A.6.1
        '''
        levels = str.split('.')
        kwargs = {'top_level': levels[0]}
        for i, level in enumerate(levels[1:], start=1):
            kwargs['level%d' % i] = level

        return TaxonomyHierarchy.objects.filter(**kwargs)

    @staticmethod
    def from_code(str):
        """
        Get a string in format B.1.1.1 and return the object
        """
        levels = [None for i in range(6)]

        lvs = str.split('.')

        for i, _j in enumerate(lvs):
            levels[i] = lvs[i]

        th = TaxonomyHierarchy.objects.get(top_level=levels[0], level1=levels[1], level2=levels[2], level3=levels[3], level4=levels[4], level5=levels[5])
        return th

    def avm_code( self ):
        elements = ( self.top_level, self.level1, self.level2, self.level3, self.level4, self.level5, )
        return ".".join( map( str, [x for x in elements if x is not None] ) )
    avm_code.short_description = _( "AVM Code" )

    class Meta:
        #ordering = ('top_level','level1', 'level2', 'level3', 'level4', 'level5', )
        unique_together = ( 'top_level', 'level1', 'level2', 'level3', 'level4', 'level5', )
        verbose_name_plural = 'Taxonomy Hierarchy'


@python_2_unicode_compatible
class AVMStringListModel( models.Model ):
    """
    Abstract model used to hold a list of values to be referenced by other models.

    In essence this gives the opportunity to have a controlled vocabulary
    """
    name = models.CharField( unique=True, max_length=255, blank=False, help_text=_('Can be a single name, or a list of names, separated by ";".'))
    alias = models.CharField( max_length=255, blank=True, help_text=_('Alternative names, separated by ";". These names will not be shown, but used to enable search.'))
    simbad_compliant = models.BooleanField( default=True, help_text=_('If "name" is a list, only the first item will be used to link to Simbad.'))
    wiki_link = models.URLField( max_length=255, blank=True )

    def split(self):
        return [it.strip() for it in self.name.split(';')]

    def simbad_link(self):
        if self.simbad_compliant:
            #  return "%s?%s" % (SIMBAD_URL, urlencode([('Ident', self.name)])) # to use the whole list
            return "%s?%s" % (SIMBAD_URL, urlencode([('Ident', self.split()[0])]))  # to use only the first name in the list
        else:
            return None

    def __str__( self ):
        return self.name

    class Meta:
        abstract = True


class Facility( AVMStringListModel ):
    """
    """
    published = models.BooleanField( default=True, verbose_name=_("Include in listings") )

    class Meta:
        verbose_name_plural = 'Facilities'
        ordering = ('name',)


class Instrument( AVMStringListModel ):
    """
    """
    published = models.BooleanField( default=True, verbose_name=_("Include in listings") )

    class Meta:
        ordering = ('name',)


class SubjectName( AVMStringListModel ):
    """
    """
    class Meta:
        verbose_name = 'Subject Name'
        ordering = ('name',)


@python_2_unicode_compatible
class Publication( models.Model ):
    """
    AVM 1.2 extension (TBC)
    """
    bibcode = models.CharField( max_length=19, verbose_name=_("Bibliographic Code"), help_text=_("ADS Bibliographic Code - see http://adsdoc.harvard.edu/abs_doc/help_pages/data.html#bibcodes") )

    def __str__(self):
        return str(self.bibcode)

    def get_absolute_url(self):
        """ Return link to ESO Telescope Bibliography """
        if hasattr(settings, 'TELBIB'):
            return TELBIB % { 'bibcode': self.bibcode }
        else:
            return TELBIB % { 'bibcode': urlencode([('bibcode', self.bibcode)]) }

    class Meta:
        ordering = ('-bibcode',)


@python_2_unicode_compatible
class ObservationProposal( models.Model ):
    """
    AVM 1.2 extension (TBC)
    """
    proposal_id = models.CharField( max_length=255, verbose_name=_("Program/Proposal ID"), help_text=_("The observation proposal ID from the specific observatory.") )

    def __str__(self):
        return str(self.proposal_id)

    class Meta:
        ordering = ('proposal_id',)


@python_2_unicode_compatible
class CategoryType( models.Model ):
    name = models.CharField( max_length=255, unique=True )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


@python_2_unicode_compatible
class Category( models.Model ):
    """
    Model for storing web categories.
    """
    url = models.SlugField( db_index=True, blank=False, null=False, verbose_name=_("URL"), )
    type = models.ForeignKey( CategoryType, help_text=_("Defines to which archive this query applies."), on_delete=models.CASCADE)
    name = models.CharField( max_length=255, blank=False, null=False, help_text=_("Title of query to be displayed to the user.") )
    logo_url = models.URLField(verbose_name="Logo URL", blank=True, null=True, max_length=255)
    enabled = models.BooleanField( default=True, )

    def __str__(self):
        result = self.name
        if not self.enabled:
            result += ' (disabled)'
        return result

    def get_absolute_url(self):
        return reverse_func('%s_query_category' % self.type.name.lower(),
                args=[self.url], **reverse_kwargs())

    class Meta:
        ordering = ('type', 'name',)
        unique_together = ('url', 'type',)
        verbose_name = _('Web Category')
        verbose_name_plural = _('Web Categories')


@python_2_unicode_compatible
class Program(models.Model):
    """
    Model for storing Programs
    """
    url = models.SlugField( db_index=True, blank=False, null=False, verbose_name=_("URL"), )
    name = models.CharField( max_length=255, blank=False, null=False, help_text=_("Title of query to be displayed to the user.") )
    types = models.ManyToManyField(CategoryType, help_text=_("Defines to which types this program applies."), related_name='+')
    logo_url = models.URLField(verbose_name="Logo URL", blank=True, null=True, max_length=255)
    enabled = models.BooleanField(default=True, )
    join_in_browser = models.CharField(
        help_text=_('Add the type of views where you want to merge the programs'),
        max_length=255,
        blank=True,
        null=True,
    )
    related_programs = models.ManyToManyField('self', verbose_name='Join with Programs', blank=True)

    def __str__(self):
        result = self.name
        if not self.enabled:
            result += ' (disabled)'
        return result

    def get_absolute_url(self, type='releases'):
        return reverse_func('%s_query_program' % type.lower(),
                            args=[self.url], **reverse_kwargs())

    class Meta:
        ordering = ('name',)
        unique_together = ('url',)
        verbose_name = _('Program')
        verbose_name_plural = _('Programs')


@python_2_unicode_compatible
class ProgramLogoLineup(models.Model):
    """
    Model for storing Programs
    """
    program = models.ForeignKey('Program', on_delete=models.CASCADE)
    name = models.CharField( max_length=255, blank=False, null=False, help_text=_("Name of the logo line-up") )
    logo_lineup_url = models.URLField(verbose_name="Logo line-up URL", blank=False, null=False)

    def __str__(self):
        return f"{self.name} ({self.program.name})"

    class Meta:
        ordering = ('name',)
        verbose_name = _('Program Logo Lineup')
        verbose_name_plural = _('Programs Logo Lineups')


@python_2_unicode_compatible
class TaggingStatus( models.Model ):
    """
    Model for tagging images with a tagging state
    """
    slug = models.SlugField( unique=True )
    name = models.CharField( unique=True, max_length=255 )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = _('tagging statuses')
