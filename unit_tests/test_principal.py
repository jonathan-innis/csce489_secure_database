from build.principal import Principal


def test_valid_password():
    p = Principal("test", "password")
    assert p.authenticate("password")


def test_invalid_password():
    p = Principal("test", "password")
    assert not p.authenticate("pas$word")


def test_prefix_password():
    p = Principal("test", "password")
    assert not p.authenticate("password123")


def test_postfix_password():
    p = Principal("test", "password")
    assert not p.authenticate("thisismypassword")
