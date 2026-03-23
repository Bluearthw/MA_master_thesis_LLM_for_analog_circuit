import os
from openai import OpenAI
# client = OpenAI(api_key="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")
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

deepseekFlag =False
if deepseekFlag:
    client = OpenAI(api_key="sk-0db11d8af3ad4ac5a128866deb4e81ed",  base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
    )
    print(response.choices[0].message.content)
    
else:
    client = OpenAI(api_key="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")

    

    response = client.responses.create(
        model="gpt-4.1-2025-04-14",
        input="Write a one-sentence bedtime story about a unicorn."
    )
    print(response.output_text)

    

