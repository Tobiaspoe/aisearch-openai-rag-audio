import logging
import os
import asyncio
from pathlib import Path

from aiohttp import web
import aiohttp_cors
from dotenv import load_dotenv
import openai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

# --- Health Check Endpoint ---
async def health_check(request):
    return web.json_response({"status": "healthy", "service": "FinMatch API"})

# --- App Factory ---
async def create_app():
    # Load environment variables
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading .env")
        load_dotenv()
    else:
        logger.info("Running in production mode")

    # Standardize API keys
    openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("Missing OpenAI API key in environment variables")

    app = web.Application()

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
        )
    })

    # --- Health Check ---
    app.router.add_get("/health", health_check)

    # --- /chat endpoint ---
    async def chat_handler(request):
        try:
            data = await request.json()
            user_input = data.get("user_input", "")

            if not user_input:
                return web.json_response({"error": "user_input is required"}, status=400)

            response = openai.ChatCompletion.create(
                api_key=openai_api_key,
                api_base=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1"),
                model=os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4"),
                messages=[
                    {"role": "system", "content": "You are a helpful financial assistant."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )

            answer = response['choices'][0]['message']['content']
            return web.json_response({"response": answer})

        except Exception as e:
            logger.error(f"/chat error: {e}", exc_info=True)
            return web.json_response({"error": "Internal server error"}, status=500)

    app.router.add_post("/chat", chat_handler)

    # --- /realtime/transcribe endpoint ---
    async def transcribe_and_respond(request):
        try:
            data = await request.post()
            if 'audio' not in data:
                return web.json_response({"error": "Audio file is required"}, status=400)

            audio_file = data['audio'].file
            temp_path = Path("temp_audio.wav")

            try:
                with open(temp_path, "wb") as f:
                    f.write(audio_file.read())

                with open(temp_path, "rb") as audio_file:
                    transcription = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file,
                        api_key=openai_api_key,
                        api_base=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1")
                    )

                user_input = transcription["text"]

                response = openai.ChatCompletion.create(
                    api_key=openai_api_key,
                    api_base=os.environ.get("AZURE_OPENAI_ENDPOINT", "https://api.openai.com/v1"),
                    model=os.environ.get("AZURE_OPENAI_REALTIME_DEPLOYMENT", "gpt-4"),
                    messages=[
                        {"role": "system", "content": "You are a helpful real-time assistant."},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.7
                )

                answer = response['choices'][0]['message']['content']

                return web.json_response({
                    "transcription": user_input,
                    "response": answer
                })
            finally:
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"/realtime/transcribe error: {e}", exc_info=True)
            return web.json_response({"error": "Internal server error"}, status=500)

    app.router.add_post("/realtime/transcribe", transcribe_and_respond)

    # --- Serve static files ---
    possible_static_dirs = [
        Path(__file__).parent / "frontend" / "dist",  # Azure deployment structure
        Path(__file__).parent.parent / "app" / "frontend" / "dist",  # Local dev structure
        Path("frontend/dist"),  # Fallback
    ]

    static_dir = None
    for dir_path in possible_static_dirs:
        if dir_path.exists():
            static_dir = dir_path
            break

    if not static_dir:
        logger.warning("Static files directory not found")
    else:
        logger.info(f"Serving static files from: {static_dir}")
        index_file = static_dir / "index.html"

        async def index_handler(request):
            if not index_file.exists():
                raise web.HTTPNotFound(text="Index file not found")
            return web.FileResponse(index_file)

        app.router.add_static("/static", path=static_dir, name="static")
        app.router.add_get("/", index_handler)
        app.router.add_get("/{tail:.*}", index_handler)

    # Apply CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)

    return app

# --- Top-level app variable for Gunicorn ---
app = asyncio.run(create_app())

# --- Local development entry point ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port, access_log=logging.getLogger('aiohttp.access'))