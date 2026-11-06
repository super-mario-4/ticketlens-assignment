from typing import Literal

from pydantic import BaseModel

ComponentStatus = Literal["ok", "unavailable"]


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadinessComponents(BaseModel):
    postgres: ComponentStatus
    elasticsearch: ComponentStatus


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    components: ReadinessComponents
