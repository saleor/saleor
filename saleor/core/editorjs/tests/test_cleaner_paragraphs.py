import pytest
from django.utils.html import strip_tags

from .. import clean_editorjs, editorjs_to_text


@pytest.mark.parametrize(
    ("input_html", "expected_output_html"),
    [
        (
            (
                "The Saleor Winter Sale is snowed under with seasonal offers. Unreal products "
                "at unreal prices. Literally, they are not real products, but the Saleor demo "
                "store is a genuine e-commerce leader."
                'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/"></a>'
                'The Saleor Sale is snowed <a href="https://docs.saleor.io/">Test</a>.'
                ""
                "The Saleor Winter Sale is snowed <a >"
            ),
            (
                "The Saleor Winter Sale is snowed under with seasonal offers. Unreal products "
                "at unreal prices. Literally, they are not real products, but the Saleor demo "
                "store is a genuine e-commerce leader."
                'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/"></a>'
                'The Saleor Sale is snowed <a href="https://docs.saleor.io/">Test</a>.'
                ""
                "The Saleor Winter Sale is snowed <a></a>"
            ),
        )
    ],
)
def test_clean_editor_js(input_html: str, expected_output_html: str, no_link_rel):
    # given
    input_data = {"blocks": [{"data": {"text": input_html}, "type": "paragraph"}]}
    expected_output = {
        "blocks": [{"data": {"text": expected_output_html}, "type": "paragraph"}]
    }

    # when
    result = clean_editorjs(input_data, for_django=False)

    # then
    assert result == expected_output

    # when
    result = editorjs_to_text(input_data)

    # then
    assert result == strip_tags(expected_output_html)


def test_clean_editor_js_for_malicious_value():
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "<img src=x onerror=alert(1)><script>alert(2);</script>Check"
                },
                "type": "paragraph",
            }
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    # Malicious elements should be stripped.
    # nh3 allows img but strips onerror. script is removed.
    text = result["blocks"][0]["data"]["text"]
    assert "onerror" not in text
    assert "<script>" not in text
    assert "alert" not in text
    assert "Check" in text
