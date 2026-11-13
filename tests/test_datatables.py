from types import SimpleNamespace

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import column

from nldcsc.datatables.server_side_dt_es import ESServerSideDataTable
from nldcsc.datatables.server_side_dt_sql import SQLServerSideDataTable


def make_datatable_query(**overrides):
    values = {
        "draw": "3",
        "start": "0",
        "length": "10",
        "search[value]": "",
        "search[regex]": "false",
        "columns[0][data]": "name",
        "columns[0][searchable]": "true",
        "columns[0][search][value]": "",
        "columns[0][search][regex]": "false",
        "order[0][column]": "0",
        "order[0][dir]": "asc",
    }
    values.update(overrides)
    return values


def test_sql_datatable_applies_sort_pagination_and_global_search():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db = SQLAlchemy(app)

    class Item(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(40), nullable=False)

        def to_data_dict(self):
            return {"id": self.id, "name": self.name}

    with app.app_context():
        db.create_all()
        db.session.add_all(
            [Item(name="alpha"), Item(name="beta"), Item(name="alphabet")]
        )
        db.session.commit()

        with app.test_request_context(
            query_string=make_datatable_query(**{"search[value]": "alpha"})
        ):
            table = SQLServerSideDataTable(
                request=request,
                backend=db,
                target_model="Item",
                model_mapping={"Item": Item},
            )

        result = table.output_result()
        assert result == {
            "draw": 3,
            "recordsTotal": 3,
            "recordsFiltered": 2,
            "data": [{"id": 1, "name": "alpha"}, {"id": 3, "name": "alphabet"}],
        }


def test_sql_datatable_supports_column_filters_custom_filters_and_hooks():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db = SQLAlchemy(app)

    class Item(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(40), nullable=False)

        def to_data_dict(self):
            return {"id": self.id, "name": self.name}

    with app.app_context():
        db.create_all()
        db.session.add_all(
            [Item(name="alpha"), Item(name="beta"), Item(name="alphabet")]
        )
        db.session.commit()

        custom_calls = []

        def custom_filter(col, value, is_regex):
            custom_calls.append((value, is_regex))
            return [col.like(f"{value}%")]

        with app.test_request_context(
            query_string=make_datatable_query(
                **{
                    "columns[0][search][value]": "alpha",
                    "columns[0][search][regex]": "false",
                    "order[0][dir]": "desc",
                }
            )
        ):
            table = SQLServerSideDataTable(
                request=request,
                backend=db,
                target_model="Item",
                model_mapping={"Item": Item},
                use_column_filters=True,
                custom_column_filters={"name": custom_filter},
                query_hook=lambda query: query.filter(Item.id > 0),
            )

        assert [row["name"] for row in table.results] == ["alphabet", "alpha"]
        assert custom_calls == [("alpha", False)]
        assert table.total_filtered == 2


def test_sql_default_filter_supports_comparison_regex_and_null_operators():
    name = column("name")

    assert str(SQLServerSideDataTable.default_filter(name, "A", False)[0]) == (
        "name LIKE :name_1"
    )
    assert str(SQLServerSideDataTable.default_filter(name, "> B", False)[0]) == (
        "name > :name_1"
    )
    assert len(SQLServerSideDataTable.default_filter(name, "A<>Z", False)) == 2
    assert str(SQLServerSideDataTable.default_filter(name, "~", False)[0]) == (
        "name IS NULL"
    )
    assert str(SQLServerSideDataTable.default_filter(name, "~A", False)[0]) == (
        "name NOT LIKE :name_1"
    )
    assert SQLServerSideDataTable.default_filter(name, "[", True)
    assert SQLServerSideDataTable.default_filter(name, "A.*", True)
    assert SQLServerSideDataTable.default_filter(name, "~A.*", True)


def test_elasticsearch_datatable_builds_search_and_fetches_results():
    class Search:
        def __init__(self):
            self.offset = 0
            self.size = 0

        def skip(self, offset):
            self.offset = offset
            return self

        def limit(self, size):
            self.size = size
            return self

        def __iter__(self):
            return iter([{"name": "alpha"}])

    class Index:
        def __init__(self):
            self.search = Search()
            self.count_calls = []

        def count(self, **kwargs):
            self.count_calls.append(kwargs)
            return 1 if kwargs else 2

        def find(self, **kwargs):
            return self.search

    index = Index()
    backend = SimpleNamespace(es=SimpleNamespace(items=index))
    app = Flask(__name__)

    with app.test_request_context(
        query_string=make_datatable_query(**{"search[value]": "alpha"})
    ):
        table = ESServerSideDataTable(
            request=request,
            backend=backend,
            index="items",
        )

    assert table.total == 2
    assert table.total_filtered == 1
    assert table.results == [{"name": "alpha"}]
    assert index.search.offset == 0
    assert index.search.size == 10
    assert index.count_calls[1]["regexp"] is True
