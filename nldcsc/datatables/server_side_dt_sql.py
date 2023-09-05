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
        **kwargs,
    ):
        self.target_model = target_model

        self.models = model_mapping

        super().__init__(request, backend, **kwargs)

    def post_fetch_processing(self):
        pass

    def get_results_and_meta(self):
        if len(self.sort) == 0:
            self.sort = ""
        else:
            self.sort = self.stringify_sort_list()

        self.total = self.models[self.target_model].query.filter().count()

        self.negate_filter, self.filtered = self.data_filter()

        self.fetch_results()

        if len(self.filtered) != 0:
            if self.negate_filter:
                self.total_filtered = (
                    self.models[self.target_model]
                    .query.filter(not_(or_(*self.filtered)))
                    .count()
                )
            else:
                self.total_filtered = (
                    self.models[self.target_model]
                    .query.filter(or_(*self.filtered))
                    .count()
                )
        else:
            self.total_filtered = self.total

    def fetch_results(self):
        """
        Method responsible for querying the backend and fetching the results from the database
        """
        if len(self.filtered) != 0:
            if self.negate_filter:
                data_objects = (
                    self.models[self.target_model]
                    .query.filter(not_(or_(*self.filtered)))
                    .order_by(text(self.sort))
                    .offset(self.data_length.start)
                    .limit(self.data_length.length)
                    .all()
                )
            else:
                data_objects = (
                    self.models[self.target_model]
                    .query.filter(or_(*self.filtered))
                    .order_by(text(self.sort))
                    .offset(self.data_length.start)
                    .limit(self.data_length.length)
                    .all()
                )
        else:
            data_objects = (
                self.models[self.target_model]
                .query.filter()
                .order_by(text(self.sort))
                .offset(self.data_length.start)
                .limit(self.data_length.length)
                .all()
            )

        self.results = [x.to_data_dict() for x in data_objects]

    def stringify_sort_list(self):
        ret_list = []

        for each in self.sort:
            ret_list.append(f"{each[0]} {each[1]}")

        return ",".join(ret_list)

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
