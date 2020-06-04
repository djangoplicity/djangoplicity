from django.conf import settings

if hasattr( settings, 'ESO_DOMAINS' ):
    ESO_DOMAINS = settings.ESO_DOMAINS
else:
    ESO_DOMAINS = ["eso.org", "partner.eso.org"]


def validate_contact( contact ):
    """ Validate  if an email address is an ESO email address. """
    if contact and contact.email:
        try:
            _username, domain = contact.email.strip( " " ).split("@")
            if domain in ESO_DOMAINS:
                return True
        except ValueError:
            pass
    return False


def validate_order( order ):
    if order and order.contact:
        return validate_contact( order.contact )
    return False
