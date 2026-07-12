from config import (
    GYNECOLOGIC,
    NON_GYNECOLOGIC,
    ROUTINE_WORKFLOW,
    ROSE_WORKFLOW,
    WORKFLOW_TEMPLATES,
    GYNECOLOGIC_POST_SCREENING_ROUTES,
    DISCREPANCY_REVIEW_ROUTES,
)

def get_base_workflow_template(
    specimen_category,
    workflow_type,
):
    """
    Return the base workflow stages for a cytology case.
    """

    if workflow_type == ROSE_WORKFLOW:
        return WORKFLOW_TEMPLATES["rose"].copy()

    if specimen_category == GYNECOLOGIC:
        return WORKFLOW_TEMPLATES[
            "gynecologic_routine"
        ].copy()

    if specimen_category == NON_GYNECOLOGIC:
        return WORKFLOW_TEMPLATES[
            "non_gynecologic_routine"
        ].copy()

    raise ValueError(
        f"Unsupported specimen category: {specimen_category}"
    )

def get_gynecologic_post_screening_route(
    screening_result,
    selected_for_quality_control=False,
):
    """
    Return the required downstream stages after gynecologic screening.
    """

    normalized_result = str(screening_result).strip().lower()

    negative_results = {
        "negative",
        "normal",
        "nilm",
    }

    if normalized_result in negative_results:
        if selected_for_quality_control:
            return GYNECOLOGIC_POST_SCREENING_ROUTES[
                "negative_selected_for_qc"
            ].copy()

        return GYNECOLOGIC_POST_SCREENING_ROUTES[
            "negative_not_selected_for_qc"
        ].copy()

    return GYNECOLOGIC_POST_SCREENING_ROUTES[
        "abnormal_or_questionable"
    ].copy()

def build_case_workflow(
    specimen_category,
    workflow_type,
    screening_result=None,
    selected_for_quality_control=False,
    discrepancy_review=None,
):
    """
    Build the complete workflow path for a cytology case.
    """

    workflow = get_base_workflow_template(
        specimen_category=specimen_category,
        workflow_type=workflow_type,
    )

    if (
        specimen_category == GYNECOLOGIC
        and workflow_type == ROUTINE_WORKFLOW
        and screening_result is not None
    ):
        workflow.extend(
            get_gynecologic_post_screening_route(
                screening_result=screening_result,
                selected_for_quality_control=(
                    selected_for_quality_control
                ),
            )
        )

    if discrepancy_review is not None:
        if discrepancy_review not in DISCREPANCY_REVIEW_ROUTES:
            raise ValueError(
                f"Unsupported quality follow-up route: "
                f"{discrepancy_review}"
            )

        workflow.extend(
            DISCREPANCY_REVIEW_ROUTES[
                discrepancy_review
            ].copy()
        )

    return workflow

def get_next_workflow_stage(
    workflow_stages,
    current_stage,
):
    """
    Return the stage immediately following the current workflow stage.
    """

    if not workflow_stages:
        return None

    if current_stage is None:
        return workflow_stages[0]

    if current_stage not in workflow_stages:
        raise ValueError(
            f"Current stage is not part of this workflow: "
            f"{current_stage}"
        )

    current_index = workflow_stages.index(
        current_stage
    )

    next_index = current_index + 1

    if next_index >= len(workflow_stages):
        return None

    return workflow_stages[next_index]

def describe_next_required_action(next_stage):
    """
    Return a user-friendly action for the next workflow stage.
    """

    action_descriptions = {
        "specimen_received": (
            "Receive and accession the specimen."
        ),
        "slide_preparation": (
            "Prepare diagnostic slides for review."
        ),
        "digital_imaging": (
            "Complete digital imaging of the prepared slide."
        ),
        "imager_review": (
            "Review image quality and resolve scan issues."
        ),
        "rose_procedure": (
            "Perform the ROSE procedure."
        ),
        "rose_adequacy_assessment": (
            "Record the ROSE adequacy assessment."
        ),
        "laboratory_processing": (
            "Complete laboratory processing before screening."
        ),
        "primary_cytologist_screening": (
            "Assign and complete primary cytologist screening."
        ),
        "quality_control_review": (
            "Complete the required quality control rescreen."
        ),
        "pathologist_review": (
            "Route the case for pathologist review."
        ),
        "final_sign_out": (
            "Complete final case sign out."
        ),
        "discrepancy_review": (
            "Review discrepancies between preliminary and final interpretations."
        ),
        "educational_review": (
            "Review the case with the pathologist and document educational findings."
        ),
    }

    if next_stage is None:
        return "No additional workflow action is required."

    return action_descriptions.get(
        next_stage,
        "Complete the next required workflow stage.",
    )

if __name__ == "__main__":
    test_workflow = build_case_workflow(
        specimen_category=NON_GYNECOLOGIC,
        workflow_type=ROSE_WORKFLOW,
        discrepancy_review="discrepancy_found",
    )

    print("Workflow stages:")

    for stage in test_workflow:
        print(f"- {stage}")

    current_stage = "laboratory_processing"

    next_stage = get_next_workflow_stage(
        test_workflow,
        current_stage,
    )

    print()
    print(f"Current stage: {current_stage}")
    print(f"Next stage: {next_stage}")
    print(
        describe_next_required_action(
            next_stage
        )
    )