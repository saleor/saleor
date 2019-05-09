"""
Dribbble OAuth2 backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/dribbble.html
    http://developer.dribbble.com/v1/oauth/
"""

from .oauth import BaseOAuth2


class DribbbleOAuth2(BaseOAuth2):
    """Dribbble OAuth authentication backend"""
    name = 'dribbble'
    AUTHORIZATION_URL = 'https://dribbble.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://dribbble.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ','
    EXTRA_DATA = [
        ('id', 'id'),
        ('name', 'name'),
        ('html_url', 'html_url'),
        ('avatar_url', 'avatar_url'),
        ('bio', 'bio'),
        ('location', 'location'),
        ('links', 'links'),
        ('buckets_count', 'buckets_count'),
        ('comments_received_count', 'comments_received_count'),
        ('followers_count', 'followers_count'),
        ('followings_count', 'followings_count'),
        ('likes_count', 'likes_count'),
        ('likes_received_count', 'likes_received_count'),
        ('projects_count', 'projects_count'),
        ('rebounds_received_count', 'rebounds_received_count'),
        ('shots_count', 'shots_count'),
        ('teams_count', 'teams_count'),
        ('pro', 'pro'),
        ('buckets_url', 'buckets_url'),
        ('followers_url', 'followers_url'),
        ('following_url', 'following_url'),
        ('likes_url', 'shots_url'),
        ('teams_url', 'teams_url'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    def get_user_details(self, response):
        """Return user details from Dribbble account"""
        fullname, first_name, last_name = self.get_user_names(
            response.get('name')
        )
        return {'username': response.get('username'),
                'email': response.get('email', ''),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        return self.get_json(
            'https://api.dribbble.com/v1/user',
            headers={
                'Authorization': 'Bearer {0}'.format(access_token)
            })
