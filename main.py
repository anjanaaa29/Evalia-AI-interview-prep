import os
import json
import logging
import streamlit as st
from voice import VoiceProcessor
from domain import predict_domain
from hr import HRInterview
from tech import TechnicalInterview
from dashboard import display_dashboard
from chatbot import chatbot_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("interview_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize all components
try:
    voice_processor = VoiceProcessor()
    hr_interview = HRInterview()
    tech_interview = TechnicalInterview()
except Exception as e:
    logger.error(f"Failed to initialize components: {str(e)}")
    st.error("Failed to initialize application components. Please try again later.")
    st.stop()

def save_results(results: dict) -> bool:
    """
    Save interview results to JSON file.
    
    Args:
        results (dict): Dictionary containing interview results to be saved
        
    Returns:
        bool: True if save was successful, False otherwise
        
    Raises:
        IOError: If there's an issue writing to the file
        TypeError: If results can't be serialized to JSON
    """
    try:
        with open("interview_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Results saved successfully")
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save results: {str(e)}")
        st.error("Failed to save interview results.")
        return False

def initialize_session_state() -> None:
    """
    Initialize all required session state variables with default values.
    
    This function ensures all required keys exist in the session state
    with appropriate default values. It handles nested dictionaries properly.
    
    Raises:
        RuntimeError: If session state initialization fails
    """
    try:
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
            'show_evaluation': False
        }
        
        for key, default_value in required_state.items():
            if key not in st.session_state:
                if isinstance(default_value, dict):
                    st.session_state[key] = default_value.copy()
                else:
                    st.session_state[key] = default_value
        logger.debug("Session state initialized successfully")
    except Exception as e:
        logger.critical(f"Session state initialization failed: {str(e)}")
        raise RuntimeError("Failed to initialize application state")

def conduct_round(round_type: str, domain: str) -> None:
    """
    Conduct an interview round (HR or Technical) one question at a time.
    
    Handles question display, audio recording, answer submission, and evaluation
    display. Manages the flow between questions and rounds.
    
    Args:
        round_type (str): Type of round ("HR" or "Technical")
        domain (str): Job domain being interviewed for
        
    Raises:
        ValueError: If round_type is invalid
        RuntimeError: If critical components fail during the round
    """
    if round_type.lower() not in ["hr", "technical"]:
        raise ValueError(f"Invalid round type: {round_type}")
    
    try:
        logger.info(f"Starting {round_type} round for domain: {domain}")
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
                logger.debug(f"Displaying question {current_idx+1}/{len(questions)}")
                st.subheader(f"Question {current_idx+1} of {len(questions)}")
                st.markdown(f"**{question}**")
                
                # Voice recording section
                try:
                    audio_data = voice_processor.record_audio(f"{round_type}_{current_idx}")
                except Exception as e:
                    logger.error(f"Audio recording failed: {str(e)}")
                    st.error("Failed to record audio. Please try again.")
                    return
                
                if audio_data:
                    st.session_state.audio_data = audio_data
                    st.audio(audio_data['bytes'], format="audio/wav")
                    
                    if st.button("Submit Answer", key=f"submit_{current_idx}"):
                        with st.spinner("Processing your answer..."):
                            try:
                                transcription = voice_processor.transcribe_audio(audio_data)
                            except Exception as e:
                                logger.error(f"Audio transcription failed: {str(e)}")
                                st.error("Failed to transcribe your answer. Please try again.")
                                return
                            
                            if transcription:
                                # Save results using consistent key
                                st.session_state.results[results_key].append({
                                    "question": question,
                                    "answer": transcription,
                                    "evaluation": None
                                })
                                
                                # Evaluate answer
                                try:
                                    if round_type == "HR":
                                        evaluation = hr_interview.evaluate_answer(question, transcription)
                                    else:
                                        evaluation = tech_interview.evaluate_answer(question, transcription, domain)
                                except Exception as e:
                                    logger.error(f"Answer evaluation failed: {str(e)}")
                                    st.error("Failed to evaluate your answer. Please try again.")
                                    return
                                
                                # Update the evaluation in results
                                st.session_state.results[results_key][-1]["evaluation"] = evaluation
                                st.session_state.show_evaluation = True
                                logger.info(f"Question {current_idx+1} evaluation completed")
                                st.rerun()
                
                    if st.button("Re-record", key=f"rerecord_{current_idx}"):
                        st.session_state.audio_data = None
                        st.rerun()
            else:
                # Evaluation display section
                evaluation = st.session_state.results[results_key][-1]["evaluation"]
                
                st.subheader("Your Answer Evaluation")
                st.metric("Score", f"{evaluation['score']}/10")
                
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
                    logger.debug(f"Moving to question {st.session_state.current_question_idx+1}")
                    st.rerun()
        else:
            st.success(f"{round_type} Round Completed!")
            if not save_results(st.session_state.results):
                return
            
            if round_type == "HR":
                if st.button("Continue to Technical Round"):
                    st.session_state.current_round = "tech_round"
                    st.session_state.current_question_idx = 0
                    st.session_state.show_evaluation = False
                    logger.info("Transitioning to technical round")
                    st.rerun()
            else:
                if st.button("View Results Dashboard"):
                    st.session_state.current_round = "dashboard"
                    logger.info("Transitioning to results dashboard")
                    st.rerun()
    except Exception as e:
        logger.critical(f"{round_type} round failed: {str(e)}")
        raise RuntimeError(f"Failed to conduct {round_type} round")

def main() -> None:
    """
    Main application function that controls the interview flow.
    
    Handles page routing, state management, and the overall interview process.
    Implements a finite state machine pattern for interview stages.
    """
    try:
        st.set_page_config(page_title="EVALIA", layout="wide")
        logger.info("Application started")
            
        # Initialize session state - MUST be first operation
        initialize_session_state()
        
        # Home Page - Domain Identification
        if st.session_state.current_round is None:
            logger.debug("Displaying home page")
            st.title("EVALIA")
            st.subheader("AI Interview Prep Friend !")
            st.write("Upload a job description to get started")
            
            job_description = st.text_area("Paste Job Description Here", height=200, key="jd_input")
            
            if st.button("Analyze Job Description"):
                if job_description.strip():
                    # Add validation checks
                    if len(job_description.split()) < 5:
                        st.error("Please enter a proper job description (at least 5 words)")
                        logger.warning("Job description too short")
                    elif not any(char.isalpha() for char in job_description):
                        st.error("Please enter meaningful text, not just numbers/symbols")
                        logger.warning("Job description contains no alphabetic characters")
                    elif len(job_description) < 30:
                        st.error("Description too short - please provide more details")
                        logger.warning("Job description character count too low")
                    else:
                        with st.spinner("Analyzing job description..."):
                            try:
                                predicted_domain = predict_domain(job_description)
                                if not predicted_domain or predicted_domain.lower() == "unknown":
                                    st.error("Couldn't identify a valid domain - please provide a clearer job description")
                                    logger.warning("Domain prediction returned unknown")
                                else:
                                    st.session_state.results["domain"] = predicted_domain
                                    st.session_state.current_round = "domain_confirmation"
                                    logger.info(f"Predicted domain: {predicted_domain}")
                                    st.rerun()
                            except Exception as e:
                                logger.error(f"Domain prediction failed: {str(e)}")
                                st.error(f"Analysis failed: {str(e)}")
                else:
                    st.error("Please enter a job description")
                    logger.warning("Empty job description submitted")
        
        # Domain Confirmation
        elif st.session_state.current_round == "domain_confirmation":
            logger.debug("Displaying domain confirmation")
            st.title("Confirm Job Domain")
            domain = st.session_state.results["domain"]
            st.success(f"Identified Domain: **{domain}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, this is correct", use_container_width=True):
                    # Generate questions for both rounds
                    with st.spinner("Preparing interview questions..."):
                        try:
                            st.session_state.results["hr_questions"] = hr_interview.generate_questions(domain)
                            st.session_state.results["tech_questions"] = tech_interview.generate_questions(domain)
                            st.session_state.current_round = "hr_round"
                            logger.info(f"Generated questions for domain: {domain}")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Question generation failed: {str(e)}")
                            st.error("Failed to generate interview questions. Please try again.")
            
            with col2:
                if st.button("✏️ No, let me edit", use_container_width=True):
                    st.session_state.current_round = "domain_edit"
                    logger.info("User requested domain edit")
                    st.rerun()
        
        # Domain Editing
        elif st.session_state.current_round == "domain_edit":
            logger.debug("Displaying domain editing")
            st.title("Enter Correct Job Domain")
            new_domain = st.text_input("Job Domain/Title", value=st.session_state.results["domain"])
            
            if st.button("Confirm Domain"):
                if new_domain.strip():
                    st.session_state.results["domain"] = new_domain
                    # Generate questions for both rounds
                    with st.spinner("Preparing interview questions..."):
                        try:
                            st.session_state.results["hr_questions"] = hr_interview.generate_questions(new_domain)
                            st.session_state.results["tech_questions"] = tech_interview.generate_questions(new_domain)
                            st.session_state.current_round = "hr_round"
                            st.session_state.current_question_idx = 0
                            logger.info(f"User updated domain to: {new_domain}")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Question generation failed for edited domain: {str(e)}")
                            st.error("Failed to generate interview questions. Please try again.")
                else:
                    st.error("Please enter a domain/title")
                    logger.warning("Empty domain submitted during edit")
        
        # HR Round
        elif st.session_state.current_round == "hr_round":
            try:
                domain = st.session_state.results["domain"]
                conduct_round("HR", domain)
            except Exception as e:
                logger.critical(f"HR round failed: {str(e)}")
                st.error("HR round encountered an error. Please start a new interview.")
                if st.button("Start New Interview"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        
        # Technical Round
        elif st.session_state.current_round == "tech_round":
            try:
                domain = st.session_state.results["domain"]
                conduct_round("Technical", domain)
            except Exception as e:
                logger.critical(f"Technical round failed: {str(e)}")
                st.error("Technical round encountered an error. Please start a new interview.")
                if st.button("Start New Interview"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        
        # Dashboard
        elif st.session_state.current_round == "dashboard":
            try:
                display_dashboard(st.session_state.results)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Start New Interview"):
                        # Reset session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        logger.info("Starting new interview session")
                        st.rerun()
                
                with col2:
                    if st.button("Talk to Evalia"):
                        st.session_state.current_round = "chatbot"
                        logger.info("Transitioning to chatbot")
                        st.rerun()
            except Exception as e:
                logger.error(f"Dashboard display failed: {str(e)}")
                st.error("Failed to display results dashboard.")

        # Chatbot
        elif st.session_state.current_round == "chatbot":
            try:
                # Run chatbot and check if it wants to return
                should_return = chatbot_page()
                
                if should_return:
                    st.session_state.current_round = "dashboard"
                    logger.info("Returning from chatbot to dashboard")
                    st.rerun()
            except Exception as e:
                logger.error(f"Chatbot failed: {str(e)}")
                st.error("Chatbot encountered an error. Returning to dashboard.")
                st.session_state.current_round = "dashboard"
                st.rerun()

    except Exception as e:
        logger.critical(f"Application crashed: {str(e)}")
        st.error("A critical error occurred. Please refresh the page and try again.")
        st.stop()

if __name__ == "__main__":
    main()
