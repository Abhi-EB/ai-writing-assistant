
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

    status = widgets.HTML(
        "<b>Status:</b> Ready"
    )

    draft_output = widgets.Output()
    review_output = widgets.Output()
    improved_output = widgets.Output()
    export_output = widgets.Output()


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
            state["improved_draft"] or state["draft"]
        )

        export_button.disabled = not (
            final_draft_exists and approve_checkbox.value
        )

    approve_checkbox.observe(
        update_controls,
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
        Do not invent missing facts.
        """

        generate_button.disabled = True

        status.value = (
            "<b>Status:</b> Generating your draft..."
        )

        try:

            state["draft"] = call_gemini(prompt)

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

        Preserve the original purpose.
        Correct writing problems.
        Do not invent facts.
        Return only the improved content.

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

        final_text = (
            state["improved_draft"] or state["draft"]
        )

        if not final_text:
            status.value = (
                "<b>Status:</b> No draft available."
            )
            return

        if not approve_checkbox.value:
            status.value = (
                "<b>Status:</b> Please approve the draft first."
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

            logger.info("Word document saved successfully")

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

    generate_button.on_click(generate_draft)
    review_button.on_click(review_draft)
    improve_button.on_click(improve_draft)
    export_button.on_click(export_document)


    # ========================================
    # 12. DISPLAY APPLICATION
    # ========================================

    interface = widgets.VBox([

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

        approve_checkbox,
        export_button,

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
