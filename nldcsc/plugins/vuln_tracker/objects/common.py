from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import dataclass_json, config as json_config

from nldcsc.generic.utils import exclude_optional_dict
from nldcsc.plugins.vuln_tracker.objects.data_class_validations import Validations


@dataclass_json
@dataclass
class CVSS2(Validations):
    """i.a.w https://www.first.org/cvss/cvss-v2.0.json"""

    version: str
    vectorString: str
    baseScore: int

    accessVector: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    accessComplexity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    authentication: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    confidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    integrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    availabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploitability: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    remediationLevel: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    reportConfidence: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    temporalScore: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    collateralDamagePotential: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    targetDistribution: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    confidentialityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    integrityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    availabilityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    environmentalScore: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class CVSS3(Validations):
    version: str
    vectorString: str
    baseScore: int
    baseSeverity: str

    attackVector: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    attackComplexity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    privilegesRequired: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    userInteraction: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    scope: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    confidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    integrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    availabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploitCodeMaturity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    remediationLevel: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    reportConfidence: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    temporalScore: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    temporalSeverity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    confidentialityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    integrityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    availabilityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAttackVector: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAttackComplexity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedPrivilegesRequired: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedUserInteraction: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedScope: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedConfidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedIntegrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAvailabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    environmentalScore: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    environmentalSeverity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )

    # temp fixes for msrc report failing to parse due to the fact they are using the wrong format....
    environmentalsScore: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    environmentalsSeverity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class CVSS30(CVSS3):
    """i.a.w. https://www.first.org/cvss/cvss-v3.0.json"""

    pass


@dataclass_json
@dataclass
class CVSS31(CVSS3):
    """i.a.w. https://www.first.org/cvss/cvss-v3.1.json"""

    pass


@dataclass_json
@dataclass
class CVSS4(Validations):
    version: str
    vectorString: str
    baseScore: float
    baseSeverity: str

    attackVector: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    attackComplexity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    attackRequirements: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    privilegesRequired: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    userInteraction: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnConfidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnIntegrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnAvailabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    subConfidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    subIntegrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    subAvailabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    exploitMaturity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    confidentialityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    integrityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    availabilityRequirement: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAttackVector: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAttackComplexity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedAttackRequirements: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedPrivilegesRequired: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedUserInteraction: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedVulnConfidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedVulnIntegrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedVulnAvailabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedSubConfidentialityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedSubIntegrityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    modifiedSubAvailabilityImpact: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    Safety: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    Automatable: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    Recovery: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    valueDensity: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    vulnerabilityResponseEffort: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )
    providerUrgency: Optional[str] = field(
        metadata=json_config(exclude=exclude_optional_dict), default=None
    )


@dataclass_json
@dataclass
class CVSS40(CVSS4):
    """i.a.w. https://www.first.org/cvss/cvss-v4.0.json"""

    pass
