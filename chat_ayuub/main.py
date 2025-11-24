from google import genai
from dotenv  import load_dotenv
import os

load_dotenv()

api = os.getenv("api_key")

client = genai.Client(api_key=api)



while True:

    userInput = input("User: ")


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=userInput,
    )

    print(f"{response.text}")