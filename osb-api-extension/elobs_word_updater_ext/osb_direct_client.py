from contextlib import contextmanager
from typing import Any


@contextmanager
def _system_user_context():
    """Set a dummy system user in the starlette request context if auth is not set.

    OSB service classes call user() in __init__ to record the author. When auth is
    disabled, context["auth"] is absent and user() returns None, causing an
    AttributeError. This sets a minimal system user for the duration of the call.
    """
    from starlette_context import context
    from common.auth.models import User

    if context.get("auth") is not None:
        yield
        return

    class _SystemAuth:
        user = User(sub="system", azp="system", oid="system",
                    name="System", username="system", email="")

    context["auth"] = _SystemAuth()
    try:
        yield
    finally:
        try:
            del context["auth"]
        except Exception:
            pass


class OsbDirectClient:
    """Calls OSB service classes directly instead of making HTTP requests.

    Drop-in replacement for StudyApiClient — implements the same async interface
    so it can be passed to update_document() without any changes to core/.
    The substitution is structural (duck typing): there is no shared ABC or Protocol.
    update_document() in core/ accepts any object that satisfies the StudyApiClient
    interface; this class satisfies it.

    All clinical_mdr_api imports are deferred to method bodies so this module
    can be imported in environments where clinical_mdr_api is not installed
    (e.g. the isolated unit tests in this repo).
    """

    async def get_studies(self, page_size: int = 0) -> list[dict[str, Any]]:
        from clinical_mdr_api.services.studies.study import StudyService
        with _system_user_context():
            result = StudyService().get_all(page_size=page_size)
        return [item.model_dump() for item in result.items]

    async def get_study(self, uid: str, version: str | None = None) -> dict[str, Any]:
        from clinical_mdr_api.services.studies.study import StudyService
        with _system_user_context():
            return StudyService().get_by_uid(uid=uid, study_value_version=version).model_dump()

    async def get_protocol_title(self, uid: str, version: str | None = None) -> dict[str, Any]:
        from clinical_mdr_api.services.studies.study import StudyService
        with _system_user_context():
            return StudyService().get_protocol_title(uid=uid, study_value_version=version).model_dump()

    async def get_study_criteria(self, uid: str, version: str | None = None) -> list[dict[str, Any]]:
        from clinical_mdr_api.services.studies.study_criteria_selection import StudyCriteriaSelectionService
        with _system_user_context():
            result = StudyCriteriaSelectionService().get_all_selection(
                study_uid=uid,
                no_brackets=False,
                page_size=0,
                study_value_version=version,
            )
        return [item.model_dump() for item in result.items]

    async def get_objectives_docx(self, uid: str, version: str | None = None) -> bytes:
        from clinical_mdr_api.services.studies.study_objectives import StudyObjectivesService
        with _system_user_context():
            return (
                StudyObjectivesService()
                .get_standard_docx(study_uid=uid, study_value_version=version)
                .get_document_stream()
                .read()
            )

    async def get_flowchart_docx(self, uid: str, version: str | None = None) -> bytes:
        from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
        from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import SoALayout
        with _system_user_context():
            return (
                StudyFlowchartService()
                .get_study_flowchart_docx(
                    study_uid=uid,
                    study_value_version=version,
                    layout=SoALayout.PROTOCOL,
                    time_unit=None,
                )
                .get_document_stream()
                .read()
            )

    async def get_design_svg(self, uid: str, version: str | None = None) -> bytes:
        from clinical_mdr_api.services.studies.study_design_figure import StudyDesignFigureService
        with _system_user_context():
            return (
                StudyDesignFigureService()
                .get_svg_document(study_uid=uid, study_value_version=version)
                .encode()
            )

    async def get_snapshot_history(self, uid: str) -> list[dict[str, Any]]:
        # Not called by update_document(); returning [] satisfies the interface
        # without hitting the database.
        return []
