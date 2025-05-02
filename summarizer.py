from groq import Groq
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

def summarize_email(email_text, label="email1"):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You are a smart summarizer agent. Summarize the following email in 1–2 sentences. Output only valid JSON in this format:
{{
  "{label}": "summary here"
}}
Do NOT include any markdown, extra notes, or <think> reasoning.

Email:
{email_text[:3000]}
"""

    try:
        completion = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.6,
            max_completion_tokens=1024,
            top_p=0.95,
            stream=True,
            stop=None,
        )

        full_response = ""
        for chunk in completion:
            full_response += chunk.choices[0].delta.content or ""

        print("🧠 Raw AI response:\n", full_response)

        # Extract JSON block from response using regex
        match = re.search(r'{.*}', full_response, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON found in response")

        json_text = match.group(0)
        parsed = json.loads(json_text)
        return parsed

    except Exception as e:
        print(f"⚠️ JSON parsing failed: {e}")
        return {label: "Failed to parse summary"}
