import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import re

def chatbot_page():
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))


    st.title("💬 Career Assistant Chatbot")
    st.caption("Ask me anything about jobs, studies, or interview preparation")

    # Inject CSS for styled chat bubbles
    st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-top: 30px;
    }
    .chat-row {
        display: flex;
        align-items: flex-start;
    }
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.bot {
        justify-content: flex-start;
    }
    .chat-bubble {
        max-width: 65%;
        padding: 12px 16px;
        border-radius: 18px;
        font-size: 16px;
        line-height: 1.4;
        word-break: break-word;
    }
    .user .chat-bubble {
        background-color: #EFEEEA;
        color: #000;
        border-bottom-right-radius: 0;
    }
    .bot .chat-bubble {
        background-color: #94B4C1;
        color: #000;
        border-bottom-left-radius: 0;
    }
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        font-weight: bold;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 10px;
        flex-shrink: 0;
    }
    .avatar.user {
        background-color: #ec407a;
    }
    .avatar.bot {
        background-color: #9c27b0;
    }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    """, unsafe_allow_html=True)

    # Initialize chat history with strict system prompt
    if "chatbot_history" not in st.session_state:
        st.session_state.chatbot_history = [{
            "role": "system",
            "content": (
                "You are a professional career assistant that only answers questions about: "
                "1. Job search strategies and techniques "
                "2. Study methods and educational topics "
                "3. Interview preparation and techniques "
                "4. Resume and cover letter writing "
                "5. Career development and advancement "
                "6. Workplace skills and professional growth "
                "7. Technical skills for specific job roles "
                "8. Salary negotiation and benefits "
                "9. Networking and professional relationships "
                "10. Industry trends and insights "
                "For any other topics, respond with: "
                "'I specialize in career and education-related topics. "
                "How can I help you with job search, studies, or interview preparation?' "
                "Never use asterisks (*) or markdown formatting in responses. "
                "Provide clear, concise answers without bullet points or numbered lists."
            )
        }]

    user_input = st.chat_input("Ask about jobs, studies, or interviews...")

    if user_input:
        st.session_state.chatbot_history.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.chatbot_history,
                temperature=0.3  # Lower temperature for more focused responses
            )
            reply = response.choices[0].message.content
            
            # Clean the response
            reply = re.sub(r'\*', '', reply)  # Remove all asterisks
            reply = reply.replace('•', '')  # Remove bullet points
            reply = re.sub(r'\d+\.\s', '', reply)  # Remove numbered lists
            
            # Check if response is off-topic
            off_topic_keywords = ['sorry', "can't help", "don't know", "not qualified", "not my area"]
            if any(keyword in reply.lower() for keyword in off_topic_keywords):
                reply = "I specialize in career and education-related topics. How can I help you with job search, studies, or interview preparation?"
                
        except Exception as e:
            reply = f"Error processing your request. Please try again later. ({str(e)})"

        st.session_state.chatbot_history.append({"role": "assistant", "content": reply})

    # Render chat UI
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chatbot_history[1:]:  # Skip system prompt
        role = msg["role"]
        content = msg["content"].replace("\n", "<br>")

        if role == "user":
            st.markdown(f'''
            <div class="chat-row user">
                <div class="chat-bubble user">{content}</div>
                <div class="avatar user"><i class="fa-solid fa-circle-user"></i></div>
            </div>
            ''', unsafe_allow_html=True)
        elif role == "assistant":
            st.markdown(f'''
            <div class="chat-row bot">
                <div class="avatar bot"><i class="fa-brands fa-bots"></i></div>
                <div class="chat-bubble bot">{content}</div>
            </div>
            ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("⬅️ Back to Interview"):
        return True
    return False

if __name__ == "__main__":

    chatbot_page()
