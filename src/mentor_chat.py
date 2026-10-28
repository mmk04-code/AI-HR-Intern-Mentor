"""
Conversational AI Mentor & Audio Feedback Module.
Provides interactive technical guidance, requirement walkthroughs, natural language HR actions,
and speech synthesis with offline local knowledge retrieval and live AI integration.
"""

import os
import re
import io
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from gtts import gTTS

from src.config import (
    get_primary_gemini_key,
    get_secondary_gemini_key,
    get_openai_key,
    get_gemini_model,
    get_openai_model
)
from src.ai_providers import AIProviderService, GeminiProvider, OpenAIProvider
from src.offline_knowledge import get_offline_knowledge_service
from src.document_parser import parse_spreadsheet, parse_document

logger = logging.getLogger(__name__)

LANG_CODES = {
    "English": "en",
    "Tamil": "ta",
    "Hindi": "hi"
}

LANG_GREETINGS = {
    "English": {
        "welcome": "Hello {name}! I am your AI Mentor for **{task_title}** ({module_name}). Which language would you like to speak in?",
        "options": ["English", "Tamil", "Hindi"],
        "lang_confirm": "Great! Let's continue in **English**. I will help explain your task, clarify doubts, and review your code.",
        "task_intro": "Here is a breakdown of your task:\n\n{explanation}\n\nFeel free to ask questions or submit your code/ZIP when ready!",
        "tts_intro": "Hello {name}! Here are your task details. Feel free to ask me anything about requirements or code.",
        "eval_intro": "I've reviewed your submission (Revision {rev_num})!\n\n**Status:** {status} ({score}/100)\n\n**Strengths:**\n{strengths}\n\n**Needs Improvement:**\n{missing}\n\n**Next Steps:**\n{corrections}",
        "tts_eval": "Your submission review is complete. Current status is {status} with a score of {score}. Please address the suggested revisions."
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
        clean_text = clean_text[:300].strip()
        if not clean_text:
            return None

        fp = io.BytesIO()
        tts = gTTS(text=clean_text, lang=lang_code, slow=False)
        tts.write_to_fp(fp)
        return fp.getvalue()
    except Exception as e:
        logger.warning(f"gTTS audio generation warning: {e}")
        return None


def _call_gemini_text(prompt: str) -> Optional[str]:
    """Query Gemini only via AIProviderService."""
    res = AIProviderService.generate_text(prompt, preferred_provider="gemini")
    if res.get("success"):
        return res.get("text")
    return None


def _call_llm_text(prompt: str) -> Optional[str]:
    """Query available LLM providers (Gemini -> OpenAI) via AIProviderService."""
    res = AIProviderService.generate_text(prompt, preferred_provider="auto")
    if res.get("success"):
        return res.get("text")
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

    if req_text:
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
        explanation = _call_llm_text(prompt)
        if explanation:
            short_tts = f"Here is what you are building for {title}. Check the key requirements and ask me anything."
            return explanation, short_tts

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
    Uses live LLM if available; falls back to verified offline dataset.
    Never claims an offline response was generated by Gemini or OpenAI.
    """
    req_text = task.get("requirements_text", "")
    title = task.get("title", "")

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
    # 1. Try Live LLM
    res = AIProviderService.generate_text(prompt, preferred_provider="auto")
    if res.get("success"):
        ans = res.get("text", "")
        provider_name = res.get("provider", "AI Provider")
        formatted = f"🤖 **{provider_name} Response:**\n\n{ans}"
        return formatted, ans[:120]

    # 2. Task Context Rule Guidance
    q_lower = question.lower()
    if any(k in q_lower for k in ["validate", "validation", "title", "சரிபார்ப்பு", "सत्यापन"]):
        ans = (
            "For input validation: Make sure to check that the title string is present and has at least 5 characters. "
            "Return an HTTP 400 or 422 with a descriptive error message if invalid."
        )
        return f"📖 **Task Specification Reference:**\n\n{ans}", ans[:100]

    if any(k in q_lower for k in ["database", "model", "schema", "sqlite", "தரவுத்தளம்", "डेटाबेस"]):
        ans = (
            "For the database layer: Define models for User, Project, and TaskItem. "
            "Make sure foreign keys link TaskItem to Project and User, and add `created_at` timestamps for tracking."
        )
        return f"📖 **Task Specification Reference:**\n\n{ans}", ans[:100]

    if any(k in q_lower for k in ["test", "testing", "pytest", "unittest", "சோதனை", "परीक्षण"]):
        ans = (
            "For testing: Write unit tests verifying both success cases (creating a valid task) "
            "and edge cases (submitting an empty title or short string to verify validation fails)."
        )
        return f"📖 **Task Specification Reference:**\n\n{ans}", ans[:100]

    # 3. Offline Knowledge Search
    offline_service = get_offline_knowledge_service()
    search_res = offline_service.search(question)

    if search_res.get("found"):
        docs = search_res.get("results", [])
        top_doc = docs[0]
        answer_body = top_doc.get("answer", "")
        source_label = top_doc.get("source_file", "Local Reference")

        ref_lines = [
            f"📖 **Offline Reference Knowledge ({source_label}):**\n",
            f"**{top_doc.get('question')}**\n",
            f"{answer_body}"
        ]
        if "example" in top_doc:
            ref_lines.append(f"\n```python\n{top_doc['example']}\n```")

        if len(docs) > 1:
            ref_lines.append("\n*Related reference topics:*")
            for d in docs[1:]:
                ref_lines.append(f"• **{d.get('question')}** ({d.get('source_file')})")

        output_md = "\n".join(ref_lines)
        return output_md, answer_body[:100]

    # 4. Explicit No-Match message
    no_match_text = offline_service.NO_MATCH_MESSAGE
    return f"ℹ️ {no_match_text}", no_match_text[:100]


def answer_hr_question(question: str) -> str:
    """Answer general HR chat messages with the configured LLM and a clear fallback."""
    prompt = f"""
You are the conversational HR assistant for an internship task review application.
Help the coordinator onboard interns, assign tasks, understand review progress,
and use the app. Reply naturally and briefly, matching the language of the
coordinator's message. Do not claim to have assigned tasks or accessed records;
the app handles those actions separately.

Coordinator message:
{question[:2000]}
"""
    answer = _call_llm_text(prompt)
    if answer:
        return answer

    message = question.strip().lower()
    if any(word in message for word in ("வணக்கம்", "vanakkam")):
        return "வணக்கம்! பயிற்சியாளர்களைச் சேர்க்கவும், பணிகளை ஒதுக்கவும், அல்லது சமர்ப்பிப்பு நிலையைப் பார்க்கவும் நான் உதவுகிறேன்."
    if any(word in message for word in ("नमस्ते", "नमस्कार")):
        return "नमस्ते! मैं इंटर्न जोड़ने, कार्य सौंपने या सबमिशन की स्थिति देखने में मदद कर सकता हूँ।"
    if message in {"hi", "hello", "hey", "வணக்கம்", "नमस्ते", "नमस्कार"}:
        return "Hello! I can help you add interns, assign tasks, or check submission progress. What would you like to do?"
    return "I can help add interns, assign tasks, or check submission progress. Tell me what you need."


def requested_roster_display_limit(prompt: str) -> Optional[int]:
    """Return the requested count for explicit roster display requests."""
    if not re.search(r"\b(show|display|list|fetch|view)\b|பெயர்|नाम", prompt, re.IGNORECASE):
        return None
    match = re.search(r"\b(?:first|top)\s+(\d+)\b|\b(?:first|top)\s+(\w+)\b", prompt, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1) or match.group(2)
    try:
        count = int(value)
    except ValueError:
        count = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}.get(value.lower())
    return count if count and 1 <= count <= 100 else None


def answer_roster_request(prompt: str, roster_records: List[Dict[str, Any]], limit: int) -> tuple[str, bool]:
    """Ask Gemini to answer a roster query using only the requested rows."""
    selected = roster_records[:limit]
    names = [str(record.get("name", "")).strip() for record in selected]
    names = [name for name in names if name]
    prompt_for_model = f"""
You are answering an HR coordinator's request about the attached intern roster.
Use only the exact names in the supplied data. Do not invent, add, or infer names.
The supplied data has already been limited to the requested first {limit} rows.
Answer naturally in one short sentence, then list those names. Do not provide code.

Coordinator request: {prompt[:1000]}
Names available to answer with:
{json.dumps(names, ensure_ascii=False)}
"""
    answer = _call_gemini_text(prompt_for_model)
    if answer:
        return f"🤖 Gemini ({get_gemini_model()}):\n\n{answer}", True

    listed_names = "\n".join(f"{index}. {name}" for index, name in enumerate(names, 1))
    return f"📋 Roster preview (fallback; Gemini unavailable):\n\n{listed_names or 'No names found in the roster.'}", False


def test_gemini_connection() -> tuple[bool, str]:
    """Test primary Gemini API connectivity using GeminiProvider."""
    key = get_primary_gemini_key()
    if not key:
        return False, "Gemini is not configured. Check GEMINI_API_KEY in .env."
    return GeminiProvider.test_connection(key, get_gemini_model())


def test_openai_connection() -> tuple[bool, str]:
    """Test OpenAI API connectivity using OpenAIProvider."""
    key = get_openai_key()
    if not key:
        return False, "OpenAI is not configured. Check OPENAI_API_KEY in .env."
    return OpenAIProvider.test_connection(key, get_openai_model())


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
