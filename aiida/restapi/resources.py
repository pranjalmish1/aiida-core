# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from urllib import unquote

from flask import request
from flask_restful import Resource

from aiida.restapi.common.utils import Utils


class ServerInfo(Resource):
    def __init__(self, **kwargs):
        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in
                            kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self):
        """
        It returns the general info about the REST API
        :return: returns current AiiDA version defined in aiida/__init__.py
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        response = []

        from aiida.restapi.common.config import PREFIX

        # Add Rest API version
        response.append("REST API version: " + PREFIX.split("/")[-1])

        # Add Rest API prefix
        response.append("REST API Prefix: " + PREFIX)

        # Add AiiDA version
        from aiida import __version__
        response.append("AiiDA==" + __version__)

        headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Build response and return it
        data = dict(method=request.method,
                    url=url,
                    url_root=url_root,
                    path=path,
                    query_string=query_string,
                    resource_type="Info",
                    data=response)
        return self.utils.build_response(status=200, headers=headers, data=data)


## TODO add the caching support. I cache total count, results, and possibly
# set_query
class BaseResource(Resource):
    ## Each derived class will instantiate a different type of translator.
    # This is the only difference in the classes.
    def __init__(self, **kwargs):

        self.trans = None

        # Flag to tell the path parser whether to expect a pk or a uuid pattern
        self.parse_pk_uuid = None

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in
                            kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self, id=None, page=None):
        """
        Get method for the Computer resource
        :return:
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, id, query_type) = self.utils.parse_path(path,                                    parse_pk_uuid=self.parse_pk_uuid)
        (limit, offset, perpage, orderby, filters, alist, nalist, elist,
         nelist) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(limit=limit, offset=offset, perpage=perpage,
                                    page=page, query_type=query_type,
                                    is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()
            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        else:
            ## Set the query, and initialize qb object
            self.trans.set_query(filters=filters, orders=orderby, id=id)

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage,
                                                                 total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(rel_pages=rel_pages,
                                                   url=request.url,
                                                   total_count=total_count)
            else:
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(url=request.url,
                                                   total_count=total_count)

            ## Retrieve results
            results = self.trans.get_results()

        ## Build response and return it
        data = dict(method=request.method,
                    url=url,
                    url_root=url_root,
                    path=request.path,
                    id=id,
                    query_string=request.query_string,
                    resource_type=resource_type,
                    data=results)
        return self.utils.build_response(status=200, headers=headers, data=data)


class Node(Resource):
    ##Differs from BaseResource in trans.set_query() mostly because it takes
    # query_type as an input and the presence of "tree" result type
    def __init__(self, **kwargs):

        # Set translator
        from aiida.restapi.translator.node import NodeTranslator
        self.trans = NodeTranslator(**kwargs)

        from aiida.orm import Node
        self.tclass = Node

        # Parse a uuid pattern in the URL path (not a pk)
        self.parse_pk_uuid = 'uuid'

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in
                            kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self, id=None, page=None):
        """
        Get method for the Node resource.
        :return:
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, id, query_type) = self.utils.parse_path(path,                                    parse_pk_uuid=self.parse_pk_uuid)

        (limit, offset, perpage, orderby, filters, alist, nalist, elist,
         nelist) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(limit=limit, offset=offset, perpage=perpage,
                                    page=page, query_type=query_type,
                                    is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()

            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Treat the statistics
        elif query_type == "statistics":
            (limit, offset, perpage, orderby, filters, alist, nalist, elist,
             nelist) = self.utils.parse_query_string(query_string)
            headers = self.utils.build_headers(url=request.url, total_count=0)
            if len(filters) > 0:
                usr = filters["user"]["=="]
            else:
                usr = []
            results = self.trans.get_statistics(usr)

        # TODO Might need to be improved
        elif query_type == "tree":
            headers = self.utils.build_headers(url=request.url, total_count=0)
            results = self.trans.get_io_tree(id)

        else:
            ## Initialize the translator
            self.trans.set_query(filters=filters, orders=orderby,
                                 query_type=query_type, id=id, alist=alist,
                                 nalist=nalist, elist=elist, nelist=nelist)

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage,
                                                                 total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(rel_pages=rel_pages,
                                                   url=request.url,
                                                   total_count=total_count)
            else:
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(url=request.url,
                                                   total_count=total_count)

            ## Retrieve results
            results = self.trans.get_results()

        ## Build response
        data = dict(method=request.method,
                    url=url,
                    url_root=url_root,
                    path=path,
                    id=id,
                    query_string=query_string,
                    resource_type=resource_type,
                    data=results)
        return self.utils.build_response(status=200, headers=headers, data=data)


class Computer(BaseResource):
    def __init__(self, **kwargs):
        super(Computer, self).__init__(**kwargs)

        ## Instantiate the correspondent translator
        from aiida.restapi.translator.computer import ComputerTranslator
        self.trans = ComputerTranslator(**kwargs)

        # Set wheteher to expect a pk (integer) or a uuid pattern (string) in
        # the URL path
        self.parse_pk_uuid = "uuid"


class Group(BaseResource):
    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)

        from aiida.restapi.translator.group import GroupTranslator
        self.trans = GroupTranslator(**kwargs)

        self.parse_pk_uuid = 'uuid'

class User(BaseResource):
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        from aiida.restapi.translator.user import UserTranslator
        self.trans = UserTranslator(**kwargs)

        self.parse_pk_uuid = 'pk'

class Calculation(Node):
    def __init__(self, **kwargs):
        super(Calculation, self).__init__(**kwargs)

        from aiida.restapi.translator.calculation import CalculationTranslator
        self.trans = CalculationTranslator(**kwargs)
        from aiida.orm import Calculation as CalculationTclass
        self.tclass = CalculationTclass

        self.parse_pk_uuid = 'uuid'


class Code(Node):
    def __init__(self, **kwargs):
        super(Code, self).__init__(**kwargs)

        from aiida.restapi.translator.code import CodeTranslator
        self.trans = CodeTranslator(**kwargs)
        from aiida.orm import Code as CodeTclass
        self.tclass = CodeTclass

        self.parse_pk_uuid = 'uuid'


class Data(Node):
    def __init__(self, **kwargs):
        super(Data, self).__init__(**kwargs)

        from aiida.restapi.translator.data import DataTranslator
        self.trans = DataTranslator(**kwargs)
        from aiida.orm import Data as DataTclass
        self.tclass = DataTclass

        self.parse_pk_uuid = 'uuid'


class StructureData(Data):
    def __init__(self, **kwargs):
        super(StructureData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.structure import \
            StructureDataTranslator
        self.trans = StructureDataTranslator(**kwargs)
        from aiida.orm.data.structure import StructureData as StructureDataTclass
        self.tclass = StructureDataTclass

        self.parse_pk_uuid = 'uuid'


class KpointsData(Data):
    def __init__(self, **kwargs):
        super(KpointsData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.kpoints import KpointsDataTranslator
        self.trans = KpointsDataTranslator(**kwargs)
        from aiida.orm.data.array.kpoints import KpointsData as KpointsDataTclass
        self.tclass = KpointsDataTclass

        self.parse_pk_uuid = 'uuid'


class BandsData(Data):
    def __init__(self, **kwargs):
        super(BandsData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.bands import \
            BandsDataTranslator
        self.trans = BandsDataTranslator(**kwargs)
        from aiida.orm.data.array.bands import BandsData as BandsDataTclass
        self.tclass = BandsDataTclass

        self.parse_pk_uuid = 'uuid'
