import base64

from fastapi import Depends, FastAPI, Header, HTTPException, Response

from app.agent import BhaskarQuoteAgent, QuoteAgentError
from app.schemas import QuoteRequest, QuoteResponse
from app.settings import Settings, get_settings

app = FastAPI(
    title="DB Quote Image Agent API",
    version="1.0.0",
    description="API wrapper around the browser-only DB/OneCMS quote image generator.",
)

agent = BhaskarQuoteAgent(get_settings())


def require_api_key(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> None:
    if not settings.api_key:
        return
    expected = f"Bearer {settings.api_key}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid API key.")


@app.on_event("shutdown")
async def shutdown() -> None:
    await agent.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/generate",
    response_model=QuoteResponse,
    dependencies=[Depends(require_api_key)],
)
async def generate_quote(request: QuoteRequest) -> QuoteResponse | Response:
    try:
        image = await agent.generate(request)
    except QuoteAgentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    if request.output == "png":
        return Response(content=image.content, media_type=image.mime_type)

    return QuoteResponse(
        mime_type=image.mime_type,
        image_base64=base64.b64encode(image.content).decode("ascii"),
        source=image.source,
    )
