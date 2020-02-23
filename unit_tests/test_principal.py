from build.principal import Principal

def test_valid_password():
    p = Principal("test", "password")
    assert True == p.authenticate("password")

def test_invalid_password():
    p = Principal("test", "password")
    assert False == p.authenticate("pas$word")

def test_prefix_password():
    p = Principal("test", "password")
    assert False == p.authenticate("password123")

def test_postfix_password():
    p = Principal("test", "password")
    assert False == p.authenticate("thisismypassword")


if __name__ == "__main__":
    unittest.main()