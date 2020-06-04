from djangoplicity.archives.contrib.serialization import SimpleSerializer


class ExtendedContactSerializer( SimpleSerializer ):
    """
    Serializer for ExtendedContact model.
    """
    fields = (
        'name',
        'email',
        'telephone',
        'cellular',
        'affiliation',
        'address',
        'city',
        'state_province',
        'postal_code',
        'country',
    )
