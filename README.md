# 🎤 Evalia – Voice-based Interview Assistant

Evalia is an AI-powered, voice-enabled interview preparation tool that simulates real HR and technical interviews.  
It helps candidates practice speaking, get evaluated on their answers, and track their progress with a clear dashboard.

---

## 🚀 Features
- Voice-based HR & technical interview simulation
- AI-powered evaluation and feedback
- Domain prediction from job description
- Dashboard with scores, insights, and answer playback
- Chat-like conversational flow for an engaging experience

---

## 🛠️ Tech Stack
| Component                  | Technology                     |
|----------------------------|--------------------------------|
| Frontend & UI              | Streamlit                      |
| Voice Recording            | streamlit-mic-recorder, WebRTC |
| Speech-to-Text             | Google Speech-to-Text API      |
| NLP & Evaluation           | OpenAI / Groq (GPT)            |
| State & Storage            | Streamlit session state, JSON  |
| Deployment                 | Docker, Google Cloud Platform  |

---

## ✨ Why This Stack?
- **Streamlit**: Quick, interactive UI without heavy frontend work.
- **Google Speech-to-Text**: Highly accurate and scalable transcription.
- **OpenAI/Groq GPT**: Reliable NLP for answer evaluation.
- Lightweight and cloud-ready for easy deployment.

---

## 📈 Future Enhancements
- Multilingual and regional accent support
- Video response and body language analysis
- Advanced dashboard with trends and graphs
- LinkedIn/email integration for sharing results
- Group/mock interview mode

---

## 🧪 Challenges Overcome
- Real-time audio capture and playback in Streamlit
- Accurate transcription despite noise and accent variability
- Seamless session management and data persistence
- All challenges have been addressed with a robust design, ensuring no recurring issues.

---

## 🔧 Setup & Run

### Prerequisites
- Python ≥ 3.8
- Google Cloud credentials for Speech-to-Text
- OpenAI or Groq API key

### Installation
```bash
git clone https://github.com/yourusername/evalia.git
cd evalia
pip install -r requirements.txt
