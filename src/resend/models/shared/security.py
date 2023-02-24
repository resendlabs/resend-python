from __future__ import annotations
import dataclasses



@dataclasses.dataclass
class SchemeBearerAuth:
    authorization: str = dataclasses.field(metadata={'security': { 'field_name': 'Authorization' }})
    

@dataclasses.dataclass
class Security:
    bearer_auth: SchemeBearerAuth = dataclasses.field(metadata={'security': { 'scheme': True, 'type': 'http', 'sub_type': 'bearer' }})
    