from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    role : str

    content: str | list[dict] | None = None


class ChatCompletionRequest(BaseModel):
    model : str
    messages : list[Message]
    temperature : float | None = None
    max_tokens : int | None = None
    stream : bool | None = None
    

    model_config = ConfigDict(extra="allow")

