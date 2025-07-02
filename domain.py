import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def predict_domain(job_description: str) -> str:
    """
    Predicts the job domain/title from a given job description using Groq's LLM.
    
    Args:
        job_description: The job description text provided by the user.
    
    Returns:
        The predicted job domain/title (e.g., "Software Engineer").
    """
    try:
        # Initialize Groq client with API key from .env
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Create a prompt for domain prediction
        prompt = f"""
        Analyze the following job description and predict the most appropriate job title/domain.
        Return ONLY the job title (e.g., "Data Scientist", "Frontend Developer") in plain text, no additional text.
        
        Job Description:
        {job_description}
        """
        
        # Get response from Groq's LLM
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",  # Groq's fast Mixtral model
            temperature=0.3,  # Lower temperature for more deterministic output
            max_tokens=50
        )
        
        # Extract and clean the response
        domain = response.choices[0].message.content.strip()
        domain = domain.strip('"')  # Remove any surrounding quotes
        
        return domain
    
    except Exception as e:
        print(f"Error predicting domain: {e}")
        return "Unknown"
