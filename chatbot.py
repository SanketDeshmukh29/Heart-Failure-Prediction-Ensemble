from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

chatbot_bp = Blueprint('chatbot', __name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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


import re

def format_response(text: str) -> str:
    """
    Convert model text (which may contain Markdown-like bullets and bold)
    into safe, nicely-formatted HTML paragraphs, lists, and <strong> tags.
    """

    # Normalize line endings
    text = text.replace("\r\n", "\n").strip()

    # Convert bold markdown **bold** -> <strong>bold</strong>
    def bold_repl(m):
        return f"<strong>{m.group(1)}</strong>"
    text = re.sub(r"\*\*(.+?)\*\*", bold_repl, text)

    # Split into lines and group into paragraphs / lists
    lines = text.split("\n")

    html_parts = []
    list_buffer = None      # None or ("ul"|"ol", [items])

    def flush_list():
        nonlocal list_buffer
        if list_buffer:
            typ, items = list_buffer
            if typ == "ul":
                html_parts.append("<ul>")
                for it in items:
                    html_parts.append(f"<li>{it}</li>")
                html_parts.append("</ul>")
            else:
                html_parts.append("<ol>")
                for it in items:
                    html_parts.append(f"<li>{it}</li>")
                html_parts.append("</ol>")
            list_buffer = None

    for raw in lines:
        line = raw.strip()
        if not line:
            # empty line -> paragraph break
            flush_list()
            continue

        # unordered list markers: -, * or •
        m_ul = re.match(r"^(\*|-|•)\s+(.*)$", line)
        # ordered list: 1. 2) etc.
        m_ol = re.match(r"^(\d+)[\.\)]\s+(.*)$", line)

        if m_ul:
            item = m_ul.group(2).strip()
            if list_buffer and list_buffer[0] != "ul":
                flush_list()
            if not list_buffer:
                list_buffer = ("ul", [])
            list_buffer[1].append(item)
        elif m_ol:
            item = m_ol.group(2).strip()
            if list_buffer and list_buffer[0] != "ol":
                flush_list()
            if not list_buffer:
                list_buffer = ("ol", [])
            list_buffer[1].append(item)
        else:
            # a normal paragraph line — flush any list and append as paragraph
            flush_list()
            # If line starts with a numbered bullet in plain words like "1)" already handled above
            html_parts.append(f"<p>{line}</p>")

    # flush any trailing list
    flush_list()

    # join and return
    return "\n".join(html_parts)


def groq_generate(prompt: str) -> str:
    """
    Generate a reply from Groq with a system instruction to avoid raw asterisks
    and to return complete answers. Also requests more tokens.
    """
    system_message = (
        "You are a helpful, concise medical assistant for heart-health. "
        "Respond clearly and completely in plain text. Do NOT use raw asterisks (*) or other markdown "
        "characters to denote bullets. If you want to present items, use numbered sentences or start new lines; "
        "the frontend will convert lists into HTML. Keep answers complete and avoid trailing incomplete sentences."
    )

    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        # increase token budget so answers don't get truncated
        max_tokens=400
    )

    # message.content is the proper accessor for the Groq SDK objects
    return chat_completion.choices[0].message.content



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
