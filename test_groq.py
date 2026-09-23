import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load GROQ_API_KEY from .env into environment variables
load_dotenv()

# 2. Create a client pointed at Groq's OpenAI-compatible endpoint
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

# 3. Send one message and get a response
response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {"role": "user", "content": "Say hello in one short sentence."}
    ],
)

# 4. Print the assistant's text
print(response.choices[0].message.content)