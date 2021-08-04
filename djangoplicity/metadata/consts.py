from django.utils.translation import ugettext_lazy as _

# AVM Controlled Vocabulary
TYPE_CHOICES = (
    ('Observation', _('Observation')),
    ('Artwork', _('Artwork')),
    ('Photographic', _('Photographic')),
    ('Planetary', _('Planetary')),
    ('Simulation', _('Simulation')),
    ('Collage', _('Collage')),
    ('Chart', _('Chart')),
)

IMAGE_PRODUCT_QUALITY_CHOICES = (
    ('Good', _('Good')),
    ('Moderate', _('Moderate')),
    ('Poor', _('Poor')),
)

SPECTRAL_COLOR_ASSIGNMENT_CHOICES = (
    ('Purple', _('Purple')),
    ('Blue', _('Blue')),
    ('Cyan', _('Cyan')),
    ('Green', _('Green')),
    ('Yellow', _('Yellow')),
    ('Orange', _('Orange')),
    ('Red', _('Red')),
    ('Magenta', _('Magenta')),
    ('Grayscale', _('Grayscale')),
    ('Pseudocolor', _('Pseudocolor')),
    ('Luminosity', _('Luminosity')),
)

SPECTRAL_BAND_CHOICES = (
    ('Radio', _('Radio')),
    ('Millimeter', _('Millimeter')),
    ('Infrared', _('Infrared')),
    ('Optical', _('Optical')),
    ('Ultraviolet', _('Ultraviolet')),
    ('X-ray', _('X-ray')),
    ('Gamma-ray', _('Gamma-ray')),
)

SPATIAL_COORDINATE_FRAME_CHOICES = (
    ('ICRS', 'ICRS'),
    ('FK5', 'FK5'),
    ('FK4', 'FK4'),
    ('ECL', 'ECL'),
    ('GAL', 'GAL'),
    ('SGAL', 'SGAL'),
)

SPATIAL_EQUINOX_CHOICES = (
    ('J2000', 'J2000'),
    ('B1950', 'B1950'),
)

SPATIAL_COORDSYSTEM_PROJECTION_CHOICES = (
    ('TAN', 'TAN'),
    ('SIN', 'SIN'),
    ('ARC', 'ARC'),
    ('AIT', 'AIT'),
    ('CAR', 'CAR'),
    ('CEA', 'CEA'),
)

SPATIAL_QUALITY_CHOICES = (
    ( 'Full', _( 'Full' ) ),
    ( 'Position', _( 'Position' ) ),
)

METADATA_VERSION_CHOICES = (
    ('1.1', 1.1),
    ('1.0', 1.0),
)

TOP_LEVEL_HIERARCHY = (
    ( 'A', _( 'Solar System' ) ),
    ( 'B', _( 'Milky Way' ) ),
    ( 'C', _( 'Local Universe', ) ),
    ( 'D', _( 'Early Universe' ) ),
    ( 'E', _( 'Unspecified' ) ),
    # ( 'X', _( 'Local use only' ) ),
 )


FILE_TYPE_CHOICES = (
    ( 'TIFF', 'TIFF' ),
    ( 'JPEG', 'JPEG' ),
    ( 'PNG', 'PNG' ),
    ( 'GIF', 'GIF' ),
    ( 'PSB', 'PSB' ),
    ( 'PSD', 'PSD' ),
    ( 'PDF', 'PDF' ),
 )

#
# NON-AVM CONSTANTS
#
FILE_ASPECT_RAITO_CHOICES = (
    ( '4:3', '4:3' ),
    ( '16:9', '16:9' ),
    ( '16:10', '16:10' ),
 )

AUDIO_SURROUND_FORMAT_CHOICES = (
    ( '5.1', '5.1' ),
    ( '6.1', '6.1' ),
    ( '7.1', '7.1' ),
    ( '8.1', '8.1' ),
    ( 'STEM', 'STEM tracks' ),
    ( 'Other', 'Other' ),
 )

FILE_EXTENSION_MAP = {
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.jpeg': 'JPEG',
    '.jpg': 'JPEG',
    '.gif': 'GIF',
    '.psb': 'PSB',
    '.psd': 'PSD',
    '.png': 'PNG',
    '.pdf': 'PDF',
}


def get_file_type(file):
    """
    given a file, will return a match of its extension to one provided in FILE_TYPE_CHOICES,
    or None if no match
    """
    import os
    (_f, ext) = os.path.splitext(file)

    return FILE_EXTENSION_MAP.get(ext, None)
