"""
Mentor Chat module for Internship Task Review Assistant.
Provides conversational AI mentorship for interns (task explanation, Q&A, submission review)
and conversational task assignment & progress tracking for HR coordinators.
Supports English, Tamil, and Hindi natural dialogue with TTS voice generation.
"""

import os
import io
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from gtts import gTTS

from src.database import (
    get_task,
    get_all_tasks,
    get_candidates,
    get_candidate,
    get_submissions_for_task,
    get_reviews_for_task,
    get_schedule_for_review,
    create_candidate,
    create_task
)
from src.document_parser import parse_document, parse_spreadsheet
from src.ai_review import get_gemini_client, analyze_submission
from src.review_service import process_submission_and_evaluate, schedule_and_notify

logger = logging.getLogger(__name__)

LANG_CODES = {
    "English": "en",
    "Tamil": "ta",
    "Hindi": "hi"
}

LANG_GREETINGS = {
    "English": {
        "welcome": "Hello {name}! I'm your AI Mentor for your **{task_title}** ({module_name}) assignment. Which language would you prefer to converse in?",
        "options": ["English", "Tamil", "Hindi"],
        "lang_confirm": "Great! We'll continue in **English**. Let me walk you through what you'll be building.",
        "task_intro": "Here is an overview of your assigned task:\n\n{explanation}\n\nYou can ask me any technical questions, request hints, or attach your code / GitHub repo right here when you're ready for review!",
        "tts_intro": "Welcome {name}! I am your AI Mentor. Here is your task: {summary_short}. Feel free to ask questions or submit your code when ready.",
        "eval_intro": "I've reviewed your latest submission (Revision {rev_num}) against the official requirements!\n\n**Status:** {status} ({score}/100)\n\n**Strengths:**\n{strengths}\n\n**Things to fix:**\n{missing}\n\n**Next Steps:**\n{corrections}",
        "tts_eval": "Your submission review is complete. Overall status is {status} with a score of {score} out of 100. Please check the feedback and submit your revision."
    },
    "Tamil": {
        "welcome": "வணக்கம் {name}! உங்கள் **{task_title}** ({module_name}) பணிக்கான AI வழிகாட்டி நான். எந்த மொழியில் உரையாட விரும்புகிறீர்கள்?",
        "options": ["English", "Tamil", "Hindi"],
        "lang_confirm": "மகிழ்ச்சி! நாம் **தமிழில்** தொடருவோம். உங்கள் பணிக்கான முக்கிய குறிப்புகளை விளக்குகிறேன்.",
        "task_intro": "உங்கள் பணிக்கான சுருக்கம்:\n\n{explanation}\n\nஉங்களுக்கு ஏதேனும் சந்தேகங்கள் இருந்தால் கேட்கலாம், அல்லது உங்கள் நிரல் கோப்புகளை / GitHub இணைப்பை இங்கே பதிவேற்றி ஆய்வு செய்யலாம்!",
        "tts_intro": "வணக்கம் {name}! உங்கள் பணி பற்றிய விவரங்கள் பகிரப்பட்டுள்ளன. ஏதேனும் சந்தேகம் இருந்தால் என்னிடம் கேளுங்கள்.",
        "eval_intro": "உங்கள் சமர்ப்பிப்பு (பதிப்பு {rev_num}) ஆய்வு செய்யப்பட்டது!\n\n**முடிவு:** {status} ({score}/100)\n\n**நன்றாக செய்தவை:**\n{strengths}\n\n**சரிசெய்ய வேண்டியவை:**\n{missing}\n\n**அடுத்த கட்ட நடவடிக்கைகள்:**\n{corrections}",
        "tts_eval": "உங்கள் பணி மதிப்பாய்வு முடிந்தது. தற்போதைய நிலை {status}, மதிப்பெண் {score} நூற்றுக்கு. பரிந்துரைகளை பின்பற்றி மீண்டும் சமர்ப்பிக்கவும்."
    },
    "Hindi": {
        "welcome": "नमस्ते {name}! मैं आपके **{task_title}** ({module_name}) कार्य के लिए आपका AI मेंटर हूँ। आप किस भाषा में बातचीत करना पसंद करेंगे?",
        "options": ["English", "Tamil", "Hindi"],
        "lang_confirm": "बहुत बढ़िया! हम **हिंदी** में बातचीत जारी रखेंगे। मैं आपको आपके कार्य के बारे में समझाता हूँ।",
        "task_intro": "आपके कार्य का संक्षिप्त विवरण:\n\n{explanation}\n\nआप मुझसे कोई भी तकनीकी प्रश्न पूछ सकते हैं, या तैयार होने पर अपनी कोड फ़ाइलें या GitHub लिंक यहाँ जमा कर सकते हैं!",
        "tts_intro": "नमस्ते {name}! आपके कार्य का विवरण तैयार है। कोई भी सवाल हो तो बेझिझक पूछें।",
        "eval_intro": "मैंने आपके काम (संशोधन {rev_num}) की समीक्षा की है!\n\n**परिणाम:** {status} ({score}/100)\n\n**सकारात्मक बिंदु:**\n{strengths}\n\n**सुधार की आवश्यकता:**\n{missing}\n\n**अगले कदम:**\n{corrections}",
        "tts_eval": "आपके असाइनमेंट की समीक्षा पूरी हो गई है। स्थिति {status} है और स्कोर {score} है। सुधार करके पुनः सबमिट करें।"
    }
}


def generate_tts_audio(text: str, language: str = "English") -> Optional[bytes]:
    """
    Generate spoken MP3 audio bytes using gTTS.
    Returns bytes or None if generation encounters an issue.
    """
    if not text or not text.strip():
        return None
    try:
        lang_code = LANG_CODES.get(language, "en")
        clean_text = re.sub(r"[\*#_`~\[\]\(\)\<\>]", "", text)
        clean_text = clean_text[:300].strip()  # Natural speech chunk
        if not clean_text:
            return None

        fp = io.BytesIO()
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        logger.warning(f"gTTS audio generation warning: {e}")
        return None


def explain_task_conversationally(
    task: Dict[str, Any],
    language: str = "English"
) -> Tuple[str, str]:
    """
    Generate friendly conversational explanation of the task requirements.
    Returns (markdown_explanation, short_tts_summary).
    """
    title = task.get("title", "Internship Task")
    req_text = task.get("requirements_text", "")
    genai_module, model = get_gemini_client()

    if model is not None and req_text:
        try:
            prompt = f"""
You are a warm, supportive Senior Engineering Mentor explaining an intern's assigned task in a conversational, engaging, friendly tone.

Task Title: {title}
Company Requirements:
{req_text[:3000]}

Explain what the intern needs to build in simple, clear, encouraging language.
Target Language: {language}.
Format with neat bullet points:
1. What the project is
2. Key features to build
3. Validation & quality tips
Keep it under 180 words. Do not use robotic jargon.
"""
            resp = model.generate_content(prompt)
            explanation = resp.text.strip()
            short_tts = f"Here is what you are building for {title}. Check the key requirements and ask me anything."
            return explanation, short_tts
        except Exception as e:
            logger.warning(f"Gemini conversational task explanation fallback: {e}")

    # Fallback explanation
    if language == "Tamil":
        exp = (
            f"**{title}** பணிக்கான முக்கிய தேவைகள்:\n\n"
            "• **தரவுத்தள வடிவமைப்பு**: தேவையான அட்டவணைகள் மற்றும் உறவுகளை உருவாக்கவும்.\n"
            "• **முக்கிய API வழிகள்**: பதிவுகளை உருவாக்க, பட்டியலிட மற்றும் திருத்த இறுதிப் புள்ளிகளை அமைக்கவும்.\n"
            "• **சரிபார்ப்பு விதிகள்**: தவறான உள்ளீடுகளைத் தடுக்க முறையான சரிபார்ப்புகளைச் சேர்க்கவும்.\n"
            "• **பிழை கையாளுதல்**: எதிர்பாராத பிழைகளை மென்மையாகக் கையாளவும்.\n"
            "• **ஆவணங்கள் & சோதனைகள்**: பயன்பாட்டு வழிகாட்டி மற்றும் எளிய அலகு சோதனைகளை எழுதவும்."
        )
        short_tts = f"{title} பணிக்கான முக்கிய குறிப்புகள் தயாராக உள்ளன."
    elif language == "Hindi":
        exp = (
            f"**{title}** कार्य के लिए मुख्य आवश्यकताएं:\n\n"
            "• **डेटाबेस डिज़ाइन**: आवश्यक तालिकाओं और संबंधों का निर्माण करें।\n"
            "• **मुख्य API रूट्स**: डेटा बनाने, सूचीबद्ध करने और अपडेट करने के लिए एंडपॉइंट्स बनाएं।\n"
            "• **सत्यापन**: अमान्य डेटा को रोकने के लिए उचित सत्यापन जोड़ें।\n"
            "• **त्रुटि प्रबंधन**: अप्रत्याशित त्रुटियों को सुचारू रूप से संभालें।\n"
            "• **दस्तावेज़ीकरण और परीक्षण**: README और बुनियादी यूनिट परीक्षण शामिल करें।"
        )
        short_tts = f"{title} कार्य के मुख्य बिंदु यहाँ दिए गए हैं।"
    else:
        exp = (
            f"Key deliverables for **{title}**:\n\n"
            "• **Database Schema & Models**: Implement clean data entities with relationships and audit timestamps.\n"
            "• **API Endpoints & Logic**: Build routes to create, list, and update records.\n"
            "• **Input Validation**: Enforce required fields and length constraints.\n"
            "• **Error Handling**: Gracefully handle missing resources (404s) and database errors.\n"
            "• **Testing & Docs**: Provide a clear README.md and test cases."
        )
        short_tts = f"Here are the core requirements for {title}. Feel free to ask any question!"

    return exp, short_tts


def answer_intern_question(
    question: str,
    task: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    language: str = "English"
) -> Tuple[str, str]:
    """
    Answer intern's technical question conversationally based on requirements.
    """
    genai_module, model = get_gemini_client()
    req_text = task.get("requirements_text", "")
    title = task.get("title", "")

    if model is not None:
        try:
            history_context = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chat_history[-6:]])
            prompt = f"""
You are an encouraging, experienced Senior AI Mentor helping an intern with their task: '{title}'.
Requirements context:
{req_text[:2500]}

Recent chat context:
{history_context}

Intern's Question:
{question}

Answer the intern warmly, pedagogically, and concisely in {language}.
Provide helpful hints, code architecture tips, or clarification without doing all the work for them.
Keep it under 150 words.
"""
            resp = model.generate_content(prompt)
            answer = resp.text.strip()
            return answer, answer[:120]
        except Exception as e:
            logger.warning(f"Gemini Q&A fallback: {e}")

    # Fallback answer based on keywords
    q_lower = question.lower()
    if any(k in q_lower for k in ["validate", "validation", "title", "சரிபார்ப்பு", "सत्यापन"]):
        ans = (
            "For input validation: Make sure to check that the title string is present and has at least 5 characters. "
            "Return an HTTP 400 or 422 with a descriptive error message if invalid."
        )
    elif any(k in q_lower for k in ["database", "model", "schema", "sqlite", "தரவுத்தளம்", "डेटाबेस"]):
        ans = (
            "For the database layer: Define models for User, Project, and TaskItem. "
            "Make sure foreign keys link TaskItem to Project and User, and add `created_at` timestamps for tracking."
        )
    elif any(k in q_lower for k in ["test", "testing", "pytest", "unittest", "சோதனை", "परीक्षण"]):
        ans = (
            "For testing: Write unit tests verifying both success cases (creating a valid task) "
            "and edge cases (submitting an empty title or short string to verify validation fails)."
        )
    elif any(k in q_lower for k in ["error", "404", "exception", "பிழை", "त्रुटि"]):
        ans = (
            "For error handling: Ensure your API endpoints return clean JSON error responses "
            "instead of crashing or returning raw stack traces."
        )
    else:
        ans = (
            f"That's a good question regarding {title}. Follow the company specifications: break your work down into "
            "the database model, API routes, input validation, and unit tests. Let me know which component you'd like a hint on!"
        )

    return ans, ans[:100]


def process_hr_instruction(
    prompt: str,
    attached_file_bytes: Optional[bytes] = None,
    attached_filename: Optional[str] = None,
    secondary_file_bytes: Optional[bytes] = None,
    secondary_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse natural HR instructions and attached spreadsheets/documents.
    Returns structured draft assignment or response.
    """
    roster_records = []
    requirements_text = ""
    req_filename = None

    # Inspect first attachment
    if attached_file_bytes and attached_filename:
        ext = os.path.splitext(attached_filename)[1].lower()
        if ext in [".xlsx", ".xls", ".csv"]:
            sp_res = parse_spreadsheet(attached_file_bytes, attached_filename)
            if sp_res["success"]:
                roster_records = sp_res["records"]
        elif ext in [".pdf", ".docx", ".txt", ".md"]:
            doc_res = parse_document(attached_file_bytes, attached_filename)
            if doc_res["success"]:
                requirements_text = doc_res["text"]
                req_filename = attached_filename

    # Inspect second attachment if provided
    if secondary_file_bytes and secondary_filename:
        ext2 = os.path.splitext(secondary_filename)[1].lower()
        if ext2 in [".xlsx", ".xls", ".csv"] and not roster_records:
            sp_res = parse_spreadsheet(secondary_file_bytes, secondary_filename)
            if sp_res["success"]:
                roster_records = sp_res["records"]
        elif ext2 in [".pdf", ".docx", ".txt", ".md"] and not requirements_text:
            doc_res = parse_document(secondary_file_bytes, secondary_filename)
            if doc_res["success"]:
                requirements_text = doc_res["text"]
                req_filename = secondary_filename

    # Extract task title and deadline from prompt
    deadline = "Upcoming Review"
    m_dead = re.search(r"deadline\s*(?:is|:)?\s*([a-zA-Z0-9\s,]+?)(?:\.|$)", prompt, re.IGNORECASE)
    if m_dead:
        deadline = m_dead.group(1).strip()

    title = "Internship Technical Assignment"
    m_title = re.search(r"(?:task|assignment|module)\s*(?:named|called|is|:)?\s*[\"']?([^\"'\.\n]+)[\"']?", prompt, re.IGNORECASE)
    if m_title and len(m_title.group(1).strip()) > 3:
        title = m_title.group(1).strip()
    elif requirements_text:
        first_line = requirements_text.splitlines()[0].strip().lstrip("#").strip()
        if len(first_line) > 5:
            title = first_line[:60]

    return {
        "has_assignment_intent": bool(roster_records or requirements_text or "assign" in prompt.lower() or "import" in prompt.lower()),
        "interns": roster_records,
        "requirements_text": requirements_text,
        "requirements_filename": req_filename,
        "task_title": title,
        "deadline": deadline,
        "raw_prompt": prompt
    }
