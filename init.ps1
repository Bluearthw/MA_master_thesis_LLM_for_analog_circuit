# 1. 自动执行官方的 ADC 脚本并静默运行（省去你每次复制粘贴的麻烦）
powershell -c "iex (irm https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.ps1)"

# 2. 自动注入你论文项目专属的环境变量
$env:GOOGLE_CLOUD_PROJECT="project-2e780bfb-5a07-44db-866"
$env:GOOGLE_CLOUD_LOCATION="global"
$env:GOOGLE_GENAI_USE_ENTERPRISE="True"

Write-Host " venv ready" -ForegroundColor Green