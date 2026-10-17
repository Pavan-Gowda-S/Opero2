"""
Form Safety Gate for TinyFish Agent Operations

Enforces mandatory user review before any consequential actions such as form
submissions, data posting, transactions, or account changes. Provides field-by-field
validation display and integrates with Opero's confirmation gate.

Phase 5 Component: Safety barrier preventing unintended automation consequences.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.logger import get_logger
from core import confirm

log = get_logger(__name__)


# ── Safety Review Data Structures ──────────────────────────────────────────────

@dataclass
class FormField:
    """Single form field with value and metadata."""
    name: str
    value: str
    field_type: str = "text"  # text, email, password, checkbox, etc.
    required: bool = False
    inferred: bool = False  # True if value was guessed/inferred
    sensitive: bool = False  # True for passwords, credit cards, SSNs


@dataclass
class FormSubmissionReview:
    """Complete review payload for form submission."""
    target_url: str
    form_name: str
    form_id: Optional[str]
    fields: List[FormField]
    action_url: Optional[str]  # Where form submits to
    method: str = "POST"  # HTTP method

    def has_missing_fields(self) -> bool:
        """Check if any required fields are missing or inferred."""
        return any(
            (f.required and not f.value) or f.inferred
            for f in self.fields
        )

    def has_sensitive_data(self) -> bool:
        """Check if form contains sensitive information."""
        return any(f.sensitive for f in self.fields)

    def get_summary(self) -> str:
        """Generate human-readable summary of form submission."""
        lines = [
            f"Form: {self.form_name}",
            f"Target: {self.target_url}",
            f"Action: {self.action_url or 'Same page'}",
            f"Method: {self.method}",
            f"",
            "Fields to be submitted:",
        ]

        for field in self.fields:
            status_flags = []
            if field.required:
                status_flags.append("REQUIRED")
            if field.inferred:
                status_flags.append("⚠️ INFERRED")
            if field.sensitive:
                status_flags.append("🔒 SENSITIVE")

            status = f" [{', '.join(status_flags)}]" if status_flags else ""

            # Mask sensitive values
            display_value = field.value
            if field.sensitive and field.value:
                display_value = "***" + field.value[-4:] if len(field.value) > 4 else "***"

            lines.append(f"  • {field.name}: {display_value}{status}")

        return "\n".join(lines)


# ── Safety Gate Functions ──────────────────────────────────────────────────────

def request_form_submission_approval(
    review: FormSubmissionReview,
    submit_handler: callable
) -> str:
    """
    Request user approval before submitting a form.

    This is the primary safety gate for consequential actions. It:
    - Displays all form fields for user review
    - Highlights missing, inferred, or sensitive data
    - Blocks submission until explicit user confirmation
    - Never auto-submits, never guesses missing values

    Args:
        review: FormSubmissionReview with all form details
        submit_handler: Callable that performs the actual submission

    Returns:
        str: Confirmation pending message or immediate error
    """
    # SAFETY CHECK 1: Never allow payment-related submissions
    if _contains_payment_fields(review):
        log.error("[FormSafety] BLOCKED: Payment form submission attempted")
        return (
            "❌ SAFETY BLOCK: Payment form submission is prohibited.\n\n"
            "This form contains payment-related fields (credit card, billing info). "
            "TinyFish agent automation does NOT support financial transactions. "
            "Complete this form manually to ensure security."
        )

    # SAFETY CHECK 2: Halt if required fields are missing or inferred
    if review.has_missing_fields():
        missing_fields = [
            f.name for f in review.fields
            if (f.required and not f.value) or f.inferred
        ]

        log.warning(f"[FormSafety] Missing/inferred fields: {missing_fields}")

        return (
            "❌ CANNOT SUBMIT: Required fields are missing or contain inferred values.\n\n"
            f"The following fields need your input:\n"
            + "\n".join(f"  • {field}" for field in missing_fields) +
            "\n\nAgent cannot guess or infer answers for form fields. "
            "Please provide explicit values for all required fields."
        )

    # SAFETY CHECK 3: Check for pending confirmation
    if confirm.pending_title():
        return (
            "Another confirmation is pending. Please respond to it first before "
            "submitting this form."
        )

    # Build confirmation details
    confirmation_title = "Form Submission Review"
    confirmation_detail = review.get_summary()

    # Add safety warnings
    confirmation_detail += "\n\n⚠️ SAFETY WARNINGS:"
    confirmation_detail += "\n• This will submit data to an external website"
    confirmation_detail += "\n• The submission cannot be undone"

    if review.has_sensitive_data():
        confirmation_detail += "\n• Form contains sensitive information"

    confirmation_detail += "\n\nReview all fields carefully before confirming."

    log.info(f"[FormSafety] Requesting approval for form: {review.form_name}")

    # Request confirmation (non-blocking)
    return confirm.request(
        key="form_submit",
        title=confirmation_title,
        detail=confirmation_detail,
        run=submit_handler
    )


def validate_form_goal(goal: str) -> tuple[bool, Optional[str]]:
    """
    Validate that an agent goal does not attempt prohibited form operations.

    This is a pre-execution check that runs before the confirmation gate.
    It rejects obviously unsafe goals using pattern matching.

    Args:
        goal: Natural language goal text

    Returns:
        tuple: (is_valid, error_message)
    """
    # Prohibited patterns (case-insensitive)
    # Note: These are broad patterns - some false positives acceptable for safety
    prohibited_patterns = [
        # Payment & Financial
        ("credit card", "Credit card entry is prohibited"),
        ("payment info", "Payment information entry is prohibited"),
        ("billing", "Billing information entry is prohibited"),
        ("purchase", "Purchase operations are prohibited"),
        ("checkout", "Checkout operations are prohibited"),

        # Account & Auth
        ("create account", "Account creation requires manual completion"),
        ("sign up", "Sign-up requires manual completion"),
        ("change password", "Password changes must be done manually"),
        ("reset password", "Password resets must be done manually"),

        # Data Modification
        ("delete my", "Deletion operations require manual confirmation"),
        ("remove my", "Removal operations require manual confirmation"),
        ("cancel my", "Cancellation operations require manual confirmation"),

        # Messaging & Communication
        ("post comment", "Comment posting requires manual review"),
    ]

    goal_lower = goal.lower()

    for pattern, error in prohibited_patterns:
        if pattern in goal_lower:
            log.warning(f"[FormSafety] Goal validation failed: {pattern}")
            return False, error

    return True, None


# ── Helper Functions ───────────────────────────────────────────────────────────

def _contains_payment_fields(review: FormSubmissionReview) -> bool:
    """
    Check if form contains payment-related fields.

    Returns True if any field appears to be payment-related.
    """
    payment_indicators = [
        "card", "credit", "cvv", "cvc", "expir",
        "billing", "payment", "purchase", "checkout"
    ]

    for field in review.fields:
        field_name_lower = field.name.lower()
        if any(indicator in field_name_lower for indicator in payment_indicators):
            return True

        # Check for numeric fields that look like credit cards
        if field.value and field.value.replace(" ", "").replace("-", "").isdigit():
            if len(field.value.replace(" ", "").replace("-", "")) == 16:
                return True

    return False


def build_form_review_from_agent_data(
    target_url: str,
    form_data: Dict[str, Any]
) -> FormSubmissionReview:
    """
    Build a FormSubmissionReview from agent-collected form data.

    This helper constructs the review object from whatever data structure
    the agent returns. Adapt this function based on actual TinyFish SDK
    response format.

    Args:
        target_url: Page URL containing the form
        form_data: Form data dictionary from agent

    Returns:
        FormSubmissionReview instance
    """
    # Extract form metadata
    form_name = form_data.get("name", "Unnamed Form")
    form_id = form_data.get("id")
    action_url = form_data.get("action")
    method = form_data.get("method", "POST").upper()

    # Build field list
    fields = []
    for field_data in form_data.get("fields", []):
        field = FormField(
            name=field_data.get("name", "unknown"),
            value=field_data.get("value", ""),
            field_type=field_data.get("type", "text"),
            required=field_data.get("required", False),
            inferred=field_data.get("inferred", False),
            sensitive=_is_sensitive_field(field_data),
        )
        fields.append(field)

    return FormSubmissionReview(
        target_url=target_url,
        form_name=form_name,
        form_id=form_id,
        fields=fields,
        action_url=action_url,
        method=method,
    )


def _is_sensitive_field(field_data: Dict[str, Any]) -> bool:
    """Determine if a field contains sensitive information."""
    field_type = field_data.get("type", "").lower()
    field_name = field_data.get("name", "").lower()

    # Password fields
    if field_type == "password":
        return True

    # Common sensitive field names
    sensitive_names = [
        "password", "pwd", "pass",
        "ssn", "social", "tax",
        "credit", "card", "cvv", "cvc",
        "secret", "pin",
    ]

    return any(name in field_name for name in sensitive_names)


# ── Integration with TinyFish Agent ────────────────────────────────────────────

def wrap_agent_for_form_safety(
    original_agent_function: callable,
    goal: str,
    url: str,
    **kwargs
) -> str:
    """
    Wrap agent execution with form safety validation.

    This is a decorator-style function that can be used to add form safety
    checks to any agent operation. It validates the goal before execution
    and inspects results for form submission attempts.

    Args:
        original_agent_function: The _agent() function to wrap
        goal: Agent goal text
        url: Target URL
        **kwargs: Additional agent parameters

    Returns:
        str: Agent result or safety block message
    """
    # Pre-execution validation
    is_valid, error_message = validate_form_goal(goal)

    if not is_valid:
        log.warning(f"[FormSafety] BLOCKED goal: {goal}")
        return (
            f"❌ GOAL REJECTED: {error_message}\n\n"
            f"The requested operation involves form submission or data modification "
            f"that requires manual completion for security. Please complete this "
            f"task directly through your browser."
        )

    # Execute agent (this may take time)
    result = original_agent_function(url=url, goal=goal, **kwargs)

    # Post-execution: Check if result indicates form submission occurred
    # This is a safety net - ideally the agent should never auto-submit
    if _detect_unauthorized_submission(result):
        log.error("[FormSafety] ALERT: Unauthorized form submission detected!")
        return (
            "⚠️ SAFETY ALERT: The agent may have submitted a form without approval.\n\n"
            "This should not happen. Please verify the operation results and "
            "contact support if you did not authorize any submissions.\n\n"
            f"Original result: {result}"
        )

    return result


def _detect_unauthorized_submission(result: str) -> bool:
    """
    Detect if agent result indicates an unauthorized form submission.

    This is a post-execution safety check that looks for submission indicators
    in the agent's result text.
    """
    submission_indicators = [
        "form submitted",
        "submission successful",
        "thank you for submitting",
        "your request has been sent",
        "confirmation number",
        "order placed",
        "payment processed",
    ]

    result_lower = result.lower()
    return any(indicator in result_lower for indicator in submission_indicators)
