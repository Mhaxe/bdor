import pytest

from scripts.stats_pipeline.config import parse_paused


@pytest.mark.parametrize("raw", ["1", "true", "TRUE", "True", "yes", "on", " true ", "\tON\n"])
def test_parse_paused_recognizes_truthy_values(raw):
    paused, warning = parse_paused(raw)

    assert paused is True
    assert warning is None


@pytest.mark.parametrize("raw", ["0", "false", "FALSE", "no", "off", "", "   ", None])
def test_parse_paused_recognizes_falsy_values(raw):
    paused, warning = parse_paused(raw)

    assert paused is False
    assert warning is None


@pytest.mark.parametrize("raw", ["treu", "3O", "maybe", "true-ish", "2"])
def test_parse_paused_fails_open_on_unrecognized_values(raw):
    """A typo must not silently freeze the pipeline - it stays unpaused and
    says so, rather than looking exactly like a working pause.
    """
    paused, warning = parse_paused(raw)

    assert paused is False
    assert warning is not None
    assert repr(raw) in warning
    assert "NOT paused" in warning
