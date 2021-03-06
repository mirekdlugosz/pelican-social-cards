from pelican.plugins.social_cards.settings import PLUGIN_SETTINGS
from pelican.plugins.social_cards.social_cards import should_skip_object


def test_og_image_is_left_alone(article, default_settings):
    """If article has og_image set, we leave it as-is"""
    article.set_custom_data({"og_image": "my value"})
    assert should_skip_object(article)


def test_custom_og_image_text(article, default_settings, cards_generator):
    """Article can set og_image_text that will be used instead of title"""
    expected = "Title set by metadata"
    article.set_custom_data({"og_image_text": expected})

    wrapped_text = cards_generator._get_article_title(article)

    assert wrapped_text == [expected]
    assert wrapped_text != [article.title]


def test_custom_attribute_name(article, default_settings, cards_generator):
    """User can set their own attribute name that will be used instead of og_image"""
    PLUGIN_SETTINGS.update(KEY_NAME="header_cover")
    expected = "Title set by metadata"
    trap = "This title is a trap"
    article.set_custom_data({"header_cover_text": expected, "og_image_text": trap})

    wrapped_text = cards_generator._get_article_title(article)

    assert wrapped_text == [expected]
    assert wrapped_text != [trap]
    assert wrapped_text != [article.title]


def test_custom_wrapping_function(article, default_settings, cards_generator):
    """User can provide their own wrapping function to use"""

    def custom_wrapper(text, width):
        return text.split()

    PLUGIN_SETTINGS.update(WRAPPING_FUNCTION=custom_wrapper)

    wrapped_text = cards_generator._get_article_title(article)

    assert wrapped_text == ["Fake", "Title"]
    assert wrapped_text != [article.title]
