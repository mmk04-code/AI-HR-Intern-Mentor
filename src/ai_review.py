"""
AI Review module for Internship Task Review Assistant.
Performs intelligent comparison of candidate submissions against company requirements
using Google Gemini API (when configured) or a robust Rule-Based Fallback Engine.
Supports English, Tamil, and Hindi output explanations.
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Fallback translation templates
FALLBACK_TRANSLATIONS = {
    "English": {
        "engine_label": "Rule-Based Demo Results (Fallback — Gemini API not configured or unavailable)",
        "summary_intro": "Automated structural audit comparing candidate files against company task requirements.",
        "met_desc": "Requirement verified in submission files.",
        "partial_desc": "Partial implementation found; key aspects missing or incomplete.",
        "missing_desc": "No matching implementation or file found in submission.",
        "unverified_note": "Runtime execution, external APIs, and dynamic styling could not be tested statically.",
        "checklist_prefix": "Address missing requirement: ",
    },
    "Tamil": {
        "engine_label": "விதிமுறை அடிப்படையிலான மாதிரி முடிவுகள் (Fallback — Gemini API இணைக்கப்படவில்லை)",
        "summary_intro": "நிறுவனத்தின் தேவைகளுடன் சமர்ப்பிக்கப்பட்ட கோப்புகளை ஒப்பிடும் தானியங்கி கட்டமைப்பு ஆய்வு.",
        "met_desc": "தேவை சமர்ப்பிப்பில் பூர்த்தி செய்யப்பட்டுள்ளது சரிபார்க்கப்பட்டது.",
        "partial_desc": "பகுதி செயலாக்கம் காணப்படுகிறது; முக்கிய கூறுகள் விடுபட்டுள்ளன.",
        "missing_desc": "சமர்ப்பிப்பில் தொடர்புடைய கோப்பு அல்லது நிரல் காணப்படவில்லை.",
        "unverified_note": "நிரல் இயக்க நேரம் மற்றும் வெளிப்புற API-கள் நிலையான முறையில் சோதிக்கப்படவில்லை.",
        "checklist_prefix": "விடுபட்ட தேவையை சரிசெய்க: ",
    },
    "Hindi": {
        "engine_label": "नियम-आधारित डेमो परिणाम (Fallback — Gemini API कॉन्फ़िगर नहीं है या अनुपलब्ध है)",
        "summary_intro": "कंपनी की आवश्यकताओं के साथ उम्मीदवार की फाइलों की तुलना करने वाला स्वचालित संरचनात्मक ऑडिट।",
        "met_desc": "प्रस्तुत फाइलों में आवश्यकता सत्यापित की गई।",
        "partial_desc": "आंशिक कार्यान्वयन पाया गया; मुख्य भाग अनुपस्थित या अधूरे हैं।",
        "missing_desc": "सबमिशन में कोई मिलान कोड या फ़ाइल नहीं मिली।",
        "unverified_note": "रनटाइम निष्पादन और बाहरी API का स्थिर रूप से परीक्षण नहीं किया जा सका।",
        "checklist_prefix": "अनुपस्थित आवश्यकता को पूरा करें: ",
    }
}


def get_gemini_client():
    """Attempt to import and configure google.generativeai if API key is present."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        model = genai.GenerativeModel(model_name)
        return genai, model
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}")
        return None, None


def analyze_submission(
    task_requirements: str,
    candidate_submission_text: str,
    candidate_notes: str = "",
    known_issues: str = "",
    files_summary: Optional[List[Dict[str, Any]]] = None,
    language: str = "English"
) -> Dict[str, Any]:
    """
    Main entry point for comparing candidate submission against company requirements.
    Attempts Gemini AI review first; falls back to rule-based engine on failure or missing API key.
    """
    valid_language = language if language in ["English", "Tamil", "Hindi"] else "English"
    genai_module, model = get_gemini_client()

    if model is not None:
        try:
            review_result = _run_gemini_review(
                model=model,
                requirements=task_requirements,
                submission_text=candidate_submission_text,
                notes=candidate_notes,
                known_issues=known_issues,
                files_summary=files_summary or [],
                language=valid_language
            )
            if review_result.get("success"):
                return review_result
            else:
                logger.warning(f"Gemini review returned failure: {review_result.get('error')}. Using fallback.")
        except Exception as e:
            logger.warning(f"Exception calling Gemini: {e}. Falling back to rule-based comparison.")

    # Rule-based fallback
    return _run_rule_based_review(
        requirements=task_requirements,
        submission_text=candidate_submission_text,
        notes=candidate_notes,
        known_issues=known_issues,
        files_summary=files_summary or [],
        language=valid_language
    )


def _run_gemini_review(
    model: Any,
    requirements: str,
    submission_text: str,
    notes: str,
    known_issues: str,
    files_summary: List[Dict[str, Any]],
    language: str
) -> Dict[str, Any]:
    """Execute AI review using configured Gemini model."""
    files_list_str = "\n".join([f"- {f.get('path', 'unknown')} ({f.get('size', 0)} bytes)" for f in files_summary])

    prompt = f"""
You are an expert Senior Technical Reviewer evaluating an intern's project submission against official company requirements.

CRITICAL INSTRUCTIONS:
1. Ground truth: Evaluate ONLY against the official company requirements provided below. Do not invent requirements or assume unmentioned features are required.
2. Accuracy: Verify actual code and text in the submission. Do not mark a requirement 'Met' just because a filename or title exists.
3. Language: All explanations, summaries, bugs, corrections, and checklist items MUST be written in {language}. Technical identifiers, file paths, and function names can remain in English.
4. Return ONLY valid JSON adhering strictly to the schema below without any markdown fences, backticks, or prefix text.

### JSON SCHEMA:
{{
  "overall_status": "Completed" | "Needs Changes" | "Incomplete",
  "overall_score": <integer from 0 to 100>,
  "summary": "<Concise high-level evaluation in {language}>",
  "requirements_analysis": [
    {{
      "requirement": "<Requirement title or statement>",
      "status": "Met" | "Partially Met" | "Missing",
      "evidence": "<Direct evidence/code reference from candidate submission or 'No evidence found'>",
      "explanation": "<Specific reason for the status in {language}>"
    }}
  ],
  "strengths": [
    "<Highlight of correctly completed component in {language}>"
  ],
  "bugs_and_issues": [
    "<Specific bug, syntax flaw, incorrect logic, or missing validation in {language}>"
  ],
  "missing_components": [
    "<Missing file, function, module, or required parameter in {language}>"
  ],
  "actionable_corrections": [
    "<Specific, step-by-step guidance on how to fix errors in {language}>"
  ],
  "prioritized_checklist": [
    "<Numbered priority action item for next revision in {language}>"
  ],
  "limitations": [
    "<Things that could not be statically verified without code execution in {language}>"
  ]
}}

### OFFICIAL COMPANY REQUIREMENTS:
{requirements[:10000]}

### CANDIDATE'S SUBMISSION METADATA:
Candidate Notes: {notes or 'None provided'}
Known Issues Declared: {known_issues or 'None declared'}
Submitted Files:
{files_list_str[:3000]}

### CANDIDATE'S SUBMITTED CODE AND CONTENT:
{submission_text[:40000]}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Clean potential markdown wrapping
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON output: {e}\nRaw output: {raw_text[:500]}")
        return {"success": False, "error": f"Invalid JSON response from AI: {str(e)}"}

    # Validate essential fields
    overall_status = data.get("overall_status", "Needs Changes")
    if overall_status not in ["Completed", "Needs Changes", "Incomplete"]:
        overall_status = "Needs Changes"

    try:
        score = int(data.get("overall_score", 50))
        score = max(0, min(100, score))
    except (ValueError, TypeError):
        score = 50

    return {
        "success": True,
        "is_ai_generated": True,
        "model_used": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "language": language,
        "overall_status": overall_status,
        "overall_score": score,
        "summary": data.get("summary", "AI evaluation completed."),
        "structured_data": data,
        "raw_response": raw_text
    }


def _run_rule_based_review(
    requirements: str,
    submission_text: str,
    notes: str,
    known_issues: str,
    files_summary: List[Dict[str, Any]],
    language: str
) -> Dict[str, Any]:
    """
    Transparent, deterministic rule-based review engine when Gemini API is not configured or unavailable.
    Explicitly labeled as Rule-Based Demo Results.
    """
    i18n = FALLBACK_TRANSLATIONS.get(language, FALLBACK_TRANSLATIONS["English"])

    # 1. Parse requirement items from requirements text
    req_lines = [line.strip() for line in requirements.splitlines() if line.strip()]
    extracted_reqs = []

    for line in req_lines:
        # Match headings, numbered lists, or bullet points
        clean = re.sub(r"^([#*\-+0-9\.\)\s]+)", "", line).strip()
        if len(clean) > 10 and not clean.lower().startswith("table of contents"):
            if any(kw in clean.lower() for kw in [
                "must", "should", "require", "feature", "task", "api", "database",
                "ui", "module", "implement", "support", "create", "model", "page", "test"
            ]) or line.startswith(("#", "-", "*", "1.", "2.", "3.", "4.", "5.")):
                if len(clean) < 120 and clean not in extracted_reqs:
                    extracted_reqs.append(clean)

    if not extracted_reqs:
        extracted_reqs = [
            "Core application implementation and entry point",
            "Data persistence / database schema setup",
            "User interface components and workflows",
            "Error handling and boundary condition checks",
            "Documentation and test verification"
        ]

    # Limit to top 8 requirements for readability
    extracted_reqs = extracted_reqs[:8]

    # 2. Check candidate submission against requirements
    submission_lower = submission_text.lower()
    files_paths_lower = [f.get("path", "").lower() for f in files_summary]
    files_paths_str = " ".join(files_paths_lower)

    req_analysis = []
    met_count = 0
    partial_count = 0
    missing_count = 0

    bugs = []
    missing_components = []
    strengths = []
    corrections = []
    checklist = []

    for idx, req in enumerate(extracted_reqs, 1):
        # Extract keywords (words > 3 chars, excluding common stop words)
        words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", req.lower())
                 if w not in {"must", "should", "with", "from", "that", "this", "have", "been", "will", "each"}]

        found_in_content = [w for w in words if w in submission_lower]
        found_in_paths = [w for w in words if w in files_paths_str]

        match_ratio = (len(found_in_content) / len(words)) if words else 0.5

        if match_ratio >= 0.7 or (len(found_in_paths) >= 2):
            status = "Met"
            met_count += 1
            # Search a brief snippet as evidence
            evidence = _extract_evidence_snippet(submission_text, found_in_content)
            explanation = f"{i18n['met_desc']} Matching keywords found: {', '.join(found_in_content[:3])}."
            strengths.append(f"Successfully implemented {req[:80]}.")
        elif match_ratio >= 0.3 or len(found_in_content) >= 1 or len(found_in_paths) >= 1:
            status = "Partially Met"
            partial_count += 1
            evidence = _extract_evidence_snippet(submission_text, found_in_content)
            explanation = f"{i18n['partial_desc']} Keywords detected: {', '.join(found_in_content[:2])}."
            missing_components.append(f"Incomplete sub-components for: {req[:80]}")
            corrections.append(f"Complete remaining aspects of '{req[:60]}'.")
            checklist.append(f"{i18n['checklist_prefix']}{req[:60]}")
        else:
            status = "Missing"
            missing_count += 1
            evidence = "No matching evidence found in submitted files."
            explanation = i18n["missing_desc"]
            missing_components.append(f"Missing implementation for: {req[:80]}")
            corrections.append(f"Implement '{req[:60]}' according to company requirements.")
            checklist.append(f"{i18n['checklist_prefix']}{req[:60]}")

        req_analysis.append({
            "requirement": req,
            "status": status,
            "evidence": evidence,
            "explanation": explanation
        })

    # Evaluate declared issues
    if known_issues.strip():
        bugs.append(f"Candidate acknowledged: {known_issues.strip()}")

    # Check for basic files
    has_readme = any("readme" in p for p in files_paths_lower)
    if not has_readme:
        missing_components.append("Missing README.md documentation file in submission.")
        corrections.append("Add a comprehensive README.md with setup and usage instructions.")

    # Calculate transparent score
    total_reqs = len(extracted_reqs)
    raw_score = (met_count * 100 + partial_count * 50) / total_reqs if total_reqs else 0
    overall_score = int(round(raw_score))

    if overall_score >= 85 and missing_count == 0:
        overall_status = "Completed"
    elif overall_score >= 45:
        overall_status = "Needs Changes"
    else:
        overall_status = "Incomplete"

    summary = (
        f"{i18n['summary_intro']} "
        f"Verified {met_count} met, {partial_count} partially met, and {missing_count} missing requirements out of {total_reqs} evaluated."
    )

    limitations = [
        i18n["unverified_note"],
        "Rule-based fallback used because GEMINI_API_KEY is not configured or network access was unavailable.",
        "To obtain full natural-language code reasoning, configure GEMINI_API_KEY in .env."
    ]

    structured_data = {
        "overall_status": overall_status,
        "overall_score": overall_score,
        "summary": summary,
        "requirements_analysis": req_analysis,
        "strengths": strengths or ["Basic project structure submitted."],
        "bugs_and_issues": bugs or ["No critical syntax bugs detected via static analysis."],
        "missing_components": missing_components or ["No critical components missing."],
        "actionable_corrections": corrections or ["Ensure all edge cases and documentation are finalized."],
        "prioritized_checklist": checklist or ["Maintain current code quality and prepare for final presentation."],
        "limitations": limitations
    }

    return {
        "success": True,
        "is_ai_generated": False,
        "model_used": "Fallback Rule-Based Engine (Demo Mode)",
        "language": language,
        "overall_status": overall_status,
        "overall_score": overall_score,
        "summary": summary,
        "structured_data": structured_data,
        "raw_response": json.dumps(structured_data)
    }


def _extract_evidence_snippet(text: str, keywords: List[str]) -> str:
    """Find a relevant snippet of code/text containing matching keywords."""
    if not text or not keywords:
        return "Found matching keyword references in submitted codebase."

    for kw in keywords:
        pos = text.lower().find(kw)
        if pos != -1:
            start = max(0, pos - 40)
            end = min(len(text), pos + 120)
            snippet = text[start:end].replace("\n", " ").strip()
            return f"...{snippet}..."
    return "Matching implementation detected in files."
