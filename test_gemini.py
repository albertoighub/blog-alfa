import os
from google import genai

# Conexión directa utilizando la variable de entorno GEMINI_API_KEY
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Responde únicamente: 'Conexión exitosa con News Internacional TEP'",
)

print(response.text)