This example uses the International Purchase Order as described in XML
Schema Part 0 : Primer.

The IPO schema from
http://www/Documentation/W3C/www.w3.org/TR/xmlschema-0/index.html#ipo.xsd
has been modified to provide a valid URI for the location of the included
address.xsd, and to define the missing UKPostcode simple type definition.

The address schema from
http://www/Documentation/W3C/www.w3.org/TR/xmlschema-0/index.html#address.xsd
is unchanged.

The example document from
http://www/Documentation/W3C/www.w3.org/TR/xmlschema-0/index.html#ipo.xml
has been modified to comment out the stanza that requires xsi:type support,
and to fix the syntax error in the ipo:comment.
