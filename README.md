# silly-merchants-for-safe-hackathon
Silly Merchants Agents Game for Safe Hackathon

## Credentials

The project supports two LLM providers:
1. Google Cloud Vertex AI (Gemini) - Primary
2. OpenRouter - Fallback

To use Gemini:
1. Place your Google Cloud service account key in `credentials/`
2. Update GOOGLE_APPLICATION_CREDENTIALS in `.env`

If Gemini credentials are not available, the system will automatically fall back to OpenRouter.
