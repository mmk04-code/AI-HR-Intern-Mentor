"""
Internship Task Review Assistant - Streamlit Application
A local pair-programming and review platform for evaluating intern submissions,
comparing against company requirements, scheduling follow-ups, and dispatching feedback.
"""

import os
import sys
import json
from datetime import datetime, date, time
import streamlit as st
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import (
    init_db,
    get_candidates,
    get_all_tasks,
    get_task,
    get_submissions_for_task,
    get_submission,
    get_reviews_for_task,
    get_review,
    get_schedule_for_review,
    get_email_logs
)
from src.review_service import (
    register_candidate_and_task,
    process_submission_and_evaluate,
    schedule_and_notify
)
from src.email_service import is_smtp_configured

# Ensure database tables exist
init_db()

# Page configuration
st.set_page_config(
    page_title="Internship Task Review Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished, professional presentation
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-completed { background-color: #dcfce7; color: #15803d; }
    .badge-needs-changes { background-color: #fef3c7; color: #b45309; }
    .badge-incomplete { background-color: #fee2e2; color: #b91c1c; }
    .badge-simulated { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }

    /* Callout notice */
    .demo-banner {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #92400e;
    }
    .ai-banner {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 5px solid #22c55e;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #166534;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/inspection.png", width=64)
st.sidebar.title("Task Review Assistant")
st.sidebar.caption("Module 1 • Candidate Evaluation & Review Loop")

navigation_option = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "👤 HR: Candidate & Task Setup",
        "📥 Submit Candidate Work",
        "📝 Review & Feedback Report",
        "🔁 Revision History & Email Logs"
    ],
    index=0
)

st.sidebar.markdown("---")

# Environment & Status Indicators in Sidebar
api_key_configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
smtp_ready = is_smtp_configured()

st.sidebar.markdown("**System Configuration**")
if api_key_configured:
    st.sidebar.success(f"🤖 Gemini API: Active (`{model_name}`)")
else:
    st.sidebar.warning("⚖️ Gemini: Fallback Rule-Based (No Key)")

if smtp_ready:
    st.sidebar.success("📧 SMTP: Configured (Real Emails)")
else:
    st.sidebar.info("📧 SMTP: Simulated Mode (Safe Demo)")

st.sidebar.caption("© 2026 Internship Review System • Local Demo")


# -------------------------------------------------------------
# PAGE 1: DASHBOARD
# -------------------------------------------------------------
if navigation_option == "📊 Dashboard":
    st.header("📊 Task Review & Candidate Overview")
    st.markdown("Monitor candidate submissions, active tasks, review outcomes, and scheduled sessions.")

    tasks = get_all_tasks()
    candidates = get_candidates()

    total_tasks = len(tasks)
    total_candidates = len(candidates)

    completed_count = 0
    needs_changes_count = 0
    total_reviews = 0
    scores = []

    for t in tasks:
        reviews = get_reviews_for_task(t["id"])
        if reviews:
            latest_review = reviews[0]
            total_reviews += 1
            scores.append(latest_review["overall_score"])
            if latest_review["overall_status"] == "Completed":
                completed_count += 1
            else:
                needs_changes_count += 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    # Top Metric Tiles
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Registered Candidates</div>
            <div class="metric-val">{total_candidates}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active Tasks</div>
            <div class="metric-val">{total_tasks}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Completed Tasks</div>
            <div class="metric-val" style="color: #16a34a;">{completed_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Average Review Score</div>
            <div class="metric-val" style="color: #2563eb;">{avg_score} <span style="font-size: 1rem; color: #64748b;">/ 100</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Candidates and Task Assignments")

    if not tasks:
        st.info("No tasks registered yet. Go to **'HR: Candidate & Task Setup'** to register the first candidate and upload requirements.")
    else:
        for t in tasks:
            reviews = get_reviews_for_task(t["id"])
            submissions = get_submissions_for_task(t["id"])
            latest_rev = reviews[0] if reviews else None
            latest_sub = submissions[0] if submissions else None

            status_badge = '<span class="badge" style="background:#e2e8f0; color:#475569;">No Submission</span>'
            score_text = "N/A"
            if latest_rev:
                status = latest_rev["overall_status"]
                score_text = f"{latest_rev['overall_score']} / 100"
                if status == "Completed":
                    status_badge = '<span class="badge badge-completed">Completed</span>'
                elif status == "Needs Changes":
                    status_badge = '<span class="badge badge-needs-changes">Needs Changes</span>'
                else:
                    status_badge = '<span class="badge badge-incomplete">Incomplete</span>'

            rev_num = latest_sub["revision_number"] if latest_sub else 0

            with st.expander(f"👤 {t['candidate_name']} — {t['module_name']}: {t['title']} (Rev {rev_num})", expanded=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                with c1:
                    st.write(f"**Email:** `{t['candidate_email']}`")
                    st.write(f"**Role:** {t['candidate_role']} | **Batch:** {t['candidate_batch']}")
                    st.write(f"**Requirements Document:** `{t['source_filename'] or 'Manual text'}`")
                with c2:
                    st.write(f"**Current Status:** {status_badge}", unsafe_allow_html=True)
                    st.write(f"**Latest Score:** {score_text}")
                    st.write(f"**Total Revisions:** {len(submissions)}")
                with c3:
                    if latest_rev:
                        sched = get_schedule_for_review(latest_rev["id"])
                        if sched:
                            st.write(f"**Next Review:** 📅 {sched['review_date']} at {sched['review_time']}")
                            if sched.get("session_link"):
                                st.caption(f"🔗 {sched['session_link']}")
                        else:
                            st.write("**Next Review:** Not scheduled")
                    else:
                        st.write("**Next Review:** Awaiting submission")
                with c4:
                    if st.button("📥 Submit Revision", key=f"btn_sub_{t['id']}"):
                        st.session_state["selected_task_id"] = t["id"]
                        st.session_state["nav_target"] = "📥 Submit Candidate Work"
                        st.rerun()
                    if latest_rev and st.button("📝 View Feedback", key=f"btn_rev_{t['id']}"):
                        st.session_state["selected_review_id"] = latest_rev["id"]
                        st.session_state["nav_target"] = "📝 Review & Feedback Report"
                        st.rerun()


# -------------------------------------------------------------
# PAGE 2: HR / TASK SETUP
# -------------------------------------------------------------
elif navigation_option == "👤 HR: Candidate & Task Setup":
    st.header("👤 HR: Candidate & Task Registration")
    st.markdown("Register an intern, configure their assigned module, and upload the official company requirements document.")

    # Quick demo filler
    col_demo, _ = st.columns([2, 5])
    with col_demo:
        if st.button("⚡ Fill Sample Demo Data"):
            st.session_state["cand_name"] = "Aarav Sharma"
            st.session_state["cand_email"] = "aarav.sharma@example.com"
            st.session_state["cand_role"] = "Full-Stack Web Development Intern"
            st.session_state["cand_batch"] = "Batch-2026-Fall"
            st.session_state["mod_name"] = "Module 1"
            st.session_state["task_title"] = "Full-Stack Task Tracker Core"
            st.session_state["task_desc"] = "Build database models, task CRUD endpoints, title validation rules, and error handling."
            st.rerun()

    with st.form("hr_setup_form"):
        st.subheader("1. Intern Profile")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Intern's Full Name *", value=st.session_state.get("cand_name", ""))
            role = st.text_input("Assigned Role *", value=st.session_state.get("cand_role", "Software Engineering Intern"))
        with col2:
            email = st.text_input("Intern's Email Address *", value=st.session_state.get("cand_email", ""))
            batch = st.text_input("Internship Batch / Cohort *", value=st.session_state.get("cand_batch", "Batch-2026-A"))

        st.subheader("2. Task Details")
        c3, c4 = st.columns([1, 2])
        with c3:
            module_name = st.text_input("Module / Sprint Name *", value=st.session_state.get("mod_name", "Module 1"))
        with c4:
            task_title = st.text_input("Task Title *", value=st.session_state.get("task_title", ""))

        task_desc = st.text_area("Task Description & Context", value=st.session_state.get("task_desc", ""), height=80)

        st.subheader("3. Company Requirements Document")
        st.caption("Upload the official specification (PDF, DOCX, TXT, Markdown). This document serves as the ground truth.")

        uploaded_req_file = st.file_uploader(
            "Upload Requirements Document",
            type=["pdf", "docx", "txt", "md"],
            help="Supported: PDF, Microsoft Word (.docx), Plain Text (.txt), Markdown (.md)"
        )

        sample_req_path = os.path.join(os.path.dirname(__file__), "sample_data", "company_requirements.md")
        use_bundled_sample = st.checkbox("Or use bundled sample requirements (`sample_data/company_requirements.md`)", value=uploaded_req_file is None)

        manual_req_text = st.text_area(
            "Or enter / paste requirements text manually:",
            placeholder="1. Database schema: User, Project, TaskItem models\n2. API: POST /tasks with title validation\n3. Tests: Unit test coverage...",
            height=120
        )

        submitted = st.form_submit_button("💾 Save Task & Register Candidate", type="primary")

        if submitted:
            if not name.strip() or not email.strip() or not task_title.strip():
                st.error("Please fill in all mandatory fields (Name, Email, Task Title).")
            else:
                req_source = None
                req_filename = None
                raw_text = None

                if uploaded_req_file is not None:
                    req_source = uploaded_req_file.read()
                    req_filename = uploaded_req_file.name
                elif use_bundled_sample and os.path.exists(sample_req_path):
                    with open(sample_req_path, "r", encoding="utf-8") as f:
                        raw_text = f.read()
                    req_filename = "company_requirements.md"
                elif manual_req_text.strip():
                    raw_text = manual_req_text.strip()
                    req_filename = "Manual_Requirements.txt"

                if not req_source and not raw_text:
                    st.error("Please upload a requirements file or enter requirements text.")
                else:
                    with st.spinner("Parsing requirements and creating task..."):
                        reg_res = register_candidate_and_task(
                            name=name,
                            email=email,
                            role=role,
                            batch=batch,
                            module_name=module_name,
                            title=task_title,
                            description=task_desc,
                            requirements_file_source=req_source,
                            requirements_filename=req_filename,
                            raw_requirements_text=raw_text
                        )

                        if reg_res["success"]:
                            st.success(f"Candidate **{name}** registered and **{task_title}** created successfully! (Task ID: {reg_res['task_id']}, Parsed: {reg_res['requirements_length']} chars)")
                            st.info("You can now proceed to **'Submit Candidate Work'** to test the evaluation.")
                        else:
                            st.error(f"Error: {reg_res['error']}")


# -------------------------------------------------------------
# PAGE 3: SUBMIT CANDIDATE WORK
# -------------------------------------------------------------
elif navigation_option == "📥 Submit Candidate Work":
    st.header("📥 Submit Candidate Work")
    st.markdown("Submit candidate files (ZIP, code files) or a public GitHub repository URL for review. Each submission automatically creates a new revision.")

    tasks = get_all_tasks()
    if not tasks:
        st.warning("No tasks registered yet. Please create a task in 'HR: Candidate & Task Setup' first.")
    else:
        task_options = {f"{t['id']} - {t['candidate_name']} ({t['module_name']}: {t['title']})": t['id'] for t in tasks}

        # Check default task
        default_index = 0
        if "selected_task_id" in st.session_state and st.session_state["selected_task_id"] in task_options.values():
            default_index = list(task_options.values()).index(st.session_state["selected_task_id"])

        selected_label = st.selectbox("Select Candidate & Task *", list(task_options.keys()), index=default_index)
        selected_task_id = task_options[selected_label]
        task = get_task(selected_task_id)

        # Show revision count
        existing_subs = get_submissions_for_task(selected_task_id)
        current_rev_num = len(existing_subs) + 1

        st.info(f"Submitting for **{task['candidate_name']}** • This will be registered as **Revision {current_rev_num}**.")

        # Submission Mode
        submission_mode = st.radio(
            "Submission Method",
            ["📦 Upload Code / Documents / ZIP Archive", "🐙 Public GitHub Repository URL"],
            horizontal=True
        )

        col_left, col_right = st.columns([3, 2])

        with col_left:
            uploaded_file = None
            github_url = None

            if "Upload" in submission_mode:
                uploaded_file = st.file_uploader(
                    "Upload Candidate Work (ZIP, Python, JS, PDF, DOCX, TXT, MD)",
                    type=["zip", "py", "js", "html", "css", "json", "pdf", "docx", "txt", "md"],
                    help="Upload a ZIP archive containing candidate's project or single files."
                )

                # Convenient buttons for sample data
                st.caption("Quick Demo Options:")
                sample_col1, sample_col2 = st.columns(2)
                v1_path = os.path.join(os.path.dirname(__file__), "sample_data", "candidate_submission_v1_partial.zip")
                v2_path = os.path.join(os.path.dirname(__file__), "sample_data", "candidate_submission_v2_completed.zip")

                use_v1 = sample_col1.button("📂 Use Sample V1 (Partial Submission)")
                use_v2 = sample_col2.button("📂 Use Sample V2 (Completed Submission)")

                if use_v1 and os.path.exists(v1_path):
                    with open(v1_path, "rb") as f:
                        st.session_state["sample_sub_bytes"] = f.read()
                        st.session_state["sample_sub_name"] = "candidate_submission_v1_partial.zip"
                        st.session_state["sample_notes"] = "Preliminary submission with core routes and models."
                        st.session_state["sample_issues"] = "Input validation and unit tests not yet implemented."
                    st.success("Loaded Sample Revision 1 (Partial)")
                    st.rerun()

                if use_v2 and os.path.exists(v2_path):
                    with open(v2_path, "rb") as f:
                        st.session_state["sample_sub_bytes"] = f.read()
                        st.session_state["sample_sub_name"] = "candidate_submission_v2_completed.zip"
                        st.session_state["sample_notes"] = "Revision 2: Added full title validation, filters, error handlers, and unit tests."
                        st.session_state["sample_issues"] = "All requirements completed and tested."
                    st.success("Loaded Sample Revision 2 (Completed)")
                    st.rerun()

            else:
                github_url = st.text_input(
                    "Public GitHub Repository URL *",
                    placeholder="https://github.com/owner/repository",
                    help="Must be a public repository. Never executes code."
                )

            notes = st.text_area(
                "Candidate's Notes & Summary of Completed Work",
                value=st.session_state.get("sample_notes", ""),
                placeholder="Briefly describe what features you implemented...",
                height=90
            )

            known_issues = st.text_area(
                "Known Issues / Pending Items",
                value=st.session_state.get("sample_issues", ""),
                placeholder="Mention any known bugs or edge cases...",
                height=70
            )

        with col_right:
            st.markdown("#### Review Configuration")
            language = st.selectbox(
                "Explanation Language",
                ["English", "Tamil", "Hindi"],
                index=0,
                help="Feedback explanations and checklists will be generated in this language."
            )

            st.markdown("---")
            st.markdown("**Review Engine Status:**")
            if api_key_configured:
                st.markdown(f'<div class="ai-banner">🤖 <b>Gemini AI Active</b><br>Model: <code>{model_name}</code></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="demo-banner">⚖️ <b>Rule-Based Fallback Mode</b><br>Gemini API key not configured. Output will be generated via transparent rule-based demo engine.</div>', unsafe_allow_html=True)

            st.caption("🔒 Security Notice: Candidate code is never executed. File sizes and counts are strictly capped.")

        submit_btn = st.button("🚀 Analyze Submission & Generate Review", type="primary", use_container_width=True)

        if submit_btn:
            # Check inputs
            file_bytes = None
            filename = None

            if "Upload" in submission_mode:
                if uploaded_file is not None:
                    file_bytes = uploaded_file.read()
                    filename = uploaded_file.name
                elif "sample_sub_bytes" in st.session_state:
                    file_bytes = st.session_state["sample_sub_bytes"]
                    filename = st.session_state.get("sample_sub_name", "submission.zip")
                else:
                    st.error("Please upload a file or choose one of the sample submission buttons.")
                    st.stop()
            else:
                if not github_url or not github_url.strip():
                    st.error("Please provide a valid GitHub repository URL.")
                    st.stop()

            with st.spinner("Processing submission, extracting files, and evaluating against requirements..."):
                eval_res = process_submission_and_evaluate(
                    task_id=selected_task_id,
                    submission_type="upload" if "Upload" in submission_mode else "github",
                    file_source=file_bytes,
                    filename=filename,
                    github_url=github_url,
                    candidate_notes=notes,
                    known_issues=known_issues,
                    language=language
                )

                if eval_res["success"]:
                    st.session_state["selected_review_id"] = eval_res["review_id"]
                    st.session_state["just_reviewed"] = True
                    st.success(f"Evaluation complete for Revision {current_rev_num}!")
                    st.info("Navigating to Review & Feedback Report...")
                    st.rerun()
                else:
                    st.error(f"Evaluation failed: {eval_res['error']}")


# -------------------------------------------------------------
# PAGE 4: REVIEW RESULTS AND FEEDBACK
# -------------------------------------------------------------
elif navigation_option == "📝 Review & Feedback Report":
    st.header("📝 Candidate Review & Feedback Report")

    tasks = get_all_tasks()
    if not tasks:
        st.warning("No tasks available. Please create a task and submit candidate work first.")
    else:
        # Collect all reviews
        all_reviews = []
        for t in tasks:
            for r in get_reviews_for_task(t["id"]):
                sub = get_submission(r["submission_id"])
                rev_num = sub["revision_number"] if sub else 1
                all_reviews.append((f"{t['candidate_name']} — {t['title']} (Rev {rev_num}) [{r['overall_status']}]", r["id"]))

        if not all_reviews:
            st.info("No reviews generated yet. Please submit candidate work in **'Submit Candidate Work'**.")
        else:
            default_r_index = 0
            if "selected_review_id" in st.session_state:
                ids = [rid for label, rid in all_reviews]
                if st.session_state["selected_review_id"] in ids:
                    default_r_index = ids.index(st.session_state["selected_review_id"])

            selected_review_label = st.selectbox(
                "Select Review Record",
                [label for label, rid in all_reviews],
                index=default_r_index
            )
            selected_rid = [rid for label, rid in all_reviews if label == selected_review_label][0]
            review = get_review(selected_rid)
            sub = get_submission(review["submission_id"])
            task = get_task(sub["task_id"])

            # Review Engine Banner
            if review["is_ai_generated"]:
                st.markdown(
                    f'<div class="ai-banner">🤖 <b>AI REVIEW (Powered by Gemini)</b> • Model: <code>{review["model_used"]}</code> • Language: <b>{review["language"]}</b></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="demo-banner">⚖️ <b>RULE-BASED DEMO RESULTS (Fallback Engine)</b> • Model: <code>{review["model_used"]}</code> • Language: <b>{review["language"]}</b><br><small>Notice: Generated via rule-based comparison because Gemini API key is not configured or unavailable.</small></div>',
                    unsafe_allow_html=True
                )

            # High-level Summary Card
            status = review["overall_status"]
            score = review["overall_score"]
            status_color = "#16a34a" if status == "Completed" else ("#d97706" if status == "Needs Changes" else "#dc2626")

            top_c1, top_c2, top_c3 = st.columns([2, 1, 1])
            with top_c1:
                st.markdown(f"### Candidate: **{task['candidate_name']}**")
                st.write(f"**Task:** {task['module_name']} — {task['title']} | **Revision:** {sub['revision_number']}")
                st.write(f"**Submission Type:** {sub['submission_type'].upper()} ({sub['submitted_at']})")
                if sub.get("github_url"):
                    st.write(f"**Repo:** [{sub['github_url']}]({sub['github_url']})")
            with top_c2:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-title">Review Outcome</div>
                    <div class="metric-val" style="color: {status_color}; font-size: 1.5rem;">{status}</div>
                </div>
                """, unsafe_allow_html=True)
            with top_c3:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-title">Evaluation Score</div>
                    <div class="metric-val" style="color: #2563eb;">{score} <span style="font-size: 1rem; color: #64748b;">/ 100</span></div>
                </div>
                """, unsafe_allow_html=True)

            structured = review.get("structured_data", {})

            st.markdown("#### 📋 Executive Feedback Summary")
            st.info(review.get("feedback_summary") or structured.get("summary", "Review complete."))

            # Requirement by Requirement Breakdown
            st.markdown("### 🔍 Requirement-by-Requirement Analysis")
            req_analysis = structured.get("requirements_analysis", [])

            if not req_analysis:
                st.write("No specific requirement breakdown available.")
            else:
                for idx, item in enumerate(req_analysis, 1):
                    item_status = item.get("status", "Missing")
                    badge_class = "badge-completed" if item_status == "Met" else ("badge-needs-changes" if item_status == "Partially Met" else "badge-incomplete")

                    with st.expander(f"{idx}. {item.get('requirement', 'Requirement')} — [{item_status}]", expanded=(item_status != "Met")):
                        st.markdown(f"**Status:** <span class='badge {badge_class}'>{item_status}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Explanation:** {item.get('explanation', '')}")
                        evidence = item.get("evidence", "No evidence found")
                        st.markdown(f"**Code / Document Evidence:**")
                        st.code(evidence, language="text")

            # Detailed Findings Columns
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.markdown("#### ✅ Strengths & Completed Work")
                strengths = structured.get("strengths", [])
                for s in strengths:
                    st.markdown(f"- {s}")

                st.markdown("#### 🐛 Identified Bugs & Issues")
                bugs = structured.get("bugs_and_issues", [])
                for b in bugs:
                    st.markdown(f"- ⚠️ {b}")

            with f_col2:
                st.markdown("#### ❌ Missing Components / Features")
                missing = structured.get("missing_components", [])
                for m in missing:
                    st.markdown(f"- 🔴 {m}")

                st.markdown("#### ⚡ Actionable Corrections")
                corrections = structured.get("actionable_corrections", [])
                for c in corrections:
                    st.markdown(f"- 💡 {c}")

            # Prioritized Checklist
            st.markdown("### 📌 Prioritized Checklist for Next Revision")
            checklist = structured.get("prioritized_checklist", [])
            for c_idx, chk in enumerate(checklist, 1):
                st.markdown(f"{c_idx}. [ ] **{chk}**")

            # Limitations
            limitations = structured.get("limitations", [])
            if limitations:
                with st.expander("ℹ️ Verification Scope & Limitations"):
                    for lim in limitations:
                        st.caption(f"• {lim}")

            st.markdown("---")

            # SECTION 5: SCHEDULING NEXT REVIEW
            st.subheader("📅 Schedule Next Review Session")
            st.caption("Specify follow-up review details. The local timezone is used (Computer Local Time).")

            existing_sched = get_schedule_for_review(selected_rid)
            default_date = date.today()
            default_time = time(11, 0)
            default_link = "http://localhost:8501 (Local Demo Review)"
            default_msg = "Please review the feedback and implement the missing items before our meeting."

            if existing_sched:
                try:
                    default_date = datetime.strptime(existing_sched["review_date"], "%Y-%m-%d").date()
                    default_time = datetime.strptime(existing_sched["review_time"], "%H:%M").time()
                except Exception:
                    pass
                default_link = existing_sched.get("session_link", default_link)
                default_msg = existing_sched.get("reviewer_message", default_msg)

            sched_col1, sched_col2, sched_col3 = st.columns(3)
            with sched_col1:
                sched_date = st.date_input("Next Review Date", value=default_date)
            with sched_col2:
                sched_time = st.time_input("Next Review Time (Local Time)", value=default_time)
            with sched_col3:
                sched_link = st.text_input("Review Session / Meeting Link", value=default_link)
                if "localhost" in sched_link:
                    st.caption("⚠️ Note: Localhost links are only accessible on your local machine.")

            reviewer_msg = st.text_area("Reviewer's Note for Intern", value=default_msg, height=70)

            st.markdown("---")

            # SECTION 6: CANDIDATE FEEDBACK EMAIL PREVIEW & DISPATCH
            st.subheader("📧 Candidate Feedback Email")
            st.caption("Generate, preview, and dispatch or simulate the candidate notification email.")

            # Email Dispatch Action Buttons
            email_btn_col1, email_btn_col2, _ = st.columns([2, 2, 3])

            with email_btn_col1:
                simulate_email_btn = st.button("💾 Save Simulated Email (Demo Mode)", type="primary")
            with email_btn_col2:
                send_real_btn = st.button("📤 Send Real Email via SMTP", disabled=not smtp_ready, help="Requires valid SMTP credentials in .env")

            if simulate_email_btn:
                with st.spinner("Saving simulated email..."):
                    res = schedule_and_notify(
                        review_id=selected_rid,
                        review_date=str(sched_date),
                        review_time=sched_time.strftime("%H:%M"),
                        session_link=sched_link,
                        reviewer_message=reviewer_msg,
                        send_real_email=False
                    )
                    st.success("✅ Email record saved with status: **SIMULATED — NOT SENT** (Safe demo mode).")
                    st.session_state["email_preview"] = res.get("email_preview_text")
                    st.session_state["email_html"] = res.get("email_preview_html")

            if send_real_btn:
                with st.spinner("Connecting to SMTP server and transmitting email..."):
                    res = schedule_and_notify(
                        review_id=selected_rid,
                        review_date=str(sched_date),
                        review_time=sched_time.strftime("%H:%M"),
                        session_link=sched_link,
                        reviewer_message=reviewer_msg,
                        send_real_email=True
                    )
                    if res["success"]:
                        st.success("✅ Real email transmitted successfully!")
                    else:
                        st.error(f"❌ Failed to send email: {res['message']}")
                    st.session_state["email_preview"] = res.get("email_preview_text")
                    st.session_state["email_html"] = res.get("email_preview_html")

            # Live preview tab
            st.markdown("#### Generated Feedback Email Preview")
            tab_text, tab_html = st.tabs(["Plain Text View", "HTML Formatted View"])

            from src.email_service import generate_feedback_email_content
            subj, b_text, b_html = generate_feedback_email_content(
                candidate_name=task["candidate_name"],
                module_name=task["module_name"],
                task_title=task["title"],
                review_status=status,
                review_score=score,
                strengths=structured.get("strengths", []),
                missing_items=structured.get("missing_components", []),
                actionable_corrections=structured.get("actionable_corrections", []),
                review_date=str(sched_date),
                review_time=sched_time.strftime("%H:%M"),
                session_link=sched_link,
                reviewer_message=reviewer_msg
            )

            with tab_text:
                st.text_area("Email Content (Plain Text)", value=f"Subject: {subj}\n\n{b_text}", height=280)
            with tab_html:
                st.components.v1.html(b_html, height=350, scrolling=True)


# -------------------------------------------------------------
# PAGE 5: REVISION HISTORY AND EMAIL LOGS
# -------------------------------------------------------------
elif navigation_option == "🔁 Revision History & Email Logs":
    st.header("🔁 Revision History & Email Audit Trail")
    st.markdown("Review the complete lifecycle of submissions, revision progressions, and persistent email transmission records.")

    tasks = get_all_tasks()
    if not tasks:
        st.info("No tasks recorded yet.")
    else:
        task_opts = {f"{t['id']} - {t['candidate_name']} ({t['title']})": t['id'] for t in tasks}
        sel_task_label = st.selectbox("Select Task to View History", list(task_opts.keys()))
        sel_task_id = task_opts[sel_task_label]

        submissions = get_submissions_for_task(sel_task_id)
        reviews = get_reviews_for_task(sel_task_id)

        st.subheader("1. Submission & Review Timeline")
        if not submissions:
            st.write("No submissions yet for this task.")
        else:
            for s in submissions:
                rev_num = s["revision_number"]
                r = get_review_for_submission(s["id"])

                status_badge = '<span class="badge" style="background:#e2e8f0; color:#475569;">Awaiting Review</span>'
                score_str = "N/A"
                if r:
                    status = r["overall_status"]
                    score_str = f"{r['overall_score']} / 100"
                    badge_class = "badge-completed" if status == "Completed" else ("badge-needs-changes" if status == "Needs Changes" else "badge-incomplete")
                    status_badge = f'<span class="badge {badge_class}">{status}</span>'

                with st.expander(f"📌 Revision {rev_num} — {s['submission_type'].upper()} ({s['submitted_at']})", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Outcome:** {status_badge}", unsafe_allow_html=True)
                        st.write(f"**Score:** {score_str}")
                        st.write(f"**Candidate Notes:** {s['candidate_notes'] or 'None'}")
                        st.write(f"**Declared Issues:** {s['known_issues'] or 'None'}")
                    with c2:
                        if r:
                            sched = get_schedule_for_review(r["id"])
                            if sched:
                                st.write(f"**Scheduled Review:** {sched['review_date']} at {sched['review_time']}")
                                st.write(f"**Meeting Link:** {sched.get('session_link') or 'None'}")
                            else:
                                st.write("**Scheduled Review:** None")

                        files = s.get("files_summary", [])
                        if files:
                            st.caption(f"Files extracted ({len(files)}):")
                            file_names = ", ".join([f.get("path", "") for f in files[:8]])
                            st.caption(f"`{file_names}`")

        st.markdown("---")
        st.subheader("2. Persistent Email Dispatch Audit Logs")
        email_logs = get_email_logs()

        if not email_logs:
            st.info("No email records logged yet. Use the 'Review & Feedback Report' page to save a simulated email or send via SMTP.")
        else:
            log_table_data = []
            for el in email_logs:
                status_color = "#15803d" if el["status"] == "SENT" else ("#0284c7" if "SIMULATED" in el["status"] else "#b91c1c")
                log_table_data.append({
                    "Log ID": el["id"],
                    "Review ID": el["review_id"],
                    "Recipient": el["recipient_email"],
                    "Subject": el["subject"],
                    "Mode": el["mode"],
                    "Status": el["status"],
                    "Timestamp": el["sent_at"]
                })

            st.dataframe(log_table_data, use_container_width=True)

            st.caption("🔍 Note: The system explicitly records all simulated notifications as `SIMULATED — NOT SENT` to ensure total audit transparency.")
