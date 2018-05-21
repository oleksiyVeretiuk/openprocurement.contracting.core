# -*- coding: utf-8 -*-
import os
import unittest
import webtest
from copy import deepcopy
from couchdb_schematics.document import SchematicsDocument
from schematics.transforms import whitelist
from schematics.types import StringType
from schematics.types.compound import ModelType
from uuid import uuid4

from openprocurement.api.models.auction_models import (
    Contract as BaseContract,
    Document as BaseDocument,
    IsoDateTimeType,
    ListType,
    Revision,
    schematics_default_role,
)
from openprocurement.api.constants import VERSION, SESSION
from openprocurement.contracting.core.tests.fixtures import (
    contract_fixtures,
)
from openprocurement.auctions.core.tests.base import (
    BaseWebTest as BaseBaseWebTest,
)
from openprocurement.auctions.core.models import (
    plain_role,
)


test_contract_data_wo_items = deepcopy(contract_fixtures.test_contract_data)
del test_contract_data_wo_items['items']


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/api/%s%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseWebTest(BaseBaseWebTest):
    """
    Setups the database before each test and delete it after.
    """
    relative_to = os.path.dirname(__file__)


class BaseContractWebTest(BaseWebTest):
    initial_data = contract_fixtures.test_contract_data

    def setUp(self):
        super(BaseContractWebTest, self).setUp()
        self.create_contract()

    def create_contract(self):
        data = deepcopy(self.initial_data)

        orig_auth = self.app.authorization
        self.app.authorization = ('Basic', ('contracting', ''))
        response = self.app.post_json('/contracts', {'data': data})
        self.contract = response.json['data']
        # self.contract_token = response.json['access']['token']
        self.contract_id = self.contract['id']
        self.app.authorization = orig_auth

    def tearDown(self):
        del self.db[self.contract_id]
        super(BaseContractWebTest, self).tearDown()


class BaseContractContentWebTest(BaseContractWebTest):

    def setUp(self):
        super(BaseContractContentWebTest, self).setUp()
        response = self.app.patch_json('/contracts/{}/credentials?acc_token={}'.format(
            self.contract_id, self.initial_data['tender_token']), {'data': {}})
        self.contract_token = response.json['access']['token']


def error_handler(variable):
    exception = Exception()
    exception.message = variable
    return exception


class Document(BaseDocument):
    documentOf = StringType(required=True, choices=['contract'],
                            default='contract')

class Contract(SchematicsDocument, BaseContract):
    contractType = StringType(default='common')
    mode = StringType(choices=['test'])
    dateModified = IsoDateTimeType()
    create_accreditation = 1
    documents = ListType(ModelType(Document), default=list())
    revisions = ListType(ModelType(Revision), default=list())
    owner_token = StringType(default=lambda: uuid4().hex)

    class Options:
        roles = {
            'plain': plain_role,
            'create': (whitelist('id', )),
            'view': (whitelist('id', )),
            'default': schematics_default_role,
        }
