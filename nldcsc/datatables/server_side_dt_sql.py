from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, or_, not_

from nldcsc.datatables.server_side_dt import ServerSideDataTable
from nldcsc.generic.utils import str2bool


class SQLServerSideDataTable(ServerSideDataTable):
    """
    This class holds all the logic for enabling and handling server side DataTables within the application

    """

    def __init__(
        self,
        request: request,
        backend: SQLAlchemy,
        target_model: str,
        model_mapping: dict,
        additional_filters: list = [],
        **kwargs,
    ):
        self.target_model = target_model
        self.additional_filters = additional_filters

        self.models = model_mapping

        super().__init__(request, backend, **kwargs)

    def post_fetch_processing(self):
        pass

    def get_results_and_meta(self):
        if len(self.sort) == 0:
            self.sort = ""
        else:
            self.sort = self.create_sort_list()

        total_query = self.models[self.target_model].query
        for query_filter in self.additional_filters:
            total_query = total_query.filter(query_filter)
        self.total = total_query.count()

        self.negate_filter, self.filtered = self.data_filter()

        self.fetch_results()

        if len(self.filtered) != 0:
            filter_query = self.models[self.target_model].query
            for query_filter in self.additional_filters:
                filter_query = filter_query.filter(query_filter)

            if self.negate_filter:
                filter_query = filter_query.filter(not_(or_(*self.filtered)))
            else:
                filter_query = filter_query.filter(or_(*self.filtered))
            self.total_filtered = filter_query.count()
        else:
            self.total_filtered = self.total

    def fetch_results(self):
        """
        Method responsible for querying the backend and fetching the results from the database
        """
        query = self.models[self.target_model].query

        for query_filter in self.additional_filters:
            query = query.filter(query_filter)

        if len(self.filtered) != 0:
            if self.negate_filter:
                query = query.filter(not_(or_(*self.filtered)))
            else:
                query = query.filter(or_(*self.filtered))

        data_objects = (
            query.order_by(*self.sort)
            .offset(self.data_length.start)
            .limit(self.data_length.length)
            .all()
        )

        self.results = [x.to_data_dict() for x in data_objects]

    def create_sort_list(self):
        ret_list = []

        for each in self.sort:
            c = getattr(self.models[self.target_model], each[0], None)

            if not c:
                continue

            if each[1] == "asc":
                ret_list.append(c.asc())
            elif each[1] == "desc":
                ret_list.append(c.desc())

        return ret_list

    def data_filter(self):
        """
        Method responsible for retrieving the filter values entered in the search box of the DataTables.

        :return: Prepared filter based on filterable columns and retrieved search value
        :rtype: dict
        """

        search_val = self.request_values["search[value]"]

        search_args = []
        negate_search = False

        if search_val != "" and search_val != "$" and search_val != "~":
            # Negate search if string starts with ~
            if search_val.lstrip()[0] == "~":
                negate_search = True
                search_val = search_val.lstrip()[1:]

            search_args = [
                getattr(
                    self.models[self.target_model], self.columns[col]["data"]
                ).regexp_match(f"{search_val}")
                for col in self.columns
                if str2bool(self.columns[col]["searchable"])
            ]

        return negate_search, search_args
