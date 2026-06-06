git add .
git commit -m "switch to vertex
"
git push



## entrance: main.py!!

venv\Scripts\Activate.ps1
# MA_master_thesis_LLM_for_analog_circuit

number of netlists : 894
"amplifier" and "Amplifier"
opamp : 470
SISO_opamps : 334
SISO_opamps without clk Iin Iout : 289
SISO_opamps with only VB,VIN1,VOUT1 and VBn : 171


69, 77 is differential
# RF
    LNA, PA, DA / IGA??
    not RF: 9, 166
467 has L and it is LNA (low nosie) for RF
465 does not have L but it is also RF
456, with IB 
522 works like a bandpass
578 with L, it is PA (power)
643 is a schimtt trigger including amplifier
832 is 3 stages
906 2 stage with feedback
1017 parallel path
# comparator, actually, if there is vin2, it is CMP
with "amplifier" :
    1039
    1041, at line 8

## vertax ai
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



(venv) PS D:\1kulStudy\8MA_Thesis\workplace> powershell -c "iex (irm https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.ps1)"
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
# 1. Set your Project ID
$env:GOOGLE_CLOUD_PROJECT="project-2e780bfb-5a07-44db-866"

# 2. CRITICAL: Change "global" to "us-central1"
# The new Agent Platform requires a specific region for Gemini 3.5. 'global' will trigger a 404.
$env:GOOGLE_CLOUD_LOCATION="global"

# 3. Tell the SDK to bypass AI Studio completely and use your 300 USD credits
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"
    
## 
workplace
├─ circuit_env.py
├─ forAmpOnly
│  ├─ dataset
│  ├─ main.py
│  ├─ memory_agent
│  │  ├─ agent.py
│  │  └─ __init__.py
│  ├─ OPAMP_agent
│  │  ├─ .env
│  │  ├─ agent.py
│  │  ├─ subagents
│  │  │  ├─ CIRfileAddModelAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ CIRfileAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ DCsimulateAgent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ OPAMPagent
│  │  │  │  ├─ agent.py
│  │  │  │  ├─ __init__.py
│  │  │  │  └─ __pycache__
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ tools
│  │  │  ├─ tool_NGspice.py
│  │  │  ├─ __init__.py
│  │  │  └─ __pycache__
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  ├─ simulation_agent
│  │  ├─ .env
│  │  ├─ agent.py
│  │  ├─ __init__.py
│  │  └─ __pycache__
│  └─ utils.py
├─ genai_agent
│  ├─ add_sim_agent.py
│  ├─ before2026_py_files
│  │  ├─ 1simplecall.py
│  │  ├─ 2structureCall.py
│  │  ├─ root_agent_about_tools.py
│  │  ├─ root_agent_before_combine_OP_cload .py
│  │  ├─ root_agent_before_tool.py
│  │  └─ root_agent_LLM_change_circuit.py
│  ├─ CAD_window
│  ├─ debug_agent.py
│  ├─ local_config.py
│  ├─ memory
│  │  ├─ category_numbers.py
│  │  └─ __pycache__
│  ├─ nmosinv.cir
│  ├─ pickup_RF_agent
│  ├─ root_agent.py
│  ├─ root_agent_2026.py
│  ├─ saved_netlist.py
│  ├─ testbench
│  │  └─ tb_SpiceResult_SpiceResultNew
│  ├─ test_functions.py
│  ├─ tools.py
│  ├─ utils.py
│  ├─ workflows
│  │  ├─ cmfb_agent.py
│  │  ├─ type40
│  │  │  └─ root_agent_type40
│  │  ├─ type4_TIA
│  │  │  └─ root_agent_type4
│  │  ├─ type7_DISO
│  │  │  └─ root_agent_type7
│  │  └─ __pycache__
│  ├─ __init__.py
│  └─ __pycache__
├─ how to start.txt
├─ ngspice_file
│  ├─ test1.cir
│  ├─ test1_by_hand.cir
│  ├─ vdiv.cir
│  └─ vdiv.log
├─ ngspice_interface
│  ├─ area_estimation.py
│  ├─ dut_testbench.py
│  ├─ files
│  │  ├─ input_netlists
│  │  │  └─ TwoStage.cir
│  │  ├─ spice_models
│  │  │  ├─ p045_FF.sp
│  │  │  ├─ p045_SS.sp
│  │  │  └─ p045_TT.sp
│  │  └─ yaml_files
│  │     └─ TwoStage.yaml
│  ├─ ngspice_wrapper.py
│  ├─ __init__.py
│  └─ __pycache__
├─ README.md
├─ solutions
│  ├─ 2026-03-23--17-18-45
│  ├─ 2026-03-23--17-21-54
│  └─ 2026-03-23--17-26-20
├─ td3
│  ├─ agent.py
│  ├─ buffer.py
│  ├─ sac_baseline.cpython-39-x86_64-linux-gnu.so
│  ├─ __init__.py
│  └─ __pycache__
├─ td3_runner.py
├─ testNGspiceWithPython
│  ├─ gemini_example.py
│  └─ Pyspice_example.py
├─ utils
│  ├─ plotting.py
│  ├─ save_response.py
│  ├─ saving.py
│  ├─ __pycache__
│  └─ ___init__.py
