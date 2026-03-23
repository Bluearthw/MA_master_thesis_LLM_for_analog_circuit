import os
from openai import OpenAI

client = OpenAI(api_key="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")

    

response = client.responses.create(
    model="gpt-4.1-2025-04-14",
    input="Write a one-sentence bedtime story about a unicorn."
)
print(response.output_text)