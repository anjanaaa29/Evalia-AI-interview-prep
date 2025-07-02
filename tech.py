import os
import re
from typing import List, Dict
from groq import Groq

class TechnicalInterview:
    def __init__(self):
        """
        Initialize Technical Interview processor with Groq client
        Requires GROQ_API_KEY in environment variables
        """
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.system_prompt = """You are a senior technical interviewer at a top tech company.
        Your tasks:
        1. Generate relevant technical questions for specific job domains
        2. Evaluate technical answers with:
           - Accuracy score (1-10)
           - Detailed technical feedback
           - Actionable improvement suggestions"""

    def generate_questions(self,domain: str, difficulty: str = "mid", num_questions: int = 5) -> List[str]:
        """
        Generate technical interview questions without introductory text
        """
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical interviewer. Return ONLY the questions as a numbered list."
                    },
                    {
                        "role": "user",
                        "content": f"""Generate exactly {num_questions} {difficulty}-level technical questions for {domain}.
                        Return ONLY a clean numbered list like:
                        1. Question one?
                        2. Question two?
                        No introductory text or additional commentary."""
                    }
                ],
                temperature=0.7,
                max_tokens=800
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
            print(f"Error generating technical questions: {str(e)}")
            # Fallback questions
            return [
                "Explain the time complexity of quicksort and when you'd use it",
                "Design a URL shortening service like bit.ly",
                "Write a function to detect cycles in a linked list",
                "How would you optimize database queries for a high-traffic app?",
                "Explain the CAP theorem with examples"
            ]

    def evaluate_answer(self, question: str, answer: str, domain: str) -> Dict:
        """
        Evaluate a technical interview answer
        Args:
            question: The technical question asked
            answer: Candidate's transcribed response
            domain: Relevant job domain
        Returns:
            Dictionary containing:
            - score (int)
            - feedback (str)
            - improvement_tips (List[str])
            - knowledge_gaps (List[str])
        """
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""Evaluate this technical interview response for {domain}:
                        Question: {question}
                        Answer: {answer}
                        
                        Provide:
                        1. Accuracy score (1-10) labeled 'Score:'
                        2. Technical feedback labeled 'Feedback:'
                        3. 2-3 improvement tips labeled 'Improvement Tips:'
                        4. Any identified knowledge gaps labeled 'Knowledge Gaps:'
                        
                        Use this exact format:
                        Score: [number]/10
                        Feedback: [detailed technical analysis]
                        Improvement Tips:
                        - [tip 1]
                        - [tip 2]
                        Knowledge Gaps:
                        - [gap 1]"""
                    }
                ],
                temperature=0.3,  # Lower temp for more factual evaluations
                max_tokens=1200
            )
            
            return self._parse_evaluation(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error evaluating technical answer: {str(e)}")
            return {
                "score": 5,
                "feedback": "Evaluation system unavailable",
                "improvement_tips": [
                    "Provide more technical specifics",
                    "Include code examples where possible"
                ],
                "knowledge_gaps": ["Unable to assess gaps"]
            }

    def _parse_evaluation(self, text: str) -> Dict:
        """
        Parse LLM evaluation response into structured format
        Args:
            text: Raw LLM response text
        Returns:
            Structured evaluation dictionary
        """
        evaluation = {
            "score": 5,
            "feedback": "No feedback available",
            "improvement_tips": [],
            "knowledge_gaps": []
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
            tips_section = re.search(r"Improvement Tips:\s*(.+?)(?=\nKnowledge Gaps:|$)", text, re.DOTALL)
            if tips_section:
                tips = [tip.strip('- ').strip() for tip in tips_section.group(1).split('\n') if tip.strip()]
                evaluation["improvement_tips"] = tips[:3]
            
            # Extract knowledge gaps
            gaps_section = re.search(r"Knowledge Gaps:\s*(.+?)(?=\n\w+:|$)", text, re.DOTALL)
            if gaps_section:
                gaps = [gap.strip('- ').strip() for gap in gaps_section.group(1).split('\n') if gap.strip()]
                evaluation["knowledge_gaps"] = gaps[:2]
                
        except Exception as e:
            print(f"Error parsing evaluation: {str(e)}")
        
        return evaluation

