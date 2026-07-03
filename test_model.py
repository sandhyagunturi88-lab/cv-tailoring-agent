import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Initialize the Claude client
client = Anthropic()

# 1. Define the prompt first! 
prompt = "Write a highly professional, one-sentence CV summary for a Project Manager who specializes as a Scrum Master facilitating agile delivery."

# 2. Your list of models to test
models = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-7"]

print("Comparing models and token usage...\n")

# 3. Loop through each model
for model in models:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Print the model name and the exact token usage data
        print(f"--- {model} ---")
        print(f"Response: {response.content[0].text}")
        print(f"Usage Stats: {response.usage}\n")
        
    except Exception as e:
        print(f"--- {model} ---")
        print(f"An error occurred: {e}\n")