import os
import re
from typing import List, Dict
from groq import Groq

class HRInterview:
    def __init__(self):
        """
        Initialize HR Interview processor with Groq client
        Requires GROQ_API_KEY in environment variables
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.system_prompt = """You are an expert HR interviewer with 15 years of experience at top tech companies.
        Your task is to generate relevant HR interview questions or evaluate answers with detailed feedback.
        For evaluations, provide:
        1. Score (1-10)
        2. Detailed feedback
        3. 3 actionable improvement tips"""

    def generate_questions(self, domain: str, num_questions: int = 5) -> List[str]:
        """
        Generate HR interview questions for a specific domain
        Args:
            domain: Job domain (e.g. "Software Engineering")
            num_questions: Number of questions to generate
        Returns:
            List of generated questions
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR interviewer. Generate only the interview questions, no additional text."
                    },
                    {
                        "role": "user", 
                        "content": f"""Generate exactly {num_questions} basic HR and behavioral interview questions. First question should be self introduction.
                        Return ONLY a clean numbered list of questions with no additional commentary or formatting.
                        Example:
                        1. Tell me about a time you faced a difficult challenge at work
                        2. Describe a situation where you had to work with a difficult teammate"""
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract and clean questions
            content = response.choices[0].message.content
            questions = []
            for line in content.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():  # Only take numbered lines
                    question = line.split('. ', 1)[1] if '. ' in line else line
                    questions.append(question.strip())
            return questions[:num_questions]
            
        except Exception as e:
            print(f"Error generating HR questions: {str(e)}")
            return [
                "Tell me about a time you resolved a conflict in your team",
                "Describe a situation where you had to adapt to major changes",
                "Give an example of how you handled a difficult coworker",
                "Share an experience where you demonstrated leadership",
                "How do you prioritize when working on multiple projects?"
            ]

    def evaluate_answer(self, question: str, answer: str) -> Dict:
        """
        Evaluate an HR interview answer
        Args:
            question: The interview question
            answer: Candidate's transcribed answer
        Returns:
            Dictionary containing:
            - score (int)
            - feedback (str)
            - improvement_tips (List[str])
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""Evaluate this HR interview response:
                        Question: {question}
                        Answer: {answer}
                        
                        Provide:
                        1. Numerical score (1-10) labeled 'Score:'
                        2. Detailed feedback labeled 'Feedback:'
                        3. Exactly 3 improvement tips labeled 'Improvement Tips:' 
                        Use this exact format:
                        Score: [number]/10
                        Feedback: [text]
                        Improvement Tips:
                        - [tip 1]
                        - [tip 2]
                        - [tip 3]"""
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            return self._parse_evaluation(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error evaluating HR answer: {str(e)}")
            return {
                "score": 5,
                "feedback": "Unable to process evaluation at this time",
                "improvement_tips": [
                    "Provide more specific examples",
                    "Structure your answer using STAR method",
                    "Focus on measurable outcomes"
                ]
            }

    def _parse_evaluation(self, text: str) -> Dict:
        """
        Parse LLM evaluation response into structured format
        Args:
            text: Raw LLM response text
        Returns:
            Structured evaluation dictionary
        """
        # Initialize default values
        evaluation = {
            "score": 5,
            "feedback": "No feedback available",
            "improvement_tips": []
        }
        
        try:
            # Extract score
            score_match = re.search(r"Score:\s*(\d+)/10", text)
            if score_match:
                evaluation["score"] = int(score_match.group(1))
            
            # Extract feedback
            feedback_match = re.search(r"Feedback:\s*(.+?)(?=\nImprovement Tips:|$)", text, re.DOTALL)
            if feedback_match:
                evaluation["feedback"] = feedback_match.group(1).strip()
            
            # Extract improvement tips
            tips_match = re.search(r"Improvement Tips:\s*(.+?)(?=\n\w+:|$)", text, re.DOTALL)
            if tips_match:
                tips = [tip.strip('- ').strip() for tip in tips_match.group(1).split('\n') if tip.strip()]
                evaluation["improvement_tips"] = tips[:3]  # Ensure max 3 tips
                
        except Exception as e:
            print(f"Error parsing evaluation: {str(e)}")
        
        return evaluation

# Example usage
# if __name__ == "__main__":
#     import dotenv
#     dotenv.load_dotenv()
    
#     hr = HRInterview()
    
#     # Test question generation
#     questions = hr.generate_questions("Data Science")
#     print("Generated HR Questions:")
#     for i, q in enumerate(questions, 1):
#         print(f"{i}. {q}")
    
#     # Test evaluation
#     sample_answer = """When I had a conflict with a teammate about project direction, 
#     I scheduled a meeting where we both presented our viewpoints. 
#     We found a compromise that incorporated elements from both approaches."""
    
#     evaluation = hr.evaluate_answer(
#         question="Tell me about a time you resolved a conflict",
#         answer=sample_answer
#     )
    
#     print("\nEvaluation Results:")
#     print(f"Score: {evaluation['score']}/10")
#     print(f"Feedback: {evaluation['feedback']}")
#     print("Improvement Tips:")
#     for tip in evaluation['improvement_tips']:

#         print(f"- {tip}")
