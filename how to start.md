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