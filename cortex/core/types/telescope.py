from pydantic import BaseModel
from pydantic.v1 import BaseModel as OldBaseModel


class TSModel(BaseModel):
    pass


class TSModelV1(OldBaseModel):
    pass
