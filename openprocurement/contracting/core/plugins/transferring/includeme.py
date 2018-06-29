# -*- coding: utf-8 -*-
from logging import getLogger

LOGGER = getLogger(__name__)


def includeme(config, plugin_map): #pylint: disable=unused-argument
    config.scan("openprocurement.contracting.core.plugins.transferring.views")
    LOGGER.info("Included contracts transferring plugin",
                extra={'MESSAGE_ID': 'included_plugin'})
