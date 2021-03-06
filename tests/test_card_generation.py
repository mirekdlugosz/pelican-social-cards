from PIL import Image
import pytest

from pelican.plugins.social_cards.settings import PLUGIN_SETTINGS


def assert_image_equal_tofile(a, filename):
    with Image.open(filename) as b:
        assert a.mode == b.mode, f"got mode {repr(a.mode)}, expected {repr(b.mode)}"
        assert a.size == b.size, f"got size {repr(a.size)}, expected {repr(b.size)}"
        assert a.tobytes() == b.tobytes()


@pytest.mark.parametrize("horizontal", ("left", "center", "right"))
@pytest.mark.parametrize("vertical", ("top", "center", "bottom"))
def test_text_positioning(default_settings, cards_generator, horizontal, vertical):
    """Check if text is properly positioned on canvas"""
    text = ["Text alignment test:", f"{horizontal} {vertical}"]
    PLUGIN_SETTINGS["HORIZONTAL_ALIGNMENT"] = horizontal
    PLUGIN_SETTINGS["VERTICAL_ALIGNMENT"] = vertical
    reference_file = f"tests/img/text_pos_{horizontal}_{vertical}.png"

    img = cards_generator._generate_card_image(text)

    assert_image_equal_tofile(img, reference_file)


def test_canvas_positioning(default_settings, cards_generator):
    """Check if canvas is properly positioned on image"""
    text = ["Canvas alignment test:", "100 100 top left"]
    PLUGIN_SETTINGS["CANVAS_TOP"] = 175
    PLUGIN_SETTINGS["CANVAS_LEFT"] = 30
    reference_file = "tests/img/canvas_position.png"

    img = cards_generator._generate_card_image(text)

    assert_image_equal_tofile(img, reference_file)
