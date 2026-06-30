from nldcsc.http_apis.viper.collections.bases import EndpointCollection
from nldcsc.http_apis.viper.collections.utils import as_object, signature_of
from nldcsc.http_apis.viper.objects import (
    ExtendedListOperator,
    IntOperator,
    SuccessResponse,
)

from .objects import (
    OTAP,
    OracleDBItem,
    OracleDBSearchResponse,
    OracleDBModifyResponse,
    OracleDBCreateResponse,
)


class OracleDBCollection(EndpointCollection, prefix="oracle_db"):
    @as_object(OracleDBSearchResponse)
    def search(
        self,
        page: int = 0,
        size: int = 50,
        sort: str = "db_id:asc",
        db_id: int | None = None,
        hostnames: list[str] | None = None,
        maintainers: list[str] | None = None,
        db_names: list[str] | None = None,
        otaps: list[OTAP | str] | None = None,
        db_id_operator: IntOperator = IntOperator.EQ,
        hostnames_operator: ExtendedListOperator = ExtendedListOperator.IN,
        maintainers_operator: ExtendedListOperator = ExtendedListOperator.IN,
        db_names_operator: ExtendedListOperator = ExtendedListOperator.IN,
        otaps_operator: ExtendedListOperator = ExtendedListOperator.IN,
    ):
        resource = "search"

        data = {
            "page": page,
            "size": size,
            "sort": sort,
        }

        if db_id is not None:
            data["db_id"] = db_id
            data["db_id_operator"] = db_id_operator

        if hostnames:
            data["hostname"] = hostnames
            data["hostname_operator"] = hostnames_operator

        if maintainers:
            data["maintainer"] = maintainers
            data["maintainer_operator"] = maintainers_operator

        if db_names:
            data["db_name"] = db_names
            data["db_name_operator"] = db_names_operator

        if otaps:
            data["otap"] = otaps
            data["otap_operator"] = otaps_operator

        return self.call(
            self.methods.GET,
            resource,
            params=data,
        )

    @signature_of(search)
    def iter_search(self, page: int = 0, size: int = 50, *args, **kwargs):
        yield from self.iter_endpoint(self.search, page, size, *args, **kwargs)

    @as_object(OracleDBCreateResponse)
    def create(self, oracle_dbs: list[OracleDBItem | dict]):
        resource = "create"

        return self.call(
            self.methods.POST,
            resource,
            json=[
                (
                    oracle_db.to_dict()
                    if isinstance(oracle_db, OracleDBItem)
                    else oracle_db
                )
                for oracle_db in oracle_dbs
            ],
        )

    @as_object(OracleDBModifyResponse)
    def modify(self, oracle_dbs: list[OracleDBItem]):
        resource = "modify"

        return self.call(
            self.methods.PUT,
            resource,
            json=[oracle_db.to_dict() for oracle_db in oracle_dbs],
        )

    @as_object(SuccessResponse, transform=SuccessResponse)
    def delete(self, ids: list[int]):
        resource = "delete"

        r = self.call(self.methods.DELETE, resource, unpack_response=False, json=ids)

        return r.status_code == 204
