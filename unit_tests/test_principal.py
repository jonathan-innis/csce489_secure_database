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


class Test_Principal_Change_Password:

    def test_change_password(self):
        p = Principal("test", "password")
        assert p.authenticate("password")
        p.change_password("another_password")
        assert p.authenticate("another_password")

    def test_invalid_password_after_change(self):
        p = Principal("test", "password")
        assert p.authenticate("password")
        p.change_password("another_password")
        assert not p.authenticate("password")

    def test_change_to_weird_password(self):
        p = Principal("test", "password")
        assert p.authenticate("password")
        p.change_password("89279uqhafdsh8gay2378etr8gi^2'4@&")
        assert p.authenticate("89279uqhafdsh8gay2378etr8gi^2'4@&")
