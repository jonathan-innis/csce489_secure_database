from build.database import Database, PrincipalKeyError, SecurityViolation
import pytest


class Test_Init:

    def test_admin_exists(self):
        d = Database("test")
        assert "admin" == d.get_principal("admin").username

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
        assert d.get_current_principal().username == "admin"
        assert d.get_current_principal().is_admin()

    def test_set_principal_other(self):
        d = Database("test")
        d.set_principal("admin", "test")

        d.create_principal("user1", "test")
        d.set_principal("user1", "test")

        assert d.get_current_principal().username == "user1"
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

        assert "user1" == d.get_principal("user1").username
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