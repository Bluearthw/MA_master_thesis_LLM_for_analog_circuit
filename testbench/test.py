from google import genai
import os
from google.genai.types import HttpOptions
# credential_path = os.path.join(os.getenv("APPDATA"), "gcloud", "application_default_credentials.json")
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-3.5-flash",
    # model= "gemini-3-flash-preview",
    contents="hi,test connection",
)
print(response.text)
# Example response:
# Okay, let's break down how AI works. It's a broad field, so I'll focus on the ...
#
# Here's a simplified overview:
# ...

# import os
# from google import genai

# # =====================================================================
# # 1. 核心防御：不管 Windows 怎么重启，强行在代码运行时给 Python 注入绝对路径
# # =====================================================================
# credential_path = os.path.join(os.getenv("APPDATA"), "gcloud", "application_default_credentials.json")
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

# # =====================================================================
# # 2. 核心项目绑定：把开机后会丢失的环境变量，直接强行塞进 Client 初始化里
# # =====================================================================
# client = genai.Client(
#     vertexai=True,                                # 100% 强制走 Vertex AI (Agent Platform) 通道
#     project='project-2e780bfb-5a07-44db-866',      # 100% 锁死你的 300 刀项目 ID
#     location='us-central1'                         # 100% 锁死支持 3.5 的美国中部机房
# )

# # =====================================================================
# # 3. 运行你的论文测试
# # =====================================================================
# try:
#     response = client.models.generate_content(
#         model='gemini-3.5-flash',
#         contents='hi, please confirm you are online.',
#     )
#     print("【开机测试成功！】:", response.text)
# except Exception as e:
#     print("【测试失败，报错原因为】:", e)