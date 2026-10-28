"""
Internship Task Review Assistant - Chat-First AI Mentor
A minimalist, conversational pair-programming and mentorship platform.
Dual roles: HR / Company Coordinator and Employee / Intern.
"""

import os
import sys
import io
import json
from datetime import datetime, date, time
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables (strictly backend, never exposed in UI)
load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import (
    init_db,
    get_candidates,
    get_candidate,
    get_all_tasks,
    get_task,
    get_tasks_for_candidate,
    get_submissions_for_task,
    get_submission,
    get_reviews_for_task,
    get_review,
    get_schedule_for_review,
    get_email_logs,
    create_candidate,
    create_task
)
from src.document_parser import parse_document, parse_spreadsheet
from src.mentor_chat import (
    explain_task_conversationally,
    answer_intern_question,
    process_hr_instruction,
    generate_tts_audio,
    LANG_GREETINGS
)
from src.review_service import process_submission_and_evaluate, schedule_and_notify
from src.email_service import is_smtp_configured

# Initialize database
init_db()

# Streamlit Page Setup - Minimalist Layout
st.set_page_config(
    page_title="AI Mentor • Internship Assistant",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Minimalist Custom CSS (Gemini-inspired conversational design)
st.markdown("""
<style>
    /* Hide default Streamlit multi-page sidebar and footer */
    [data-testid="stSidebar"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Clean typography & background */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Minimalist Top App Bar */
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 16px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .user-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #f1f5f9;
        color: #334155;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 9999px;
    }

    /* Assignment context banner */
    .task-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.9rem;
        color: #1e293b;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Chat bubble enhancements */
    .voice-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #2563eb;
        background: #eff6ff;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
    }

    /* Status badges */
    .badge-comp { background: #dcfce7; color: #166534; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-warn { background: #fef3c7; color: #92400e; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-fail { background: #fee2e2; color: #991b1b; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "role" not in st.session_state:
    st.session_state["role"] = None
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "hr_messages" not in st.session_state:
    st.session_state["hr_messages"] = [
        {
            "role": "assistant",
            "content": "Hello HR Coordinator! I can help you onboard interns and assign technical tasks.\n\n"
                       "You can type instructions naturally and attach your **Excel/CSV roster** and **Company Requirements document** below.",
            "audio": None
        }
    ]
if "intern_messages" not in st.session_state:
    st.session_state["intern_messages"] = []
if "intern_lang" not in st.session_state:
    st.session_state["intern_lang"] = None
if "pending_assignment" not in st.session_state:
    st.session_state["pending_assignment"] = None


# ---------------------------------------------------------------------
# VIEW 1: CLEAN LOGIN SCREEN
# ---------------------------------------------------------------------
if not st.session_state["role"]:
    st.markdown("<div style='text-align: center; margin-top: 40px; margin-bottom: 25px;'>", unsafe_allow_html=True)
    st.markdown("# 🎓 AI Mentor & Task Assistant")
    st.markdown("<p style='color: #64748b; font-size: 1.05rem;'>Conversational internship task onboarding, mentorship, and automated evaluation.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🏢 HR / Company")
            st.caption("Import intern rosters, assign tasks using requirements docs, and monitor progress.")
            if st.button("Enter as HR Coordinator", type="primary", use_container_width=True):
                st.session_state["role"] = "hr"
                st.session_state["current_user"] = {"name": "HR Coordinator", "role": "HR Manager"}
                st.rerun()

    with col2:
        with st.container(border=True):
            st.markdown("### 🎓 Employee / Intern")
            st.caption("Receive 1-on-1 AI mentorship, ask questions in Tamil/English/Hindi, and submit work.")

            all_candidates = get_candidates()
            if all_candidates:
                cand_map = {f"{c['name']} ({c['role']})": c for c in all_candidates}
                selected_label = st.selectbox("Select Your Profile:", list(cand_map.keys()), key="login_cand_select")
                if st.button("Log In as Intern", use_container_width=True):
                    cand = cand_map[selected_label]
                    st.session_state["role"] = "intern"
                    st.session_state["current_user"] = cand
                    st.session_state["intern_messages"] = []
                    st.session_state["intern_lang"] = None
                    st.rerun()
            else:
                st.info("No interns registered yet.")
                if st.button("⚡ Quick Demo Intern (Aarav Sharma)", use_container_width=True):
                    # Auto-register sample candidate and task for instant testing
                    cid = create_candidate(
                        name="Aarav Sharma",
                        email="aarav.sharma@example.com",
                        role="Full-Stack Web Development Intern",
                        batch="Batch-2026-Fall"
                    )
                    sample_req_path = os.path.join(os.path.dirname(__file__), "sample_data", "company_requirements.md")
                    req_text = "Build a modular Full-Stack Task Tracker application with database models, validation, and tests."
                    if os.path.exists(sample_req_path):
                        with open(sample_req_path, "r", encoding="utf-8") as f:
                            req_text = f.read()

                    tid = create_task(
                        candidate_id=cid,
                        module_name="Module 1",
                        title="Full-Stack Task Tracker Core",
                        description="Implement models, title validation, and unit tests.",
                        requirements_text=req_text,
                        source_filename="company_requirements.md"
                    )
                    st.session_state["role"] = "intern"
                    st.session_state["current_user"] = get_candidate(cid)
                    st.session_state["intern_messages"] = []
                    st.session_state["intern_lang"] = None
                    st.rerun()

    st.stop()


# ---------------------------------------------------------------------
# MINIMALIST TOP NAVBAR (Rendered for both roles)
# ---------------------------------------------------------------------
user_data = st.session_state["current_user"]
role_type = st.session_state["role"]

nav_col1, nav_col2 = st.columns([3, 1])
with nav_col1:
    st.markdown(f"""
    <div class="top-navbar">
        <div class="brand-title">
            <span>🎓</span> AI Mentor
        </div>
        <div class="user-pill">
            <span>{'🏢' if role_type == 'hr' else '👤'}</span> {user_data.get('name', 'User')} ({'HR' if role_type == 'hr' else user_data.get('role', 'Intern')})
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_col2:
    if st.button("Sign Out", key="logout_btn", use_container_width=True):
        st.session_state["role"] = None
        st.session_state["current_user"] = None
        st.session_state["intern_messages"] = []
        st.session_state["intern_lang"] = None
        st.session_state["pending_assignment"] = None
        st.rerun()


# ---------------------------------------------------------------------
# VIEW 2: HR CHAT INTERFACE
# ---------------------------------------------------------------------
if role_type == "hr":
    # Display HR Chat Messages
    for msg in st.session_state["hr_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("card"):
                card = msg["card"]
                with st.container(border=True):
                    st.markdown(f"### 📋 Assignment Summary: **{card['task_title']}**")
                    st.markdown(f"**Deadline:** `{card['deadline']}`")
                    st.markdown(f"**Interns to Assign ({len(card['interns'])}):**")
                    for i in card["interns"]:
                        st.markdown(f"- **{i['name']}** (`{i['email']}`) — {i['role']}")
                    if card.get("requirements_filename"):
                        st.caption(f"Requirements: `{card['requirements_filename']}` ({len(card['requirements_text'])} chars)")

                    if not card.get("confirmed"):
                        if st.button("✅ Confirm & Assign Tasks to Interns", key=f"confirm_btn_{card['id']}"):
                            # Save all candidates and tasks to DB
                            assigned_names = []
                            for intern in card["interns"]:
                                cid = create_candidate(
                                    name=intern["name"],
                                    email=intern["email"],
                                    role=intern["role"],
                                    batch=intern["batch"]
                                )
                                create_task(
                                    candidate_id=cid,
                                    module_name="Module 1",
                                    title=card["task_title"],
                                    description=f"Assigned by HR. Deadline: {card['deadline']}",
                                    requirements_text=card["requirements_text"],
                                    source_filename=card.get("requirements_filename", "requirements.md")
                                )
                                assigned_names.append(intern["name"])

                            card["confirmed"] = True
                            st.session_state["pending_assignment"] = None
                            st.session_state["hr_messages"].append({
                                "role": "assistant",
                                "content": f"✅ **Assignment Completed!** Successfully created tasks for {len(assigned_names)} interns: {', '.join(assigned_names)}.\n\nThey can now log in to receive their AI mentor debriefing.",
                                "audio": None
                            })
                            st.rerun()
                    else:
                        st.success("Tasks confirmed and assigned.")

    # Attachment & Voice Controls (Collapsible clean bar)
    with st.expander("📎 Attach Documents & Voice Input", expanded=False):
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            hr_roster_file = st.file_uploader(
                "Upload Interns Spreadsheet (Excel .xlsx / CSV)",
                type=["xlsx", "xls", "csv"],
                key="hr_roster_upload"
            )
        with c_att2:
            hr_req_file = st.file_uploader(
                "Upload Requirements Document (PDF, Word .docx, Markdown, Text)",
                type=["pdf", "docx", "txt", "md"],
                key="hr_req_upload"
            )

        col_sample_hr, col_mic_hr = st.columns([2, 1])
        with col_sample_hr:
            if st.button("⚡ Use Sample Roster & Requirements"):
                sample_roster = os.path.join(os.path.dirname(__file__), "sample_data", "interns_roster.xlsx")
                sample_req = os.path.join(os.path.dirname(__file__), "sample_data", "company_requirements.md")
                with open(sample_roster, "rb") as f:
                    st.session_state["cached_roster_bytes"] = f.read()
                    st.session_state["cached_roster_name"] = "interns_roster.xlsx"
                with open(sample_req, "rb") as f:
                    st.session_state["cached_req_bytes"] = f.read()
                    st.session_state["cached_req_name"] = "company_requirements.md"
                st.success("Loaded sample Excel roster & requirements. Now type your instruction below!")

        with col_mic_hr:
            st.caption("🎙️ Voice Input")
            hr_audio = st.audio_input("Record HR instruction", key="hr_audio_mic")

    # HR Chat Input Box
    hr_prompt = st.chat_input("Instruct HR Assistant... e.g. 'Import interns from Excel and assign Module 1. Deadline is Friday.'")

    # Handle voice prompt if recorded
    if hr_audio is not None and not hr_prompt:
        hr_prompt = "Import interns from the attached spreadsheet and assign the company requirements task. Deadline is Friday."

    if hr_prompt:
        st.session_state["hr_messages"].append({"role": "user", "content": hr_prompt, "audio": None})

        # Process attachments
        r_bytes = None
        r_name = None
        doc_bytes = None
        doc_name = None

        if hr_roster_file:
            r_bytes = hr_roster_file.read()
            r_name = hr_roster_file.name
        elif "cached_roster_bytes" in st.session_state:
            r_bytes = st.session_state["cached_roster_bytes"]
            r_name = st.session_state.get("cached_roster_name", "roster.xlsx")

        if hr_req_file:
            doc_bytes = hr_req_file.read()
            doc_name = hr_req_file.name
        elif "cached_req_bytes" in st.session_state:
            doc_bytes = st.session_state["cached_req_bytes"]
            doc_name = st.session_state.get("cached_req_name", "requirements.md")

        # Parse instruction
        parsed_action = process_hr_instruction(
            prompt=hr_prompt,
            attached_file_bytes=r_bytes,
            attached_filename=r_name,
            secondary_file_bytes=doc_bytes,
            secondary_filename=doc_name
        )

        if parsed_action["has_assignment_intent"] and (parsed_action["interns"] or r_bytes):
            if not parsed_action["interns"] and r_bytes:
                # Parse spreadsheet directly
                sp = parse_spreadsheet(r_bytes, r_name)
                parsed_action["interns"] = sp.get("records", [])

            if not parsed_action["requirements_text"] and doc_bytes:
                dp = parse_document(doc_bytes, doc_name)
                parsed_action["requirements_text"] = dp.get("text", "")
                parsed_action["requirements_filename"] = doc_name

            card_id = int(datetime.now().timestamp())
            card_data = {
                "id": card_id,
                "task_title": parsed_action["task_title"],
                "deadline": parsed_action["deadline"],
                "interns": parsed_action["interns"],
                "requirements_text": parsed_action["requirements_text"] or "General Engineering Specifications",
                "requirements_filename": parsed_action.get("requirements_filename", "requirements.md"),
                "confirmed": False
            }
            st.session_state["pending_assignment"] = card_data
            st.session_state["hr_messages"].append({
                "role": "assistant",
                "content": f"I parsed your instruction and identified **{len(card_data['interns'])} interns** to assign to **{card_data['task_title']}**.\n\nPlease review the details below and confirm.",
                "card": card_data,
                "audio": None
            })
            st.rerun()

        elif any(k in hr_prompt.lower() for k in ["progress", "status", "who", "submitted", "review"]):
            # Progress inquiry
            tasks = get_all_tasks()
            if not tasks:
                reply = "No tasks or submissions have been registered yet."
            else:
                lines = ["Here is the current status of all assigned interns:\n"]
                for t in tasks:
                    subs = get_submissions_for_task(t["id"])
                    reviews = get_reviews_for_task(t["id"])
                    latest_r = reviews[0] if reviews else None
                    rev_count = len(subs)
                    status_text = latest_r["overall_status"] if latest_r else "Not Submitted"
                    score_text = f"{latest_r['overall_score']}/100" if latest_r else "N/A"
                    lines.append(f"• **{t['candidate_name']}**: `{t['title']}` — Status: **{status_text}** (Score: {score_text}, Revisions: {rev_count})")
                reply = "\n".join(lines)

            st.session_state["hr_messages"].append({"role": "assistant", "content": reply, "audio": None})
            st.rerun()

        else:
            # General HR query
            st.session_state["hr_messages"].append({
                "role": "assistant",
                "content": "I'm ready to help. You can attach an **Excel intern roster** and a **requirements document**, then instruct me to assign tasks. Or ask me about candidate progress at any time!",
                "audio": None
            })
            st.rerun()


# ---------------------------------------------------------------------
# VIEW 3: EMPLOYEE / INTERN AI MENTOR CHAT INTERFACE
# ---------------------------------------------------------------------
elif role_type == "intern":
    candidate = user_data
    intern_tasks = get_tasks_for_candidate(candidate["id"])
    active_task = intern_tasks[0] if intern_tasks else None

    # Context Pill at top of chat
    if active_task:
        subs = get_submissions_for_task(active_task["id"])
        rev_text = f"Revision {len(subs)}" if subs else "Awaiting Submission"
        st.markdown(f"""
        <div class="task-banner">
            <div>
                <strong>📌 Task:</strong> {active_task['module_name']} — <em>{active_task['title']}</em>
            </div>
            <div style="font-size: 0.8rem; color: #64748b;">
                {rev_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("You do not have any active assigned tasks. Please contact HR.")
        st.stop()

    # Step 1: Initial Mentor Welcome if conversation is empty
    if not st.session_state["intern_messages"]:
        i18n_welcome = (
            f"Hello **{candidate['name']}**! 👋 I am your dedicated AI Mentor for **{active_task['title']}**.\n\n"
            "I will walk you through your requirements, answer your questions, and evaluate your code when ready.\n\n"
            "**Which language would you prefer to converse in?**"
        )
        tts_bytes = generate_tts_audio(f"Hello {candidate['name']}! I am your AI Mentor. Which language do you prefer: English, Tamil, or Hindi?", "English")
        st.session_state["intern_messages"].append({
            "role": "assistant",
            "content": i18n_welcome,
            "audio": tts_bytes,
            "show_lang_options": True
        })

    # Render Intern Chat Messages
    for idx, msg in enumerate(st.session_state["intern_messages"]):
        with st.chat_message(msg["role"]):
            if msg.get("audio"):
                st.markdown("<span class='voice-tag'>🔊 AI Mentor Voice</span>", unsafe_allow_html=True)
                st.audio(msg["audio"], format="audio/mp3")

            st.markdown(msg["content"])

            # Language Choice Quick Buttons
            if msg.get("show_lang_options") and not st.session_state["intern_lang"]:
                col_l1, col_l2, col_l3 = st.columns(3)
                with col_l1:
                    if st.button("🇬🇧 English", key="btn_lang_en"):
                        st.session_state["intern_lang"] = "English"
                        msg["show_lang_options"] = False
                        # Bot gives task explanation in English
                        exp, tts_str = explain_task_conversationally(active_task, language="English")
                        audio = generate_tts_audio(tts_str, "English")
                        st.session_state["intern_messages"].append({
                            "role": "assistant",
                            "content": f"Great! Let's continue in **English**.\n\n{exp}",
                            "audio": audio
                        })
                        st.rerun()
                with col_l2:
                    if st.button("🇮🇳 தமிழ் (Tamil)", key="btn_lang_ta"):
                        st.session_state["intern_lang"] = "Tamil"
                        msg["show_lang_options"] = False
                        exp, tts_str = explain_task_conversationally(active_task, language="Tamil")
                        audio = generate_tts_audio(tts_str, "Tamil")
                        st.session_state["intern_messages"].append({
                            "role": "assistant",
                            "content": f"மகிழ்ச்சி! நாம் **தமிழில்** உரையாடுவோம்.\n\n{exp}",
                            "audio": audio
                        })
                        st.rerun()
                with col_l3:
                    if st.button("🇮🇳 हिंदी (Hindi)", key="btn_lang_hi"):
                        st.session_state["intern_lang"] = "Hindi"
                        msg["show_lang_options"] = False
                        exp, tts_str = explain_task_conversationally(active_task, language="Hindi")
                        audio = generate_tts_audio(tts_str, "Hindi")
                        st.session_state["intern_messages"].append({
                            "role": "assistant",
                            "content": f"बहुत बढ़िया! हम **हिंदी** में बातचीत करेंगे।\n\n{exp}",
                            "audio": audio
                        })
                        st.rerun()

            # Schedule & Email Action Card (if review generated)
            if msg.get("review_data"):
                rd = msg["review_data"]
                rev_id = rd["review_id"]
                sched = get_schedule_for_review(rev_id)
                with st.container(border=True):
                    st.markdown("#### 📅 Next Review & Email Follow-up")
                    if sched:
                        st.markdown(f"**Scheduled Session:** {sched['review_date']} at {sched['review_time']} (Local Time)")
                        st.caption(f"Meeting link: {sched.get('session_link') or 'Local Demo'}")
                    else:
                        st.markdown(f"**Next Session:** Friday at 11:00 AM (Host Local Time)")

                    col_em1, col_em2 = st.columns(2)
                    with col_em1:
                        if st.button("📨 Save Feedback Notification (Demo)", key=f"btn_sim_em_{idx}"):
                            res = schedule_and_notify(
                                review_id=rev_id,
                                review_date=str(date.today()),
                                review_time="11:00",
                                session_link="http://localhost:8501 (Local Session)",
                                reviewer_message="Please follow the AI mentor suggestions before our meeting.",
                                send_real_email=False
                            )
                            st.success("Feedback recorded with status: **SIMULATED — NOT SENT**.")
                    with col_em2:
                        smtp_ok = is_smtp_configured()
                        if st.button("📤 Send Real Email via SMTP", key=f"btn_real_em_{idx}", disabled=not smtp_ok):
                            res = schedule_and_notify(
                                review_id=rev_id,
                                review_date=str(date.today()),
                                review_time="11:00",
                                session_link="http://localhost:8501 (Local Session)",
                                reviewer_message="Please follow the AI mentor suggestions before our meeting.",
                                send_real_email=True
                            )
                            if res["success"]:
                                st.success("Email sent successfully!")
                            else:
                                st.error(f"Failed to send: {res['message']}")

    # Attachment & Voice submission drawer
    with st.expander("📎 Attach Submission Files or Speak", expanded=False):
        c_sub1, c_sub2 = st.columns([2, 1])
        with c_sub1:
            uploaded_sub_file = st.file_uploader(
                "Upload Code Files or ZIP Archive",
                type=["zip", "py", "js", "html", "css", "json", "pdf", "docx", "txt", "md"],
                key="intern_sub_file"
            )
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("📂 Attach Sample V1 (Partial)"):
                    sample_v1 = os.path.join(os.path.dirname(__file__), "sample_data", "candidate_submission_v1_partial.zip")
                    with open(sample_v1, "rb") as f:
                        st.session_state["cached_sub_bytes"] = f.read()
                        st.session_state["cached_sub_name"] = "candidate_submission_v1_partial.zip"
                    st.success("Attached Sample V1 (Partial Submission). Type a message or click Send!")
            with col_s2:
                if st.button("📂 Attach Sample V2 (Completed)"):
                    sample_v2 = os.path.join(os.path.dirname(__file__), "sample_data", "candidate_submission_v2_completed.zip")
                    with open(sample_v2, "rb") as f:
                        st.session_state["cached_sub_bytes"] = f.read()
                        st.session_state["cached_sub_name"] = "candidate_submission_v2_completed.zip"
                    st.success("Attached Sample V2 (Completed Submission). Type a message or click Send!")

        with c_sub2:
            st.caption("🎙️ Voice Question / Instruction")
            intern_audio = st.audio_input("Speak to AI Mentor", key="intern_audio_mic")

    # Intern Chat Input Box
    intern_prompt = st.chat_input("Ask your mentor a question or submit a GitHub URL / code...")

    # Handle voice prompt if recorded
    if intern_audio is not None and not intern_prompt:
        intern_prompt = "Can you explain the main requirements for my task?"

    if intern_prompt:
        current_lang = st.session_state.get("intern_lang") or "English"

        # Check if user is choosing language via text
        p_lower = intern_prompt.strip().lower()
        if p_lower in ["tamil", "தமிழ்", "tamizh"]:
            st.session_state["intern_lang"] = "Tamil"
            current_lang = "Tamil"
            st.session_state["intern_messages"].append({"role": "user", "content": intern_prompt, "audio": None})
            exp, tts_str = explain_task_conversationally(active_task, language="Tamil")
            audio = generate_tts_audio(tts_str, "Tamil")
            st.session_state["intern_messages"].append({
                "role": "assistant",
                "content": f"மகிழ்ச்சி! நாம் **தமிழில்** உரையாடுவோம்.\n\n{exp}",
                "audio": audio
            })
            st.rerun()
        elif p_lower in ["hindi", "हिंदी"]:
            st.session_state["intern_lang"] = "Hindi"
            current_lang = "Hindi"
            st.session_state["intern_messages"].append({"role": "user", "content": intern_prompt, "audio": None})
            exp, tts_str = explain_task_conversationally(active_task, language="Hindi")
            audio = generate_tts_audio(tts_str, "Hindi")
            st.session_state["intern_messages"].append({
                "role": "assistant",
                "content": f"बहुत बढ़िया! हम **हिंदी** में बातचीत करेंगे।\n\n{exp}",
                "audio": audio
            })
            st.rerun()
        elif p_lower in ["english", "eng"]:
            st.session_state["intern_lang"] = "English"
            current_lang = "English"
            st.session_state["intern_messages"].append({"role": "user", "content": intern_prompt, "audio": None})
            exp, tts_str = explain_task_conversationally(active_task, language="English")
            audio = generate_tts_audio(tts_str, "English")
            st.session_state["intern_messages"].append({
                "role": "assistant",
                "content": f"Great! Let's continue in **English**.\n\n{exp}",
                "audio": audio
            })
            st.rerun()

        # Regular user message
        st.session_state["intern_messages"].append({"role": "user", "content": intern_prompt, "audio": None})

        # Check if submission is attached (file or GitHub URL)
        sub_bytes = None
        sub_name = None
        if uploaded_sub_file:
            sub_bytes = uploaded_sub_file.read()
            sub_name = uploaded_sub_file.name
        elif "cached_sub_bytes" in st.session_state:
            sub_bytes = st.session_state["cached_sub_bytes"]
            sub_name = st.session_state.get("cached_sub_name", "submission.zip")
            del st.session_state["cached_sub_bytes"]

        is_github_url = "github.com/" in intern_prompt.lower()

        if sub_bytes or is_github_url:
            # Process candidate submission & evaluate
            with st.spinner("AI Mentor is reviewing your submission against company requirements..."):
                gh_url = intern_prompt.strip() if is_github_url else None
                eval_res = process_submission_and_evaluate(
                    task_id=active_task["id"],
                    submission_type="github" if is_github_url else "upload",
                    file_source=sub_bytes,
                    filename=sub_name,
                    github_url=gh_url,
                    candidate_notes="Submitted via conversational AI mentor.",
                    known_issues="",
                    language=current_lang
                )

                if eval_res["success"]:
                    rev_info = eval_res["review_result"]
                    structured = rev_info["structured_data"]
                    status = rev_info["overall_status"]
                    score = rev_info["overall_score"]
                    rev_num = len(get_submissions_for_task(active_task["id"]))

                    status_badge = "badge-comp" if status == "Completed" else ("badge-warn" if status == "Needs Changes" else "badge-fail")

                    strengths_list = "\n".join([f"• {s}" for s in structured.get("strengths", [])[:3]]) or "• Basic structure submitted."
                    missing_list = "\n".join([f"• {m}" for m in structured.get("missing_components", [])[:3]]) or "• No critical omissions."
                    corrections_list = "\n".join([f"• {c}" for c in structured.get("actionable_corrections", [])[:3]]) or "• Review final details."

                    feedback_md = (
                        f"### 📋 Review Summary — Revision {rev_num}\n\n"
                        f"**Outcome:** <span class='{status_badge}'>{status}</span> &nbsp;|&nbsp; **Score:** **{score} / 100**\n\n"
                        f"**Strengths:**\n{strengths_list}\n\n"
                        f"**Areas for Improvement:**\n{missing_list}\n\n"
                        f"**Actionable Next Steps:**\n{corrections_list}"
                    )

                    tts_feedback = f"Review complete for Revision {rev_num}. Status is {status} with a score of {score} out of 100."
                    if status == "Completed":
                        tts_feedback += " Excellent work, your submission meets company requirements!"
                    else:
                        tts_feedback += " Please check the suggestions and submit your revision."

                    tts_audio = generate_tts_audio(tts_feedback, current_lang)

                    st.session_state["intern_messages"].append({
                        "role": "assistant",
                        "content": feedback_md,
                        "audio": tts_audio,
                        "review_data": eval_res
                    })
                    st.rerun()
                else:
                    st.session_state["intern_messages"].append({
                        "role": "assistant",
                        "content": f"⚠️ I encountered an issue evaluating your submission: {eval_res['error']}",
                        "audio": None
                    })
                    st.rerun()

        else:
            # Answering Intern's Question conversationally
            with st.spinner("AI Mentor is typing..."):
                answer, tts_str = answer_intern_question(
                    question=intern_prompt,
                    task=active_task,
                    chat_history=st.session_state["intern_messages"],
                    language=current_lang
                )
                tts_audio = generate_tts_audio(tts_str, current_lang)
                st.session_state["intern_messages"].append({
                    "role": "assistant",
                    "content": answer,
                    "audio": tts_audio
                })
                st.rerun()
