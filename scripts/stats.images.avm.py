# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.conf import settings
from djangoplicity.utils import optionparser
from djangoplicity.media.models import Image
import os

def default_test( val ):
    if val:
        return 1
    else:
        return 0

def cmp_val(i):
    def cmp_func(x,y):
        if x[i]<y[i]:
            return -1
        elif x[i]==y[i]:
            return 0
        else:
            return 1
    return cmp_func

def cmp_str(i):
    def cmp_func(x,y):
        return cmp(x[i].lower(),y[i].lower())
    return cmp_func


if __name__ == '__main__':
    args = optionparser.get_options( [] )
    
    counter = {}
    
    conf = {
        'Creator' : 'creator',
        'CreatorURL' : 'creator_url',
        'Contact.Name' : '',
        'Contact.Email' : '',
        'Contact.Telephone' : '',
        'Contact.Address' : 'contact_address',
        'Contact.City' : 'contact_city',
        'Contact.City' : 'contact_city',
        'Contact.StateProvince' : 'contact_stateprovince',
        'Contact.PostalCode' : 'contact_postalcode',
        'Contact.Country' : 'contact_country',
        'Contact.Rights' : 'rights',
    }
    im_c = 0
    
    ims = Image.objects.all()
    for im in ims:
        im_c += 1
        for f in im._meta.local_fields:
            try:
                c = counter[f.name]
            except KeyError:
                c = { 'total': 0, 'data' : 0 }
                        
            val = getattr( im, f.name )
            
            try:
                datafunc = conf[f.name]['datafunc']
            except:
                datafunc = default_test 
    
            res = datafunc( val )
            
            c['total'] += 1
            c['data'] += res
            
            counter[f.name] = c
            
            
    summary = []
    for (name,data) in counter.items():
        summary.append( (round(float(data['data'])*100/float(data['total'])),data['data'],data['total'],name ) )
        
    summary.sort( cmp_val(0) )

    print "#################"   
    for s in summary:
        print "%s,%s,%s,%s" % (s[3],s[0],s[1],s[2])
    
    summary.sort( cmp_str(3) )
    print "#################"   
    for s in summary:
        print "%s,%s,%s,%s" % (s[3],s[0],s[1],s[2])