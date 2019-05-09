from django.test.runner import DiscoverRunner


class DiscoverPostProcessorRunner(DiscoverRunner):

    def __init__(self, pattern='post_processor_tests.py', **kwargs):
        super(DiscoverPostProcessorRunner, self).__init__(pattern, **kwargs)
