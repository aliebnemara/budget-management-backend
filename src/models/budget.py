from pydantic import BaseModel, Field
from datetime import date

class defaultBudgetModel(BaseModel):
    compare_year:int=Field(min=2024, description="Compare year should be greater than 2024")
    ramadan_CY: date=Field(description="Should be a Date")
    ramadan_BY: date=Field(description="Should be a Date")
    ramadan_daycount_CY:int=Field(min=1, description="Day count should be at least 1")
    ramadan_daycount_BY:int=Field(min=1, description="Day count should be at least 1")
    muharram_CY: date=Field(description="Should be a Date")
    muharram_BY: date=Field(description="Should be a Date")
    muharram_daycount_CY:int=Field(min=1, description="Day count should be at least 1")
    muharram_daycount_BY:int=Field(min=1, description="Day count should be at least 1")
    eid2_CY: date=Field(description="Should be a Date")
    eid2_BY: date=Field(description="Should be a Date")

