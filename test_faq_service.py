from faq_service import FAQ, suggest_for_checkout


class FakeClient:
    def suggest(self, question):
        return [FAQ("Where is my order?", "Open Orders to see the latest carrier scan.", "order")]


def test_checkout_question_returns_order_update():
    result = suggest_for_checkout("tracking update", FakeClient())
    assert result[0].topic == "order"
    assert "carrier" in result[0].answer
