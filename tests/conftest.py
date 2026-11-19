import os

# Empty values prevent dotenv from loading real credentials into tests.
for name in ("DASHSCOPE_API_KEY", "QODER_API_KEY", "OPENAI_API_KEY"):
    os.environ[name] = ""
os.environ["WHATSAPP_ENABLED"] = "false"
