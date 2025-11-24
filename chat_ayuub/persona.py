from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api = os.getenv("api_key")

client = genai.Client(api_key=api)

# Persona text
persona = """
You are Loan Assistant, a friendly loan agent.
Your job:
- Greet politely
- Ask follow-up questions
- Explain loans in simple language
- Maintain a calm, professional tone
- Always reply in brief
"""

while True:
    userInput = input("User: ")

    final_prompt = f"{persona}\n\nUser: {userInput}\nLoanAssist Pro:"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=final_prompt
    )

    print("\nAgent:", response.text, "\n")
