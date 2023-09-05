import logging
from collections import defaultdict

from elasticsearch import BadRequestError
from flask import request

from nldcsc.datatables.server_side_dt import ServerSideDataTable
from nldcsc.flask_plugins.flask_eswrap import FlaskEsWrap
from nldcsc.generic.utils import str2bool
from nldcsc.loggers.app_logger import AppLogger

logging.setLoggerClass(AppLogger)


class ESServerSideDataTable(ServerSideDataTable):
    def __init__(self, request: request, backend: FlaskEsWrap, index: str, **kwargs):
        self.index = index
        self.logger = logging.getLogger(__name__)

        super().__init__(request, backend, **kwargs)

    def get_results_and_meta(self):
        self.total = getattr(self.backend.es, self.index).count()

        self.filtered = self.data_filter()

        self.fetch_results()

        if len(self.filtered) != 0:
            try:
                self.total_filtered = getattr(self.backend.es, self.index).count(
                    filter=self.filtered, regexp=True, bool_query=True
                )
            except BadRequestError as err:
                self.logger.warning(
                    f"Received BadRequestError from elasticsearch -> {err}"
                )
                self.logger.exception(err)
                self.total_filtered = 0
        else:
            self.total_filtered = self.total

    def fetch_results(self):
        try:
            if len(self.filtered) != 0:
                data_objects = list(
                    getattr(self.backend.es, self.index)
                    .find(filter=self.filtered, regexp=True, bool_query=True)
                    .skip(self.data_length.start)
                    .limit(self.data_length.length)
                )
            else:
                data_objects = list(
                    getattr(self.backend.es, self.index)
                    .find()
                    .skip(self.data_length.start)
                    .limit(self.data_length.length)
                )
        except BadRequestError as err:
            self.logger.warning(f"Received BadRequestError from elasticsearch -> {err}")
            self.logger.exception(err)
            data_objects = []

        self.results = data_objects

    def post_fetch_processing(self):
        pass

    def data_filter(self):
        docfilter = defaultdict(list)

        search_val = self.request_values["search[value]"]

        if search_val != "" and search_val != "[":
            column_search_list = [
                self.columns[i]["data"]
                for i in self.columns
                if str2bool(self.columns[i]["searchable"])
            ]

            for each in column_search_list:
                docfilter["should"].append({"regexp": {each: search_val}})

        return dict(docfilter)
