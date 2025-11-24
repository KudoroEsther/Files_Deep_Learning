from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api=os.getenv('api_key')
client = genai.Client(api_key=api)

# added a while loop to ensure recursion
while True:
    user_prompt = input("How may I help you? ").lower()
    if user_prompt != "exit":
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents= user_prompt,
        )

        print(response.text)
    else:
        break


# Persona chatbot
# To run this code you need to install the following dependencies:
# pip install google-genai

# import base64
# import os
# from google import genai
# from google.genai import types


# def generate():
#     client = genai.Client(
#         api_key=os.environ.get("GEMINI_API_KEY"),
#     )

#     model = "gemini-flash-latest"
#     contents = [
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_text(text="""INSERT_INPUT_HERE"""),
#             ],
#         ),
#     ]
#     tools = [
#         types.Tool(googleSearch=types.GoogleSearch(
#         )),
#     ]
#     generate_content_config = types.GenerateContentConfig(
#         thinkingConfig: {
#             thinkingBudget: -1,
#         },
#         tools=tools,
#         system_instruction=[
#             types.Part.from_text(text="""You are an electrical engineering assistant.
# Your job:
# - Answer all questions related to electrical engineering
# - Ask follow-up questions when needed
# - Break down complex concepts into simple ones
# _ Remain friendly always"""),
#         ],
#     )

#     for chunk in client.models.generate_content_stream(
#         model=model,
#         contents=contents,
#         config=generate_content_config,
#     ):
#         print(chunk.text, end="")

# if __name__ == "__main__":
#     generate()
