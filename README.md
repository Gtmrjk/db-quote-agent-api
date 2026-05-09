# DB Quote Image Agent API

This service wraps the browser-only DB/OneCMS quote image generator at:

https://www.bhaskar.com/onecms/quote-image-generator

The page is behind OneCMS login, so the API uses Playwright to sign in, drive the generator UI, and return the generated image.

## API

```bash
curl -X POST https://YOUR-RENDER-URL/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "quote": "The problem is the path.",
    "author": "DB",
    "output": "base64"
  }'
```

For raw image bytes, set `"output": "png"`.

## Environment Variables

| Name | Required | Purpose |
| --- | --- | --- |
| `API_KEY` | Recommended | Bearer token for your API. |
| `ONECMS_QUOTE_URL` | Yes | Defaults to the Bhaskar quote generator URL. |
| `ONECMS_USERNAME` | Yes, unless storage state is supplied | OneCMS username. |
| `ONECMS_PASSWORD` | Yes, unless storage state is supplied | OneCMS password. |
| `ONECMS_STORAGE_STATE_JSON` | Optional | Playwright storage state JSON for accounts that need OTP/session reuse. |

If the OneCMS account requires OTP, log in once locally, export Playwright storage state, and paste that JSON into `ONECMS_STORAGE_STATE_JSON` on Render.

```bash
source .venv/bin/activate
playwright install chromium
python scripts/export_storage_state.py
```

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Deploy To Render

1. Push this repository to GitHub.
2. In Render, create a new Blueprint from the GitHub repository.
3. Render will read `render.yaml` and build the Docker service.
4. Add the secret environment variables in Render:
   - `API_KEY`
   - `ONECMS_USERNAME`
   - `ONECMS_PASSWORD`
   - optionally `ONECMS_STORAGE_STATE_JSON`

## Notes

The generator UI is not public, so the selectors are intentionally flexible. After a successful authenticated inspection, tighten the selectors in `app/agent.py` if the post-login page has stable field names.
