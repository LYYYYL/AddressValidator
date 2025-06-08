"""
UI route registration for the Singapore Address Validator web app.

This module exposes a single `build_home_page()` function which mounts the
NiceGUI UI at the root URL ("/") and instantiates a `HomePage` object
to handle layout and user interaction.
"""

from nicegui import ui

from address_validator.constants import (
    BLOCK_NUMBER,
    COUNTRY_CODE_SINGAPORE,
    POSTAL_CODE,
    PROPERTY_TYPE,
    RAW_ADDRESS,
    STREET_NAME,
    UNIT_NUMBER,
    VALIDATE_STATUS,
)
from address_validator.validation import AddressValidationFlow
from app.ui.row_mapper import map_ctx_to_row


def build_home_page():
    """
    Register the root URL ("/") with the `HomePage` UI class.

    When a user visits the homepage, a new `HomePage()` instance is created
    to build the interactive UI for that session.
    """

    @ui.page("/")
    def home_page():
        HomePage()


class HomePage:
    """
    UI component for the Singapore Address Validator homepage.

    Handles input of one or more addresses, validation via backend pipeline,
    and rendering results in a table. Wrapped in a NiceGUI `@ui.page` function
    to ensure separate state per user session.
    """

    def __init__(self):
        """Initialize the HomePage and build the UI layout."""
        self.textarea = None
        self.results_container = None
        self._build_ui()

    def _build_ui(self):
        """
        Construct the full UI layout: header, address input section,
        and an initially empty container for results.
        """
        ui.page_title("Singapore Address Validator")

        with ui.column().classes("items-center q-pa-lg").style("max-width: 900px; margin: auto;"):
            self._render_intro()
            self._render_input_area()
            self._render_results_container()

    def _render_intro(self):
        """
        Render the top section of the page including title, description,
        and a list of address validation checks performed.
        """
        ui.label("Singapore Address Validator").classes("text-h3 text-primary q-mb-sm")
        ui.label("Validate your customers’ shipping addresses before sending out the packages!").classes(
            "text-subtitle1 text-grey-8 q-mb-md"
        )
        with ui.card().classes("q-pa-md bg-grey-1 q-mb-md").style("width: 100%"):
            ui.label("✅ Checks for:").classes("text-body1 text-bold q-mb-sm")
            ui.html(
                """
                <ul style="margin-left: 1.2em; padding-left: 0.5em;">
                    <li>Missing unit number based on property type</li>
                    <li>Invalid or missing postal code</li>
                    <li>Match block number & street name against postal code</li>
                    <li>Uses OneMap API and streetdirectory.com under the hood</li>
                </ul>
                """
            )

    def _render_input_area(self):
        """
        Render the input form: a textarea for multiline address input
        and a 'Validate All' button that triggers backend validation.
        """
        with ui.card().classes("q-pa-md q-mb-md").style("width: 100%"):
            ui.label("Paste address(es) below:").classes("text-h6 q-mb-xs")
            ui.label("💡 One address per line. Example format shown below:").classes("text-caption text-grey q-mb-sm")

            ui.html(
                (
                    '<div style="background-color: #f5f5f5; border: 1px dashed #ccc; '
                    'padding: 8px; font-family: monospace; white-space: pre-line;">'
                    "Address 1: 3A Ridley Park, Singapore 248472<br>"
                    "Address 2: 288E Jurong East Street 21, #12-34, 605288"
                    "</div>"
                )
            )

            self.textarea = (
                ui.textarea(
                    placeholder="Paste one address per line here...",
                    value="3A Ridley Park, Singapore 248472\n288E Jurong East Street 21, #12-34, 605288",
                )
                .props("autogrow rows=6")
                .style("width: 100%")
            )

            ui.button("Validate All", on_click=self.on_validate_click).classes("q-mt-md")

    def _render_results_container(self):
        """
        Create an empty container where the results table will be injected
        after address validation.
        """
        self.results_container = ui.element("div").classes("q-mt-md").style("width: 100%")

    async def on_validate_click(self):
        """
        Validate all addresses entered in the textarea. Sends each address
        to the `AddressValidationFlow`, maps the results into rows, and
        renders a results table. Shows a warning if no input is provided.
        """
        self.results_container.clear()

        raw_text = self.textarea.value or ""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            ui.notify("⚠️ Please enter at least one address.", color="warning")
            return

        table_rows = []
        for addr in lines:
            ctx = AddressValidationFlow.validate(address=addr, country=COUNTRY_CODE_SINGAPORE, ctx={})
            row = map_ctx_to_row(ctx, raw_address=addr)
            table_rows.append(row)

        if table_rows:
            with self.results_container:
                with ui.card().classes("q-pa-md"):
                    ui.table(
                        columns=[
                            {"name": RAW_ADDRESS, "label": "Address", "field": RAW_ADDRESS},
                            {"name": VALIDATE_STATUS, "label": "Validation", "field": VALIDATE_STATUS},
                            {"name": BLOCK_NUMBER, "label": "Block Number", "field": BLOCK_NUMBER},
                            {"name": STREET_NAME, "label": "Street", "field": STREET_NAME},
                            {"name": UNIT_NUMBER, "label": "Unit Number", "field": UNIT_NUMBER},
                            {"name": POSTAL_CODE, "label": "Postal Code", "field": POSTAL_CODE},
                            {"name": PROPERTY_TYPE, "label": "Property Type", "field": PROPERTY_TYPE},
                        ],
                        rows=table_rows,
                    ).props("wrap-cells").style("overflow-x: auto;")
