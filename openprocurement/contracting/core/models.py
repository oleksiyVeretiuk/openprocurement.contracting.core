# -*- coding: utf-8 -*-
from uuid import uuid4
from zope.interface import implementer, Interface
from pyramid.security import Allow
from schematics.types import StringType, MD5Type
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist

from openprocurement.api.validation import validate_items_uniq
from openprocurement.api.utils import get_now
from openprocurement.api.models.auction_models import (
    AdditionalClassification as BaseAdditionalClassification,
    CPVClassification as BaseCPVClassification,
    Contract as BaseContract,
    Document as BaseDocument,
    IsoDateTimeType,
    Item as BaseItem,
    ListType,
    Model,
    Organization as BaseOrganization,
    Revision,
    Value,
    schematics_default_role,
    schematics_embedded_role,
)
from openprocurement.api.models.common import (
    BaseResourceItem,
    ContactPoint as BaseContactPoint,
)
from openprocurement.auctions.core.models import (
    Administrator_role,
    flashItem,
    plain_role,
)

contract_create_role = (whitelist(
    'relatedProcessID',
    'merchandisingObject',
    'transfer_token',
    'awardID',
    'contractID',
    'contractNumber',
    'dateSigned',
    'description',
    'description_en',
    'description_ru',
    'id',
    'items',
    'mode',
    'owner',
    'period',
    'procuringEntity',
    'sandbox_parameters',
    'status',
    'suppliers',
    'title',
    'title_en',
    'title_ru',
    'value',
))

contract_edit_role = (whitelist(
    'amountPaid',
    'contract_amountPaid',
    'description',
    'description_en',
    'description_ru',
    'items',
    'period',
    'status',
    'terminationDetails',
    'title',
    'title_en',
    'title_ru',
))

contract_view_role = (whitelist(
    'amountPaid',
    'relatedProcessID',
    'merchandisingObject',
    'awardID',
    'changes',
    'contractID',
    'contractNumber',
    'contract_amountPaid',
    'dateModified',
    'dateSigned',
    'description',
    'description_en',
    'description_ru',
    'documents',
    'id',
    'items',
    'mode',
    'owner',
    'period',
    'procuringEntity',
    'sandbox_parameters',
    'status',
    'suppliers',
    'terminationDetails',
    'title',
    'title_en',
    'title_ru',
    'value',
))

contract_administrator_role = (Administrator_role + whitelist('suppliers',))

item_edit_role = whitelist(
    'deliveryAddress',
    'deliveryDate',
    'deliveryLocation',
    'description',
    'description_en',
    'description_ru',
    'id',
    'quantity',
    'unit',
)


class IContract(Interface):
    """ Contract marker interface """


def get_contract(model):
    while not IContract.providedBy(model):
        model = model.__parent__
    return model


class Document(BaseDocument):
    """ Contract Document """
    documentType_choices = (
        'approvalProtocol',
        'conflictOfInterest',
        'contractAnnexe',
        'contractArrangements',
        'contractGuarantees',
        'contractNotice',
        'contractSchedule',
        'contractSigned',
        'debarments',
        'registerExtract',
        'rejectionProtocol',
        'subContract',
    )
    documentOf = StringType(
        required=True,
        choices=['tender', 'item', 'lot', 'contract', 'change', 'milestone'],
        default='contract'
    )
    documentType = StringType(choices=documentType_choices)

    def validate_relatedItem(self, data, relatedItem):
        if not relatedItem and data.get('documentOf') in ['item', 'change', 'milestone']:
            raise ValidationError(u'This field is required.')
        if relatedItem and isinstance(data['__parent__'], Model):
            contract = get_contract(data['__parent__'])
            if data.get('documentOf') == 'change' and relatedItem not in [i.id for i in contract.changes]:
                raise ValidationError(u"relatedItem should be one of changes")
            if data.get('documentOf') == 'item' and relatedItem not in [i.id for i in contract.items]:
                raise ValidationError(u"relatedItem should be one of items")
            if data.get('documentOf') == 'milestone' and relatedItem not in [i.id for i in contract.milestones]:
                raise ValidationError(u"relatedItem should be one of milestones")


class ContactPoint(BaseContactPoint):
    availableLanguage = StringType()


class Organization(BaseOrganization):
    """An organization."""
    contactPoint = ModelType(ContactPoint, required=True)
    additionalContactPoints = ListType(ModelType(ContactPoint, required=True),
                                       required=False)


class ProcuringEntity(Organization):
    """An organization."""
    class Options:
        roles = {
            'embedded': schematics_embedded_role,
            'view': schematics_default_role,
            'edit_active': schematics_default_role + blacklist("kind"),
        }

    kind = StringType(choices=['general', 'special', 'defense', 'other'])


class CPVClassification(BaseCPVClassification):

    def validate_scheme(self, data, scheme):
        pass


class AdditionalClassification(BaseAdditionalClassification):

    def validate_id(self, data, code):
        pass


class Item(BaseItem):

    class Options:
        roles = {
            'edit_active': item_edit_role,
            'view': schematics_default_role,
            'embedded': schematics_embedded_role,
        }

    classification = ModelType(CPVClassification, required=True)
    additionalClassifications = ListType(ModelType(AdditionalClassification, default=list()))


class Change(Model):
    class Options:
        roles = {
            # 'edit': blacklist('id', 'date'),
            'create': whitelist('rationale', 'rationale_ru', 'rationale_en',
                                'rationaleTypes', 'contractNumber', 'dateSigned'),
            'edit': whitelist('rationale', 'rationale_ru', 'rationale_en',
                              'rationaleTypes', 'contractNumber', 'status', 'dateSigned'),
            'view': schematics_default_role,
            'embedded': schematics_embedded_role,
        }

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    status = StringType(choices=['pending', 'active'], default='pending')
    date = IsoDateTimeType(default=get_now)
    rationale = StringType(required=True, min_length=1)
    rationale_en = StringType()
    rationale_ru = StringType()
    rationaleTypes = ListType(StringType(choices=['volumeCuts', 'itemPriceVariation',
                                                  'qualityImprovement', 'thirdParty',
                                                  'durationExtension', 'priceReduction',
                                                  'taxRate', 'fiscalYearExtension'],
                                         required=True), min_size=1, required=True)
    contractNumber = StringType()
    dateSigned = IsoDateTimeType()

    def validate_dateSigned(self, data, value):
        if value and value > get_now():
            raise ValidationError(u"Contract signature date can't be in the future")


@implementer(IContract)
class Contract(BaseResourceItem, BaseContract):
    """ Contract """

    revisions = ListType(ModelType(Revision), default=list())
    dateModified = IsoDateTimeType()
    items = ListType(ModelType(flashItem), required=False, min_size=1, validators=[validate_items_uniq])
    relatedProcessID = StringType()
    owner_token = StringType(default=lambda: uuid4().hex)
    owner = StringType()
    status = StringType(choices=['terminated', 'active'], default='active')
    suppliers = ListType(ModelType(Organization), min_size=1, max_size=1)
    '''
    The entity managing the procurement, which may be different from the buyer
    who is paying / using the items being procured.
    '''
    procuringEntity = ModelType(ProcuringEntity, required=True)
    changes = ListType(ModelType(Change), default=list())
    documents = ListType(ModelType(Document), default=list())
    amountPaid = ModelType(Value)
    terminationDetails = StringType()

    class Options:
        roles = {
            'plain': plain_role,
            'create': contract_create_role,
            'edit_active': contract_edit_role,
            'edit_terminated': whitelist(),
            'view': contract_view_role,
            'Administrator': contract_administrator_role,
            'default': schematics_default_role,
        }

    def __local_roles__(self):
        return dict([('{}_{}'.format(self.owner, self.owner_token), 'contract_owner')])

    def __acl__(self):

        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_contract'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_contract_documents')
        ]
        return acl

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [
            k for k in data.keys()
            if data[k] == self.__class__.fields[k].default
            or data[k] == getattr(self, k)
        ]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        else:
            role = 'edit_{}'.format(request.context.status)
        return role

    @serializable(serialized_name='amountPaid', serialize_when_none=False, type=ModelType(Value))
    def contract_amountPaid(self):
        if self.amountPaid:
            return Value(
                dict(
                    amount=self.amountPaid.amount,
                    currency=self.value.currency,
                    valueAddedTaxIncluded=self.value.valueAddedTaxIncluded
                ))
