from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class WhoisReverseNSRecord:
    name: str = ""
    first_seen: int = 0
    last_visit: int = 0
