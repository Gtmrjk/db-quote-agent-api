# Deploy Without Render

## Recommended: Koyeb

Koyeb can deploy this API from GitHub using the existing `Dockerfile`.

1. Open [Koyeb](https://app.koyeb.com/).
2. Create a new app or service.
3. Choose GitHub as the deployment source.
4. Select `Gtmrjk/db-quote-agent-api`.
5. Choose Dockerfile deployment.
6. Set the service type to web service.
7. Add this environment variable:

```text
API_KEY=your-long-secret-token
```

8. Deploy.

After deploy, test:

```bash
curl -X POST https://YOUR-KOYEB-DOMAIN/generate \
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

## Backup Option: Railway

Railway can also deploy this Dockerfile from GitHub. Configure `/health` as the healthcheck path and add the same `API_KEY` environment variable.

## Not Recommended

Vercel and Netlify are not good fits for this project because the API uses Playwright/Chromium, which needs a container-style backend.
