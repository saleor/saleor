def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    location = response['Location']
    if location.startswith('http'):
        location = location.split('http://testserver')[1]
    return location
