
from oslo_log import log as logging
import pecan
from pecan import expose
from pecan import request

import six

from playnetmano_rm.api.controllers import restcomm
from playnetmano_rm.common import consts
from playnetmano_rm.common import exceptions
from playnetmano_rm.common.i18n import _
from playnetmano_rm.common import utils
from playnetmano_rm.db import api as db_api

LOG = logging.getLogger(__name__)


class QuotaClassSetController(object):
    supported_quotas = []

    def __init__(self, *args, **kwargs):
        self.supported_quotas = list(
            consts.CINDER_QUOTA_FIELDS +
            consts.NEUTRON_QUOTA_FIELDS +
            consts.NOVA_QUOTA_FIELDS)

    def _format_quota_set(self, quota_class, quota_set):
        """Convert the quota object to a result dict."""

        if quota_class:
            result = dict(id=str(quota_class))
        else:
            result = {}

        for quota in self.supported_quotas:
            if quota in quota_set:
                result[quota] = quota_set[quota]

        return dict(quota_class_set=result)

    @expose(generic=True, template='json')
    def index(self):
        # Route the request to specific methods with parameters
        pass

    @index.when(method='GET', template='json')
    def get(self, class_name):
        context = restcomm.extract_context_from_environ()

        LOG.info("Fetch quotas for [class_name=%s]" % class_name)

        values = db_api.quota_class_get_all_by_name(context, class_name)

        return self._format_quota_set(class_name, values)

    @index.when(method='PUT', template='json')
    def put(self, class_name):
        """Update a class."""
        context = restcomm.extract_context_from_environ()

        LOG.info("Update quota class [class_name=%s]" % class_name)

        if not context.is_admin:
            pecan.abort(403, _('Admin required'))
        if not request.body:
            pecan.abort(400, _('Body required'))

        quota_class_set = eval(request.body).get('quota_class_set')

        if not quota_class_set:
            pecan.abort(400, _('Missing quota_class_set in the body'))

        utils.validate_quota_limits(quota_class_set)

        for key, value in six.iteritems(quota_class_set):
            try:
                db_api.quota_class_update(context, class_name, key, value)
            except exceptions.QuotaClassNotFound:
                db_api.quota_class_create(context, class_name, key, value)

        values = db_api.quota_class_get_all_by_name(context, class_name)

        return self._format_quota_set(class_name, values)

    @index.when(method='delete', template='json')
    def delete(self, class_name):
        context = restcomm.extract_context_from_environ()
        if not context.is_admin:
            pecan.abort(403, _('Admin required'))

        LOG.info("Delete quota class [class_name=%s]" % class_name)
        try:
            db_api.quota_class_destroy_all(context, class_name)
        except exceptions.QuotaClassNotFound:
            pecan.abort(404, _('Quota class not found'))
