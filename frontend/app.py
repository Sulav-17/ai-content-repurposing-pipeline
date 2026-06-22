import streamlit as st

from frontend.api_client import (
    ApiClient,
    ApiRequestError,
    ApiResponseError,
    ApiUnavailableError,
)
from frontend.config import FrontendConfigurationError, get_frontend_settings
from frontend.renderers import (
    calculate_offset,
    has_next_page,
    render_generation_result,
)


PAGE_SIZE = 10


def main() -> None:
    st.set_page_config(
        page_title="AI Content Repurposing Pipeline",
        layout="wide",
    )
    _initialize_state()

    st.title("AI Content Repurposing Pipeline")
    client = _build_client()
    _render_health(client)
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    generate_tab, history_tab = st.tabs(["Generate", "Saved History"])
    with generate_tab:
        _render_generate_tab(client)
    with history_tab:
        _render_history_tab(client)


def _initialize_state() -> None:
    defaults = {
        "latest_result": None,
        "selected_record": None,
        "history_offset": 0,
        "pending_delete_id": None,
        "pending_delete_label": None,
        "success_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _build_client() -> ApiClient | None:
    try:
        settings = get_frontend_settings()
    except FrontendConfigurationError as exc:
        st.error(str(exc))
        return None
    return ApiClient(settings)


def _render_health(client: ApiClient | None) -> None:
    if client is None:
        return
    try:
        health = client.health_check()
    except (ApiUnavailableError, ApiRequestError, ApiResponseError):
        st.warning("Backend unavailable. You can still edit inputs, but requests may fail.")
        return
    st.success(f"Backend healthy: {health.get('service', 'API')}")


def _render_generate_tab(client: ApiClient | None) -> None:
    project_name = st.text_input("Project name", key="project_name_input")
    transcript_text = st.text_area("Transcript text", height=240, key="transcript_input")
    provider = st.selectbox(
        "Provider",
        ["deterministic", "ollama"],
        key="provider_select",
    )

    col_preview, col_save = st.columns(2)
    with col_preview:
        preview_clicked = st.button("Generate Preview", key="generate_preview")
    with col_save:
        save_clicked = st.button("Generate and Save", key="generate_save")

    if preview_clicked:
        _handle_generation_action(
            client=client,
            project_name=project_name,
            transcript_text=transcript_text,
            provider=provider,
            save=False,
        )
    if save_clicked:
        _handle_generation_action(
            client=client,
            project_name=project_name,
            transcript_text=transcript_text,
            provider=provider,
            save=True,
        )

    if st.session_state.latest_result:
        render_generation_result(st.session_state.latest_result)


def _handle_generation_action(
    client: ApiClient | None,
    project_name: str,
    transcript_text: str,
    provider: str,
    save: bool,
) -> None:
    if client is None:
        st.error("API client is not configured.")
        return
    if not project_name.strip():
        st.error("Project name is required.")
        return
    if not transcript_text.strip():
        st.error("Transcript text is required.")
        return

    request = {
        "project_name": project_name.strip(),
        "text": transcript_text,
        "provider": provider,
    }
    try:
        with st.spinner("Generating content..."):
            if save:
                result = client.generate_and_save(request)
                st.session_state.success_message = f"Saved generation {result['id']}."
            else:
                result = client.generate_preview(request)
                st.session_state.success_message = "Generated preview."
            st.session_state.latest_result = result
    except (ApiUnavailableError, ApiRequestError, ApiResponseError) as exc:
        st.error(str(exc))


def _render_history_tab(client: ApiClient | None) -> None:
    if client is None:
        st.info("Configure the API client before loading saved history.")
        return

    if st.button("Refresh History", key="refresh_history"):
        st.session_state.selected_record = None
        st.rerun()

    try:
        history = client.list_generations(
            limit=PAGE_SIZE,
            offset=st.session_state.history_offset,
        )
    except (ApiUnavailableError, ApiRequestError, ApiResponseError) as exc:
        st.warning(str(exc))
        return

    st.write(f"Total saved records: {history['total']}")
    _render_pagination(history)
    _render_history_items(client, history)

    if st.session_state.selected_record:
        st.divider()
        render_generation_result(st.session_state.selected_record)


def _render_pagination(history: dict) -> None:
    previous_col, next_col = st.columns(2)
    offset = history["offset"]
    total = history["total"]

    with previous_col:
        if st.button("Previous", disabled=offset <= 0, key="previous_page"):
            st.session_state.history_offset = calculate_offset(
                offset,
                -1,
                PAGE_SIZE,
                total,
            )
            st.rerun()
    with next_col:
        if st.button(
            "Next",
            disabled=not has_next_page(offset, PAGE_SIZE, total),
            key="next_page",
        ):
            st.session_state.history_offset = calculate_offset(
                offset,
                1,
                PAGE_SIZE,
                total,
            )
            st.rerun()


def _render_history_items(client: ApiClient, history: dict) -> None:
    if not history["items"]:
        st.info("No saved generations yet.")
        return

    for item in history["items"]:
        item_id = item["id"]
        with st.container():
            st.markdown(f"### {item['project_name']}")
            st.caption(f"{item['provider']} - {item['created_at']}")
            st.write(item["project_summary"])
            open_col, download_col, delete_col = st.columns(3)
            with open_col:
                if st.button("Open", key=f"open_{item_id}"):
                    _open_record(client, item_id)
            with download_col:
                if st.button("Download Markdown", key=f"download_history_{item_id}"):
                    _open_record(client, item_id)
            with delete_col:
                if st.button("Delete", key=f"delete_{item_id}"):
                    st.session_state.pending_delete_id = item_id
                    st.session_state.pending_delete_label = item["project_name"]
                    st.rerun()

    _render_delete_confirmation(client, history)


def _open_record(client: ApiClient, item_id: str) -> None:
    try:
        st.session_state.selected_record = client.get_generation(item_id)
    except (ApiUnavailableError, ApiRequestError, ApiResponseError) as exc:
        st.error(str(exc))


def _render_delete_confirmation(client: ApiClient, history: dict) -> None:
    pending_id = st.session_state.pending_delete_id
    if not pending_id:
        return

    st.warning(
        f"Permanently delete {st.session_state.pending_delete_label or pending_id}?"
    )
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Confirm delete", key=f"confirm_delete_{pending_id}"):
            _confirm_delete(client, history)
    with cancel_col:
        if st.button("Cancel delete", key=f"cancel_delete_{pending_id}"):
            st.session_state.pending_delete_id = None
            st.session_state.pending_delete_label = None
            st.rerun()


def _confirm_delete(client: ApiClient, history: dict) -> None:
    pending_id = st.session_state.pending_delete_id
    try:
        client.delete_generation(pending_id)
    except (ApiUnavailableError, ApiRequestError, ApiResponseError) as exc:
        st.error(str(exc))
        return

    if (
        st.session_state.selected_record
        and st.session_state.selected_record.get("id") == pending_id
    ):
        st.session_state.selected_record = None
    st.session_state.pending_delete_id = None
    st.session_state.pending_delete_label = None
    new_total = max(history["total"] - 1, 0)
    if st.session_state.history_offset > 0 and st.session_state.history_offset >= new_total:
        st.session_state.history_offset = max(
            st.session_state.history_offset - PAGE_SIZE,
            0,
        )
    st.session_state.success_message = "Deleted saved generation."
    st.rerun()


if __name__ == "__main__":
    main()
