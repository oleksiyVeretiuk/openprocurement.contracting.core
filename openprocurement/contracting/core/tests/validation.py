# -*- coding: utf-8 -*-
import unittest

from mock import patch, MagicMock
from pyramid.request import Request

from openprocurement.contracting.core.models import Contract, Change
from openprocurement.contracting.core.validation import validate_contract_data
from openprocurement.contracting.core.tests.base import error_handler
from openprocurement.contracting.core.validation import (
    validate_patch_contract_data,
    validate_change_data,
    validate_patch_change_data,
    validate_create_contract_change,
    validate_contract_change_add_not_in_allowed_contract_status,
    validate_contract_change_update_not_in_allowed_change_status,
    validate_update_contract_change_status,
    validate_contract_update_not_in_allowed_status,
    validate_terminate_contract_without_amountPaid,
    validate_credentials_generate,
    validate_contract_document_operation_not_in_allowed_contract_status,
    validate_add_document_to_active_change
)


class TestValidationFucntions(unittest.TestCase):

    def setUp(self):
        self.contract = Contract()
        self.request = Request(dict())

    @patch('openprocurement.contracting.core.validation.validate_data')
    def test_validate_patch_contract_data(self, mocker_validate_data):
        mocker_validate_data.return_value = True
        self.request.contract = self.contract
        self.assertEquals(validate_patch_contract_data(self.request), True)

    @patch(
        'openprocurement.contracting.core.validation.update_logging_context')
    @patch('openprocurement.contracting.core.validation.validate_json_data')
    @patch('openprocurement.contracting.core.validation.validate_data')
    def test_validate_change_data(self, mocker_validate_data,
                                  mocker_validate_json_data,
                                  mocker_update_logging_context):
        mocker_validate_data.return_value = True
        mocker_validate_json_data.return_value = None
        mocker_update_logging_context.return_value = None
        self.assertEquals(validate_change_data(None), True)

    @patch('openprocurement.contracting.core.validation.validate_data')
    def test_validate_patch_change_data(self, mocker_validate_data):
        mocker_validate_data.return_value = True

        self.assertEquals(validate_patch_change_data(None), True)

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_contract_change_add_not_in_allowed_contract_status(self,
                                                 mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.contract.status = 'draft'
        self.request.validated = dict()
        self.request.validated['contract'] = self.contract

        self.assertEquals(
          validate_contract_change_add_not_in_allowed_contract_status(
              self.request),
          None
        )
        mocker_raise_operation_error.assert_called_once_with(self.request,
        'Can\'t add contract change in current ({}) contract status'.format(
                                                        self.contract.status))

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_create_contract_change(self,
                                             mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        change = Change()
        change.status = 'pending'
        self.contract.changes = [change]
        self.request.validated = dict()
        self.request.validated['contract'] = self.contract
        self.assertEquals(validate_create_contract_change(self.request), None)
        mocker_raise_operation_error.assert_called_once_with(self.request,
         'Can\'t create new contract change while any (pending) change exists')

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_contract_change_update_not_in_allowed_change_status(self,
                                             mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        change = Change()
        change.status = 'active'
        self.request.validated = dict()
        self.request.validated['change'] = change
        self.assertEquals(
            validate_contract_change_update_not_in_allowed_change_status(
                self.request
            ),
            None
        )
        mocker_raise_operation_error.assert_called_once_with(
            self.request,
            'Can\'t update contract change in current ({}) status'.format(
             change.status)
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_update_contract_change_status(self,
                                             mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.request.validated = {'data': dict()}
        self.assertEquals(validate_update_contract_change_status(self.request),
                          None)
        mocker_raise_operation_error.assert_called_once_with(
            self.request,
            'Can\'t update contract change status. \'dateSigned\' is required.'
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_contract_update_not_in_allowed_status(self,
                                                 mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.request.validated = dict()
        self.contract.status = 'draft'
        self.request.validated['contract'] = self.contract
        self.request.authenticated_role = 'Broker'
        self.assertEquals(
            validate_contract_update_not_in_allowed_status(self.request),
            None
        )
        mocker_raise_operation_error.assert_called_once_with(
            self.request,
            'Can\'t update contract in current ({}) status'.format(
                self.contract.status)
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_terminate_contract_without_amountPaid(self,
                                                 mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        request = Request(dict())
        request.validated = dict()
        self.contract.status = 'terminated'
        request.validated['contract'] = self.contract
        self.assertEquals(
            validate_terminate_contract_without_amountPaid(request),
            None
        )
        mocker_raise_operation_error.assert_called_once_with(
            request,
            'Can\'t terminate contract while \'amountPaid\' is not set'
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_credentials_generate(self, mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.request.validated = dict()
        self.contract.status = 'draft'
        self.request.validated['contract'] = self.contract

        self.assertEquals(validate_credentials_generate(self.request), None)
        mocker_raise_operation_error.assert_called_once_with(
            self.request,
            'Can\'t generate credentials in current ({}) contract status'\
            .format(self.contract.status)
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_contract_document_operation_not_in_allowed_contract(
            self, mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.request.method = 'POST'
        self.request.validated = dict()
        self.contract.status = 'draft'
        self.request.validated['contract'] = self.contract

        self.assertEquals(
           validate_contract_document_operation_not_in_allowed_contract_status(
               self.request),
           None
        )
        mocker_raise_operation_error.assert_called_once_with(
            self.request,
            'Can\'t add document in current ({}) contract status'\
                .format(self.contract.status)
        )

    @patch('openprocurement.contracting.core.validation.raise_operation_error')
    def test_validate_add_document_to_active_change(self,
                                               mocker_raise_operation_error):
        mocker_raise_operation_error.return_value = False

        self.request.validated = dict()
        self.contract.changes = []
        self.request.validated['contract'] = self.contract
        self.request.validated['data'] = {'relatedItem': None,
                                     'documentOf': 'change'}

        self.assertEquals(validate_add_document_to_active_change(self.request),
                          None)
        mocker_raise_operation_error.assert_called_once_with(self.request,
            'Can\'t add document to \'active\' change')


class TestValidateContractData(unittest.TestCase):
    """The point of this test cases if test specific functions behavior
       so all functions that are called inside tested functions are patched."""

    def setUp(self):
        self.expected_result = True
        self.request = Request(dict())
        self.request.validated = dict()
        self.model = MagicMock()
        self.request.contract_from_data = self.model
        self.request.errors = MagicMock()

    @patch('openprocurement.contracting.core.validation.validate_data')
    @patch('openprocurement.contracting.core.validation.validate_json_data')
    @patch('openprocurement.contracting.core.validation.update_logging_context')
    def test_validate_contract_data_no_error(self,
                                             mocker_update_logging_context,
                                             mocker_validate_json_data,
                                             mocker_validate_data):
        mocker_update_logging_context.return_value = True
        mocker_validate_json_data.return_value = {'id': 'fake_id'}
        mocker_validate_data.return_value = self.expected_result

        self.assertEquals(
            validate_contract_data(self.request),
            self.expected_result
        )

    @patch('openprocurement.contracting.core.validation.error_handler')
    @patch('openprocurement.contracting.core.validation.validate_json_data')
    @patch('openprocurement.contracting.core.validation.update_logging_context')
    def test_validate_contract_data_with_error(
        self, mocker_update_logging_context, mocker_validate_json_data, mocker_error_handler
    ):
        mocker_update_logging_context.return_value = True
        mocker_validate_json_data.return_value = {'id': 'fake_id'}
        checked_accreditation = MagicMock(return_value=False)
        mocker_error_handler.side_effect = error_handler
        self.request.check_accreditation = checked_accreditation

        with self.assertRaises(Exception) as cm:
            validate_contract_data(self.request)
        self.assertEqual(self.request.errors.status, 403)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestValidationFucntions))
    suite.addTest(unittest.makeSuite(TestValidateContractData))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
