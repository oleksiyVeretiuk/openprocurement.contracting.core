# -*- coding: utf-8 -*-
from openprocurement.api.plugins.transferring.validation import (
    validate_ownership_data
)
from openprocurement.contracting.core.plugins.transferring.validation import (
    validate_change_ownership_accreditation
)

from openprocurement.api.utils import (
    APIResource,
    context_unpack,
    json_view,
    set_ownership,
    ROUTE_PREFIX
)
from openprocurement.contracting.core.utils import (
    apply_patch,
    contractingresource,
    save_contract,
    get_contract_route_name
)


@contractingresource(name='Contract ownership',
                     path='/contracts/{contract_id}/ownership',
                     description="Contracts Ownership")
class ContractsResource(APIResource):

    @json_view(permission='create_contract',
               validators=(validate_change_ownership_accreditation,
                           validate_ownership_data))
    def post(self):
        contract = self.request.validated['contract']
        contract_path = get_contract_route_name(self.request, contract)
        location = self.request.route_path(contract_path, contract_id=contract.id)
        location = location[len(ROUTE_PREFIX):]  # strips /api/<version>
        ownership_changed = self.request.change_ownership(location)

        if ownership_changed and save_contract(self.request):
            self.LOGGER.info(
                'Updated ownership of contract {}'.format(contract.id),
                extra=context_unpack(
                    self.request, {'MESSAGE_ID': 'contract_ownership_update'}
                )
            )

            return {'data': self.request.context.serialize('view')}
