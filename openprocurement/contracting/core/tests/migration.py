# -*- coding: utf-8 -*-
import os
import json
import unittest

from copy import deepcopy
from mock import MagicMock, patch

from openprocurement.auctions.flash.models import Auction
from openprocurement.api.utils import get_now
from openprocurement.contracting.core.models import Contract
from openprocurement.contracting.core.migration import (
    migrate_data,
    get_db_schema_version,
    set_db_schema_version,
    SCHEMA_VERSION
)
from openprocurement.contracting.core.tests.base import (
    BaseWebTest
)
from openprocurement.contracting.core.tests.fixtures import contract_fixtures


class MigrateTest(BaseWebTest):

    def setUp(self):
        super(MigrateTest, self).setUp()
        migrate_data(self.app.app.registry)

    def test_migrate(self):
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)
        migrate_data(self.app.app.registry, 1)
        self.assertEqual(get_db_schema_version(self.db), SCHEMA_VERSION)

    def test_migrate_from0to1(self):
        set_db_schema_version(self.db, 0)

        with open(os.path.join(os.path.dirname(__file__), 'data/auction-contract-complete.json'), 'r') as df:
            data = json.loads(df.read())
        a = Auction(data)
        a.store(self.db)
        auction = self.db.get(a.id)
        self.assertEqual(auction['awards'][0]['value'], data['awards'][0]['value'])
        self.assertEqual(auction['awards'][0]['suppliers'], data['awards'][0]['suppliers'])

        contract_data = deepcopy(auction['contracts'][0])
        del contract_data['value']
        del contract_data['suppliers']
        contract_data['auction_id'] = auction['_id']
        contract_data['auction_token'] = 'xxx'
        contract_data['procuringEntity'] = auction['procuringEntity']
        contract = Contract(contract_data)
        contract.dateModified = get_now()
        contract.store(self.db)
        contract_data = self.db.get(contract.id)
        self.assertNotIn("value", contract_data)
        self.assertNotIn("suppliers", contract_data)

        migrate_data(self.app.app.registry, 1)
        migrated_item = self.db.get(contract.id)
        self.assertIn("value", migrated_item)
        self.assertEqual(migrated_item['value'], auction['awards'][0]['value'])
        self.assertIn("suppliers", migrated_item)
        self.assertEqual(migrated_item['suppliers'], auction['awards'][0]['suppliers'])

    def test_migrate_from1to2(self):
        set_db_schema_version(self.db, 1)
        u = Contract(contract_fixtures.test_contract_data)
        u.contractID = "UA-X"
        u.store(self.db)
        data = self.db.get(u.id)
        data["documents"] = [
            {
                "id": "ebcb5dd7f7384b0fbfbed2dc4252fa6e",
                "title": "name.txt",
                "url": "/auctions/{}/documents/ebcb5dd7f7384b0fbfbed2dc4252fa6e?download=10367238a2964ee18513f209d9b6d1d3".format(u.id),
                "datePublished": "2016-06-01T00:00:00+03:00",
                "dateModified": "2016-06-01T00:00:00+03:00",
                "format": "text/plain",
            }
        ]
        _id, _rev = self.db.save(data)
        self.app.app.registry.docservice_url = 'http://localhost'
        migrate_data(self.app.app.registry, 2)
        migrated_item = self.db.get(u.id)
        self.assertIn('http://localhost/get/10367238a2964ee18513f209d9b6d1d3?', migrated_item['documents'][0]['url'])
        self.assertIn('Prefix={}%2Febcb5dd7f7384b0fbfbed2dc4252fa6e'.format(u.id), migrated_item['documents'][0]['url'])
        self.assertIn('KeyID=', migrated_item['documents'][0]['url'])
        self.assertIn('Signature=', migrated_item['documents'][0]['url'])

    @patch('openprocurement.contracting.core.migration.get_plugins')
    @patch('openprocurement.contracting.core.migration.read_yaml')
    def test_migrate_data_return_none(self, mock_read_yaml, mock_get_plugins):
        mock_read_yaml.return_value = None
        mock_get_plugins.return_value = {
            'fake_plugin':
                {'plugins': 'fake_plugin2'}
        }
        self.assertIsNone(migrate_data(self.app.app.registry))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MigrateTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
