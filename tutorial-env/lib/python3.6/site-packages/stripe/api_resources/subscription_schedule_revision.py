from __future__ import absolute_import, division, print_function

from stripe import util
from stripe.api_resources.abstract.api_resource import APIResource
from stripe.api_resources.subscription_schedule import SubscriptionSchedule
from stripe.six.moves.urllib.parse import quote_plus


class SubscriptionScheduleRevision(APIResource):
    OBJECT_NAME = "subscription_schedule_revision"

    def instance_url(self):
        token = util.utf8(self.id)
        schedule = util.utf8(self.schedule)
        base = SubscriptionSchedule.class_url()
        schedule_extn = quote_plus(schedule)
        extn = quote_plus(token)
        return "%s/%s/revisions/%s" % (base, schedule_extn, extn)

    @classmethod
    def retrieve(cls, id, api_key=None, **params):
        raise NotImplementedError(
            "Can't retrieve a subscription schedule revision without a schedule "
            "ID. Use schedule.revisions.retrieve('revision_id')"
        )
