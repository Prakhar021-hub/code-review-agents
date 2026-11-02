import os

# Set these BEFORE our code is imported, so tests can never use your real
# keys or send traces to LangSmith, even by accident.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["OPENROUTER_API_KEY"] = "test-key"
os.environ["MODEL"] = "test-model"