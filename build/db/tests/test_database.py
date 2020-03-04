from db.database import Database, PrincipalKeyError, RecordKeyError, SecurityViolation
import pytest


class Test_Init:

    def test_admin_exists(self):
        d = Database("test")
        assert "admin" == d.get_principal("admin").get_username()

    def test_admin_marked_admin(self):
        d = Database("test")
        assert d.get_principal("admin").is_admin()

    def test_admin_password_correct(self):
        d = Database("test")
        admin = d.get_principal("admin")
        assert admin.authenticate("test")
        assert not admin.authenticate("thisisanotherpassword")


class Test_Set_Current_Principal:

    def test_set_principal_admin(self):
        d = Database("test")
        d.set_principal("admin", "test")
        assert d.get_current_principal().get_username() == "admin"
        assert d.get_current_principal().is_admin()

    def test_set_principal_other(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.create_principal("user1", "test")
        d.set_principal("user1", "test")

        assert d.get_current_principal().get_username() == "user1"
        assert not d.get_current_principal().is_admin()

    def test_username_not_exist(self):
        d = Database("test")
        with pytest.raises(SecurityViolation) as excinfo:
            d.set_principal("user1", "test")
        assert "invalid username/password combination for principal" in str(excinfo.value)
        d.set_principal("admin", "test")

    def test_password_invalid(self):
        d = Database("test")
        with pytest.raises(SecurityViolation) as excinfo:
            d.set_principal("admin", "invalidpassword")
        assert "invalid username/password combination for principal" in str(excinfo.value)
        d.set_principal("admin", "test")


class Test_Create_Principal:

    def test_create_principal_without_setting_current_principal(self):
        d = Database("test")

        with pytest.raises(SecurityViolation) as excinfo:
            d.create_principal("user1", "password")
        assert "current principal is not set" in str(excinfo.value)

    def test_create_principal_without_admin(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.create_principal("user1", "password") == "CREATE_PRINCIPAL"
        d.set_principal("user1", "password")

        with pytest.raises(SecurityViolation) as excinfo:
            d.create_principal("user2", "anothertestpassword")
        assert "current principal is not admin user" in str(excinfo.value)

    def test_create_basic_principal(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.create_principal("user1", "test") == "CREATE_PRINCIPAL"

        assert "user1" == d.get_principal("user1").get_username()
        assert d.get_principal("user1").authenticate("test")

    def test_create_duplicate_username(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.create_principal("user1", "thisisalongerpassword") == "CREATE_PRINCIPAL"

        with pytest.raises(PrincipalKeyError) as excinfo:
            d.create_principal("user1", "differentpassword")
        assert "username for principal exists in database" in str(excinfo.value)

    def test_create_duplicate_password(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.create_principal("user1", "password") == "CREATE_PRINCIPAL"
        assert d.create_principal("user2", "password") == "CREATE_PRINCIPAL"


class Test_Change_Password:

    def test_current_principal_not_set(self):
        d = Database("test")

        with pytest.raises(SecurityViolation) as excinfo:
            d.change_password("admin", "newpassword")
        assert "current principal is not set" in str(excinfo.value)

    def test_admin_change_admin_password(self):
        d = Database("test")
        d.set_principal("admin", "test")
        assert d.get_principal("admin").authenticate("test")

        assert d.change_password("admin", "newpassword") == "CHANGE_PASSWORD"
        assert d.get_principal("admin").authenticate("newpassword")

    def test_admin_change_other_password(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.create_principal("user1", "otherpassword")
        assert d.get_principal("user1").authenticate("otherpassword")

        assert d.change_password("user1", "newpassword") == "CHANGE_PASSWORD"
        assert d.get_principal("user1").authenticate("newpassword")

    def test_user_change_user_password(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.create_principal("user1", "otherpassword")
        d.set_principal("user1", "otherpassword")
        assert d.get_principal("user1").authenticate("otherpassword")

        assert d.change_password("user1", "newpassword") == "CHANGE_PASSWORD"
        assert d.get_principal("user1").authenticate("newpassword")

    def test_user_change_other_password(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.create_principal("user1", "password")
        d.set_principal("user1", "password")

        with pytest.raises(SecurityViolation) as excinfo:
            d.change_password("admin", "newpassword")
        assert "cannot change password of another principal without admin privileges" in str(excinfo.value)

    def test_user_change_password_no_exist(self):
        d = Database("test")
        d.set_principal("admin", "test")

        with pytest.raises(PrincipalKeyError) as excinfo:
            d.change_password("user2", "newpassword")
        assert "username for principal does not exist in the database" in str(excinfo.value)


class Test_Set_Record:

    def test_current_principal_not_set(self):
        d = Database("test")

        with pytest.raises(SecurityViolation) as excinfo:
            d.set_record("x", "this is a record")
        assert "current principal is not set" in str(excinfo.value)

    def test_set_new_global_record(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.set_record("x", "this is a record") == "SET"
        assert d.return_record("x") == "this is a record"

    def test_set_old_global_record(self):
        d = Database("test")
        d.set_principal("admin", "test")

        assert d.set_record("x", "this is a record") == "SET"
        assert d.return_record("x") == "this is a record"

        assert d.set_record("x", ["first_elem", "second_elem"]) == "SET"
        ret = d.return_record("x")
        assert ret[0] == "first_elem" and ret[1] == "second_elem"

    def test_write_record_no_permissions(self):
        d = Database("test")
        d.set_principal("admin", "test")
        d.create_principal("user1", "password")

        assert d.set_record("x", "this is a record") == "SET"
        assert d.return_record("x") == "this is a record"

        d.set_principal("user1", "password")

        with pytest.raises(SecurityViolation) as excinfo:
            d.set_record("x", "different_record")
        assert "principal does not have write permission on record" in str(excinfo.value)

    def test_read_record_no_permissions(self):
        d = Database("test")
        d.set_principal("admin", "test")
        d.create_principal("user1", "password")

        assert d.set_record("x", "this is a record") == "SET"
        assert d.return_record("x") == "this is a record"

        d.set_principal("user1", "password")

        with pytest.raises(SecurityViolation) as excinfo:
            d.return_record("x")
        assert "principal does not have read permission on record" in str(excinfo.value)

    def test_read_record_no_exist(self):
        d = Database("test")
        d.set_principal("admin", "test")

        with pytest.raises(RecordKeyError) as excinfo:
            d.return_record("x")
        assert "record does not exist in the database" in str(excinfo.value)


class Test_Append_Record:

    def test_current_principal_not_set(self):
        d = Database("test")
        d.set_principal("admin", "test")
        d.set_record("x", ["record"])
        d.exit()

        with pytest.raises(SecurityViolation) as excinfo:
            d.append_record("x", "this is a record")
        assert "current principal is not set" in str(excinfo.value)

    def test_append_string_global_record(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.set_record("x", ["one"])
        record = d.return_record("x")
        assert len(record) == 1
        assert record[0] == "one"

        d.append_record("x", "two")
        record = d.return_record("x")
        assert len(record) == 2
        assert record[0] == "one"
        assert record[1] == "two"

    def test_append_dict_global_record(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.set_record("x", ["one"])
        record = d.return_record("x")
        assert len(record) == 1
        assert record[0] == "one"

        d.append_record("x", {"another": ["record"]})
        record = d.return_record("x")
        assert len(record) == 2
        assert record[0] == "one"

        assert "another" in record[1]
        assert len(record[1]["another"]) == 1
        assert record[1]["another"][0] == "record"

    def test_append_list_global_record(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.set_record("x", ["one"])
        record = d.return_record("x")
        assert len(record) == 1
        assert record[0] == "one"

        d.append_record("x", ["two", "three", "four"])
        record = d.return_record("x")
        assert len(record) == 4
        assert record[0] == "one"
        assert record[1] == "two"
        assert record[2] == "three"
        assert record[3] == "four"

    def test_append_no_permissions(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.set_record("x", ["one", "two"])
        record = d.return_record("x")
        assert len(record) == 2
        assert record[0] == "one"
        assert record[1] == "two"

        d.create_principal("user1", "password")
        d.set_principal("user1", "password")

        with pytest.raises(SecurityViolation) as excinfo:
            d.append_record("x", "three")
        assert "principal does not have write permission or append permission on record" in str(excinfo.value)

    def test_append_no_exist(self):
        d = Database("test")
        d.set_principal("admin", "test")

        with pytest.raises(RecordKeyError) as excinfo:
            d.append_record("x", "record")
        assert "record does not exist in the database" in str(excinfo.value)


class Test_Exit:

    def test_exit(self):
        d = Database("test")
        d.set_principal("admin", "test")
        assert d.get_current_principal().get_username() == "admin"

        d.exit()
        with pytest.raises(SecurityViolation) as excinfo:
            d.get_current_principal()
        assert "current principal is not set" in str(excinfo.value)