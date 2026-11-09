from dataclasses import dataclass
from datetime import datetime

from nldcsc.http_apis.fbf.objects import FBFInfo, NCSCFeedUpdateSquence
from nldcsc.http_apis.mailgun.mail_objects import Email, EmailAttachment
from nldcsc.http_apis.nexpose.objects import (
    NexposeAssetType,
    NexposeResource,
    NexposeVulnerability,
)
from nldcsc.plugins.hybrid_analysis.objects import (
    Certificate,
    HybridAnalysisHashRecord,
    Process,
    SignatureMatch,
    Stream,
)
from nldcsc.plugins.vuln_tracker.objects.common import CVSS31, CVSS40
from nldcsc.plugins.vuln_tracker.objects.csaf import CSAF, Document
from nldcsc.plugins.vuln_tracker.objects.cve_record import CveRecord
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations
from nldcsc.plugins.vuln_tracker.objects.nist import Nist
from nldcsc.plugins.vuln_tracker.objects.osv import OSV, Affected, Range
from nldcsc.plugins.whoisxml.objects.whois import (
    NameServers,
    RegistryData,
    WhoisRecord,
    WhoisReverseIPRecord,
)


def test_vulnerability_score_models_round_trip_nested_data():
    score = CVSS31(
        version="3.1",
        vectorString="CVSS:3.1/AV:N/AC:L",
        baseScore=8.1,
        baseSeverity="HIGH",
        attackVector="NETWORK",
    )
    serialized = score.to_dict()
    restored = CVSS31.from_dict(serialized)

    assert restored.baseScore == 8
    assert restored.to_dict()["attackVector"] == "NETWORK"
    assert CVSS40(
        version="4.0", vectorString="CVSS:4.0/AV:N", baseScore=8.0, baseSeverity="HIGH"
    ).baseScore == 8.0


def test_osv_builds_nested_objects_and_exposes_identifier_properties():
    advisory = OSV(
        id="GHSA-1234",
        modified="2025-01-01T00:00:00Z",
        affected=[
            {
                "package": {"ecosystem": "PyPI", "name": "sample"},
                "ranges": [
                    {
                        "type": "ECOSYSTEM",
                        "events": [{"introduced": "1.0"}, {"fixed": "1.2"}],
                    }
                ],
                "versions": ["1.0", "1.1"],
            }
        ],
        references=[{"type": "WEB", "url": "https://example.test"}],
        credits=[{"name": "Researcher"}],
    )

    assert advisory.cve_id == "GHSA-1234"
    assert advisory.publisher == "GHSA"
    assert "OSV(GHSA[GHSA-1234])" == repr(advisory)
    assert isinstance(advisory.affected[0], Affected)
    assert isinstance(advisory.affected[0].ranges[0], Range)
    assert advisory.affected[0].ranges[0].events[1].fixed == "1.2"
    assert advisory.to_dict()["affected"][0]["package"]["name"] == "sample"


def test_csaf_builds_nested_document_and_renders_identity():
    document = {
        "category": "csaf_security_advisory",
        "csaf_version": "2.0",
        "title": "Advisory",
        "publisher": {"category": "vendor", "name": "Example", "namespace": "example"},
        "tracking": {
            "current_release_date": "2025-01-01T00:00:00Z",
            "id": "ADV-1",
            "initial_release_date": "2024-12-01T00:00:00Z",
            "revision_history": [{"date": "2025-01-01", "number": "1", "summary": "Update"}],
            "status": "final",
            "version": "1",
            "generator": {"engine": {"name": "test"}},
        },
        "references": [{"summary": "Details", "url": "https://example.test"}],
        "distribution": {"text": "public", "tlp": {"label": "WHITE"}},
    }

    advisory = CSAF(document=document)

    assert isinstance(advisory.document, Document)
    assert advisory.cve_id == "ADV-1"
    assert advisory.publisher == "Example"
    assert "CSAF(Example[ADV-1])" == repr(advisory)
    assert advisory.document.tracking.generator.engine.name == "test"
    assert advisory.document.references[0].url == "https://example.test"


def test_cve_record_builds_cna_data_and_rss_representation():
    record = CveRecord(
        dataType="CVE_RECORD",
        dataVersion="5.1",
        cveMetadata={
            "cveId": "CVE-2025-1234",
            "assignerOrgId": "org",
            "state": "PUBLISHED",
        },
        containers={
            "cna": {
                "providerMetadata": {"orgId": "org", "shortName": "Example"},
                "descriptions": [{"lang": "en", "value": "Issue description"}],
                "affected": [
                    {
                        "vendor": "Example",
                        "product": "Widget",
                        "versions": [{"version": "1.0", "status": "affected"}],
                    }
                ],
                "references": [{"url": "https://example.test/advisory"}],
                "title": "Widget issue",
            }
        },
    )

    assert record.cve_id == "CVE-2025-1234"
    assert record.state == "PUBLISHED"
    assert record.containers.cna.title == "Widget issue"
    assert record.to_rss_format() == {
        "cve_id": "CVE-2025-1234",
        "state": "PUBLISHED",
        "shortName": "Example",
        "product": "Widget",
        "vendor": "Example",
        "versions": "[{'status': 'affected', 'version': '1.0'}]",
        "descriptions": "['Issue description']",
        "references": "['https://example.test/advisory']",
    }
    assert "CVE_RECORD(PUBLISHED[CVE-2025-1234])" == repr(record)


def test_nist_cve_schema_nested_values_and_serialization():
    advisory = Nist(
        id="CVE-2025-42",
        published="2025-01-01",
        lastModified="2025-01-02",
        references=[{"url": "https://example.test"}],
        descriptions=[{"lang": "en", "value": "Issue"}],
        metrics={
            "cvssMetricV31": [
                {
                    "source": "nvd",
                    "type": "Primary",
                    "cvssData": {
                        "version": "3.1",
                        "vectorString": "CVSS:3.1/AV:N",
                        "baseScore": 7.5,
                        "baseSeverity": "HIGH",
                    },
                }
            ]
        },
        weaknesses=[
            {
                "source": "nvd",
                "type": "Primary",
                "description": [{"lang": "en", "value": "CWE-79"}],
            }
        ],
    )

    assert advisory.id == "CVE-2025-42"
    assert advisory.metrics.cvssMetricV31[0].cvssData.baseScore == 7.5
    assert advisory.weaknesses[0].description[0].value == "CWE-79"
    assert advisory.to_dict()["id"] == "CVE-2025-42"


def test_hybrid_analysis_records_construct_nested_models():
    record = HybridAnalysisHashRecord.from_dict(
        {
            "sha256": "abc",
            "analysis_start_time": 1735689600,
            "certificates": [{"owner": "Example", "valid_from": 1735689600}],
            "processes": [
                {
                    "name": "sample",
                    "streams": [
                        {
                            "uid": "stream-1",
                            "matched_signatures": [{"id": "sig-1", "value": "match"}],
                        }
                    ],
                }
            ],
        }
    )

    assert record.certificates[0].owner == "Example"
    assert record.analysis_start_time.timestamp() == 1735689600
    assert isinstance(record.processes[0], Process)
    assert isinstance(record.processes[0].streams[0], Stream)
    assert record.processes[0].streams[0].matched_signatures[0] == SignatureMatch(
        id="sig-1", value="match"
    )


def test_whois_nested_records_and_date_helpers():
    record = WhoisRecord(
        domainName="example.test",
        registrarName="Example Registrar",
        nameServers={"hostNames": ["ns1.example.test"], "ips": ["192.0.2.1"]},
        registryData={
            "createdDate": "2025-05-12T00:00:00Z",
            "updatedDate": None,
            "expiresDate": None,
            "nameServers": {"hostNames": ["ns1.example.test"]},
        },
    )

    assert isinstance(record.nameServers, NameServers)
    assert isinstance(record.registryData, RegistryData)
    assert record.domain_is_available is True
    assert record.get_registrar == "Example Registrar"
    assert record.get_created_date == 1747008000
    assert record.get_updated_date == 0
    assert record.get_expires_date == 0
    assert WhoisRecord(domainAvailability="UNAVAILABLE").domain_is_available is False
    assert WhoisReverseIPRecord(name="example.test").to_dict()["name"] == "example.test"


def test_http_api_schema_models_serialize_field_names_and_defaults():
    info = FBFInfo.from_dict(
        {"ApplicationName": "feed", "ApplicationVersion": "2"}
    )
    update = NCSCFeedUpdateSquence.from_dict(
        {"timestamp": 10, "updates": [{"name": "feed", "count": 2}]}
    )
    email = Email(
        From="sender@example.test",
        To="receiver@example.test",
        Subject="Notice",
        TemplateData={"name": "Ada"},
        Attachments=[EmailAttachment(Name="file.txt", Content="YQ==")],
    )

    assert info.application_name == "feed"
    assert info.to_dict() == {
        "ApplicationName": "feed",
        "ApplicationVersion": "2",
    }
    assert update.updates[0].count == 2
    assert email.Attachments[0].ContentType == "text/plain"
    assert email.model_dump()["TemplateData"] == {"name": "Ada"}


def test_nexpose_resource_and_vulnerability_models_decode_enums():
    resource = NexposeResource.from_dict(
        {
            "id": 9,
            "type": "physical",
            "addresses": [{"ip": "192.0.2.9"}],
            "vulnerabilities": {"critical": 1, "total": 1},
        }
    )
    vulnerability = NexposeVulnerability.from_dict(
        {"id": "vuln-1", "severity": "Critical", "cves": ["CVE-2025-1"]}
    )

    assert resource.type == NexposeAssetType.PHYSICAL
    assert resource.addresses[0].ip == "192.0.2.9"
    assert resource.vulnerabilities.critical == 1
    assert vulnerability.severity.value == "Critical"
    assert vulnerability.cves == ["CVE-2025-1"]


def test_validation_base_runs_declared_field_transformers():
    @dataclass
    class Validated(Validations):
        value: str

        def validate_value(self, value, field):
            return value.strip().upper()

    assert Validated("  safe ").value == "SAFE"
