# coding=utf-8
from __future__ import unicode_literals

from text_unidecode import unidecode

from .. import BaseProvider

from ipaddress import ip_address, ip_network, IPV4LENGTH, IPV6LENGTH

# from faker.generator import random
# from faker.providers.lorem.la import Provider as Lorem
from faker.utils.decorators import lowercase, slugify, slugify_unicode


localized = True


class _IPv4Constants:
    """
    IPv4 network constants used to group networks into different categories.
    Structure derived from `ipaddress._IPv4Constants`.

    Excluded network list is updated to comply with current IANA list of
    private and reserved networks.
    """
    _network_classes = {
        'a': ip_network('0.0.0.0/1'),
        'b': ip_network('128.0.0.0/2'),
        'c': ip_network('192.0.0.0/3'),
    }

    _linklocal_network = ip_network('169.254.0.0/16')

    _loopback_network = ip_network('127.0.0.0/8')

    _multicast_network = ip_network('224.0.0.0/4')

    # Three common private networks from class A, B and CIDR
    # to generate private addresses from.
    _private_networks = [
        ip_network('10.0.0.0/8'),
        ip_network('172.16.0.0/12'),
        ip_network('192.168.0.0/16'),
    ]

    # List of networks from which IP addresses will never be generated,
    # includes other private IANA and reserved networks from
    # ttps://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml
    _excluded_networks = [
        ip_network('0.0.0.0/8'),
        ip_network('100.64.0.0/10'),
        ip_network('127.0.0.0/8'),
        ip_network('169.254.0.0/16'),
        ip_network('192.0.0.0/24'),
        ip_network('192.0.2.0/24'),
        ip_network('192.31.196.0/24'),
        ip_network('192.52.193.0/24'),
        ip_network('192.88.99.0/24'),
        ip_network('192.175.48.0/24'),
        ip_network('198.18.0.0/15'),
        ip_network('198.51.100.0/24'),
        ip_network('203.0.113.0/24'),
        ip_network('240.0.0.0/4'),
        ip_network('255.255.255.255/32'),
    ] + [
        _linklocal_network,
        _loopback_network,
        _multicast_network,
    ]


class Provider(BaseProvider):
    safe_email_tlds = ('org', 'com', 'net')
    free_email_domains = ('gmail.com', 'yahoo.com', 'hotmail.com')
    tlds = (
        'com', 'com', 'com', 'com', 'com', 'com', 'biz', 'info', 'net', 'org',
    )
    hostname_prefixes = ('db', 'srv', 'desktop', 'laptop', 'lt', 'email', 'web')
    uri_pages = (
        'index', 'home', 'search', 'main', 'post', 'homepage', 'category',
        'register', 'login', 'faq', 'about', 'terms', 'privacy', 'author',
    )
    uri_paths = (
        'app', 'main', 'wp-content', 'search', 'category', 'tag', 'categories',
        'tags', 'blog', 'posts', 'list', 'explore',
    )
    uri_extensions = (
        '.html', '.html', '.html', '.htm', '.htm', '.php', '.php', '.jsp',
        '.asp',
    )

    user_name_formats = (
        '{{last_name}}.{{first_name}}',
        '{{first_name}}.{{last_name}}',
        '{{first_name}}##',
        '?{{last_name}}',
    )
    email_formats = (
        '{{user_name}}@{{domain_name}}',
        '{{user_name}}@{{free_email_domain}}',
    )
    url_formats = (
        'www.{{domain_name}}/',
        '{{domain_name}}/',
    )
    uri_formats = (
        '{{url}}',
        '{{url}}{{uri_page}}/',
        '{{url}}{{uri_page}}{{uri_extension}}',
        '{{url}}{{uri_path}}/{{uri_page}}/',
        '{{url}}{{uri_path}}/{{uri_page}}{{uri_extension}}',
    )
    image_placeholder_services = (
        'https://placeholdit.imgix.net/~text'
        '?txtsize=55&txt={width}x{height}&w={width}&h={height}',
        'https://www.lorempixel.com/{width}/{height}',
        'https://dummyimage.com/{width}x{height}',
        'https://placekitten.com/{width}/{height}',
        'https://placeimg.com/{width}/{height}/any',
    )

    replacements = ()

    def _to_ascii(self, string):
        for search, replace in self.replacements:
            string = string.replace(search, replace)

        string = unidecode(string)
        return string

    @lowercase
    def email(self, domain=None):
        if domain:
            email = '{0}@{1}'.format(self.user_name(), domain)
        else:
            pattern = self.random_element(self.email_formats)
            email = "".join(self.generator.parse(pattern).split(" "))
        return email

    @lowercase
    def safe_email(self):
        return '{}@example.{}'.format(
            self.user_name(), self.random_element(self.safe_email_tlds),
        )

    @lowercase
    def free_email(self):
        return self.user_name() + '@' + self.free_email_domain()

    @lowercase
    def company_email(self):
        return self.user_name() + '@' + self.domain_name()

    @lowercase
    def free_email_domain(self):
        return self.random_element(self.free_email_domains)

    @lowercase
    def ascii_email(self):
        pattern = self.random_element(self.email_formats)
        return self._to_ascii(
            "".join(self.generator.parse(pattern).split(" ")),
        )

    @lowercase
    def ascii_safe_email(self):
        return self._to_ascii(
            self.user_name() +
            '@example.' +
            self.random_element(self.safe_email_tlds),
        )

    @lowercase
    def ascii_free_email(self):
        return self._to_ascii(
            self.user_name() + '@' + self.free_email_domain(),
        )

    @lowercase
    def ascii_company_email(self):
        return self._to_ascii(
            self.user_name() + '@' + self.domain_name(),
        )

    @slugify_unicode
    def user_name(self):
        pattern = self.random_element(self.user_name_formats)
        username = self._to_ascii(
            self.bothify(self.generator.parse(pattern)).lower(),
        )
        return username

    @lowercase
    def hostname(self, levels=1):
        """
        Produce a hostname with specified number of subdomain levels.

        >>> hostname()
        db-01.nichols-phillips.com
        >>> hostname(0)
        laptop-56
        >>> hostname(2)
        web-12.williamson-hopkins.jackson.com
        """
        if levels < 1:
            return self.random_element(self.hostname_prefixes) + '-' + self.numerify('##')
        return self.random_element(self.hostname_prefixes) + '-' + self.numerify('##') + '.' + self.domain_name(levels)

    @lowercase
    def domain_name(self, levels=1):
        """
        Produce an Internet domain name with the specified number of
        subdomain levels.

        >>> domain_name()
        nichols-phillips.com
        >>> domain_name(2)
        williamson-hopkins.jackson.com
        """
        if levels < 1:
            raise ValueError("levels must be greater than or equal to 1")
        if levels == 1:
            return self.domain_word() + '.' + self.tld()
        else:
            return self.domain_word() + '.' + self.domain_name(levels - 1)

    @lowercase
    @slugify_unicode
    def domain_word(self):
        company = self.generator.format('company')
        company_elements = company.split(' ')
        company = self._to_ascii(company_elements.pop(0))
        return company

    def tld(self):
        return self.random_element(self.tlds)

    def url(self, schemes=None):
        """
        :param schemes: a list of strings to use as schemes, one will chosen randomly.
        If None, it will generate http and https urls.
        Passing an empty list will result in schemeless url generation like "://domain.com".

        :returns: a random url string.
        """
        if schemes is None:
            schemes = ['http', 'https']

        pattern = '{}://{}'.format(
            self.random_element(schemes) if schemes else "",
            self.random_element(self.url_formats),
        )

        return self.generator.parse(pattern)

    def _random_ipv4_address_from_subnet(self, subnet, network=False):
        """
        Produces a random IPv4 address or network with a valid CIDR
        from within a given subnet.

        :param subnet: IPv4Network to choose from within
        :param network: Return a network address, and not an IP address
        """
        address = str(
            subnet[self.generator.random.randint(
                0, subnet.num_addresses - 1,
            )],
        )

        if network:
            address += '/' + str(self.generator.random.randint(
                subnet.prefixlen,
                subnet.max_prefixlen,
            ))
            address = str(ip_network(address, strict=False))

        return address

    def _exclude_ipv4_networks(self, networks, networks_to_exclude):
        """
        Exclude the list of networks from another list of networks
        and return a flat list of new networks.

        :param networks: List of IPv4 networks to exclude from
        :param networks_to_exclude: List of IPv4 networks to exclude
        :returns: Flat list of IPv4 networks
        """
        for network_to_exclude in networks_to_exclude:
            def _exclude_ipv4_network(network):
                """
                Exclude a single network from another single network
                and return a list of networks. Network to exclude
                comes from the outer scope.

                :param network: Network to exclude from
                :returns: Flat list of IPv4 networks after exclusion.
                          If exclude fails because networks do not
                          overlap, a single element list with the
                          orignal network is returned. If it overlaps,
                          even partially, the network is excluded.
                """
                try:
                    return list(network.address_exclude(network_to_exclude))
                except ValueError:
                    # If networks overlap partially, `address_exclude`
                    # will fail, but the network still must not be used
                    # in generation.
                    if network.overlaps(network_to_exclude):
                        return []
                    else:
                        return [network]

            networks = list(map(_exclude_ipv4_network, networks))

            # flatten list of lists
            networks = [
                item for nested in networks for item in nested
            ]

        return networks

    def ipv4_network_class(self):
        """
        Returns a IPv4 network class 'a', 'b' or 'c'.

        :returns: IPv4 network class
        """
        return self.random_element('abc')

    def ipv4(self, network=False, address_class=None, private=None):
        """
        Produce a random IPv4 address or network with a valid CIDR.

        :param network: Network address
        :param address_class: IPv4 address class (a, b, or c)
        :param private: Public or private
        :returns: IPv4
        """
        if private is True:
            return self.ipv4_private(address_class=address_class,
                                     network=network)
        elif private is False:
            return self.ipv4_public(address_class=address_class,
                                    network=network)

        # if neither private nor public is required explicitly,
        # generate from whole requested address space
        if address_class:
            all_networks = [_IPv4Constants._network_classes[address_class]]
        else:
            # if no address class is choosen, use whole IPv4 pool
            all_networks = [ip_network('0.0.0.0/0')]

        # exclude special networks
        all_networks = self._exclude_ipv4_networks(
            all_networks,
            _IPv4Constants._excluded_networks,
        )

        # choose random network from the list
        random_network = self.generator.random.choice(all_networks)

        return self._random_ipv4_address_from_subnet(random_network, network)

    def ipv4_private(self, network=False, address_class=None):
        """
        Returns a private IPv4.

        :param network: Network address
        :param address_class: IPv4 address class (a, b, or c)
        :returns: Private IPv4
        """
        # compute private networks from given class
        supernet = _IPv4Constants._network_classes[
            address_class or self.ipv4_network_class()
        ]

        private_networks = [
            subnet for subnet in _IPv4Constants._private_networks
            if subnet.overlaps(supernet)
        ]

        # exclude special networks
        private_networks = self._exclude_ipv4_networks(
            private_networks,
            _IPv4Constants._excluded_networks,
        )

        # choose random private network from the list
        private_network = self.generator.random.choice(private_networks)

        return self._random_ipv4_address_from_subnet(private_network, network)

    def ipv4_public(self, network=False, address_class=None):
        """
        Returns a public IPv4 excluding private blocks.

        :param network: Network address
        :param address_class: IPv4 address class (a, b, or c)
        :returns: Public IPv4
        """
        # compute public networks
        public_networks = [_IPv4Constants._network_classes[
            address_class or self.ipv4_network_class()
        ]]

        # exclude private and excluded special networks
        public_networks = self._exclude_ipv4_networks(
            public_networks,
            _IPv4Constants._private_networks +
            _IPv4Constants._excluded_networks,
        )

        # choose random public network from the list
        public_network = self.generator.random.choice(public_networks)

        return self._random_ipv4_address_from_subnet(public_network, network)

    def ipv6(self, network=False):
        """Produce a random IPv6 address or network with a valid CIDR"""
        address = str(ip_address(self.generator.random.randint(
            2 ** IPV4LENGTH, (2 ** IPV6LENGTH) - 1)))
        if network:
            address += '/' + str(self.generator.random.randint(0, IPV6LENGTH))
            address = str(ip_network(address, strict=False))
        return address

    def mac_address(self):
        mac = [self.generator.random.randint(0x00, 0xff) for _ in range(0, 6)]
        return ":".join(map(lambda x: "%02x" % x, mac))

    def uri_page(self):
        return self.random_element(self.uri_pages)

    def uri_path(self, deep=None):
        deep = deep if deep else self.generator.random.randint(1, 3)
        return "/".join(
            self.random_elements(self.uri_paths, length=deep),
        )

    def uri_extension(self):
        return self.random_element(self.uri_extensions)

    def uri(self):
        pattern = self.random_element(self.uri_formats)
        return self.generator.parse(pattern)

    @slugify
    def slug(self, value=None):
        """Django algorithm"""
        if value is None:
            value = self.generator.text(20)
        return value

    def image_url(self, width=None, height=None):
        """
        Returns URL to placeholder image
        Example: http://placehold.it/640x480
        """
        width_ = width or self.random_int(max=1024)
        height_ = height or self.random_int(max=1024)
        placeholder_url = self.random_element(self.image_placeholder_services)
        return placeholder_url.format(width=width_, height=height_)
