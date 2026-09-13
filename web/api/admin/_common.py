from typing import Annotated

from fastapi import Form

# A bulk form posts the ticked row ids under one name; an untouched form posts none.
type SelectedIds = Annotated[list[int] | None, Form(alias="ids")]
