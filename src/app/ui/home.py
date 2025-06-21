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
    ui.add_head_html("""
    <script>
    function emitSize() {
      emitEvent('resize', {
        width: document.body.offsetWidth,
        height: document.body.offsetHeight
      });
    }
    window.onload = emitSize;
    window.onresize = emitSize;
    </script>
    """)

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
        self.textarea = None
        self.results_container = None
        self._last_known_width = None  # ⮅ track screen width
        self.expanded_rows = set()  # ⮅ make expand state per session
        self._build_ui()

    def _handle_resize(self, e):
        self._last_known_width = e.args["width"]
        print(f"📱 Resized to {self._last_known_width}px wide")

    def _build_ui(self):
        """
        Construct the full UI layout: header, address input section,
        and an initially empty container for results.
        """
        ui.page_title("Singapore Address Validator")

        # ⮅ Add resize listener
        ui.on("resize", self._handle_resize)

        with (
            ui.column()
            .classes("items-center")
            .style("width: 100vw; overflow-x: hidden; min-height: 100vh; margin: 0; padding-top: 56px;")
        ):
            with ui.column().style("max-width: 1140px; width: 100%; margin: auto;"):
                self._render_navbar()
                self._render_intro()  # Removed redundant main title
                self._render_input_area()
                self._render_results_container()

    def _render_navbar(self):
        """Render a full-width top navigation bar."""
        with (
            ui.element("header")
            .classes("bg-primary text-white shadow-2")
            .style("position: fixed; top: 0; left: 0; z-index: 1000; width: 100vw;")
        ):
            with (
                ui.row()
                .classes("items-center justify-between q-px-md")
                .style("max-width: 1140px; margin: auto; flex-wrap: wrap; gap: 4px; height: auto; min-height: 56px;")
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("home").classes("text-white")
                    ui.label("Singapore Address Validator").classes("text-h5 text-white")

                with ui.row().classes("items-center gap-4"):
                    ui.link("GitHub", "https://github.com/LYYYYL/AddressValidator").classes("text-white text-body2")
                    ui.label("v1.0").classes("text-body2 text-grey-3")

    def _render_intro(self):
        """Render checklist with inline tick icons and clean vertical alignment."""
        with ui.card().classes("bg-grey-1 q-mt-none").style("width: 100%"):
            ui.label("Checks for:").classes("text-body1 text-bold")

            checklist_items = [
                "Missing unit number based on property type",
                "Invalid or missing postal code",
                "Match block number & street name against postal code",
                "Uses OneMap API and streetdirectory.com under the hood",
            ]

            for item in checklist_items:
                with ui.row().classes("items-start").style("gap: 8px; margin-bottom: 6px; align-items: flex-start;"):
                    ui.icon("check_circle").classes("text-green-6").style("font-size: 18px; margin-top: 2px;")
                    ui.label(item).classes("text-body2").style("line-height: 1.4;")

    def _render_input_area(self):
        with ui.card().classes("bg-white").style("width: 100%; padding: 16px;"):
            ui.label("Paste address(es) below:").classes("text-body1 text-bold q-mb-sm")

            with ui.row().classes("items-start q-mb-sm").style("gap: 8px;"):
                ui.icon("lightbulb").classes("text-yellow-7").style("font-size: 18px; margin-top: 2px;")
                ui.label("One address per line. Example format shown below:").classes("text-caption text-grey")

            ui.html(
                (
                    '<div style="background-color: #f5f5f5; border: 1px dashed #ccc; '
                    'padding: 8px; font-family: monospace; white-space: pre-line; margin-bottom: 12px;">'
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
                .props("autogrow rows=4")
                .style("width: 100%; margin-bottom: 12px;")
            )

            ui.button("VALIDATE ALL", on_click=self.on_validate_click).classes("q-mt-sm")

    def _render_results_container(self):
        """
        Create an empty container where the results table will be injected
        after address validation.
        """
        self.results_container = ui.element("div").style("width: 100%; min-height: 300px;")

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

        FULL_COLUMNS = [
            {"name": RAW_ADDRESS, "label": "Address", "field": RAW_ADDRESS},
            {"name": VALIDATE_STATUS, "label": "Validation", "field": VALIDATE_STATUS},
            {"name": BLOCK_NUMBER, "label": "Block Number", "field": BLOCK_NUMBER},
            {"name": STREET_NAME, "label": "Street", "field": STREET_NAME},
            {"name": UNIT_NUMBER, "label": "Unit Number", "field": UNIT_NUMBER},
            {"name": POSTAL_CODE, "label": "Postal Code", "field": POSTAL_CODE},
            {"name": PROPERTY_TYPE, "label": "Property Type", "field": PROPERTY_TYPE},
        ]

        MOBILE_COLUMNS = [
            {"name": RAW_ADDRESS, "label": "Address", "field": RAW_ADDRESS},
            {"name": VALIDATE_STATUS, "label": "Validation", "field": VALIDATE_STATUS},
            {"name": PROPERTY_TYPE, "label": "Property Type", "field": PROPERTY_TYPE},
        ]

        expanded_rows = self.expanded_rows

        viewport_width = self._last_known_width or 9999
        is_mobile = viewport_width < 600

        def toggle_row(row):
            key = row[RAW_ADDRESS]
            if key in expanded_rows:
                expanded_rows.remove(key)
            else:
                expanded_rows.add(key)
            ui.refresh()

        with self.results_container:
            with ui.card().style("overflow-x: auto; width: 100%;"):
                if is_mobile:
                    ui.table(
                        columns=MOBILE_COLUMNS,
                        rows=table_rows,
                    ).props("wrap-cells").style("width: 100%;")
                else:
                    ui.table(
                        columns=FULL_COLUMNS,
                        rows=table_rows,
                    ).props("wrap-cells").style("width: 100%;")
