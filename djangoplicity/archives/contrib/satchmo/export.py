# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

from builtins import str
from builtins import object
import csv
import sys
from collections import deque
from xml.etree.ElementTree import Element, SubElement, ElementTree

from django.conf import settings

from satchmo_utils.numbers import round_decimal


class OrderExporterFactory( object ):
    """
    Create an order exporter. E.g.::

    from djangoplicity.archive.contrib.satchmo.export import factory
    exporter = factory.create(" csv", response )
    exporter.export( orders )
    """
    _instance = None

    @classmethod
    def instance( cls ):
        if OrderExporterFactory._instance is None:
            OrderExporterFactory._instance = OrderExporterFactory()
        return OrderExporterFactory._instance

    def __init__( self ):
        self.factories = {}
        self._default = None

    def register( self, key, factorycls, default=False ):
        self.factories[ key ] = factorycls
        if default:
            self._default = key

    def create( self, typ, filestream, **kwargs ):
        fact = self.factories[ typ ]
        return fact.create( filestream, **kwargs )

    def create_default( self, filestream, **kwargs ):
        fact = self.factories[ self._default ]
        return fact.create( filestream, **kwargs )


class OrderExporter( object ):
    """
    Abstract class for exporting orders

    Should only be used through the export() method.
    """
    content_type = "text/plain"

    @classmethod
    def create( cls, filestream, **kwargs ):
        """
        Factory method for creating an order exporter. Note, this
        class may be overwritten in each exporter class
        if they need complex creational patterns.
        """
        return cls( filestream, **kwargs )

    def export( self, orders ):
        raise NotImplementedError

    @staticmethod
    def round( val, places=2 ):
        return str( round_decimal( val=val, places=places, normalize=False ) )

    @staticmethod
    def product_attrs( item ):
        """ Get all product attributes """
        pattrs = {}
        for att in item.product.translated_attributes():
            pattrs[att.option.name] = att.value

        return pattrs

    @staticmethod
    def encode_list( items, encoding='ascii', handler='replace' ):
        return [str( x ).encode( encoding, handler ) for x in items]

    @staticmethod
    def get_order_no( order ):
        """ Get order number from order """
        try:
            return order.get_variable( "ORDER_ID" ).value
        except AttributeError:
            return None

    def _splitname( self, val, *args, **kwargs ):
        """
        Split a string using ``split_str'' (defaults to whitespace) into several
        strings of a certain maximum lengths.

        >>> splitname( somestr, 50, 50, split_str=' ' )
        >>> splitname( somestr, 50, 50, 50 )
        """
        split_str = kwargs['split_str'] if 'split_str' in kwargs else " "

        if len(args) == 0:
            raise TypeError("_splitname takes at least two arguments (1 given)")

        lengths = deque( args )
        tokens = val.split(split_str)
        i = 0
        results = []
        try:
            while True:
                maxlen_x = lengths.popleft() + 1
                x = []
                len_x = 0

                while i < len(tokens):
                    t = tokens[i]
                    len_t = len(t) + 1

                    if len_x + len_t <= maxlen_x:
                        x.append(t)
                        len_x += len_t
                        i += 1
                    else:
                        break
                results.append( split_str.join(x) )
        except IndexError:
            pass
        return results

    def _max_length( self, val, maxlen ):
        if val:
            val = val[:maxlen]
        return val

    def get_header( self, order ):
        shipto_firstname, shipto_lastname = self._splitname( order.ship_addressee, 50, 50 )
        billto_firstname, billto_lastname = self._splitname( order.bill_addressee, 50, 50 )

        return {
                'orderno': self._max_length( self.get_order_no( order ), 20 ),  # order no
                'amount': self.round( order.discounted_sub_total ),  # amount
                'shippingcost': self.round( order.shipping_sub_total ),  # shipping cost
                'total': self.round( order.total ),  # total
                'shipto_firstname': shipto_firstname if shipto_firstname else billto_firstname,  # firstname m
                'shipto_lastname': shipto_lastname if shipto_lastname else billto_lastname,  # lastname
                'shipto_street1': self._max_length( order.ship_street1, 60 ),  # addrr 1
                'shipto_street2': self._max_length( order.ship_street2, 60),
                'shipto_postalcode': self._max_length( order.ship_postal_code, 20),
                'shipto_tax_code': self._max_length( order.ship_tax_code, 20),
                'shipto_city': self._max_length( order.ship_city, 30),
                'shipto_state': self._max_length( order.ship_state, 30),
                'shipto_country': self._max_length( order.ship_country, 10),
                'shipto_email': self._max_length( order.contact.email, 80),
                'billto_firstname': billto_firstname,  # firstname
                'billto_lastname': billto_lastname,  # lastname
                'billto_street1': self._max_length( order.bill_street1, 60),  # addrr 1
                'billto_street2': self._max_length( order.bill_street2, 60),
                'billto_postalcode': self._max_length( order.bill_postal_code, 20),
                'billto_city': self._max_length( order.bill_city, 30),
                'billto_state': self._max_length( order.bill_state, 30),
                'billto_country': self._max_length( order.bill_country, 10),
                'contact': self._max_length( order.contact.full_name, 50),
            }

    def get_items( self, order ):
        """ Get all items to include in export """
        return order.orderitem_set.all()

    def get_item( self, item, order ):
        """ Get item fields """
        attrs = self.product_attrs( item )

        job = attrs['Job'] if 'Job' in attrs else ''
        jsp = attrs['JSP'] if 'JSP' in attrs else ''
        account = attrs['Account'] if 'Account' in attrs else ''

        # Job/JSP added August 2010
        if not job and not jsp:
            try:
                job = settings.SHOP_CONF['DEFAULT_NAVISION_JOB']
                jsp = settings.SHOP_CONF['DEFAULT_NAVISION_JSP']
            except KeyError:
                job = jsp = ''
        elif not job or not jsp:
            raise Exception("Product only defined either the Job or the JSP - both or none must be specified.")

        # Account added april 2011
        if not account:
            try:
                settings.SHOP_CONF['DEFAULT_NAVISION_ACCOUNT']
            except KeyError:
                account = ''

        return {
            'orderno': self._max_length( self.get_order_no( order ), 20),
            'description': self._max_length( item.product.name, 100),
            'id': self._max_length( item.product.sku, 60),
            'qty': self.round( item.quantity, places=0 ),
            'unit_price': self.round( item.unit_price ),
            'discount': self.round( item.discount ),
            'job': self._max_length( job, 20),
            'jsp': self._max_length( jsp, 20),
            'account': self._max_length( account, 20),
        }


class CSVOrderExporter( OrderExporter ):
    content_type = "text/csv"

    delimiter = '|'
    quotechar = '"'
    lineterminator = "\r\n"

    def __init__( self, filestream, encoding="cp1252", handler="replace" ):
        self.writer = csv.writer( filestream, delimiter=self.delimiter, quotechar=self.quotechar, lineterminator=self.lineterminator )
        self.encoding = encoding
        self.handler = handler

    def header_rows( self, order ):
        header = self.get_header( order )

        return [[
            header['orderno'],  # order no
            header['amount'],
            header['shippingcost'],
            header['total'],
            header['shipto_firstname'],
            header['shipto_lastname'],
            header['shipto_street1'],
            header['shipto_street2'],
            header['shipto_postalcode'],
            header['shipto_tax_code'],
            header['shipto_city'],
            header['shipto_state'],
            header['shipto_country'],
            header['shipto_email'],
            header['billto_firstname'],
            header['billto_lastname'],
            header['billto_street1'],
            header['billto_street2'],
            header['billto_postalcode'],
            header['billto_city'],
            header['billto_state'],
            header['billto_country'],
        ], []]

    def item_rows( self, item, order ):
        """ Get CSV rows for item """
        row = self.get_item( item, order )

        return [[
            row['description'],
            row['id'],
            row['qty'],
            row['unit_price'],
            row['discount'],
            row['job'],
            row['jsp'],
        ]]

    def _export_order( self, order ):
        """
        Export order as CSV
        """
        for row in self.header_rows( order ):
            self.writer.writerow( self.encode_list( row, self.encoding, self.handler ) )

        for item in self.get_items( order ):
            for row in self.item_rows( item, order ):
                self.writer.writerow( self.encode_list( row, self.encoding, self.handler ) )

    def export( self, orders ):
        """
        Export orders in CSV format
        """
        if len(orders) > 1:
            raise Exception( "%s only supports exporting one order" % self.__class__.__name__ )

        for order in orders:
            self._export_order( order )


class CSVOrderExporter2( CSVOrderExporter ):
    content_type = "text/csv"

    def header_rows( self, order ):
        header = self.get_header( order )

        return [[
            "H",
            header['orderno'],  # order no
            header['amount'],
            header['shippingcost'],
            header['total'],
            header['shipto_firstname'],
            header['shipto_lastname'],
            header['shipto_street1'],
            header['shipto_street2'],
            header['shipto_postalcode'],
            header['shipto_tax_code'],
            header['shipto_city'],
            header['shipto_state'],
            header['shipto_country'],
            header['shipto_email'],
            header['billto_firstname'],
            header['billto_lastname'],
            header['billto_street1'],
            header['billto_street2'],
            header['billto_postalcode'],
            header['billto_city'],
            header['billto_state'],
            header['billto_country'],
        ]]

    def item_rows( self, item, order ):
        """ Get CSV rows for item """
        row = self.get_item( item, order )

        return [[
            "L",
            row['orderno'],
            row['description'],
            row['id'],
            row['qty'],
            row['unit_price'],
            row['discount'],
            row['job'],
            row['jsp'],
            row['account'],
        ]]

    def export( self, orders ):
        """
        Export orders in CSV format
        """
        for order in orders:
            self._export_order( order )


class XMLOrderExporter( OrderExporter ):
    """
    XML order exporter
    """
    content_type = "application/xml"

    def __init__( self, filestream ):
        self.filestream = filestream

    def _create_simple(self, root, tag, subelements=None ):
        """
        Helper function for creating tags from a dictionary.
        """
        if subelements is None:
            subelements = []

        elem = SubElement( root, tag )

        for k, v in subelements:
            tag = SubElement( elem, k )
            tag.text = v

        return elem

    def item_tags( self, root, item, order ):
        """
        Create tags for items
        """
        line = self.get_item( item, order )

        self._create_simple( root, "line",
            subelements=[
                ('id', line['id']),
                ('description', line['description']),
                ('account', line['account']),
                ('qty', line['qty']),
                ('unitprice', line['unit_price']),
                ('discount', line['discount']),
                ('job', line['job']),
                ('jsp', line['jsp']),

        ])

    def header_tags(self, root, order ):
        """
        Create tags for header information
        """
        header = self.get_header( order )

        self._create_simple( root, "shipto",
            subelements=[
                ("sellto", 'CS004301'),
                ("firstname", header["shipto_firstname"]),
                ("lastname", header["shipto_lastname"]),
                ("address1", header["shipto_street1"]),
                ("address2", header["shipto_street2"]),
                ("zipcode", header["shipto_postalcode"]),
                # ("taxcode", header["shipto_tax_code"]),
                ("city", header["shipto_city"]),
                ("county", header["shipto_state"]),
                ("country", header["shipto_country"]),
                ("email", header["shipto_email"]),
            ] )

        self._create_simple( root, "invoiceto",
            subelements=[
                ("firstname", header["billto_firstname"]),
                ("lastname", header["billto_lastname"]),
                ("address1", header["billto_street1"]),
                ("address2", header["billto_street2"]),
                ("zipcode", header["billto_postalcode"]),
                ("taxcode", header["shipto_tax_code"]),
                ("city", header["billto_city"]),
                ("county", header["billto_state"]),
                ("country", header["billto_country"]),
            ])

        self._create_simple( root, "payment",
            subelements=[
                ('amount', header["amount"]),
                ('shippingcost', header["shippingcost"]),
                ('total', header["total"]),
            ] )

    def _export_order( self, root, order ):
        """
        Create XML tag for order
        """
        elem = SubElement( root, "order" )
        elem.set( "id", self.get_order_no( order ) )

        self.header_tags( elem, order )

        items_tag = SubElement( elem, "items" )
        for item in self.get_items( order ):
            self.item_tags( items_tag, item, order )

    def export( self, orders ):
        """ Export orders to XML """
        root = Element( "orders" )

        for order in orders:
            self._export_order( root, order )

        tree = ElementTree( root )
        # Differences between ElementTree from version 2.7 and up
        if sys.version_info[0] >= 2 and sys.version_info[1] >= 7:
            tree.write( self.filestream, encoding='utf-8', xml_declaration=True, method='xml' )
        else:
            self.filestream.write("<?xml version='1.0' encoding='utf-8'?>\n")
            tree.write( self.filestream, 'utf-8' )


class XMLOrderExporter2( XMLOrderExporter ):
    def header_tags( self, root, order ):
        super( XMLOrderExporter2, self ).header_tags( root, order )

        header = self.get_header( order )

        tag = SubElement( root, "contact" )
        tag.text = header['contact']


factory = OrderExporterFactory.instance()
factory.register( "csv", CSVOrderExporter )
factory.register( "csv2", CSVOrderExporter2 )
factory.register( "xml1", XMLOrderExporter )
factory.register( "xml", XMLOrderExporter2, default=True )
