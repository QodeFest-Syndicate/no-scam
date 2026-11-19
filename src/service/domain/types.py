from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Incident = Literal["clicked_link", "entered_credentials", "sent_money", "shared_info"]
Engine = Literal["rules", "qwen"]
Level = Literal["no_signals", "pause"]
CheckStatus = Literal["completed", "not_run", "unavailable"]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class MessageIn(ApiModel):
    sender: str = Field(min_length=1, max_length=120)
    familiar_contact: bool = True
    channel: str = Field(default="whatsapp", min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=2000)


class AssessRequest(ApiModel):
    message: MessageIn


class Signal(ApiModel):
    id: str
    icon: str
    title: str
    detail: str


class Check(ApiModel):
    id: str
    label: str
    source: str
    status: CheckStatus
    result: str


class Assessment(ApiModel):
    level: Level
    engine: Engine
    signals: list[Signal]
    summary: str
    disclaimer: str
    ai_available: bool
    checks: list[Check] = Field(default_factory=list)


class AssessResponse(ApiModel):
    assessment: Assessment


class RecoveryStep(ApiModel):
    order: int
    title: str
    detail: str
    urgent: bool = False


class RecoveryRequest(ApiModel):
    incident: Incident


class RecoveryResponse(ApiModel):
    incident: str
    steps: list[RecoveryStep]
    disclaimer: str


class Scenario(ApiModel):
    id: str
    label: str
    message: MessageIn


class ScenariosResponse(ApiModel):
    scenarios: list[Scenario]


class MetaResponse(ApiModel):
    service: str
    engine: str
    ai_enabled: bool
    demo_data_only: bool
    version: str
