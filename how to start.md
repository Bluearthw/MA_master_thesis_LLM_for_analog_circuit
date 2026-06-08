# try
. .\init.ps1

# after setup the env once
powershell -c "iex (irm https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.ps1)"

# project id: 
project-2e780bfb-5a07-44db-866
# after web authentication:
$env:GOOGLE_CLOUD_PROJECT="project-2e780bfb-5a07-44db-866"
$env:GOOGLE_CLOUD_LOCATION="global"
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"
$$$$$


# how to setup vertex ai
# usage：
https://console.cloud.google.com/agent-platform/studio/settings/usage-dashboard?authuser=1&project=project-2e780bfb-5a07-44db-866
# tutorial
https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start?authuser=1&_gl=1*13l94x8*_ga*OTU0MzMzMDEyLjE3NzIxMDEyOTI.*_ga_WH2QY8WWF5*czE3ODA3NDUxNDIkbzEyJGcxJHQxNzgwNzQ1MTYyJGo0MCRsMCRoMA..
# example code
from google.genai.types import HttpOptions
client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="hi, am i using the vertex ai free credit?",
)
print(response.text)

$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\$env:USERNAME\AppData\Roaming\gcloud\application_default_credentials.json"
& “D:\tool\google_cloud_cli\google-cloud-sdk\bin\gcloud.cmd" auth application-default login


# access
(venv) PS D:\1kulStudy\8MA_Thesis\workplace> powershell -c "iex (irm https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.ps1)"
project id: project-2e780bfb-5a07-44db-866
# grant access
https://console.cloud.google.com/iam-admin/iam?authuser=1
================================================================
   Google Cloud Model API & Gemini: ADC setup script
================================================================

--- Checking prerequisites ---
â gcloud CLI detected via PATH at: D:\tool\google_cloud_cli\google-cloud-sdk\bin\gcloud.ps1

--- Project Setup ---
Enter your Google Cloud Project ID (NOT the name): project-2e780bfb-5a07-44db-866

--- Authenticating ---
Authorizing Application Default Credentials (ADC)...
Your browser has been opened to visit:

    https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A8085%2F&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fsqlservice.login&state=b89Vn8sMPYqhoqQ6t6QDkI11MgDc02&access_type=offline&code_challenge=7tNtj2rWRY1H97Bg8TSsuVyhntwHSbHTXZqXLYlj-x0&code_challenge_method=S256


Credentials saved to file: [D:\Users\82039\AppData\Roaming\gcloud\application_default_credentials.json]

These credentials will be used by any library that requests Application Default Credentials (ADC).

Quota project "project-2e780bfb-5a07-44db-866" was added to ADC which can be used by Google client libraries for billing and quota. Note that some services may still bill the project owning the resource.

Setting active gcloud account...
Updated property [core/account].
â Active account set to 3zhiyongwang@gmail.com

--- Finalizing Configuration ---
[environment: untagged] Read more to tag: g.co/cloud/project-env-tag.
Updated property [core/project].

Credentials saved to file: [D:\Users\82039\AppData\Roaming\gcloud\application_default_credentials.json]

These credentials will be used by any library that requests Application Default Credentials (ADC).

Quota project "project-2e780bfb-5a07-44db-866" was added to ADC which can be used by Google client libraries for billing and quota. Note that some services may still bill the project owning the resource.
ð Ensuring Google Cloud Model API is enabled...

--- Verifying Access ---
ð SUCCESS! Your Model API access is fully working.
ADC Credentials stored at: D:\Users\82039\AppData\Roaming\gcloud\application_default_credentials.json


## 去ima控制台里开权限

# Replace the `GOOGLE_CLOUD_PROJECT_ID` and `GOOGLE_CLOUD_LOCATION` values
# with appropriate values for your project.
export GOOGLE_CLOUD_PROJECT=project-2e780bfb-5a07-44db-866
export GOOGLE_CLOUD_LOCATION=global
export GOOGLE_GENAI_USE_ENTERPRISE=True

在vscode下用：

$env:GOOGLE_CLOUD_PROJECT="project-2e780bfb-5a07-44db-866"
$env:GOOGLE_CLOUD_LOCATION="global"
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"

# 1. Set your Project ID
$env:GOOGLE_CLOUD_PROJECT="project-2e780bfb-5a07-44db-866"
# 2. CRITICAL: Change "global" to "us-central1"
# The new Agent Platform requires a specific region for Gemini 3.5. 'global' will trigger a 404.
$env:GOOGLE_CLOUD_LOCATION="global"

# 3. Tell the SDK to bypass AI Studio completely and use your 300 USD credits
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"

# usage
gcloud beta quotas info list \
  --service=aiplatform.googleapis.com \
  --project="project-2e780bfb-5a07-44db-866" \
  --format="table(quotaId, metric, limit, dimensions)"



# before june 2026
venv\Scripts\Activate.ps1

##Then you can start 
cd .\forAmpOnly\
adk web

cd ../testNGspiceWithPython/ 
python .\Pyspice_example.py

some pyspice ddl problem
pyspice-post-installation --install-ngspice-dll
pyspice-post-installation --check-install