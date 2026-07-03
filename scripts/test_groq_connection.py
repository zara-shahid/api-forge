"""
Day 1 sanity check: confirm the Groq API key works before building
anything else.

Run with:
    python scripts/test_groq_connection.py
"""



import os
from langchain_groq import ChatGroq

from dotenv import load_dotenv
load_dotenv()

def main():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set. Add it to your .env or export it first.")
        return

    llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)
    response = llm.invoke("Reply with exactly: connection ok")
    print(response.content)


if __name__ == "__main__":
    main()
