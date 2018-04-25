# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    apply_data_patch,
    generate_id,
)


def save_contract(request):
    """ Save contract object to database
    :param request:
    :return: True if Ok
    """
    contract = request.validated['contract']

    if contract.mode == u'test':
        set_modetest_titles(contract)
    patch = get_revision_changes(contract.serialize("plain"),
                                 request.validated['contract_src'])
    if patch:
        contract.revisions.append(
            Revision({'author': request.authenticated_userid,
                      'changes': patch, 'rev': contract.rev}))
        old_date_modified = contract.dateModified
        contract.dateModified = get_now()
        try:
            contract.store(request.registry.db)
        except ModelValidationError, e:  # pragma: no cover
            for i in e.message:
                request.errors.add('body', i, e.message[i])
            request.errors.status = 422
        except Exception, e:  # pragma: no cover
            request.errors.add('body', 'data', str(e))
        else:
            LOGGER.info('Saved contract {}: dateModified {} -> {}'.format(
                contract.id, old_date_modified and old_date_modified.isoformat(),
                contract.dateModified.isoformat()),
                extra=context_unpack(request, {'MESSAGE_ID': 'save_contract'},
                                     {'CONTRACT_REV': contract.rev}))
            return True


class isContract(object):
    """ Route predicate. """

    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'contractType = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        if request.contract is not None:
            c_type = getattr(request.contract, 'contractType',
                             None) or "common"
            return c_type == self.val
        return False


def register_contract_contractType(config, model):
    """Register a contract contractType.
    :param config:
        The pyramid configuration object that will be populated.
    :param model:
        The contract model class
    """
    contract_type = model.contractType.default or 'common'
    config.registry.contract_contractTypes[contract_type] = model


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated['data'] if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_contract(request)


def set_ownership(item, request):
    item.owner_token = generate_id()
