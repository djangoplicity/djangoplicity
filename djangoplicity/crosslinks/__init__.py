"""
Simple module for defining cross-links between archives on ESO-hosted djangoplicity sites.
"""

_ = lambda x: x

ARCHIVE_CROSSLINKS = {
    'announcements': (
            ( 'eso.org', 'https://www.eso.org/public/announcements/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/announcements/' ),
        ),
    'releases': (
            ( 'eso.org', 'https://www.eso.org/public/news/' ),
            ( 'iau.org', 'http://www.iau.org/public_press/news/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/news/' ),
        ),
    'images': (
            ( 'eso.org', 'https://www.eso.org/public/images/' ),
            ( 'iau.org', 'http://www.iau.org/public_press/images/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/images/' ),
        ),
    'videos': (
            ( 'eso.org', 'https://www.eso.org/public/videos/' ),
            ( 'iau.org', 'http://www.iau.org/public_press/videos/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/videos/' ),
        ),
    'potw': (
            ( 'eso.org', 'https://www.eso.org/public/images/potw/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/images/potw/' ),
        ),
    'posters': (
            ( 'eso.org', 'https://www.eso.org/public/products/posters/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/posters/archive/printposters/' ),
        ),
    'books': (
            ( 'eso.org', 'https://www.eso.org/public/products/books/' ),
            ( 'iau.org', 'http://www.iau.org/science/publications/iau/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/about/further_information/books/' ),
        ),
    'brochures': (
            ( 'eso.org', 'https://www.eso.org/public/products/brochures/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/about/further_information/brochures/' ),
        ),
    'calendars': (
            ( 'eso.org', 'https://www.eso.org/public/products/calendars/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/calendars/' ),
        ),
    'education': (
            ( 'eso.org', 'https://www.eso.org/public/products/education/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/kidsandteachers/education/' ),
        ),
    'newsletters': (
            ( 'eso.org', 'https://www.eso.org/public/newsletters/esonews/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/newsletters/hubblenews/' ),
        ),
    'periodicals': (
            ( 'eso.org', 'https://www.eso.org/public/products/periodicals/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/about/further_information/newsletters/' ),
        ),
    'postcards': (
            ( 'eso.org', 'https://www.eso.org/public/products/postcards/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/postcards/' ),
        ),
    'logos': (
            ( 'eso.org', 'https://www.eso.org/public/products/logos/' ),
            ( 'iau.org', 'http://www.iau.org/public_press/images/archive/category/logos/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/logos/' ),
        ),
    'conferenceposters': (
            ( 'eso.org', 'https://www.eso.org/public/products/posters/archive/electronic/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/conferenceposters/' ),
        ),
    'presentations': (
            ( 'eso.org', 'https://www.eso.org/public/products/presentations/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/presentations/' ),
        ),
    'exhibitions': (
            ( 'eso.org', 'https://www.eso.org/public/products/exhibitions/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/exhibitions/' ),
        ),
    'dvds': (
            ( 'eso.org', 'https://www.eso.org/public/products/dvds/' ),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/extras/dvds/' ),
        ),
    'techdocs': (
            ( 'eso.org', 'https://www.eso.org/public/products/reports/'),
            ( 'spacetelescope.org', 'http://www.spacetelescope.org/about/further_information/techdocs/' ),
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
