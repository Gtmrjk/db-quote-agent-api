# Deploy For Free

## Recommended: Hugging Face Spaces

Hugging Face Spaces supports Docker apps and provides free CPU hardware. This repo is already configured for Docker Spaces with `app_port: 7860` in `README.md`.

1. Open [Hugging Face Spaces](https://huggingface.co/new-space).
2. Create a new Space.
3. Choose **Docker** as the SDK.
4. Keep it public if you want the free option.
5. Upload/push this repo's files to the Space repository.
6. Add this secret in Space Settings:

```text
API_KEY=your-long-secret-token
```

The app listens on port `7860`, which is the Hugging Face Spaces default for Docker apps.

After deploy, test:

```bash
curl -X POST https://YOUR-SPACE-SUBDOMAIN.hf.space/generate \
  -H "Authorization: Bearer YOUR_API_KEY" \
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

## Backup Option: Google Cloud Run

Google Cloud Run has an always-free allowance, but it requires a Google Cloud billing account. The same Dockerfile works there because it also respects the `PORT` environment variable.

## Not Recommended

Vercel and Netlify are not good fits for this project because the API uses Playwright/Chromium, which needs a container-style backend.
