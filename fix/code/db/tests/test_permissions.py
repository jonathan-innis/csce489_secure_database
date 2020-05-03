from db.permissions import Permissions, Right, ALL_RIGHTS


class Test_Add_Permissions:

    def test_add_permission(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ, Right.WRITE])
        p.add_permissions("x", "alice", "bob", [Right.READ, Right.APPEND])

        assert p.check_permission("x", "bob", Right.READ)
        assert not p.check_permission("x", "bob", Right.APPEND)

    def test_longer_add_permission(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", ALL_RIGHTS)
        p.add_permissions("x", "alice", "bob", ALL_RIGHTS)
        p.add_permissions("x", "bob", "charlie", ALL_RIGHTS)
        p.add_permissions("x", "charlie", "dave", ALL_RIGHTS)

        assert p.check_permission("x", "dave", Right.READ)
        assert p.check_permission("x", "dave", Right.WRITE)
        assert p.check_permission("x", "dave", Right.APPEND)
        assert p.check_permission("x", "dave", Right.DELEGATE)

        assert p.check_permission("x", "charlie", Right.READ)
        assert p.check_permission("x", "charlie", Right.WRITE)
        assert p.check_permission("x", "charlie", Right.APPEND)
        assert p.check_permission("x", "charlie", Right.DELEGATE)

    def test_check_permission_no_exist(self):
        p = Permissions()

        assert not p.check_permission("x", "alice", Right.READ)

    def test_check_permission_on_admin(self):
        p = Permissions()

        assert p.check_permission("x", "admin", Right.READ)

    def test_different_record(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ])
        p.add_permissions("y", "admin", "bob", [Right.READ])

        assert p.check_permission("x", "alice", Right.READ)
        assert not p.check_permission("x", "bob", Right.READ)
        assert not p.check_permission("y", "alice", Right.READ)
        assert p.check_permission("y", "bob", Right.READ)

    def test_record_not_attached_to_admin(self):
        p = Permissions()

        p.add_permissions("x", "alice", "bob", [Right.READ])

        assert not p.check_permission("x", "alice", Right.READ)
        assert not p.check_permission("x", "bob", Right.READ)

        p.add_permissions("x", "admin", "alice", [Right.READ])

        assert p.check_permission("x", "alice", Right.READ)
        assert p.check_permission("x", "bob", Right.READ)

    def test_add_permission_to_current_permission(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ])
        p.add_permissions("x", "admin", "alice", [Right.WRITE])
        p.add_permissions("x", "admin", "alice", [Right.APPEND])
        p.add_permissions("x", "admin", "alice", [Right.DELEGATE])

        assert p.check_permission("x", "alice", Right.READ)
        assert p.check_permission("x", "alice", Right.WRITE)
        assert p.check_permission("x", "alice", Right.APPEND)
        assert p.check_permission("x", "alice", Right.DELEGATE)


class Test_Delete_Permission:

    def test_delete_permission(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ, Right.WRITE])
        p.add_permissions("x", "alice", "bob", [Right.READ, Right.APPEND])

        assert p.check_permission("x", "alice", Right.READ)
        assert p.check_permission("x", "bob", Right.READ)
        assert not p.check_permission("x", "bob", Right.APPEND)

        p.delete_permission("x", "admin", "alice", Right.READ)

        assert not p.check_permission("x", "alice", Right.READ)
        assert not p.check_permission("x", "bob", Right.READ)

    def test_delete_permission_no_exist(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ])

        p.delete_permission("x", "admin", "alice", Right.WRITE)

        assert p.check_permission("x", "alice", Right.READ)

    def test_delete_principal_no_exist(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ])

        p.delete_permission("x", "bob", "dave", Right.READ)

class Test_Return_Permission_Keys:

    def test_num_permission_keys(self):
        p = Permissions()

        p.add_permissions("x", "admin", "alice", [Right.READ])

        assert 1 == len(p.return_permission_keys("alice"))
        assert "x" in p.return_permission_keys("alice")

        p.delete_permission("x", "admin", "alice", Right.READ)

        assert 0 == len(p.return_permission_keys("alice"))