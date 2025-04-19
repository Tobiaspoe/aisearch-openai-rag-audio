import logging
import os
import asyncio
from aiohttp import web
import aiohttp_cors
from dotenv import load_dotenv
import openai
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")

async def create_app():
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading .env")
        load_dotenv()

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

    # --- /chat endpoint ---
    async def chat_handler(request):
        try:
            data = await request.json()
            user_input = data.get("user_input", "")

            openai.api_key = os.environ["OPENAI_API_KEY"]
            openai.api_base = "https://api.openai.com/v1"

            response = openai.ChatCompletion.create(
                model="o1",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )

            answer = response['choices'][0]['message']['content']
            return web.json_response({"response": answer})

        except Exception as e:
            logger.error(f"/chat error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    app.router.add_post("/chat", chat_handler)

    # --- /realtime/transcribe endpoint ---
    async def transcribe_and_respond(request):
        try:
            data = await request.post()
            audio_file = data['audio'].file

            temp_path = Path("temp_audio.wav")
            with open(temp_path, "wb") as f:
                f.write(audio_file.read())

            with open(temp_path, "rb") as audio_file:
                transcription = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    api_key=os.environ["AZURE_OPENAI_API_KEY"],
                    api_base=os.environ["AZURE_OPENAI_ENDPOINT"]
                )

            temp_path.unlink()
            user_input = transcription["text"]

            openai.api_key = os.environ["OPENAI_API_KEY"]
            openai.api_base = "https://api.openai.com/v1"

            response = openai.ChatCompletion.create(
                model="o1",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_input}
                ]
            )

            answer = response['choices'][0]['message']['content']

            return web.json_response({
                "transcription": user_input,
                "response": answer
            })

        except Exception as e:
            logger.error(f"/realtime/transcribe error: {e}")
            return web.json_response({"error": str(e)}, status=500)

    app.router.add_post("/realtime/transcribe", transcribe_and_respond)

    # Apply CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)

    return app

app = asyncio.run(create_app())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)
