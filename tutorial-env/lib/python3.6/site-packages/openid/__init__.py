#-*- coding: utf-8 -*-
"""
This package is an implementation of the OpenID specification in
Python.  It contains code for both server and consumer
implementations.  For information on implementing an OpenID consumer,
see the C{L{openid.consumer.consumer}} module.  For information on
implementing an OpenID server, see the C{L{openid.server.server}}
module.

@contact: U{http://github.com/necaris/python3-openid/}

@copyright: (C) 2005-2008 JanRain, Inc., 2012-2017 Rami Chowdhury

@license: Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
    U{http://www.apache.org/licenses/LICENSE-2.0}

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions
    and limitations under the License.
"""

version_info = (3, 1, 0)



__version__ = ".".join(str(x) for x in version_info)

__all__ = [
    'association',
    'consumer',
    'cryptutil',
    'dh',
    'extension',
    'extensions',
    'fetchers',
    'kvform',
    'message',
    'oidutil',
    'server',
    'sreg',
    'store',
    'urinorm',
    'yadis',
]
