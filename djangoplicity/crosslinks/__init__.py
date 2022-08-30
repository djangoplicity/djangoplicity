"""
Simple module for defining cross-links between archives on ESO-hosted djangoplicity sites.
"""

_ = lambda x: x

ARCHIVE_CROSSLINKS = {
    'announcements': (
        ('esawebb.org', 'https://esawebb.org/announcements/'),
    ),
    'releases': (
        ('esawebb.org', 'https://esawebb.org/news/'),
    ),
    'images': (
        ('esawebb.org', 'https://esawebb.org/images/'),
    ),
    'videos': (
        ('esawebb.org', 'https://esawebb.org/videos/'),
    ),
    'potw': (
        ('esawebb.org', 'https://esawebb.org/images/potm/'),
    ),
    'posters': (
        ('esawebb.org', 'https://esawebb.org/products/print_posters/'),
    ),
    'books': (
        ('esawebb.org', 'https://esawebb.org/about/further_information/books/'),
    ),
    'brochures': (
        ('esawebb.org', 'https://esawebb.org/about/further_information/brochures/'),
    ),
    'calendars': (
        ('esawebb.org', 'https://esawebb.org/products/calendars/'),
    ),
    'education': (
        #('esawebb.org', 'https://esawebb.org/projects/anniversary/educational_material/'),
    ),
    'newsletters': (
        ('esawebb.org', 'https://esawebb.org/newsletters/'),

    ),
    'periodicals': (
        # ( 'esawebb.org', 'https://esawebb.org/about/further_information/newsletters/' )#brokend
    ),
    'postcards': (
        ('esawebb.org', 'https://esawebb.org/products/postcards/'),
    ),
    'logos': (
        ('esawebb.org', 'https://esawebb.org/products/logos/'),
    ),
    'conferenceposters': (
        ('esawebb.org', 'https://esawebb.org/products/conf_posters/'),
    ),
    'presentations': (
        ('esawebb.org', 'https://esawebb.org/products/presentations/'),
    ),
    'exhibitions': (
        ('esawebb.org', 'https://esawebb.org/products/exhibitions/'),
    ),
    'dvds': (
        ('esawebb.org', 'https://esawebb.org/products/media/'),
    ),
    'techdocs': (
        # ( 'esawebb.org', 'http://www.esawebb.org/about/further_information/techdocs/' )#roto
    ),

}


STRINGS = (
    _('Also see our images on %(websites)s'),
    _('Also see our videos on %(websites)s'),
    _('Also see our press releases on %(websites)s'),
    _('Also see our technical documents on %(websites)s'),
    _('Also see our exhibitions on %(websites)s'),
    _('Also see our announcements on %(websites)s'),
    _('Also see our postcards on %(websites)s'),
    _('Also see our books on %(websites)s'),
    _('Also see our brochures on %(websites)s'),
    _('Also see our dvds on %(websites)s'),
    _('Also see our newsletters on %(websites)s'),
    _('Also see our posters on %(websites)s'),
    _('Also see our pictures of the week on %(websites)s'),
    _('Also see our calendars on %(websites)s'),
    _('Also see our conference posters on %(websites)s'),

    _('images on %(websites)s'),
    _('videos on %(websites)s'),
    _('press releases on %(websites)s'),
    _('technical documents on %(websites)s'),
    _('exhibitions on %(websites)s'),
    _('announcements on %(websites)s'),
    _('postcards on %(websites)s'),
    _('books on %(websites)s'),
    _('brochures on %(websites)s'),
    _('dvds on %(websites)s'),
    _('newsletters on %(websites)s'),
    _('posters on %(websites)s'),
    _('pictures of the week on %(websites)s'),
    _('calendars on %(websites)s'),
    _('conference posters on %(websites)s'),
)


def crosslinks_for_domain( domain ):
    tmp = {}

    for key, values in list(ARCHIVE_CROSSLINKS.items()):
        tmp[key] = [d_u for d_u in values if d_u[0] != domain]

    return tmp
