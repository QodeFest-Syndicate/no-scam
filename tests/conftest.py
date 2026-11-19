import os

# Keep the suite hermetic: never call DashScope from tests.
os.environ["DASHSCOPE_API_KEY"] = ""
