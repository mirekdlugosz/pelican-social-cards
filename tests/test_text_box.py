import pytest

from pelican.plugins.social_cards.cards_generator import TextBox


@pytest.mark.parametrize(
    "property_name,expected",
    [("width", 204), ("height", 114), ("lines", 4), ("line_height", 31)],
    ids=["width", "height", "lines", "line_height"],
)
def test_text_box_dimensions(
    default_settings, cards_generator, property_name, expected
):
    """Check calculated text_box dimensions"""
    text = ["This is fake text", "with", "variable-length", "lines"]
    tb = TextBox(text, cards_generator._font)

    assert getattr(tb, property_name) == expected
