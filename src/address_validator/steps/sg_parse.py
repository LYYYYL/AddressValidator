import re

from address_validator.constants import DEBUG_PRINT
from address_validator.steps.base import ValidationStep


class SingaporeAddressParseStep(ValidationStep):
    STREET_SUFFIXES = [
        "Street",
        "Road",
        "Avenue",
        "Drive",
        "Lane",
        "Crescent",
        "Boulevard",
        "Walk",
        "Place",
        "Way",
        "Loop",
        "Terrace",
        "View",
        "Close",
        "Rise",
        "Field",
        # Abbreviations
        "St",
        "Rd",
        "Ave",
        "Dr",
        "Ln",
        "Cres",
        "Blvd",
    ]

    # ————————————————————————————————————————————————
    # Public API
    # ————————————————————————————————————————————————
    def __call__(self, ctx: dict) -> dict:
        raw = ctx.get("raw_address", "")
        # 1) Extract unit and strip it off
        unit, rem1 = self.extract_unit(raw)
        rem1 = self.normalize(rem1)
        # 2) Extract postcode and strip it off
        pc, rem2 = self.extract_postcode(rem1)
        rem2 = self.normalize(rem2)
        # 3) Now split out house & road
        house, road = self.extract_house_and_road(rem2)
        # 4) Finally, figure out the building
        building = self.extract_building(rem2, house, road)
        # Post-process: if “building” is actually just a unit or a postcode, drop it:
        u, _ = self.extract_unit(building)
        if u:
            building = ""
        else:
            p, _ = self.extract_postcode(building)
            if p:
                building = ""

        if DEBUG_PRINT:
            print(f"🧾 Raw address: {raw}")
            print(f"📦 Extracted unit: {unit}")
            print(f"➡️ Remaining after unit: {rem1}")
            print(f"📦 Extracted postcode: {pc}")
            print(f"➡️ Remaining after postcode: {rem2}")
            print(f"📦 Extracted house number: {house}")
            print(f"➡️ Final road: {road}")
            print(f"🏢 Extracted building: {building}")

        ctx["parsed"] = {
            "house_number": house or None,
            "road": road or None,
            "unit": unit or None,
            "postcode": pc or None,
            "building": building or None,
        }
        return ctx

    # ————————————————————————————————————————————————
    # Normalization and Utility Methods
    # ————————————————————————————————————————————————
    @staticmethod
    def normalize(text: str) -> str:
        text = text.replace(".", " ")
        text = re.sub(r"\s*[,;]+\s*", ", ", text)
        text = re.sub(r",{2,}", ",", text)
        text = re.sub(r"\s+,", ",", text)
        text = re.sub(r",\s+", ", ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" ,.")

    def looks_like_street(self, text: str) -> bool:
        return any(
            re.search(rf"\b{suffix}\b", text, re.IGNORECASE) for suffix in SingaporeAddressParseStep.STREET_SUFFIXES
        )

    def extract_unit(self, text: str) -> tuple[str, str]:
        txt = text
        unit = ""

        # 1) Dash‐separated with optional letter suffix (e.g., '16-52', '03-1D')
        m = re.search(r"#?\s*(\d{1,3})\s*-\s*(\d{1,4}[A-Za-z]?)", txt)
        if m:
            unit = f"{m.group(1)}-{m.group(2)}"
        else:
            # 2) Space‐separated fallback (e.g., '03 16')
            m2 = re.search(r"#?\s*(\d{1,3})\s+(\d{1,4}[A-Za-z]?)\b", txt)
            if m2:
                unit = f"{m2.group(1)}-{m2.group(2)}"
            else:
                # 3) Slash format fallback (e.g., '3/14D')
                m3 = re.search(r"(\d{1,3}/\d{1,4}[A-Za-z]?)", txt)
                if m3:
                    unit = m3.group(1)

        if unit:
            remainder = re.sub(rf"#?\s*{re.escape(unit)}", "", txt, flags=re.IGNORECASE)
            return unit, remainder

        # 4) No unit found
        return "", text

    def extract_postcode(self, text: str) -> tuple[str, str]:
        patterns = [r"Singapore\s+(\d{6})", r"S(\d{6})", r"\b(\d{6})\b"]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                pc = m.group(1)
                remainder = re.sub(pat, "", text, count=1, flags=re.IGNORECASE)
                return pc, remainder
        return "", text

    # ————————————————————————————————————————————————
    # High‐level “split house & road” orchestration
    # ————————————————————————————————————————————————
    def extract_house_and_road(self, text: str) -> tuple[str, str]:
        """
        Try each pattern in order (0 → 8). Return the first non‐None match:
           0) Two parts exactly, second purely digits(+letter).
           1) “Blk/Block <num> <road>” in one segment
           2) Comma‐separated “Blk/Block <num>” anywhere
           3) Inline “<road> Blk <num>”
           4) Building-first pattern (“[Building, BlockNumber, Road]”)
           5) Apt-prefix at start (“Apt <num> …”)
           6) Numeric prefix in first part (“<num> <text>”)
           7) Any segment that looks like a street (“… Street”, “… Road”, etc.)
           8) Fallback: any segment containing a digit
        If none match, return ("", "").
        """
        txt = self.normalize(text)
        parts = [p.strip() for p in txt.split(",") if p.strip()]

        # 0) Two‐part: second is only digits(+letter)
        result = self._match_two_part_numeric(parts)
        if result is not None:
            return result

        # 1) Pure “Blk X <road>” in one segment
        result = self._match_blk_prefix_single(parts)
        if result is not None:
            return result

        # 2) Comma‐separated “Blk X” anywhere
        result = self._match_blk_prefix_comma(parts)
        if result is not None:
            return result

        # 3) Inline “<road> Blk X”
        result = self._match_inline_blk(txt)
        if result is not None:
            return result

        # 4) Building-first pattern: [Building, BlockNumber, Road]
        result = self._match_building_first(parts)
        if result is not None:
            return result

        # 5) Apt-prefix at start
        result = self._match_apt_prefix(txt)
        if result is not None:
            return result

        # 6) Numeric prefix in the first comma‐segment
        result = self._match_numeric_prefix(parts)
        if result is not None:
            return result

        # 7) Any segment that “looks like a street”
        result = self._match_any_street_like(parts)
        if result is not None:
            return result

        # 8) Fallback: segment containing a digit
        result = self._match_any_digit(parts)
        if result is not None:
            return result

        # Nothing matched
        return "", ""

    # ————————————————————————————————————————————————
    # Pattern‐0: Two parts exactly, second purely digits(+letter)
    # ————————————————————————————————————————————————
    def _match_two_part_numeric(self, parts: list[str]) -> tuple[str, str] | None:
        if len(parts) == 2:
            if re.fullmatch(r"\d+[A-Za-z]?", parts[1], re.IGNORECASE):
                return parts[1], parts[0]
        return None

    # ————————————————————————————————————————————————
    # Pattern‐1: “Blk/Block <num> <road>” in a single comma‐segment
    # ————————————————————————————————————————————————
    def _match_blk_prefix_single(self, parts: list[str]) -> tuple[str, str] | None:
        for part in parts:
            m1 = re.match(r"^(?:Blk|Block)\s*(\d+[A-Za-z]?)[,\s]+(.+)$", part, re.IGNORECASE)
            if m1:
                return m1.group(1), m1.group(2)
        return None

    # ————————————————————————————————————————————————
    # Pattern‐2: Comma‐separated “Blk <num>” anywhere in the list
    # ————————————————————————————————————————————————
    def _match_blk_prefix_comma(self, parts: list[str]) -> tuple[str, str] | None:
        for i, part in enumerate(parts):
            m2 = re.match(r"\b(?:Blk|Block)\s*(\d+[A-Za-z]?)\b", part, re.IGNORECASE)
            if m2:
                house = m2.group(1)
                road = ", ".join(parts[:i] + parts[i + 1 :])
                return house, road
        return None

    # ————————————————————————————————————————————————
    # Pattern‐3: Inline “<road> Blk <num>” in the same segment
    # ————————————————————————————————————————————————
    def _match_inline_blk(self, txt: str) -> tuple[str, str] | None:
        inline = re.match(
            r"^(?P<road>.+?)\s+\b(?:Blk|Block)\s*(?P<num>\d+[A-Za-z]?)\b",
            txt,
            re.IGNORECASE,
        )
        if inline:
            return inline.group("num"), inline.group("road").strip()
        return None

    # ————————————————————————————————————————————————
    # Pattern‐4: Building‐first pattern: [ Building, BlockNumber, Road ]
    # ————————————————————————————————————————————————
    def _match_building_first(self, parts: list[str]) -> tuple[str, str] | None:
        if (
            len(parts) >= 3
            and not parts[0][0].isdigit()
            and parts[1][0].isdigit()
            and self.looks_like_street(parts[2])
        ):
            return parts[1], parts[2]
        return None

    # ————————————————————————————————————————————————
    # Pattern‐5: Apt‐prefix (“Apt <num> …”)
    # ————————————————————————————————————————————————
    def _match_apt_prefix(self, txt: str) -> tuple[str, str] | None:
        apt = re.match(
            r"\b(?:Apt|Apartment)\s*(\d+[A-Za-z]?)(?:\s+(.*))?",
            txt,
            re.IGNORECASE,
        )
        if apt:
            return apt.group(1), apt.group(2) or ""
        return None

    # ————————————————————————————————————————————————
    # Pattern‐6: Numeric prefix in the first comma‐segment
    # ————————————————————————————————————————————————
    def _match_numeric_prefix(self, parts: list[str]) -> tuple[str, str] | None:
        if parts:
            m6 = re.match(r"^(\d+[A-Za-z]?)(?:\s+(.*))?$", parts[0])
            if m6:
                return m6.group(1), m6.group(2) or (parts[1] if len(parts) > 1 else "")
        return None

    # ————————————————————————————————————————————————
    # Pattern‐7: Any “street-like” segment (suffix in STREET_SUFFIXES)
    # ————————————————————————————————————————————————
    def _match_any_street_like(self, parts: list[str]) -> tuple[str, str] | None:
        for part in parts:
            if self.looks_like_street(part):
                # If there’s a leading number + space + rest, grab that
                m7 = re.match(r"^(\d+[A-Za-z]?)(?:\s+(.*))?$", part)
                if m7 and m7.group(2):
                    return m7.group(1), m7.group(2)
                # Otherwise the entire “part” is the road, no house
                return "", part
        return None

    # ————————————————————————————————————————————————
    # Pattern‐8: Fallback—any segment containing a digit
    # ————————————————————————————————————————————————
    def _match_any_digit(self, parts: list[str]) -> tuple[str, str] | None:
        for part in parts:
            if re.search(r"\d", part):
                return "", part
        return None

    # ————————————————————————————————————————————————
    # Extract “building” from the leftover text
    # ————————————————————————————————————————————————
    def extract_building(self, remainder: str, house: str, road: str) -> str:
        rem = self.normalize(remainder)
        parts = [p.strip() for p in rem.split(",") if p.strip()]
        candidates = []
        for p in parts:
            if house and re.search(rf"\b{re.escape(house)}\b", p):
                continue
            if road and re.search(re.escape(road), p, flags=re.IGNORECASE):
                continue
            if self.looks_like_street(p):
                continue
            if re.fullmatch(r"Singapore", p, re.IGNORECASE):
                continue
            candidates.append(p)
        return candidates[0] if candidates else ""


# Single instance you can import elsewhere:
sg_parse_step = SingaporeAddressParseStep()
