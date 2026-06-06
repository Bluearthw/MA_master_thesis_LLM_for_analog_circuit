from google import genai
import os
from google.genai.types import HttpOptions
client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="hi, am i using the vertex ai free credit?",
)
print(response.text)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getenv("APPDATA"), "gcloud", "application_default_credentials.json")


client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="hi, am i using the vertex ai free credit?",
)
print(response.text)
# Example response:
# Okay, let's break down how AI works. It's a broad field, so I'll focus on the ...
#
# Here's a simplified overview:
# ...