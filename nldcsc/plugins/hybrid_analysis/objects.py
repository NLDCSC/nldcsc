from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Certificate:
    owner: Optional[str] = None
    issuer: Optional[str] = None
    serial_number: Optional[str] = None
    md5: Optional[str] = None
    sha1: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


@dataclass_json
@dataclass
class ExtractedFile:
    name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    md5: Optional[str] = None
    type_tags: Optional[List[str]] = None
    description: Optional[str] = None
    runtime_process: Optional[str] = None
    threat_level: Optional[int] = None
    threat_level_readable: Optional[str] = None
    av_label: Optional[str] = None
    av_matched: Optional[int] = None
    av_total: Optional[int] = None
    file_available_to_download: Optional[bool] = None


@dataclass_json
@dataclass
class FileMetadata:
    file_compositions: Optional[List[str]] = None
    imported_objects: Optional[List[str]] = None
    file_analysis: Optional[List[str]] = None
    total_file_compositions_imports: Optional[int] = None


@dataclass_json
@dataclass
class FileAccess:
    type: Optional[str] = None
    path: Optional[str] = None
    mask: Optional[str] = None


@dataclass_json
@dataclass
class CreatedFile:
    file: Optional[str] = None
    null_byte: Optional[bool] = None


@dataclass_json
@dataclass
class RegistryEntry:
    operation: Optional[str] = None
    path: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None
    status_human_readable: Optional[str] = None


@dataclass_json
@dataclass
class Handle:
    id: Optional[int] = None
    type: Optional[str] = None
    path: Optional[str] = None


@dataclass_json
@dataclass
class SignatureMatch:
    id: Optional[str] = None
    value: Optional[str] = None


@dataclass_json
@dataclass
class Stream:
    uid: Optional[str] = None
    file_name: Optional[str] = None
    human_keywords: Optional[str] = None
    instructions: Optional[List[str]] = None
    executed: Optional[bool] = None
    matched_signatures: Optional[List[SignatureMatch]] = None


@dataclass_json
@dataclass
class ScriptParameter:
    name: Optional[str] = None
    value: Optional[str] = None
    comment: Optional[str] = None
    argument_number: Optional[int] = None
    meaning: Optional[str] = None


@dataclass_json
@dataclass
class ScriptCall:
    cls_id: Optional[str] = None
    dispatch_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    parameters: Optional[List[ScriptParameter]] = None
    matched_malicious_signatures: Optional[List[str]] = None


@dataclass_json
@dataclass
class ProcessFlag:
    name: Optional[str] = None
    data: Optional[str] = None


@dataclass_json
@dataclass
class AmsiCall:
    app_name: Optional[str] = None
    filename: Optional[str] = None
    raw_script_content: Optional[str] = None


@dataclass_json
@dataclass
class Module:
    path: Optional[str] = None
    base: Optional[str] = None
    interesting: Optional[bool] = None


@dataclass_json
@dataclass
class Process:
    uid: Optional[str] = None
    parentuid: Optional[str] = None
    name: Optional[str] = None
    normalized_path: Optional[str] = None
    command_line: Optional[str] = None
    sha256: Optional[str] = None
    av_label: Optional[str] = None
    av_matched: Optional[int] = None
    av_total: Optional[int] = None
    pid: Optional[str] = None
    icon: Optional[str] = None
    file_accesses: Optional[List[FileAccess]] = None
    created_files: Optional[List[CreatedFile]] = None
    registry: Optional[List[RegistryEntry]] = None
    mutants: Optional[List[str]] = None
    handles: Optional[List[Handle]] = None
    streams: Optional[List[Stream]] = None
    script_calls: Optional[List[ScriptCall]] = None
    process_flags: Optional[List[ProcessFlag]] = None
    amsi_calls: Optional[List[AmsiCall]] = None
    modules: Optional[List[Module]] = None


@dataclass_json
@dataclass
class MitreAttackParent:
    technique: Optional[str] = None
    attck_id: Optional[str] = None
    attck_id_wiki: Optional[str] = None


@dataclass_json
@dataclass
class MitreAttack:
    tactic: Optional[str] = None
    technique: Optional[str] = None
    attck_id: Optional[str] = None
    attck_id_wiki: Optional[str] = None
    parent: Optional[MitreAttackParent] = None
    malicious_identifiers_count: Optional[int] = None
    malicious_identifiers: Optional[List[str]] = None
    suspicious_identifiers_count: Optional[int] = None
    suspicious_identifiers: Optional[List[str]] = None
    informative_identifiers_count: Optional[int] = None
    informative_identifiers: Optional[List[str]] = None


@dataclass_json
@dataclass
class Signature:
    threat_level: Optional[int] = None
    threat_level_human: Optional[str] = None
    category: Optional[str] = None
    identifier: Optional[str] = None
    type: Optional[int] = None
    relevance: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    attck_id: Optional[str] = None
    capec_id: Optional[str] = None
    attck_id_wiki: Optional[str] = None


@dataclass_json
@dataclass
class Submission:
    submission_id: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass_json
@dataclass
class MLModelData:
    id: Optional[str] = None
    value: Optional[str] = None


@dataclass_json
@dataclass
class MachineLearningModel:
    name: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None
    data: Optional[List[MLModelData]] = None
    created_at: Optional[datetime] = None


@dataclass_json
@dataclass
class ExecutableProcessMemoryAnalysis:
    filename: Optional[str] = None
    address: Optional[str] = None
    flags: Optional[str] = None
    file_process: Optional[str] = None
    file_process_pid: Optional[int] = None
    file_process_sha256: Optional[str] = None
    file_process_disc_pathway: Optional[str] = None
    verdict: Optional[str] = None


@dataclass_json
@dataclass
class AnalysisRelatedUrl:
    url: Optional[str] = None
    verdict: Optional[str] = None
    type: Optional[str] = None


@dataclass_json
@dataclass
class CrowdstrikeAI:
    executable_process_memory_analysis: Optional[
        List[ExecutableProcessMemoryAnalysis]
    ] = None
    analysis_related_urls: Optional[List[AnalysisRelatedUrl]] = None


@dataclass_json
@dataclass
class HybridAnalysisHashRecord:
    job_id: Optional[str] = None
    environment_id: Optional[int] = None
    environment_description: Optional[str] = None
    size: Optional[int] = None
    type: Optional[str] = None
    type_short: Optional[List[str]] = None
    target_url: Optional[str] = None
    state: Optional[str] = None
    error_type: Optional[str] = None
    error_origin: Optional[str] = None
    submit_name: Optional[str] = None
    md5: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    sha512: Optional[str] = None
    ssdeep: Optional[str] = None
    imphash: Optional[str] = None
    entrypoint: Optional[str] = None
    entrypoint_section: Optional[str] = None
    image_base: Optional[str] = None
    subsystem: Optional[str] = None
    image_file_characteristics: Optional[List[str]] = None
    dll_characteristics: Optional[List[str]] = None
    major_os_version: Optional[int] = None
    minor_os_version: Optional[int] = None
    av_detect: Optional[int] = None
    vx_family: Optional[str] = None
    url_analysis: Optional[bool] = None
    analysis_start_time: Optional[datetime] = None
    threat_score: Optional[int] = None
    interesting: Optional[bool] = None
    threat_level: Optional[int] = None
    verdict: Optional[str] = None
    certificates: Optional[List[Certificate]] = None
    is_certificates_valid: Optional[bool] = None
    certificates_validation_message: Optional[str] = None
    domains: Optional[List[str]] = None
    compromised_hosts: Optional[List[str]] = None
    hosts: Optional[List[str]] = None
    total_network_connections: Optional[int] = None
    total_processes: Optional[int] = None
    total_signatures: Optional[int] = None
    extracted_files: Optional[List[ExtractedFile]] = None
    file_metadata: Optional[FileMetadata] = None
    processes: Optional[List[Process]] = None
    mitre_attcks: Optional[List[MitreAttack]] = None
    network_mode: Optional[str] = None
    signatures: Optional[List[Signature]] = None
    classification_tags: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    submissions: Optional[List[Submission]] = None
    machine_learning_models: Optional[List[MachineLearningModel]] = None
    crowdstrike_ai: Optional[CrowdstrikeAI] = None
    validation_errors: Optional[List[str]] = None
