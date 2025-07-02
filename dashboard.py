import json
import os
import urllib.parse
import logging
from groq import Groq
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

# Constants
MAX_JOBS = 6  # Maximum number of job links to display
RESULTS_FILE = "interview_results.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Groq client
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {str(e)}")
    groq_client = None

@st.cache_data(show_spinner=False)
def load_results() -> Optional[Dict]:
    """Load interview results from JSON file with validation"""
    try:
        if not os.path.exists(RESULTS_FILE):
            st.error("No interview results file found")
            return None
            
        with open(RESULTS_FILE) as f:
            data = json.load(f)
            
        # Validate basic structure
        if not all(key in data for key in ['domain', 'hr_results', 'tech_results']):
            st.error("Invalid results format")
            return None
            
        return data
        
    except json.JSONDecodeError:
        st.error("Invalid JSON format in results file")
    except Exception as e:
        logger.error(f"Error loading results: {str(e)}")
        st.error("Failed to load results")
    
    return None

def calculate_scores(results: Dict) -> Optional[Dict]:
    """Calculate summary scores with input validation"""
    if not results or not isinstance(results, dict):
        return None
    
    try:
        hr_scores = []
        for q in results.get('hr_results', []):
            if isinstance(q, dict) and 'evaluation' in q:
                score = q['evaluation'].get('score', 0)
                if isinstance(score, (int, float)):
                    hr_scores.append(score)

        tech_scores = []
        for q in results.get('tech_results', []):
            if isinstance(q, dict) and 'evaluation' in q:
                score = q['evaluation'].get('score', 0)
                if isinstance(score, (int, float)):
                    tech_scores.append(score)

        def safe_avg(scores: List[float]) -> float:
            return sum(scores)/len(scores) if scores else 0.0
    
        return {
            'hr_total': sum(hr_scores),
            'tech_total': sum(tech_scores),
            'hr_avg': safe_avg(hr_scores),
            'tech_avg': safe_avg(tech_scores),
            'overall_avg': safe_avg(hr_scores + tech_scores),
            'domain': results.get('domain', 'Unknown')
        }
    except Exception as e:
        logger.error(f"Error calculating scores: {str(e)}")
        return None

def display_score_summary(scores: Dict) -> None:
    """Display the main score metrics"""
    if not scores:
        st.warning("No scores available")
        return
    
    st.header("📊 Interview Performance Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total HR Score", 
                 f"{scores['hr_total']}/{(len(st.session_state.results.get('hr_results', [])) * 10)}")
    with col2:
        st.metric("Total Tech Score", 
                 f"{scores['tech_total']}/{(len(st.session_state.results.get('tech_results', [])) * 10)}")
    with col3:
        st.metric("Overall Average", 
                 f"{scores['overall_avg']:.1f}/10")

def plot_question_scores(results: Dict) -> None:
    """Create visualizations for question scores"""
    if not results:
        st.warning("No results available for visualization")
        return
    
    try:
        # Prepare data for plotting
        hr_data = []
        for i, q in enumerate(results.get('hr_results', [])):
            if isinstance(q, dict) and 'evaluation' in q:
                hr_data.append({
                    'Type': 'HR',
                    'Question': f"Q{i+1}",
                    'Score': q['evaluation'].get('score', 0),
                    'Full Question': q.get('question', '')
                })

        tech_data = []
        for i, q in enumerate(results.get('tech_results', [])):
            if isinstance(q, dict) and 'evaluation' in q:
                tech_data.append({
                    'Type': 'Technical',
                    'Question': f"Q{i+1}",
                    'Score': q['evaluation'].get('score', 0),
                    'Full Question': q.get('question', '')
                })

        if not hr_data and not tech_data:
            st.warning("No valid question data available")
            return

        df = pd.DataFrame(hr_data + tech_data)
        
        st.header("📈 Question-wise Performance")
        fig = px.bar(df, x='Question', y='Score', color='Type',
                     hover_data=['Full Question'],
                     title="Scores by Question",
                     barmode='group')
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        st.error("Failed to generate performance chart")

def display_detailed_feedback(results: Dict) -> None:
    """Show detailed question-by-question feedback"""
    if not results:
        st.warning("No results available for feedback")
        return
    
    st.header("📝 Detailed Feedback")
    
    try:
        # Combine HR and tech results with type indicator
        all_questions = []
        for q in results.get('hr_results', []):
            if isinstance(q, dict):
                q['type'] = 'HR'
                all_questions.append(q)
                
        for q in results.get('tech_results', []):
            if isinstance(q, dict):
                q['type'] = 'Technical'
                all_questions.append(q)

        if not all_questions:
            st.info("No interview questions available")
            return

        # Create expandable sections for each question
        for i, q in enumerate(all_questions):
            with st.expander(f"{q.get('type', 'Question')} {i+1}: {q.get('question', '')[:50]}..."):
                eval_data = q.get('evaluation', {})
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Score", f"{eval_data.get('score', 0)}/10")
                with col2:
                    st.write(f"**Your Answer:** {q.get('answer', '')}")
                
                st.write(f"**Feedback:** {eval_data.get('feedback', 'No feedback available')}")
                
                if eval_data.get('improvement_tips'):
                    st.write("**Improvement Tips:**")
                    for tip in eval_data.get('improvement_tips', []):
                        st.write(f"- {tip}")
                
                if eval_data.get('knowledge_gaps'):
                    st.write("**Knowledge Gaps:**")
                    for gap in eval_data.get('knowledge_gaps', []):
                        st.write(f"- {gap}")
                        
    except Exception as e:
        logger.error(f"Error displaying feedback: {str(e)}")
        st.error("Failed to display detailed feedback")

@st.cache_data(ttl=3600, show_spinner="Generating improvement suggestions...")
def generate_improvement_suggestions(results: Dict) -> Dict:
    """Generate AI-powered improvement suggestions with caching"""
    if not results or not groq_client:
        return {
            "strengths": [],
            "improvements": [],
            "action_items": []
        }
    
    try:
        # Prepare interview data for AI analysis
        interview_data = []
        for q in results.get('hr_results', []):
            if isinstance(q, dict):
                interview_data.append({
                    "type": "HR",
                    "question": q.get('question'),
                    "answer": q.get('answer'),
                    "evaluation": q.get('evaluation', {})
                })

        for q in results.get('tech_results', []):
            if isinstance(q, dict):
                interview_data.append({
                    "type": "Technical",
                    "question": q.get('question'),
                    "answer": q.get('answer'),
                    "evaluation": q.get('evaluation', {})
                })

        if not interview_data:
            return {
                "strengths": ["No interview data available for analysis"],
                "improvements": [],
                "action_items": []
            }

        # Create prompt for LLM
        prompt = f"""Analyze these interview responses and provide:
        1. 3 key strengths (bullet points)
        2. 3 areas needing improvement (bullet points)
        3. 3 specific action items (bullet points)
        
        Interview Performance:
        {json.dumps(interview_data)}
        
        Format as JSON with keys: strengths, improvements, action_items"""
        
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return {
            "strengths": [],
            "improvements": ["Failed to generate improvement suggestions"],
            "action_items": ["Check your API connection", "Verify your results data"]
        }

@st.cache_data(ttl=86400, show_spinner="Fetching course recommendations...")  # Cache for 24 hours
def fetch_course_recommendations(domain: str) -> List[Dict]:
    """Fetch course recommendations using Groq with caching"""
    if not domain or not groq_client:
        return []

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{
                "role": "user",
                "content": f"""Recommend 5 best online courses for {domain}.
                For each provide: title, platform, description, and url.
                Format as JSON with 'courses' array."""
            }],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        data = json.loads(response.choices[0].message.content)
        return data.get('courses', [])[:5]
    except Exception as e:
        logger.error(f"Course search failed: {str(e)}")
        return []

def search_job_portals(domain: str, location: str = "") -> List[Tuple[str, str]]:
    """Enhanced job search with LLM-suggested titles and multiple platforms"""
    titles_prompt = f"""
    Suggest 3 entry-level job titles in {domain} for someone with beginner skills.
    Just return the job titles as a comma-separated list. Do NOT include any explanation or extra text.
    """
    
    try:
        if not groq_client:
            raise RuntimeError("Groq client not available")
            
        # Get job titles from LLM
        titles_response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": titles_prompt}],
            temperature=0.3
        )
        
        # Clean and parse titles
        raw = titles_response.choices[0].message.content.strip()
        clean_text = raw.replace("\n", "").replace("•", "").replace("1.", "").replace("2.", "").replace("3.", "")
        titles = [t.strip() for t in clean_text.split(",") if len(t.strip()) > 2]

        if not titles:
            raise ValueError("No valid titles extracted")
            
        logger.info(f"Generated job titles: {titles}")
    except Exception as e:
        logger.warning(f"Using fallback job titles: {str(e)}")
        titles = ["Junior Data Analyst", "Business Analyst Intern", "Data Reporting Assistant"]

    job_links = []
    platforms = {
        "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords={query}&location={location}",
        "Indeed": "https://www.indeed.com/jobs?q={query}&l={location}",
        "Glassdoor": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}",
        "Naukri": "https://www.naukri.com/{query}-jobs-in-{location}",
        "Monster": "https://www.monster.com/jobs/search/?q={query}&where={location}"
    }

    for title in titles:
        query = urllib.parse.quote_plus(title)
        loc = urllib.parse.quote_plus(location) if location else ""
        
        for platform, url_template in platforms.items():
            try:
                url = url_template.format(query=query, location=loc)
                job_links.append((f"{title} ({platform})", url))
                if len(job_links) >= MAX_JOBS:
                    break
            except Exception as e:
                logger.error(f"Error generating URL for {title}: {str(e)}")
        
        if len(job_links) >= MAX_JOBS:
            break

    return job_links[:MAX_JOBS]

def display_job_search(domain: str):
    """Interactive job search component"""
    st.header("💼 Job Opportunities")
    
    with st.expander("Search Jobs in Your Preferred Location", expanded=True):
        location = st.text_input(
            "📍 Preferred location (city, country, or 'remote'):",
            placeholder="e.g., New York, Berlin, Remote",
            key="job_search_location"
        )
        
        if st.button("🔍 Find Jobs", key="job_search_button"):
            if not domain:
                st.warning("Please complete an interview first")
                return
                
            with st.spinner(f"Searching {domain} jobs in {location or 'all locations'}..."):
                try:
                    job_links = search_job_portals(domain, location)
                    
                    if not job_links:
                        st.warning("No job openings found. Try a different location.")
                        return
                        
                    st.success(f"Found {len(job_links)} opportunities:")
                    
                    for title, url in job_links:
                        st.markdown(f"- [{title}]({url})", unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Job search failed: {str(e)}")
                    logger.exception("Job search error")

def display_dashboard(results=None) -> None:
    """Main dashboard function with improved layout and error handling"""
    st.set_page_config(
        page_title="Interview Results Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state if not exists
    if 'results' not in st.session_state:
        st.session_state.results = load_results()
    
    if not st.session_state.results:
        st.warning("Please complete an interview first to see results")
        st.stop()  # Stop execution if no results
    
    # Calculate scores with error handling
    scores = calculate_scores(st.session_state.results)
    if not scores:
        st.error("Failed to calculate interview scores")
        st.stop()
    
    domain = scores.get('domain', 'your field')
    
    # Main dashboard layout
    with st.container():
        display_score_summary(scores)
        st.divider()
        
        plot_question_scores(st.session_state.results)
        st.divider()
        
        display_detailed_feedback(st.session_state.results)
        st.divider()
        
        # Improvement Plan Section
        st.header("💡 Improvement Plan")
        with st.spinner("Analyzing your performance..."):
            suggestions = generate_improvement_suggestions(st.session_state.results)
        
        cols = st.columns(3)
        with cols[0]:
            st.subheader("✅ Your Strengths")
            for strength in suggestions.get('strengths', ["No strengths identified"]):
                st.write(f"- {strength}")
        
        with cols[1]:
            st.subheader("📈 Areas to Improve")
            for improvement in suggestions.get('improvements', ["No specific improvements suggested"]):
                st.write(f"- {improvement}")
        
        with cols[2]:
            st.subheader("📌 Action Items")
            for action in suggestions.get('action_items', ["No action items suggested"]):
                st.write(f"- {action}")
        
        st.divider()
        
        # Job Search Section
        st.header("🔎 Job Opportunities")
        display_job_search(domain)
        
        # Course Recommendations Section
        st.header("🎓 Recommended Courses")
        with st.spinner("Finding relevant courses..."):
            courses = fetch_course_recommendations(domain)
        
        if not courses:
            st.info("No course recommendations available")
        else:
            for course in courses:
                with st.expander(f"{course.get('title', 'Course')} ({course.get('platform', 'Unknown')})"):
                    st.write(f"📖 **Description:** {course.get('description', 'No description available')}")
                    if course.get('level'):
                        st.write(f"🎚️ **Level:** {course.get('level')}")
                    if course.get('url'):
                        st.markdown(f"[🔗 Visit Course]({course['url']})", unsafe_allow_html=True)

if __name__ == "__main__":
    display_dashboard()