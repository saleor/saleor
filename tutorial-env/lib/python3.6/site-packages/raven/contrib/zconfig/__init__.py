# -*- coding: utf-8 -*-
from __future__ import absolute_import
"""
raven.contrib.zconfig
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import logging
import ZConfig.components.logger.factory
import raven.handlers.logging


class Factory(ZConfig.components.logger.factory.Factory):

    def __init__(self, section):
        ZConfig.components.logger.factory.Factory.__init__(self)
        self.section = section
        self.section.level = self.section.level or logging.ERROR

    def getLevel(self):
        return self.section.level

    def create(self):
        return raven.handlers.logging.SentryHandler(
            dsn=self.section.dsn,
            site=self.section.site,
            name=self.section.name,
            release=self.section.release,
            environment=self.section.environment,
            exclude_paths=self.section.exclude_paths,
            include_paths=self.section.include_paths,
            sample_rate=self.section.sample_rate,
            list_max_length=self.section.list_max_length,
            string_max_length=self.section.string_max_length,
            auto_log_stacks=self.section.auto_log_stacks,
            processors=self.section.processors,
            level=self.section.level)
