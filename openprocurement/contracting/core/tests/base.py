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

from openprocurement.api.utils import connection_mock_config
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
from openprocurement.api.tests.base import (
    BaseResourceWebTest,
    snitch,
    MOCK_CONFIG as BASE_MOCK_CONFIG
)


from openprocurement.contracting.core.tests.fixtures.config import PARTIAL_MOCK_CONFIG
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





MOCK_CONFIG = connection_mock_config(PARTIAL_MOCK_CONFIG, ('plugins', 'api', 'plugins'), BASE_MOCK_CONFIG)

class BaseWebTest(BaseResourceWebTest):
    """
    Setups the database before each test and delete it after.
    """
    relative_to = os.path.dirname(__file__)
    mock_config = MOCK_CONFIG


class BaseContractWebTest(BaseWebTest):
    initial_data = contract_fixtures.test_contract_data
    mock_config = MOCK_CONFIG

    def setUp(self):
        super(BaseContractWebTest, self).setUp()
        self.create_contract()

    def create_contract(self):
        data = deepcopy(self.initial_data)

        # orig_auth = self.app.authorization
        # self.app.authorization = ('Basic', ('contracting', ''))
        response = self.app.post_json('/contracts', {'data': data})
        self.contract = response.json['data']
        self.contract_token = response.json['access']['token']
        self.contract_transfer = response.json['access']['transfer']
        self.contract_id = self.contract['id']
        # self.app.authorization = orig_auth
        return response.json

    def use_transfer(self, transfer, contract_id, origin_transfer):
        req_data = {"data": {"id": transfer['data']['id'],
                             'transfer': origin_transfer}}

        self.app.post_json('/contracts/{}/ownership'.format(contract_id), req_data)
        response = self.app.get('/transfers/{}'.format(transfer['data']['id']))
        return response.json

    def create_transfer(self):
        response = self.app.post_json('transfers', {"data": {}})
        return response.json

    def get_contract(self, contract_id):
        response = self.app.get('/contracts/{}'.format(contract_id))
        return response.json

    def set_contract_mode(self, contract_id, mode):
        current_auth = self.app.authorization

        self.app.authorization = ('Basic', ('administrator', ''))
        response = self.app.patch_json('/contracts/{}'.format(contract_id),
                                       {'data': {'mode': mode}})
        self.app.authorization = current_auth
        return response

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
