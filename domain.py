import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
    
def predict_domain(job_description: str) -> str:
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        prompt = f"""
        Analyze the following job description and predict the most appropriate job title/domain.
        Return ONLY the job title (e.g., Data Scientist, Frontend Developer).
        Do NOT include punctuation, explanation, or extra text.

        Job Description:
        {job_description}
        """

        # Try main model first
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",   # ✅ Updated
                temperature=0.3,
                max_tokens=50
            )
        except Exception as e:
            print("Primary model failed, trying fallback...", e)
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",       # ✅ Fallback
                temperature=0.3,
                max_tokens=50
            )

        raw_output = response.choices[0].message.content
        print("Raw output:", raw_output)

        domain = raw_output.strip().strip('"')
        return domain

    except Exception as e:
        print(f"Error predicting domain: {e}")
        return "Unknown"

