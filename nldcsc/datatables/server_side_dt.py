import re
from abc import ABC, abstractmethod
from collections import namedtuple, defaultdict


class ServerSideDataTable(ABC):
    """
    This class holds all the logic for enabling and handling server side DataTables within the application

    """

    def __init__(self, request, backend, **kwargs):
        self.request_values = request.values

        self.backend = backend

        self.columns, self.ordering, self.results, self.fields, self.data_length = (
            None,
            None,
            None,
            None,
            None,
        )

        self.total, self.total_filtered, self.current_draw = 0, 0, 0

        self.filtered = {}

        self.sort = []

        self.pre_fetch_processing()

        self.post_fetch_processing()

    def output_result(self):
        return {
            "draw": int(self.current_draw),
            "recordsTotal": int(self.total),
            "recordsFiltered": int(self.total_filtered),
            "data": self.results,
        }

    def pre_fetch_processing(self):
        """
        Method to provision the necessary variables for the correct retrieval of the results from the Database
        """
        self.current_draw = int(self.request_values["draw"])

        self.data_length = self.__data_dimension()

        self.columns, self.ordering = self.__data_columns_ordering()

        for each in self.ordering:
            if self.ordering[each]["dir"] == "asc":
                self.sort.append(
                    (
                        self.columns[self.ordering[each]["column"]]["data"],
                        "asc",
                    )
                )
            else:
                self.sort.append(
                    (
                        self.columns[self.ordering[each]["column"]]["data"],
                        "desc",
                    )
                )

        self.fields = defaultdict(int)

        for each in self.columns:
            self.fields[self.columns[each]["data"]] = 1

        self.get_results_and_meta()

    @abstractmethod
    def get_results_and_meta(self):
        raise NotImplementedError

    @abstractmethod
    def fetch_results(self):
        """
        Method responsible for querying the backend and fetching the results from the database
        """
        raise NotImplementedError

    @abstractmethod
    def post_fetch_processing(self):
        raise NotImplementedError

    def __data_dimension(self):
        """
        Method responsible for retrieving the requested start and length parameters from the DataTables request values

        :return: Namedtuple 'data_length' with a start and length attribute
        :rtype: namedtuple
        """

        data_length = namedtuple("data_length", ["start", "length"])

        data_length.start = int(self.request_values["start"])
        data_length.length = int(self.request_values["length"])

        return data_length

    def __data_columns_ordering(self):
        """
        Method responsible for retrieving the column and order details from the DataTables request values

        :return: 2 Dictionaries the column details and order details
        :rtype: defaultdict, defaultdict
        """

        col = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        order = defaultdict(lambda: defaultdict(dict))

        col_regex = re.compile(r"columns\[(\d*)\]\[(\w*)\](?:\[(\w*)\])?")
        order_regex = re.compile(r"order\[(\d*)\]\[(\w*)\]")

        for each in sorted(self.request_values.keys()):
            check_col_match = col_regex.match(each)
            check_order_match = order_regex.match(each)
            if check_col_match:
                if check_col_match.group(2) == "search":
                    try:
                        col[check_col_match.group(1)][check_col_match.group(2)][
                            check_col_match.group(3)
                        ] = int(self.request_values[each])
                    except ValueError:
                        col[check_col_match.group(1)][check_col_match.group(2)][
                            check_col_match.group(3)
                        ] = self.request_values[each]
                else:
                    col[check_col_match.group(1)][
                        check_col_match.group(2)
                    ] = self.request_values[each]
            if check_order_match:
                order[check_order_match.group(1)][
                    check_order_match.group(2)
                ] = self.request_values[each]

        return col, order

    @abstractmethod
    def data_filter(self):
        """
        Method responsible for retrieving the filter values entered in the search box of the DataTables.

        :return: Prepared filter based on filterable columns and retrieved search value
        :rtype: dict
        """
        raise NotImplementedError
