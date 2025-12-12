from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
from groq import Groq
import re

load_dotenv()

chatbot_bp = Blueprint('chatbot', __name__)

# -------------------------------
# SAFE GROQ CLIENT INITIALIZATION
# -------------------------------
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("ERROR: GROQ_API_KEY is NOT set in environment variables.")
    client = None
else:
    try:
        # Fix proxy error: ensure correct httpx version is installed
        client = Groq(api_key=GROQ_KEY)
    except Exception as e:
        print("Groq client initialization failed:", e)
        client = None


# -------------------------------
# HEART KEYWORDS
# -------------------------------
HEART_RELATED_KEYWORDS = [
    "heart", "cardiac", "cardiovascular", "cholesterol", "blood pressure",
    "heart attack", "heart failure", "hypertension", "arrhythmia", "angina",
    "atherosclerosis", "myocardial infarction", "stroke", "heart disease",
    "heart health", "heart rate", "heartbeat", "palpitations", "edema",
    "shortness of breath", "chest pain", "cardiomyopathy", "heart valve",
    "coronary artery", "heart surgery", "heart transplant", "pacemaker",
    "defibrillator", "heart monitor", "echocardiogram", "electrocardiogram",
    "stress test", "cardiac arrest", "heart rhythm", "heart murmur",
    "heart inflammation", "heart failure symptoms",
    "heart attack symptoms", "heart health tips",
    "heart healthy diet", "heart exercise", "heart medication",
    "heart risk factors", "heart prevention"
]


def is_heart_related(message: str) -> bool:
    message = message.lower()
    return any(keyword in message for keyword in HEART_RELATED_KEYWORDS)


# -------------------------------
# FORMAT RESPONSE (HTML OUTPUT)
# -------------------------------
def format_response(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()

    # Convert markdown bold to HTML <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    lines = text.split("\n")
    html_parts = []
    list_buffer = None  # ("ul"/"ol", items)

    def flush_list():
        nonlocal list_buffer
        if list_buffer:
            list_type, items = list_buffer
            html_parts.append(f"<{list_type}>")
            for it in items:
                html_parts.append(f"<li>{it}</li>")
            html_parts.append(f"</{list_type}>")
            list_buffer = None

    for line in lines:
        raw = line.strip()
        if not raw:
            flush_list()
            continue

        # UL
        m_ul = re.match(r"^(\*|-|•)\s+(.*)$", raw)
        # OL
        m_ol = re.match(r"^(\d+)[\.\)]\s+(.*)$", raw)

        if m_ul:
            if not list_buffer or list_buffer[0] != "ul":
                flush_list()
                list_buffer = ("ul", [])
            list_buffer[1].append(m_ul.group(2).strip())

        elif m_ol:
            if not list_buffer or list_buffer[0] != "ol":
                flush_list()
                list_buffer = ("ol", [])
            list_buffer[1].append(m_ol.group(2).strip())

        else:
            flush_list()
            html_parts.append(f"<p>{raw}</p>")

    flush_list()
    return "\n".join(html_parts)


# -------------------------------
# GROQ GENERATION FUNCTION
# -------------------------------
def groq_generate(prompt: str) -> str:
    if client is None:
        return "Groq client is not initialized. Please check GROQ_API_KEY settings."

    try:
        system_message = (
            "You are a helpful medical assistant for heart-health. "
            "Respond clearly in plain text. Do NOT use raw asterisks (*) for bullets. "
            "Use simple numbered sentences or new lines. Avoid incomplete responses."
        )

        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print("Groq API Error:", e)
        return "Sorry, I am unable to process your request right now. Please try again later."


# -------------------------------
# FLASK ROUTE
# -------------------------------
@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": "Please enter a valid message."}), 400

    if not is_heart_related(user_msg):
        return jsonify({"reply": "I'm here to help with HEART-related topics only. Please ask about heart health ❤️"}), 200

    bot_reply = groq_generate(user_msg)
    formatted = format_response(bot_reply)

    return jsonify({"reply": formatted})
