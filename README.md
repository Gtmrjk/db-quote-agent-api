# DB Quote Image Agent API

This service wraps a bundled browser-only DB-style quote image generator. The API uses Playwright to open the local canvas tool, fill the quote fields, and return the generated image.

## API

```bash
curl -X POST https://YOUR-RENDER-URL/generate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "quote": "The problem is the path.",
    "author": "DB",
    "designation": "Editor",
    "brand": "bhaskar",
    "image_format": "jpeg",
    "output": "base64"
  }'
```

For raw image bytes, set `"output": "png"`. Use `"image_format": "jpeg"` or `"image_format": "png"` to choose the generated image format.

## Environment Variables

| Name | Required | Purpose |
| --- | --- | --- |
| `API_KEY` | Recommended | Bearer token for your API. |
| `QUOTE_TOOL_FILE` | Optional | Path to the bundled generator HTML. Defaults to `quote_tool/index.html`. |

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

## Notes

The API currently supports the bundled local generator fields: quote, author, designation, brand, optional uploaded base64 image, and JPEG/PNG output.
