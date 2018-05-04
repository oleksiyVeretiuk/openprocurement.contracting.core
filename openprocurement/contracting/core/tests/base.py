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
    plain_role,
    schematics_default_role,
)
from openprocurement.api.constants import VERSION, SESSION
from openprocurement.contracting.core.tests.fixtures import (
    contract_fixtures,
)


test_contract_data_wo_items = deepcopy(contract_fixtures.test_contract_data)
del test_contract_data_wo_items['items']


class PrefixedRequestClass(webtest.app.TestRequest):

    @classmethod
    def blank(cls, path, *args, **kwargs):
        path = '/api/%s%s' % (VERSION, path)
        return webtest.app.TestRequest.blank(path, *args, **kwargs)


class BaseBaseWebTest(unittest.TestCase):
    """Base Web Test to test openprocurement.contractning.core.

    It setups the database before each test and delete it after.
    """
    initial_auth = ('Basic', ('token', ''))
    docservice = False
    relative_to = os.path.dirname(__file__)

    def setUp(self):
        self.app = webtest.TestApp(
            "config:tests.ini", relative_to=self.relative_to)
        self.app.RequestClass = PrefixedRequestClass
        self.app.authorization = self.initial_auth
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db
        if self.docservice:
            self.setUpDS()

    def setUpDS(self):
        self.app.app.registry.docservice_url = 'http://localhost'
        test = self

        def request(method, url, **kwargs):
            response = Response()
            if method == 'POST' and '/upload' in url:
                url = test.generate_docservice_url()
                response.status_code = 200
                response.encoding = 'application/json'
                response._content = '{{"data":{{"url":"{url}","hash":"md5:{md5}","format":"application/msword",\
                                     "title":"name.doc"}},"get_url":"{url}"}}'.format(url=url, md5='0'*32)
                response.reason = '200 OK'
            return response

        self._srequest = SESSION.request
        SESSION.request = request

    def generate_docservice_url(self):
        uuid = uuid4().hex
        key = self.app.app.registry.docservice_key
        keyid = key.hex_vk()[:8]
        signature = b64encode(key.signature("{}\0{}".format(uuid, '0' * 32)))
        query = {'Signature': signature, 'KeyID': keyid}
        return "http://localhost/get/{}?{}".format(uuid, urlencode(query))

    def tearDownDS(self):
        SESSION.request = self._srequest

    def tearDown(self):
        if self.docservice:
            self.tearDownDS()
        del self.couchdb_server[self.db.name]

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
