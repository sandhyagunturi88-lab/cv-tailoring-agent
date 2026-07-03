import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Initialize the Claude client
client = Anthropic()

# The buggy code we want Claude to review
buggy_code = """
function add(a, b) {
  return a - b;
}
"""

try:
    print("Sending code to Claude Haiku for review...\n")
    
    # Make the Messages API call
    response = client.messages.create(
        model="claude-haiku-4-5", # Updated to the fast, cost-effective Haiku model
        max_tokens=1024,
        system="You are a terse senior code reviewer. Give feedback in one paragraph.",
        messages=[
            {
                "role": "user", 
                "content": f"Review this code:\n{buggy_code}"
            }
        ]
    )
    
    # Loop through the response blocks
    for block in response.content:
        if block.type == "text":
            print(block.text)

except Exception as e:
    print(f"\nAn error occurred: {e}")