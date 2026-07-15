import pandas as pd

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

def resolve_effective_next_stage(
    workflow_stages,
    next_stage,
    last_action=None,
    assigned_to=None,
):
    """
    Resolve session-based workflow progression without changing source data.
    """

    if next_stage != "imager_review":
        return next_stage

    if last_action == "Pathologist Review Completed":
        if "pathologist_review" not in workflow_stages:
            return None

        pathologist_review_index = workflow_stages.index(
            "pathologist_review"
        )

        next_index = pathologist_review_index + 1

        if next_index >= len(workflow_stages):
            return None

        return workflow_stages[next_index]

    if assigned_to == "Pathologist":
        return "pathologist_review"

    if last_action == "Primary Review Completed":
        if "primary_cytologist_screening" not in workflow_stages:
            return None

        primary_review_index = workflow_stages.index(
            "primary_cytologist_screening"
        )

        next_index = primary_review_index + 1

        if next_index >= len(workflow_stages):
            return None

        return workflow_stages[next_index]

    if (
        last_action == "Imager Review Completed"
        or assigned_to in {
            "Cytologist",
            "Senior Cytologist",
        }
    ):
        return "primary_cytologist_screening"

    return next_stage

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
            "Assign and complete primary cytologist review."
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

def add_workflow_metadata(cases):
    """
    Add workflow path, next stage, and next required action to case data.
    """

    workflow_cases = cases.copy()

    required_columns = {
        "specimen_category",
        "workflow_type",
        "current_stage",
        "screening_result",
        "selected_for_quality_control",
        "discrepancy_review_status",
        "qc_flag",
    }

    missing_columns = required_columns - set(workflow_cases.columns)

    if missing_columns:
        raise ValueError(
            "Missing workflow columns: "
            + ", ".join(sorted(missing_columns))
        )

    workflow_paths = []
    next_stages = []
    next_actions = []

    for _, case in workflow_cases.iterrows():
        screening_result = case.get("screening_result")

        if pd.isna(screening_result) or str(screening_result).strip() == "":
            screening_result = None

        discrepancy_review = case.get(
            "discrepancy_review_status"
        )

        if (
            pd.isna(discrepancy_review)
            or str(discrepancy_review).strip() == ""
            or discrepancy_review == "no_discrepancy"
        ):
            discrepancy_review = None

        selected_for_quality_control = case.get(
            "selected_for_quality_control",
            False,
        )

        if pd.isna(selected_for_quality_control):
            selected_for_quality_control = False

        workflow_path = build_case_workflow(
            specimen_category=case["specimen_category"],
            workflow_type=case["workflow_type"],
            screening_result=screening_result,
            selected_for_quality_control=bool(
                selected_for_quality_control
            ),
            discrepancy_review=discrepancy_review,
        )

        if case.get("qc_flag") != "imager_qc_review":
            workflow_path = [
                stage
                for stage in workflow_path
                if stage != "imager_review"
            ]

        current_stage = case.get("current_stage")

        if pd.isna(current_stage) or str(current_stage).strip() == "":
            current_stage = None

        next_stage = get_next_workflow_stage(
            workflow_stages=workflow_path,
            current_stage=current_stage,
        )

        workflow_paths.append(workflow_path)
        next_stages.append(next_stage)
        next_actions.append(
            describe_next_required_action(next_stage)
        )

    workflow_cases["workflow_path"] = workflow_paths
    workflow_cases["next_stage"] = next_stages
    workflow_cases["next_required_action"] = next_actions

    return workflow_cases

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