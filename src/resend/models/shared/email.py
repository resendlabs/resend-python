from __future__ import annotations
import dataclasses
from dataclasses_json import Undefined, dataclass_json
from resend import utils
from typing import Optional


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclasses.dataclass
class Email:
    from_: str = dataclasses.field(metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('from') }})
    subject: str = dataclasses.field(metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('subject') }})
    to: str = dataclasses.field(metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('to') }})
    bcc: Optional[str] = dataclasses.field(default=None, metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('bcc'), 'exclude': lambda f: f is None }})
    cc: Optional[str] = dataclasses.field(default=None, metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('cc'), 'exclude': lambda f: f is None }})
    html: Optional[str] = dataclasses.field(default=None, metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('html'), 'exclude': lambda f: f is None }})
    reply_to: Optional[str] = dataclasses.field(default=None, metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('reply_to'), 'exclude': lambda f: f is None }})
    text: Optional[str] = dataclasses.field(default=None, metadata={'dataclasses_json': { 'letter_case': utils.get_field_name('text'), 'exclude': lambda f: f is None }})
    