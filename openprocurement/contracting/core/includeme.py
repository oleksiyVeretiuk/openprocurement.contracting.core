# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution, iter_entry_points
from pyramid.interfaces import IRequest

from openprocurement.contracting.core.utils import (
    isContract,
    register_contract_contractType
)
from openprocurement.api.interfaces import IContentConfigurator
from openprocurement.contracting.core.models import IContract
from openprocurement.contracting.core.adapters import ContractConfigurator
from openprocurement.contracting.core.utils import contract_from_data, extract_contract
from openprocurement.contracting.core.design import add_design


PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init contracting.core plugin.')
    # contractType plugins support
    add_design()
    config.add_request_method(extract_contract, 'contract', reify=True)
    config.add_request_method(contract_from_data)
    config.scan("openprocurement.contracting.core.views")
    config.registry.contract_contractTypes = {}
    config.add_route_predicate('contractType', isContract)
    config.add_directive('add_contract_contractType',
                         register_contract_contractType)
    config.scan("openprocurement.contracting.core.views")
    config.registry.registerAdapter(ContractConfigurator, (IContract, IRequest),
                                    IContentConfigurator)

    # search for plugins
    settings = config.get_settings()
    plugins = settings.get('plugins') and settings['plugins'].split(',')
    for entry_point in iter_entry_points('openprocurement.contracting.core.plugins'):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)
