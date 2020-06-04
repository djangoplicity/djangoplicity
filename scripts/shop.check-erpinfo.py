
from djangoplicity.products.models import AnnualReport, EducationalMaterial, \
    CDROM, Book, Brochure, Merchandise, Newsletter, PostCard, MountedImage, Poster, \
    Sticker, TechnicalDocument, Calendar, ConferenceItem
    
    
shoparchives = [AnnualReport, EducationalMaterial, 
    CDROM, Book, Brochure, Merchandise, Newsletter, PostCard, MountedImage, Poster, 
    Sticker, TechnicalDocument, Calendar, ConferenceItem]


for a in shoparchives:
    for obj in a.objects.filter( product__isnull=False ):
        print "Updating attributes for (%s) %s" % ( obj.__class__.__name__, obj.id )
        obj.update_attributes( obj.product )
        
