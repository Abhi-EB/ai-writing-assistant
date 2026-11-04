
import os
import logging
from pathlib import Path
from datetime import datetime

import ipywidgets as widgets
from IPython.display import display, clear_output, Markdown
from google import genai
from docx import Document


# ============================================
# 1. PROJECT FOLDERS
# ============================================

PROJECT_DIR = Path(__file__).resolve().parent

import sys

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from validation import find_placeholders


LOG_DIR = PROJECT_DIR / "logs"
OUTPUT_DIR = PROJECT_DIR / "outputs"

LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# 2. LOGGING CONFIGURATION
# ============================================

logger = logging.getLogger("ai_writing_assistant")
logger.setLevel(logging.INFO)
logger.propagate = False

# Avoid duplicate handlers
for handler in list(logger.handlers):
    logger.removeHandler(handler)
    handler.close()

file_handler = logging.FileHandler(
    LOG_DIR / "app.log",
    encoding="utf-8"
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("Application started")


# ============================================
# 3. MAIN APPLICATION
# ============================================

def build_app():

    # Read Gemini API key from environment
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("Gemini API key unavailable")
        raise RuntimeError("Gemini API key is unavailable.")

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite"
    )

    client = genai.Client(api_key=api_key)

    # Store application data
    state = {
        "draft": "",
        "review": "",
        "improved_draft": ""
    }


    # ========================================
    # 4. USER INTERFACE
    # ========================================

    title = widgets.HTML(
        "<h2>AI Writing Assistant</h2>"
        "<p>Generate, review and improve your writing.</p>"
    )

    topic_input = widgets.Textarea(
        description="Topic:",
        placeholder="Enter your writing topic",
        rows=3,
        layout=widgets.Layout(width="100%"),
        style={"description_width": "initial"}
    )

    audience_input = widgets.Text(
        description="Audience:",
        placeholder="Example: Friends, students, customers",
        layout=widgets.Layout(width="100%"),
        style={"description_width": "initial"}
    )

    format_dropdown = widgets.Dropdown(
        description="Format:",
        options=[
            "Email",
            "Social media post",
            "Formal letter",
            "Short article"
        ],
        value="Email",
        style={"description_width": "initial"}
    )

    tone_dropdown = widgets.Dropdown(
        description="Tone:",
        options=[
            "Professional",
            "Friendly",
            "Formal",
            "Creative",
            "Persuasive"
        ],
        value="Professional",
        style={"description_width": "initial"}
    )

    length_dropdown = widgets.Dropdown(
        description="Length:",
        options=[
            "Short",
            "Medium",
            "Detailed"
        ],
        value="Medium",
        style={"description_width": "initial"}
    )

    generate_button = widgets.Button(
        description="Generate Draft",
        button_style="primary"
    )

    review_button = widgets.Button(
        description="Review Draft",
        button_style="info",
        disabled=True
    )

    improve_button = widgets.Button(
        description="Improve Draft",
        button_style="warning",
        disabled=True
    )

    approve_checkbox = widgets.Checkbox(
        description="I have reviewed and approved the final draft",
        value=False
    )

    export_button = widgets.Button(
        description="Export Word Document",
        button_style="success",
        disabled=True
    )

    pdf_export_button = widgets.Button(
        description="Export PDF",
        button_style="success",
        disabled=True
    )

    status = widgets.HTML(
        "<b>Status:</b> Ready"
    )

    draft_output = widgets.Output()
    review_output = widgets.Output()
    improved_output = widgets.Output()
    export_output = widgets.Output()

    final_editor = widgets.Textarea(
        description="Final Draft:",
        placeholder="Edit your final draft here.",
        rows=12,
        layout=widgets.Layout(width="100%"),
        style={"description_width": "initial"}
    )


    # ========================================
    # 5. GEMINI API FUNCTION
    # ========================================

    def call_gemini(prompt):

        logger.info("Gemini request started")

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        result = (response.text or "").strip()

        if not result:
            raise ValueError("Gemini returned an empty response.")

        logger.info("Gemini request completed")

        return result


    # ========================================
    # 6. BUTTON CONTROL
    # ========================================

    def update_controls(change=None):

        review_button.disabled = not bool(
            state["draft"]
        )

        improve_button.disabled = not bool(
            state["draft"] and state["review"]
        )

        final_draft_exists = bool(
            final_editor.value.strip()
        )

        export_button.disabled = not (
            final_draft_exists and approve_checkbox.value
        )
        pdf_export_button.disabled = not (
            final_draft_exists and approve_checkbox.value
        )

    approve_checkbox.observe(
        update_controls,
        names="value"
    )

    def on_final_draft_change(change):
        approve_checkbox.value = False
        update_controls()

    final_editor.observe(
        on_final_draft_change,
        names="value"
    )


    # ========================================
    # 7. GENERATE DRAFT
    # ========================================

    def generate_draft(button):

        topic = topic_input.value.strip()

        if not topic:
            status.value = (
                "<b>Status:</b> Please enter a topic first."
            )
            return

        state["draft"] = ""
        state["review"] = ""
        state["improved_draft"] = ""
        final_editor.value = ""

        approve_checkbox.value = False

        update_controls()

        with draft_output:
            clear_output(wait=True)

        with review_output:
            clear_output(wait=True)

        with improved_output:
            clear_output(wait=True)

        prompt = f"""
        You are a professional writing assistant.

        Write content using these requirements:

        Topic: {topic}
        Audience: {audience_input.value or "General audience"}
        Format: {format_dropdown.value}
        Tone: {tone_dropdown.value}
        Length: {length_dropdown.value}

        Make the content clear, relevant and well structured.

        Never invent dates, times, locations, names,
        prices or contact details.

        If information is missing, use placeholders:
        [Date], [Time], [Location], [Contact Details].

        Do not assume or create missing information.
        """

        generate_button.disabled = True

        status.value = (
            "<b>Status:</b> Generating your draft..."
        )

        try:

            state["draft"] = call_gemini(prompt)
            final_editor.value = state["draft"]

            with draft_output:
                display(Markdown(state["draft"]))

            logger.info("Draft generated successfully")

            status.value = (
                "<b>Status:</b> Draft generated successfully."
            )

        except Exception:

            logger.exception("Draft generation failed")

            status.value = (
                "<b>Error:</b> Content generation failed. "
                "Please try again."
            )

        finally:

            generate_button.disabled = False
            update_controls()


    # ========================================
    # 8. REVIEW DRAFT
    # ========================================

    def review_draft(button):

        if not state["draft"]:
            return

        prompt = f"""
        Act as a professional writing quality reviewer.

        Review this content for:

        1. Grammar
        2. Spelling
        3. Clarity
        4. Relevance to the topic
        5. Tone
        6. Completeness

        Identify factual claims that need verification.
        Do not assume that claims are true.

        Original topic:
        {topic_input.value}

        Draft:
        {state["draft"]}

        Provide an overall assessment and suggestions.

        Compare explicit and implied factual details
        against the original user requirements.

        Flag unsupported dates, times, locations, names,
        prices, contact details and assumptions about
        the time of day.

        A weekend does not automatically mean afternoon
        or evening.

        Check whether the book title and author are supplied.
        If missing, recommend [Book Title] and [Author].

        Do not approve unsupported assumptions.
        """

        review_button.disabled = True

        status.value = (
            "<b>Status:</b> Reviewing your draft..."
        )

        try:

            state["review"] = call_gemini(prompt)

            with review_output:
                clear_output(wait=True)
                display(Markdown(state["review"]))

            logger.info("Draft review completed")

            status.value = (
                "<b>Status:</b> Review completed."
            )

        except Exception:

            logger.exception("Draft review failed")

            status.value = (
                "<b>Error:</b> Draft review failed. "
                "Please try again."
            )

        finally:

            review_button.disabled = False
            update_controls()


    # ========================================
    # 9. IMPROVE DRAFT
    # ========================================

    def improve_draft(button):

        if not state["draft"] or not state["review"]:
            return

        prompt = f"""
        Act as a professional editor.

        Improve the original draft using the review feedback.

        Preserve the original purpose and friendly tone.

        Apply all necessary corrections from the review.

        Remove unsupported assumptions, including
        references to a specific time of day when none
        was provided.

        If the book title and author are missing, insert
        [Book Title] and [Author] in the appropriate place.

        Keep [Date], [Time], [Location] and
        [Contact Details] unchanged.

        Do not invent facts.

        Do not add optional recommendations, such as
        dietary reminders, unless specifically requested.

        Return only the complete improved draft.

        Original topic:
        {topic_input.value}

        Original draft:
        {state["draft"]}

        Review feedback:
        {state["review"]}
        """

        improve_button.disabled = True

        status.value = (
            "<b>Status:</b> Improving your draft..."
        )

        try:

            state["improved_draft"] = call_gemini(prompt)
            final_editor.value = state["improved_draft"]

            approve_checkbox.value = False

            with improved_output:
                clear_output(wait=True)
                display(Markdown(state["improved_draft"]))

            logger.info("Draft improvement completed")

            status.value = (
                "<b>Status:</b> Improved draft ready. "
                "Please review it."
            )

        except Exception:

            logger.exception("Draft improvement failed")

            status.value = (
                "<b>Error:</b> Draft improvement failed. "
                "Please try again."
            )

        finally:

            improve_button.disabled = False
            update_controls()


    # ========================================
    # 10. EXPORT WORD DOCUMENT
    # ========================================

    def export_document(button):

        import re

        final_text = final_editor.value.strip()

        if not final_text:
            status.value = (
                "<b>Status:</b> No draft available."
            )
            return

        # Check for unfinished placeholders
        # Detect unfinished placeholders
        placeholders = []
        remaining_text = final_text

        while True:
            opening = remaining_text.find("[")

            if opening == -1:
                break

            closing = remaining_text.find("]", opening + 1)

            if closing == -1:
                break

            item = remaining_text[opening:closing + 1]

            if item[1:-1].strip():
                placeholders.append(item)

            remaining_text = remaining_text[closing + 1:]

        placeholders = list(dict.fromkeys(placeholders))


        placeholders = find_placeholders(final_text)

        if placeholders:

            missing_items = list(dict.fromkeys(placeholders))

            logger.warning(
                "Document export blocked. Missing placeholders: %s",
                ", ".join(missing_items)
            )

            approve_checkbox.value = False

            with export_output:
                clear_output(wait=True)
                print("EXPORT BLOCKED")
                print("Please complete these details:")
                for item in missing_items:
                    print("-", item)

            status.value = (
                "<b>Status:</b> Export blocked. "
                "Please complete all placeholders."
            )
            return

        if not approve_checkbox.value:
            status.value = (
                "<b>Status:</b> Please review and approve "
                "the final draft first."
            )
            return

        try:

            document = Document()

            document.add_heading(
                "AI Writing Assistant - Final Draft",
                level=1
            )

            document.add_paragraph(
                "Topic: " + topic_input.value.strip()
            )

            document.add_paragraph(final_text)

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            file_path = OUTPUT_DIR / (
                f"final_draft_{timestamp}.docx"
            )

            document.save(file_path)

            logger.info(
                "Word document saved successfully: %s",
                file_path.name
            )

            with export_output:
                clear_output(wait=True)
                print("Document saved:", file_path)

            from google.colab import files
            files.download(str(file_path))

            logger.info("Word document download requested")

            status.value = (
                "<b>Status:</b> Word document exported successfully."
            )

        except Exception:
            logger.exception("Word export failed")

            status.value = (
                "<b>Error:</b> Word document export failed. "
                "Please try again."
            )

    # ========================================
    # 11. CONNECT BUTTONS
    # ========================================

    # ========================================
    # PDF EXPORT
    # ========================================

    def export_pdf(button):

        import re
        import subprocess
        import tempfile
        import shutil

        final_text = final_editor.value.strip()

        if not final_text:
            status.value = "<b>Status:</b> No draft available."
            return

        # Check for unfinished placeholders
        # Detect unfinished placeholders
        placeholders = []
        remaining_text = final_text

        while True:
            opening = remaining_text.find("[")

            if opening == -1:
                break

            closing = remaining_text.find("]", opening + 1)

            if closing == -1:
                break

            item = remaining_text[opening:closing + 1]

            if item[1:-1].strip():
                placeholders.append(item)

            remaining_text = remaining_text[closing + 1:]

        placeholders = list(dict.fromkeys(placeholders))


        placeholders = find_placeholders(final_text)

        if placeholders:

            missing = list(dict.fromkeys(placeholders))

            with export_output:
                clear_output(wait=True)
                print("PDF EXPORT BLOCKED")
                print("Complete these placeholders:")
                for item in missing:
                    print("-", item)

            logger.warning("PDF export blocked by placeholders")

            status.value = (
                "<b>Status:</b> Complete all placeholders first."
            )
            return

        if not approve_checkbox.value:
            status.value = (
                "<b>Status:</b> Please approve the final draft first."
            )
            return

        converter = (
            shutil.which("libreoffice")
            or shutil.which("soffice")
        )

        if not converter:
            status.value = (
                "<b>Error:</b> LibreOffice is not installed. "
                "Please install the PDF conversion tool."
            )
            logger.error("LibreOffice PDF converter unavailable")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            pdf_path = OUTPUT_DIR / (
                f"final_draft_{timestamp}.pdf"
            )

            # Create temporary Word file for conversion
            with tempfile.TemporaryDirectory(
                dir=str(OUTPUT_DIR)
            ) as temporary_folder:

                temporary_docx = (
                    Path(temporary_folder)
                    / f"final_draft_{timestamp}.docx"
                )

                document = Document()

                document.add_heading(
                    "AI Writing Assistant - Final Draft",
                    level=1
                )

                document.add_paragraph(
                    "Topic: " + topic_input.value.strip()
                )

                document.add_paragraph(final_text)

                document.save(temporary_docx)

                # Convert Word document to PDF
                result = subprocess.run(
                    [
                        converter,
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(OUTPUT_DIR),
                        str(temporary_docx)
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=True
                )

            if not pdf_path.exists() or pdf_path.stat().st_size == 0:
                raise RuntimeError(
                    "PDF conversion did not create a valid file. "
                    + result.stderr
                )

            logger.info("PDF document saved successfully: %s",
                        pdf_path.name)

            with export_output:
                clear_output(wait=True)
                print("PDF saved successfully:")
                print(pdf_path)

            from google.colab import files
            files.download(str(pdf_path))

            logger.info("PDF download requested")

            status.value = (
                "<b>Status:</b> PDF exported successfully."
            )

        except Exception:
            logger.exception("PDF export failed")

            status.value = (
                "<b>Error:</b> PDF export failed. "
                "Please check the application log."
            )


    generate_button.on_click(generate_draft)
    review_button.on_click(review_draft)
    improve_button.on_click(improve_draft)
    export_button.on_click(export_document)
    pdf_export_button.on_click(export_pdf)



    # ========================================
    # DOCUMENT ANALYTICS DASHBOARD
    # ========================================

    import html as html_lib

    dashboard_display = widgets.HTML()
    refresh_dashboard_button = widgets.Button(
        description="Refresh Dashboard",
        icon="refresh",
        button_style="info"
    )

    def refresh_dashboard(_=None):

        log_file = LOG_DIR / "app.log"

        if not log_file.exists():
            dashboard_display.value = "<p>No application log found.</p>"
            return

        log_lines = log_file.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()

        messages = []

        for line in log_lines:
            parts = line.split(" | ", 2)

            if len(parts) == 3:
                messages.append({
                    "timestamp": parts[0],
                    "level": parts[1],
                    "message": parts[2]
                })

        def count_events(prefix):
            return sum(
                1 for item in messages
                if item["message"].startswith(prefix)
            )

        generated = count_events("Draft generated successfully")
        reviewed = count_events("Draft review completed")
        improved = count_events("Draft improvement completed")
        word_exports = count_events("Word document saved successfully")
        pdf_exports = count_events("PDF document saved successfully")

        blocked = (
            count_events("Document export blocked")
            + count_events("PDF export blocked")
        )

        cards = [
            ("Drafts Generated", generated),
            ("Drafts Reviewed", reviewed),
            ("Drafts Improved", improved),
            ("Word Exports", word_exports),
            ("PDF Exports", pdf_exports),
            ("Blocked Exports", blocked)
        ]

        cards_html = ""

        for label, value in cards:
            cards_html += f"""
            <div style="
                border:1px solid #888;
                border-radius:10px;
                padding:14px;
                min-width:125px;
                flex:1;
                margin:4px;
            ">
                <div style="font-size:25px;font-weight:bold;">
                    {value}
                </div>
                <div style="font-size:13px;">
                    {label}
                </div>
            </div>
            """

        recent_html = ""

        for item in reversed(messages[-8:]):
            timestamp = html_lib.escape(item["timestamp"])
            level = html_lib.escape(item["level"])
            message = html_lib.escape(item["message"])

            recent_html += f"""
            <div style="
                padding:8px 4px;
                border-bottom:1px solid #888;
                font-size:13px;
            ">
                <b>{timestamp}</b> | {level}<br>
                {message}
            </div>
            """

        if not recent_html:
            recent_html = "<p>No activity recorded yet.</p>"

        dashboard_display.value = f"""
        <div style="margin:12px 0;">
            <h3>Document Analytics Dashboard</h3>

            <div style="
                display:flex;
                flex-wrap:wrap;
                margin:0 -4px;
            ">
                {cards_html}
            </div>

            <h4>Recent Activity (Last 8 Events)</h4>
            {recent_html}

            <p style="font-size:12px;opacity:0.7;">
                Last refreshed: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
            </p>
        </div>
        """

    refresh_dashboard_button.on_click(refresh_dashboard)

    refresh_dashboard()

    dashboard_section = widgets.VBox([
        widgets.HTML("<h2>Application Dashboard</h2>"),
        refresh_dashboard_button,
        dashboard_display
    ])


    # ========================================
    # 12. DISPLAY APPLICATION
    # ========================================

    interface = widgets.VBox([

        dashboard_section,
        title,

        topic_input,
        audience_input,
        format_dropdown,
        tone_dropdown,
        length_dropdown,

        widgets.HBox([
            generate_button,
            review_button,
            improve_button
        ]),

        widgets.HTML("<h3>Generated Draft</h3>"),
        draft_output,

        widgets.HTML("<h3>AI Quality Review</h3>"),
        review_output,

        widgets.HTML("<h3>Improved Draft</h3>"),
        improved_output,

        widgets.HTML("<h3>Edit Your Final Draft</h3>"),
        final_editor,

        approve_checkbox,
        widgets.HBox([
            export_button,
            pdf_export_button
        ]),

        export_output,
        status
    ])

    display(interface)

    logger.info("Application interface displayed")


# ============================================
# 13. START APPLICATION
# ============================================

if __name__ == "__main__":
    build_app()
