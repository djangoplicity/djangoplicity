"""
Simple module for defining cross-links between archives on ESO-hosted djangoplicity sites.
"""

_ = lambda x: x

ARCHIVE_CROSSLINKS = {
    'announcements': (
        ('esahubble.org', 'https://esahubble.org/announcements/')
    ),
    'releases': (
        ('esahubble.org', 'https://esahubble.org/news/')
    ),
    'images': (
        ('esahubble.org', 'http://www.esahubble.org/images/')
    ),
    'videos': (
        ('esahubble.org', 'http://www.esahubble.org/videos/')
    ),
    'potw': (
        ('esahubble.org', 'https://esahubble.org/images/potw/')
    ),
    'posters': (
        ('esahubble.org', 'https://esahubble.org/products/print_posters/')
    ),
    'books': (
        ('esahubble.org', 'http://www.esahubble.org/about/further_information/books/')
    ),
    'brochures': (
        ('esahubble.org', 'http://www.esahubble.org/about/further_information/brochures/')
    ),
    'calendars': (
        ('esahubble.org', 'http://www.esahubble.org/products/calendars/')
    ),
    'education': (
        ('esahubble.org', 'http://www.esahubble.org/projects/anniversary/educational_material/')
    ),
    'newsletters': (
        ('esahubble.org', 'https://esahubble.org/newsletters/')

    ),
    'periodicals': (
        # ( 'esahubble.org', 'http://www.esahubble.org/about/further_information/newsletters/' )#brokend
    ),
    'postcards': (
        ('esahubble.org', 'https://esahubble.org/products/postcards/')
    ),
    'logos': (
        ('esahubble.org', 'http://www.esahubble.org/products/logos/')
    ),
    'conferenceposters': (
        ('esahubble.org', 'http://www.esahubble.org/products/conf_posters/')
    ),
    'presentations': (
        ('esahubble.org', 'http://www.esahubble.org/products/presentations/')
    ),
    'exhibitions': (
        ('esahubble.org', 'http://www.esahubble.org/products/exhibitions/')
    ),
    'dvds': (
        ('esahubble.org', 'http://www.esahubble.org/products/media/')
    ),
    'techdocs': (
        # ( 'esahubble.org', 'http://www.esahubble.org/about/further_information/techdocs/' )#roto
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
