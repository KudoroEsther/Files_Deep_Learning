from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api=os.getenv('api_key')
client = genai.Client(api_key=api)


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)