from build.principal import Principal, Permission, ALL_PERMISSIONS


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

class Test_Principal_Permissions:

    def test_add_specific_permissions(self):
        p = Principal("test", "password")
        p.add_permissions("record1", [Permission.READ])
        assert p.has_permission("record1", Permission.READ)

        p.add_permissions("record1", [Permission.WRITE])
        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)

        p.add_permissions("record1", [Permission.APPEND])
        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)

    def test_add_multiple_permissions(self):
        p = Principal("test", "password")
        p.add_permissions("record1", [Permission.READ, Permission.WRITE, Permission.APPEND])
        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)

    def test_add_all_permissions(self):
        p = Principal("test", "password")
        p.add_permissions("record1", ALL_PERMISSIONS)
        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)
        assert p.has_permission("record1", Permission.DELEGATE)

    def test_multiple_records_permissions(self):
        p = Principal("test", "password")
        p.add_permissions("record1", [Permission.READ])
        p.add_permissions("record2", [Permission.WRITE])

        assert p.has_permission("record2", Permission.WRITE)
        assert p.has_permission ("record1", Permission.READ)

    def test_delete_permissions(self):
        p = Principal("test", "principal")
        p.add_permissions("record1", ALL_PERMISSIONS)
        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)
        assert p.has_permission("record1", Permission.DELEGATE)

        p.delete_permission("record1", Permission.DELEGATE)

        assert p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)
        assert not p.has_permission("record1", Permission.DELEGATE)

        p.delete_permission("record1", Permission.READ)

        assert not p.has_permission("record1", Permission.READ)
        assert p.has_permission("record1", Permission.WRITE)
        assert p.has_permission("record1", Permission.APPEND)
        assert not p.has_permission("record1", Permission.DELEGATE)
