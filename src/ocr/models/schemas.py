from pydantic import BaseModel, Field
from typing import Annotated, Literal, Union

class Circuit(BaseModel):
    tag: str = Field(description="Identifier as printed (e.g., '10Q1', '20F5.1')")
    rating: str = Field(description="Rating as printed (e.g., '4x10A/30mA')")
    description: str = Field(description="Functional name of the circuit/equipment")

class Legend(BaseModel):
    issuing_company: str = Field(description="Installer/planner/utility company")
    project_site: str = Field(description="Project/site: building name and full address")
    distribution_board: str = Field(description="Board/panel designation and location")
    circuits: list[Circuit] = Field(description="Ordered list of schedule lines")

class LegendUpdate(BaseModel):
    response_type: Literal["legend_update"]
    batch_summary: str = Field(description="Several sentences summary of content of current pages")
    legend: Legend = Field(description="Legend updated with content from current pages")

class HaltSignal(BaseModel):
    response_type: Literal["halt_signal"]
    error_message: str = Field(description="Detailed explanation of why the fallback was called.")

LLMResponse = Annotated[
    Union[LegendUpdate, HaltSignal],
    Field(discriminator="response_type")
]
