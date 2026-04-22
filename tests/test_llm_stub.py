from pipeline.llm import StubClient, Msg

def test_stub_returns_fixture():
    c = StubClient()
    r = c.complete(system="x", messages=[Msg("user", "hello")], fixture_key="gen_a_default")
    assert "Razorpay" in r.content
    assert r.input_tokens > 0
    assert r.model == "stub"

def test_stub_missing_key_raises():
    c = StubClient()
    try:
        c.complete(system="x", messages=[], fixture_key="does_not_exist")
    except KeyError as e:
        assert "does_not_exist" in str(e)
    else:
        assert False, "expected KeyError"
