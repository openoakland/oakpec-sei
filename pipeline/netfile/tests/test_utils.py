from ..utils import clean_string


def test_clean_string():
    assert clean_string('a ') == 'a'
    assert clean_string('') == ''
    assert clean_string(None) is None
    assert clean_string('a\nb') == 'a b'
    assert clean_string('a\n\nb') == 'a b'
