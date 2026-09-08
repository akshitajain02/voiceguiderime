"""Formats numbers/codes so Rime speaks them digit-by-digit instead of as a big number.

Use this on any OTP, PNR, PIN, phone number, or ID before sending text to Rime.
"""

import re


def format_for_speech(text: str) -> str:
    """Find number sequences (4+ digits) in text and space them out digit-by-digit.

    Example:
        "Your PNR is 4567892" -> "Your PNR is 4 5 6 7 8 9 2"
        "OTP: 123456"         -> "OTP: 1 2 3 4 5 6"

    Short numbers (1-3 digits, like "5 stars" or "Room 12") are left alone,
    since those usually should be read as a normal number, not spelled out.
    """

    def spell_out(match: re.Match) -> str:
        digits = match.group(0)
        return " ".join(digits)

    # 4+ consecutive digits = treat as a code/ID, not a quantity.
    return re.sub(r"\d{4,}", spell_out, text)


if __name__ == "__main__":
    # Quick manual test - run: python number_formatter.py
    tests = [
        "Your PNR number is 4567892.",
        "OTP: 123456",
        "You have 5 new messages.",
        "Room number 12, floor 3.",
    ]
    for t in tests:
        print(f"{t!r:45} -> {format_for_speech(t)!r}")