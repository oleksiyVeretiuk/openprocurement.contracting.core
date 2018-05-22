# -*- coding: utf-8 -*-
from zope.interface import Interface


class IContractManager(Interface):

    def create_contract(self, request, **kwargs):
        raise NotImplementedError

    def change_contract(self, request, **kwargs):
        raise NotImplementedError

class IMilestoneManager(Interface):

    def create_milestones(self, request, **kwargs):
        raise NotImplementedError

    def change_milestone(self, request, **kwargs):
        raise NotImplementedError
