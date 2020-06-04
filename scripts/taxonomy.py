import csv

taxcsv = csv.reader( open('taxonomy.csv',"rb"), )

l1 = ''
l2 = ''
l3 = ''
l4 = ''
l5 = ''

n1 = None
n2 = None
n3 = None
n4 = None
n5 = None


for row in taxcsv:
    if l5 != row[4]:
        n5 = row[5] 
        l5 = row[4]
    
    if l4 != row[3]:
        n4 = row[5] 
        l4 = row[3]
        n5 = ''

    if l3 != row[2]:
        n3 = row[5] 
        l3 = row[2]
        n4 = ''
        n5 = ''
        
    if l2 != row[1]:
        n2 = row[5] 
        l2 = row[1]
        n3 = ''
        n4 = ''
        n5 = ''
    
    if l1 != row[0]:
        n1 = row[5] 
        l1 = row[0]
        n2 = ''
        n3 = ''
        n4 = ''
        n5 = ''

    name = " : ".join( filter(lambda x : x is not None and x != '', [n1,n2,n3,n4,n5]) )
    
    print "(%s,'%s')," % (map(lambda x : x if x != '' else None, [l1,l2,l3,l4,l5]), name)