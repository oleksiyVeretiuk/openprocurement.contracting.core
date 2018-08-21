# -*- coding: utf-8 -*-
import unittest

from uuid import uuid4
from openprocurement.auctions.core.tests.base import snitch
from openprocurement.contracting.core.tests.base import (
    BaseWebTest,
    Contract
)
from openprocurement.contracting.core.tests.contract_blanks import (
    # ContractResourceTest
    empty_listing,
)


class ContractResourceTest(BaseWebTest):
    """ contract resource test """

    test_empty_listing = snitch(empty_listing)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContractResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
