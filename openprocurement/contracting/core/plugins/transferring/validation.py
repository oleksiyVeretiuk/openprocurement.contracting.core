# -*- coding: utf-8 -*-
from openprocurement.api.plugins.transferring.validation import (
    validate_accreditation_level
)


def validate_contract_accreditation_level(request, **kwargs): #pylint: disable=unused-argument
    if hasattr(request.validated['contract'], 'transfer_accreditation'):
        predicate = 'transfer_accreditation'
    else:
        predicate = 'create_accreditation'
    validate_accreditation_level(request, request.validated['contract'], predicate)


def validate_bid_accreditation_level(request):
    validate_accreditation_level(request, request.validated['contract'], 'edit_accreditation')

validate_complaint_accreditation_level = validate_bid_accreditation_level
