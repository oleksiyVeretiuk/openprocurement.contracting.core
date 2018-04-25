# -*- coding: utf-8 -*-
import unittest

from mock import MagicMock, patch
from pyramid.exceptions import URLDecodeError
from pyramid.request import Request
from schematics.types import StringType

from openprocurement.contracting.core.tests.base import error_handler
from openprocurement.contracting.core.utils import (
    extract_contract_adapter,
    extract_contract,
    contract_from_data,
    contract_serialize,
    save_contract
)
from openprocurement.contracting.core.models import Contract as BaseContract
from openprocurement.contracting.core.utils import (
    apply_patch,
    isContract,
    register_contract_contractType,
    set_ownership
)


class Contract(BaseContract):
    contractType = StringType(choices=['esco', 'common'], default='common')


class TestisContract(unittest.TestCase):
    """ isContract tests"""

    def setUp(self):
        self.test_value = 'test_value'
        self.isContract = isContract(self.test_value, None)

    def test_init(self):
        self.assertEqual(self.test_value, self.isContract.val)

    def test_text(self):
        self.assertEqual(self.isContract.text(),
                         'contractType = %s' % (self.test_value,))

    def test_call(self):
        contract = Contract()
        request = Request(dict())

        request.contract = None
        self.assertEqual(self.isContract(None, request), False)

        request.contract = Contract()
        self.assertEqual(self.isContract(None, request), False)

        request.contract.contractType = 'common'
        self.isContract.val = 'common'
        self.assertEqual(self.isContract(None, request), True)


class TestUtilsFucntions(unittest.TestCase):
    """Testing all functions inside utils.py"""

    def test_register_contract_contractType(self):
        config = MagicMock()
        config.registry.contract_contractTypes = {}

        self.assertEqual(config.registry.contract_contractTypes, {})
        register_contract_contractType(config, Contract)
        common = config.registry.contract_contractTypes.get(
            'common'
        )
        self.assertEqual(common, Contract)

    @patch('openprocurement.contracting.core.utils.save_contract',
           return_value=True)
    @patch('openprocurement.contracting.core.utils.apply_data_patch')
    def test_apply_patch(self, mocked_apply_data_patch, mocked_save_contract):
        request = MagicMock()
        request.context = Contract()
        data = {'status': 'draft'}
        mocked_apply_data_patch.return_value = False
        self.assertEqual(apply_patch(request, data=data), None)

        mocked_apply_data_patch.return_value = request.context
        self.assertEqual(apply_patch(request, data=data, save=False), None)

        self.assertEqual(apply_patch(request, data=data, save=True), True)

    def test_set_ownership(self):
        item = MagicMock()
        set_ownership(item, None)
        self.assertIsNotNone(item.owner_token)


class TestApiFucntions(unittest.TestCase):
    """Testing all functions inside utils.py"""

    def setUp(self):
        self.contract_id = '1' * 32
        self.doc = {
            self.contract_id: {'id': 'fake_id', 'doc_type': 'contract'}}
        self.request = MagicMock()
        self.request.validated = {'contract_src': None}
        self.contract_mock = MagicMock()
        self.request.validated['contract'] = self.contract_mock
        self.db_mock = MagicMock()
        self.db_mock.configure_mock(**{'db': self.doc})
        self.request.configure_mock(**{'registry': self.db_mock})

    @patch('openprocurement.contracting.core.utils.error_handler')
    def test_extract_contract_adapter_410_error(self, mocker_error_handler):
        mocker_error_handler.side_effect = error_handler

        with self.assertRaises(Exception) as cm:
            extract_contract_adapter(self.request, self.contract_id)
        self.assertEqual(cm.exception.message.errors.status, 410)
        cm.exception.message.errors.add.assert_called_once_with(
            'url', 'contract_id', 'Archived'
        )

    @patch('openprocurement.contracting.core.utils.error_handler')
    def test_extract_contract_adapter_404_error(self, mocker_error_handler):
        mocker_error_handler.side_effect = error_handler
        self.doc[self.contract_id]['doc_type'] = 'Tender'

        with self.assertRaises(Exception) as cm:
            extract_contract_adapter(self.request, self.contract_id)
        self.assertEqual(cm.exception.message.errors.status, 404)
        cm.exception.message.errors.add.assert_called_once_with(
            'url', 'contract_id', 'Not Found'
        )

    def test_extract_contract_adapter_success(self):
        self.doc[self.contract_id]['doc_type'] = 'Contract'
        self.request.contract_from_data.return_value = True

        self.assertEqual(
            extract_contract_adapter(self.request, self.contract_id), True)

    @patch('openprocurement.contracting.core.utils.decode_path_info')
    def test_extract_contract_URLDecodeError(self, mocker_decode_path_info):
        error = UnicodeDecodeError('', '', 0, 0, '')
        mocker_decode_path_info.side_effect = error

        with self.assertRaises(Exception) as cm:
            extract_contract(self.request)
        self.assertEqual(type(cm.exception), URLDecodeError)

    @patch('openprocurement.contracting.core.utils.decode_path_info')
    def test_extract_contract_KeyError(self, mocker_decode_path_info):
        mocker_decode_path_info.side_effect = KeyError()

        self.assertEqual(extract_contract(self.request), None)

    @patch('openprocurement.contracting.core.utils.extract_contract_adapter')
    @patch('openprocurement.contracting.core.utils.decode_path_info')
    def test_extract_contract_success(self, mocker_decode_path_info,
                                      mocker_extract_contract_adapter):
        mocker_decode_path_info.return_value = \
            '2.3/tenders/7dc086c4a213492ab9c43b95b43bd817/' \
            'contracts/bebdbaf7777d4bd39756f3e8872c1f46'
        mocker_extract_contract_adapter.return_value = True

        self.assertEqual(extract_contract(self.request), True)

    @patch('openprocurement.contracting.core.utils.error_handler')
    def test_contract_from_data_415_error(self, mocker_error_handler):
        mocker_error_handler.side_effect = error_handler
        self.request.registry.configure_mock(
            **{'contract_contractTypes': {'common': None}})

        with self.assertRaises(Exception) as cm:
            contract_from_data(self.request, dict())
        self.assertEqual(cm.exception.message.errors.status, 415)
        cm.exception.message.errors.add.assert_called_once_with(
            'data', 'contractType', 'Not implemented'
        )

    def test_contract_from_data_success(self):
        test_mock = MagicMock()
        test_mock.return_value = test_mock
        self.request.registry.configure_mock(**{'contract_contractTypes':
                                                    {'common': test_mock}})

        self.assertEqual(contract_from_data(self.request, dict()), test_mock)
        test_mock.assert_called_once_with(dict())

    def test_contract_serialize(self):
        self.contract_mock.serialize.return_value = {
            'id': self.contract_id, 'status': 'active'}
        self.request.contract_from_data.return_value = self.contract_mock

        self.assertEqual(contract_serialize(self.request, None, ['id']),
                         {'id': self.contract_id})

    @patch('openprocurement.contracting.core.utils.set_modetest_titles')
    @patch('openprocurement.contracting.core.utils.get_revision_changes')
    def test_save_contract_return_None(self, mocker_get_revision_changes,
                                       mocker_set_modetest_titles):
        mocker_get_revision_changes.return_value = None
        mocker_set_modetest_titles.return_value = None
        self.contract_mock.configure_mock(**{'mode': u'test'})

        self.assertEqual(save_contract(self.request), None)

    @patch('openprocurement.contracting.core.utils.get_revision_changes')
    def test_save_contract_return_True(self, mocker_get_revision_changes):
        mocker_get_revision_changes.return_value = [{'id': self.contract_id}]
        self.contract_mock.store.return_value = True
        self.request.configure_mock(**{'authenticated_userid': 'Quinta'})
        self.contract_mock.configure_mock(**{'rev': self.contract_id,
                                             'mode': u'prod'})

        self.assertEqual(save_contract(self.request), True)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestisContract))
    suite.addTest(unittest.makeSuite(TestUtilsFucntions))
    suite.addTest(unittest.makeSuite(TestApiFucntions))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
