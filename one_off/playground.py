import google.generativeai as genai

# Replace with your API key
genai.configure(api_key="AIzaSyDBSipOVlCsEWODyaGCcSfMjFDpBHrvE-g")

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)