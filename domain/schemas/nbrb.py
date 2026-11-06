from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class NBRBRateSchema(BaseModel):
    cur_abbr: str = Field(alias="Cur_Abbreviation")
    cur_scale: int = Field(alias="Cur_Scale", gt=0)
    cur_offrate: Decimal = Field(
        alias="Cur_OfficialRate", gt=0, max_digits=12, decimal_places=6
    )
    date: datetime = Field(alias="Date")
