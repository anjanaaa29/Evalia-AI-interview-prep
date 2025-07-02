import os
import json
import streamlit as st
from voice import VoiceProcessor
from domain import predict_domain
from hr import HRInterview
from tech import TechnicalInterview
from dashboard import display_dashboard
from chatbot import chatbot_page

# Initialize all components
voice_processor = VoiceProcessor()
hr_interview = HRInterview()
tech_interview = TechnicalInterview()

def save_results(results: dict):
    """Save interview results to JSON file"""
    with open("interview_results.json", "w") as f:
        json.dump(results, f, indent=2)

def initialize_session_state():
    """Initialize all required session state variables"""
    required_state = {
        'results': {
            "domain": "",
            "hr_questions": [],
            "tech_questions": [],  
            "hr_results": [],
            "tech_results": []     
        },
        'current_round': None,
        'current_question_idx': 0,
        'audio_data': None,
        'show_evaluation': False  # New state to track evaluation display
    }
    
    for key, default_value in required_state.items():
        if key not in st.session_state:
            if isinstance(default_value, dict):
                st.session_state[key] = default_value.copy()
            else:
                st.session_state[key] = default_value

def conduct_round(round_type: str, domain: str):
    """Conduct interview round one question at a time"""
    st.header(f"{round_type} Interview Round")
    
    # Use consistent key naming throughout
    round_prefix = "tech" if round_type.lower() == "technical" else "hr"
    question_key = f"{round_prefix}_questions"
    results_key = f"{round_prefix}_results"
    
    questions = st.session_state.results[question_key]
    current_idx = st.session_state.current_question_idx
    
    if current_idx < len(questions):
        question = questions[current_idx]
        
        if not st.session_state.show_evaluation:
            # Question and recording section
            st.subheader(f"Question {current_idx+1} of {len(questions)}")
            st.markdown(f"**{question}**")
            
            # Voice recording section
            # st.write("Record your answer (click the mic icon):")
            audio_data = voice_processor.record_audio(f"{round_type}_{current_idx}")
            
            if audio_data:
                st.session_state.audio_data = audio_data
                st.audio(audio_data['bytes'], format="audio/wav")
                
                if st.button("Submit Answer", key=f"submit_{current_idx}"):
                    with st.spinner("Processing your answer..."):
                        transcription = voice_processor.transcribe_audio(audio_data)
                        
                        if transcription:
                            # Save results using consistent key
                            st.session_state.results[results_key].append({
                                "question": question,
                                "answer": transcription,
                                "evaluation": None  # Will be filled below
                            })
                            
                            # Evaluate answer
                            if round_type == "HR":
                                evaluation = hr_interview.evaluate_answer(question, transcription)
                            else:
                                evaluation = tech_interview.evaluate_answer(question, transcription, domain)
                            
                            # Update the evaluation in results
                            st.session_state.results[results_key][-1]["evaluation"] = evaluation
                            st.session_state.show_evaluation = True
                            st.rerun()
                
                if st.button("Re-record", key=f"rerecord_{current_idx}"):
                    st.session_state.audio_data = None
                    st.rerun()
        else:
            # Evaluation display section
            evaluation = st.session_state.results[results_key][-1]["evaluation"]
            
            st.subheader("Your Answer Evaluation")
            # col1 = st.columns(1)
            # with col1:
            st.metric("Score", f"{evaluation['score']}/10")
            # with col2:
            #     st.metric("Feedback", evaluation.get('feedback', 'No feedback'))
            
            st.write("**Feedback:**")
            st.write(evaluation.get('feedback', 'No feedback available'))
            
            if 'improvement_tips' in evaluation:
                st.write("**Improvement Tips:**")
                for tip in evaluation['improvement_tips']:
                    st.write(f"- {tip}")
            
            if 'knowledge_gaps' in evaluation:
                st.write("**Knowledge Gaps:**")
                for gap in evaluation['knowledge_gaps']:
                    st.write(f"- {gap}")
            
            st.progress(evaluation['score']/10)
            
            # Next question button
            if st.button("Next Question", key=f"next_{current_idx}"):
                st.session_state.current_question_idx += 1
                st.session_state.audio_data = None
                st.session_state.show_evaluation = False
                st.rerun()
    else:
        st.success(f"{round_type} Round Completed!")
        save_results(st.session_state.results)
        
        if round_type == "HR":
            if st.button("Continue to Technical Round"):
                st.session_state.current_round = "tech_round"
                st.session_state.current_question_idx = 0
                st.session_state.show_evaluation = False
                st.rerun()
        else:
            if st.button("View Results Dashboard"):
                st.session_state.current_round = "dashboard"
                st.rerun()

def main():
    st.set_page_config(page_title="EVALIA", layout="wide")
        
    # Initialize session state - MUST be first operation
    initialize_session_state()
    
    # Home Page - Domain Identification
    if st.session_state.current_round is None:
        st.title("EVALIA")
        st.subheader("AI Interview Prep Friend !")
        st.write("Upload a job description to get started")
        
        job_description = st.text_area("Paste Job Description Here", height=200, key="jd_input")
        
        if st.button("Analyze Job Description"):
            if job_description.strip():
                # Add validation checks
                if len(job_description.split()) < 5:  # Minimum 5 words
                    st.error("Please enter a proper job description (at least 5 words)")
                elif not any(char.isalpha() for char in job_description):  # Check for actual text
                    st.error("Please enter meaningful text, not just numbers/symbols")
                elif len(job_description) < 30:  # Minimum character length
                    st.error("Description too short - please provide more details")
                else:
                    with st.spinner("Analyzing job description..."):
                        try:
                            predicted_domain = predict_domain(job_description)
                            if not predicted_domain or predicted_domain.lower() == "unknown":
                                st.error("Couldn't identify a valid domain - please provide a clearer job description")
                            else:
                                st.session_state.results["domain"] = predicted_domain
                                st.session_state.current_round = "domain_confirmation"
                                st.rerun()
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
            else:
                st.error("Please enter a job description")
    
    # Domain Confirmation
    elif st.session_state.current_round == "domain_confirmation":
        st.title("Confirm Job Domain")
        domain = st.session_state.results["domain"]
        st.success(f"Identified Domain: **{domain}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, this is correct", use_container_width=True):
                # Generate questions for both rounds
                with st.spinner("Preparing interview questions..."):
                    st.session_state.results["hr_questions"] = hr_interview.generate_questions(domain)
                    st.session_state.results["tech_questions"] = tech_interview.generate_questions(domain)
                st.session_state.current_round = "hr_round"
                st.rerun()
        
        with col2:
            if st.button("✏️ No, let me edit", use_container_width=True):
                st.session_state.current_round = "domain_edit"
                st.rerun()
    
    # Domain Editing
    elif st.session_state.current_round == "domain_edit":
        st.title("Enter Correct Job Domain")
        new_domain = st.text_input("Job Domain/Title", value=st.session_state.results["domain"])
        
        if st.button("Confirm Domain"):
            if new_domain.strip():
                st.session_state.results["domain"] = new_domain
                # Generate questions for both rounds
                with st.spinner("Preparing interview questions..."):
                    st.session_state.results["hr_questions"] = hr_interview.generate_questions(new_domain)
                    st.session_state.results["tech_questions"] = tech_interview.generate_questions(new_domain)
                st.session_state.current_round = "hr_round"
                st.session_state.current_question_idx = 0
                st.rerun()
            else:
                st.error("Please enter a domain/title")
    
    # HR Round
    elif st.session_state.current_round == "hr_round":
        domain = st.session_state.results["domain"]
        conduct_round("HR", domain)
    
    # Technical Round
    elif st.session_state.current_round == "tech_round":
        domain = st.session_state.results["domain"]
        conduct_round("Technical", domain)
    
    # Dashboard
    # In your main app file (replace the dashboard section)

    elif st.session_state.current_round == "dashboard":
        display_dashboard(st.session_state.results)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start New Interview"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            if st.button("Talk to Evalia"):
                st.session_state.current_round = "chatbot"
                st.rerun()

    # Add this new condition after the dashboard block
    elif st.session_state.current_round == "chatbot":
        
        # Run chatbot and check if it wants to return
        should_return = chatbot_page()
        
        if should_return:
            st.session_state.current_round = "dashboard"
            st.rerun()


if __name__ == "__main__":
    main()
