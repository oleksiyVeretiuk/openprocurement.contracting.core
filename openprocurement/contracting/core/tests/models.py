# -*- coding: utf-8 -*-
import json
import unittest
import os

from datetime import timedelta
from mock import MagicMock
from pyramid.security import Allow
from schematics.exceptions import ValidationError
from uuid import uuid4

from openprocurement.contracting.core.models import (
    Document,
    Contract,
    Item,
    get_contract,
    CPVClassification,
    AdditionalClassification,
    Change
)
from openprocurement.api.utils import get_now


class TestDocument(unittest.TestCase):
    """ Document validate_relatedItem test"""

    def test_validate_relatedItem(self):
        data, relatedItem = {'documentOf': 'item'}, None
        document = Document()
        with self.assertRaises(ValidationError) as cm:
            document.validate_relatedItem(data, relatedItem)
        self.assertEqual(cm.exception.message, [u'This field is required.'])

        data, relatedItem = {'__parent__': Contract(),
                             'documentOf': 'change'}, 'some item'
        with self.assertRaises(ValidationError) as cm:
            document.validate_relatedItem(data, relatedItem)
        self.assertEqual(cm.exception.message,
                         [u'relatedItem should be one of changes'])

        contract = Contract()
        item = Item()
        contract.items = [item]
        data, relatedItem = {'__parent__': contract,
                             'documentOf': 'item'}, 'some item'
        with self.assertRaises(ValidationError) as cm:
            document.validate_relatedItem(data, relatedItem)
        self.assertEqual(cm.exception.message,
                         [u'relatedItem should be one of items'])


class TestModelsFunctions(unittest.TestCase):

    def test_get_contract(self):
        contract = Contract()
        fake_model = MagicMock()
        setattr(fake_model, '__parent__', contract)
        new_contract = get_contract(fake_model)

        self.assertEqual(contract, new_contract)


class TestCPVClassification(unittest.TestCase):
    """Check that no exeption was rised"""

    def test_validate_scheme(self):
        cpvclassification = CPVClassification()
        cpvclassification.validate_scheme(None, None)


class TestAdditionalClassification(unittest.TestCase):
    """Check that no exeption was rised"""

    def test_validate_id(self):
        additional_classification = AdditionalClassification()
        additional_classification.validate_id(None, None)


class TestChange(unittest.TestCase):
    """ Change validate_dateSigned test"""

    def test_validate_dateSigned(self):
        change = Change()
        value = get_now() + timedelta(days=1)

        with self.assertRaises(ValidationError) as cm:
            change.validate_dateSigned(None, value)
        self.assertEqual(cm.exception.message,
                         [u"Contract signature date can't be in the future"])


class TestContract(unittest.TestCase):
    """ Contract  tests"""

    def setUp(self):
        self.amountPaid = {
            "currency": "UAH",
            "amount": 5000.0,
            "valueAddedTaxIncluded": True}

        path = os.path.dirname(
            __file__) + '/data/auction-contract-complete.json'
        with open(path) as temp_file:
            self.auction_data = json.load(temp_file)
        self.auction_data['contracts'][0]['amountPaid'] = self.amountPaid

        self.owner_token = uuid4().hex
        self.auction_token = uuid4().hex
        self.owner = uuid4().hex
        self.contract = Contract(self.auction_data['contracts'][0])
        self.contract.amountPaid = self.amountPaid

        self.contract.auction_token = self.auction_token
        self.contract.owner = self.owner
        self.contract.owner_token = self.owner_token

        #  for get_role test
        self.root = MagicMock()
        self.request = MagicMock()
        self.root.request = self.request
        self.contract.__parent__ = self.root

    def test_local_roles(self):
        self.assertEqual(self.contract.__local_roles__(), dict(
            [('{}_{}'.format(self.owner, self.owner_token), 'contract_owner'),
             # ('{}_{}'.format(self.owner, self.auction_token), 'auction_owner')
             ]))

    def test_acl(self):

        self.assertEqual(self.contract.__acl__(),
             [
                 (Allow, '{}_{}'.format(self.owner, self.owner_token),
                  'edit_contract'),
                 (Allow, '{}_{}'.format(self.owner, self.owner_token),
                  'upload_contract_documents'),
                 # (Allow, '{}_{}'.format(self.owner, self.auction_token),
                 #  'generate_credentials')
             ]
         )

    def test_get_role(self):
        self.request.authenticated_role = 'Administrator'

        self.assertEqual(self.contract.get_role(), 'Administrator')

        self.request.context = MagicMock()
        self.request.context.status = 'active'
        self.request.authenticated_role = 'Broker'

        self.assertEqual(self.contract.get_role(), 'edit_active')

    def test_contract_amountPaid(self):
        self.assertEqual(self.contract.serialize()['amountPaid'],
                         self.amountPaid)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDocument))
    suite.addTest(unittest.makeSuite(TestModelsFunctions))
    suite.addTest(unittest.makeSuite(TestCPVClassification))
    suite.addTest(unittest.makeSuite(TestAdditionalClassification))
    suite.addTest(unittest.makeSuite(TestChange))
    suite.addTest(unittest.makeSuite(TestContract))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
