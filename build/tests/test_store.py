from ..store import Store


class Test_Set_Record:

    def test_set_record(self):
        s = Store()
        s.set_record("x", "record")

        assert s.read_record("x") == "record"

        s.set_record("x", "another_record")

        assert s.read_record("x") == "another_record"

    def test_set_different_types(self):
        s = Store()
        s.set_record("x", "string_type")

        assert s.read_record("x") == "string_type"

        s.set_record("x", ["list", "type"])

        assert s.read_record("x")[0] == "list" and s.read_record("x")[1] == "type"

        s.set_record("x", {"dict": "type"})

        assert "dict" in s.read_record("x") and s.read_record("x")["dict"] == "type"

    def test_read_record_no_exist(self):
        s = Store()
        assert s.read_record("x") is None

        assert s.read_record("y") is None

    def test_record_read_copy(self):
        s = Store()

        # Testing that we are copying list elements
        value = ["first", "second"]
        s.set_record("x", value)

        assert id(value) != id(s.read_record("x"))

        # Testing that we are copying dict elements
        value = {"first": "value", "second": "value"}
        s.set_record("x", value)

        assert id(value) != id(s.read_record("x"))
