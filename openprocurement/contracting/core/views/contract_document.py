# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    APIResource,
    json_view,
    context_unpack,
    get_file,
)
from openprocurement.api.validation import validate_file_upload
from openprocurement.contracting.core.utils import (
    apply_patch,
    contractingresource,
    save_contract,
)
from openprocurement.contracting.core.interfaces import (
    IContractManager,
)
from openprocurement.contracting.core.constants import (
    ENDPOINTS,
)
from openprocurement.contracting.core.validation import (
    validate_contract_document,
    validate_patch_contract_document,
)


@contractingresource(
    name="Contract document",
    path=ENDPOINTS['documents'],
    collection_path=ENDPOINTS['documents_collection'])
class CeasefireContractDocumentResource(APIResource):

    @json_view(
        content_type="application/json",
        validators=(validate_file_upload,),
        permission='edit_contract')
    def collection_post(self):
        contract = self.request.validated['contract']
        document = self.request.validated['document']
        manager = self.request.registry.getAdapter(contract, IContractManager).document_manager()
        manager.create_document(self.request)
        if save_contract(self.request):
            self.LOGGER.info(
                'Created contract document. contract ID: {0} documentID: {1}'.format(
                    contract.id,
                    document.id
                ),
                extra=context_unpack(
                    self.request,
                    {'MESSAGE_ID': 'contract_document_create'},
                    {
                        'contract_id': contract.id,
                        'document_id': document.id
                    }
                )
            )
            self.request.response.status = 201
            return {
                'data': document.serialize("view"),
            }

    @json_view(content_type="application/json", permission='view_listing')
    def get(self):
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        return {'data': document.serialize("view")}

    @json_view(
            content_type="application/json",
            validators=(validate_patch_contract_document,),
            permission='edit_contract')
    def patch(self):
        contract = self.request.validated['contract']
        document = self.request.context
        manager = self.request.registry.getAdapter(contract, IContractManager).document_manager()
        manager.change_document(self.request)

        if apply_patch(self.request):
            self.LOGGER.info(
                'Updated ceasefire contract document. '
                'contractID: {0} documentID: {1}'.format(
                    contract.id,
                    document.id,
                ),
                extra=context_unpack(
                    self.request,
                    {'MESSAGE_ID': 'ceasefire_contract_document_patch'}
                    )
                )
            return {'data': document.serialize('view')}
