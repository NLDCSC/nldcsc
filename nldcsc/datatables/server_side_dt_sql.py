import re
from typing import Callable, Iterable
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query
from sqlalchemy import or_, and_
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import BinaryExpression

from nldcsc.datatables.server_side_dt import ServerSideDataTable
from nldcsc.generic.utils import str2bool
from nldcsc.generic.times import timestringTOtimestamp


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
        additional_filters: list[BinaryExpression] = None,
        use_column_filters: bool = False,
        custom_column_filters: dict[
            str,
            Callable[[InstrumentedAttribute, str, bool], Iterable[BinaryExpression]],
        ] = None,
        query_hook: Callable[[Query], Query] = None,
        **kwargs,
    ):
        """
        Sql server side datatable.

        Generates a response needed from a datatable request.

        Args:
            request (request): The request the datatable info is in.
            backend (SQLAlchemy): The backend to use to retrieve data from.
            target_model (str): The targeted model to fetch.
            model_mapping (dict): Mapping of models to their class.
            additional_filters (list[BinaryExpression], optional): list of additional filter to apply. Defaults to None.
            use_column_filters (bool, optional): apply filters on the column level. Defaults to False.
            custom_column_filters (dict[ str, Callable[[InstrumentedAttribute, str, bool], BinaryExpression] ], optional): apply a custom filter to specific columns. Defaults to None.
            query_hook (Callable[[Query], Query], optional): hook that is called before the query is submitted, gives the ability to modify the query. Defaults to None.
        """
        if additional_filters is None:
            additional_filters = []

        if custom_column_filters is None:
            custom_column_filters = {}

        self.target_model = target_model
        self.additional_filters = additional_filters
        self.use_column_filters = use_column_filters
        self.custom_column_filters = custom_column_filters
        self.query_hook = query_hook

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

        self.filtered = []

        if self.use_column_filters:
            column_filters = self.column_data_filter()
            global_filters = self.data_filter()
            if len(column_filters) != 0 and len(global_filters) != 0:
                self.filtered.append(and_(*column_filters, or_(*global_filters)))
            elif len(column_filters) != 0:
                self.filtered.append(and_(*column_filters))
            elif len(global_filters) != 0:
                self.filtered.append(or_(*global_filters))
        else:
            global_filters = self.data_filter()
            if len(global_filters) != 0:
                self.filtered.append(or_(*global_filters))

        self.fetch_results()

        if len(self.filtered) != 0:
            filter_query = self.models[self.target_model].query
            for query_filter in self.additional_filters:
                filter_query = filter_query.filter(query_filter)

            filter_query = filter_query.filter(*self.filtered)
            self.total_filtered = filter_query.count()
        else:
            self.total_filtered = self.total

    def fetch_results(self):
        """
        Method responsible for querying the backend and fetching the results from the database
        """
        query: Query = self.models[self.target_model].query

        for query_filter in self.additional_filters:
            query = query.filter(query_filter)

        if len(self.filtered) != 0:
            query = query.filter(*self.filtered)

        if self.query_hook:
            query = self.query_hook(query)

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

    @staticmethod
    def default_filter(
        col: InstrumentedAttribute,
        filter_val: str,
        is_regex: bool,
        check_date: bool = True,
    ) -> list[BinaryExpression]:
        def is_date(value: str) -> int | str:
            if not check_date:
                return value

            is_date = timestringTOtimestamp(value)

            if is_date is not False:
                return is_date

            return value

        filter_args = []

        if is_regex:
            try:
                negate_search = False

                if filter_val[0] == "~":
                    filter_val = filter_val[1:]
                    negate_search = True

                re.compile(filter_val)

                if negate_search:
                    filter_args.append(~col.regexp_match(filter_val))
                else:
                    filter_args.append(col.regexp_match(filter_val))

                return filter_args
            except re.error:
                if negate_search:
                    filter_val = "~" + filter_val

        if "<>" in filter_val:
            start, end = filter_val.split("<>", 1)

            start = is_date(start.strip())
            end = is_date(end.strip())

            filter_args.append(col > start)
            filter_args.append(col < end)
        elif filter_val[0] == ">":
            filter_val = is_date(filter_val[1:].strip())
            filter_args.append(col > filter_val)
        elif filter_val[0] == "<":
            filter_val = is_date(filter_val[1:].strip())
            filter_args.append(col < filter_val)
        elif filter_val[0] == "~":
            if len(filter_val.strip()) == 1:
                filter_args.append(col == None)  # noqa: E711
            else:
                filter_val = filter_val[1:].strip()
                filter_args.append(~col.like(f"%{filter_val}%"))
        else:
            filter_args.append(col.like(f"%{filter_val}%"))

        return filter_args

    def get_filter_args(
        self, column: str, filter_val: str, is_regex: bool, check_date: bool = True
    ) -> list:
        """
        parses search values to valid search expressions for sqlalchemy.

        when searching without regex the <>, >, < and ~ operators are supported.
        where <> searches between two values, > searches for larger values, < searches for smaller values and ~
        reverses the search operation. If only ~ is searched it is treated as a NULL filter, meaning column must
        be holding value NULL.

        when searching with regex only ~ is supported, reversing the search to a negate search.

        If a custom filter is given for a column that function will be called with the column, filter_val and is_regex.
        If the custom filter can't filter the values it can raise a ValueError to proceed with the normal filters.
        The custom filter should return a list of filters.
            Example:
                def my_custom_filter(col: InstrumentedAttribute, filter_val: str, is_regex: bool):
                    if filter_val.startswith("A"):
                        return [col != "A", col != "a"]
                    else:
                        raise ValueError

        Args:
            column (str): str value representing the ORM column to filter on.
            filter_val (str): value to search on.
            is_regex (bool): if the search is a regex search or a regular search
            check_date (bool, optional): will check if strings represent a date and convert it to a timestamp value.
            Defaults to True.

        Returns:
            list: List of filter values
        """
        filter_val = str(filter_val)

        custom_filter = self.custom_column_filters.get(column, None)

        filter_args = []

        try:
            col = getattr(self.models[self.target_model], column)
        except AttributeError:
            return filter_args

        if custom_filter is not None:
            try:
                # noinspection PyCallingNonCallable
                filter_args.extend(custom_filter(col, filter_val, is_regex))
                return filter_args
            except ValueError:
                # If the custom filter throws a ValueError we apply the normal filters
                pass

        filter_args.extend(self.default_filter(col, filter_val, is_regex, check_date))

        return filter_args

    def data_filter(self) -> list:
        """
        method responsible for retrieving filter values based on the table wide search value for every supported column.

        Returns:
            list: list containing prepared filters.
        """

        search_val = self.request_values["search[value]"]
        is_regex = str2bool(
            self.request_values.get(key="search[regex]", default="false")
        )

        search_args = []

        if search_val != "" and search_val != "$" and search_val != "~":
            for col in self.columns:
                if str2bool(self.columns[col]["searchable"]):
                    search_args.extend(
                        self.get_filter_args(
                            self.columns[col]["data"], search_val, is_regex
                        )
                    )

        return search_args

    def column_data_filter(self) -> list:
        """
        method responsible for retrieving filter values based on a per column based search value.

        Returns:
            list: list containing prepared filters.
        """
        search_args = []

        for col in self.columns:
            search_val_dict = self.columns[col].get(
                "search", {"regex": "false", "value": ""}
            )

            if search_val_dict["value"] in ["", "$"]:
                continue

            search_val_dict["regex"] = str2bool(search_val_dict["regex"])

            search_args.extend(
                self.get_filter_args(
                    self.columns[col]["data"],
                    search_val_dict["value"],
                    search_val_dict["regex"],
                )
            )

        return search_args
