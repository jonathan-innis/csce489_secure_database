from build.principal import Principal


class Test_Principal_Authentication:

    def test_valid_password(self):
        p = Principal("test", "password")
        assert p.authenticate("password")

    def test_invalid_password(self):
        p = Principal("test", "password")
        assert not p.authenticate("pas$word")

    def test_prefix_password(self):
        p = Principal("test", "password")
        assert not p.authenticate("password123")

    def test_postfix_password(self):
        p = Principal("test", "password")
        assert not p.authenticate("thisismypassword")
