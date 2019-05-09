__all__ = ['YADIS_HEADER_NAME', 'YADIS_CONTENT_TYPE', 'YADIS_ACCEPT_HEADER']
from openid.yadis.accept import generateAcceptHeader

YADIS_HEADER_NAME = 'X-XRDS-Location'
YADIS_CONTENT_TYPE = 'application/xrds+xml'

# A value suitable for using as an accept header when performing YADIS
# discovery, unless the application has special requirements
YADIS_ACCEPT_HEADER = generateAcceptHeader(
    ('text/html', 0.3),
    ('application/xhtml+xml', 0.5),
    (YADIS_CONTENT_TYPE, 1.0), )
