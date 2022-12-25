This is a basic manual test for processing XHTML documents.  An example
document is obtained (if necessary) then read in and written out by PyXB.
Formatted versions of the input and output are generated and the differences
written to a file.  The result may be manually inspected to ensure no
significant changes were introduced.

Direct comparison is not feasible since the order of attributes in element
start tags is not preserved by xml.dom in Python, and the origin document
has comments and non-significant whitespace that are also not preserved.
