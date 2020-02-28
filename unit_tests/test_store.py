from build.store import Store, AppendException, ForEachException
import pytest


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


class Test_Append_Record:

    def test_append_string_to_record(self):
        s = Store()
        s.set_record("x", ["first", "second"])

        s.append_record("x", "last elem")
        record = s.read_record("x")

        assert len(record) == 3
        assert record[0] == "first"
        assert record[1] == "second"
        assert record[2] == "last elem"

    def test_append_dict_to_record(self):
        s = Store()
        s.set_record("x", ["first", "second"])

        s.append_record("x", {"another": "elem"})
        record = s.read_record("x")

        assert len(record) == 3
        assert record[0] == "first"
        assert record[1] == "second"

        # Testing that the dictionary is the third element
        assert "another" in record[2]
        assert record[2]["another"] == "elem"

    def test_append_list_to_record(self):
        s = Store()
        s.set_record("x", ["first", "second"])

        s.append_record("x", ["third", "fourth"])
        record = s.read_record("x")

        assert len(record) == 4
        assert record[0] == "first"
        assert record[1] == "second"
        assert record[2] == "third"
        assert record[3] == "fourth"

    def test_append_not_list(self):
        s = Store()
        s.set_record("x", "this is another record")

        with pytest.raises(AppendException) as excinfo:
            s.append_record("x", "appended record")
        assert "unable to append record to non-list object" in str(excinfo.value)


class Test_For_Each_Record:
    
    def test_string_for_each(self):
        s = Store()
        s.set_record("x", ["first", "second", "third"]) == "SET"

        s.for_each_record("x", lambda x: x + " elem") == "FOREACH"
        
        record = s.read_record("x")
        assert len(record) == 3
        assert record[0] == "first elem"
        assert record[1] == "second elem"
        assert record[2] == "third elem"

    def test_record_for_each(self):
        s = Store()
        s.set_record("x", [{"name": "Jonathan"}, {"name": "Reuben"}]) == "SET"

        s.for_each_record("x", lambda x: x["name"]) == "FOREACH"

        record = s.read_record("x")
        assert len(record) == 2
        assert record[0] == "Jonathan"
        assert record[1] == "Reuben"

    def test_list_for_each(self):
        s = Store()
        s.set_record("x", [["one", "two"], ["three", "four"]]) == "SET"

        s.for_each_record("x", lambda x: x[1]) == "FOREACH"

        record = s.read_record("x")
        assert len(record) == 2
        assert record[0] == "two"
        assert record[1] == "four"

    def test_fail_eval_to_list(self):
        s = Store()
        s.set_record("x", [{"name": ["Jonathan", "Innis"]}, {"name": ["Reuben", "Tadpatri"]}])

        with pytest.raises(ForEachException) as excinfo:
            s.for_each_record("x", lambda x: x["name"])
        assert "expression evaluates to list object" in str(excinfo.value)

    def test_fail_list(self):
        s = Store()
        s.set_record("x", "element")

        with pytest.raises(ForEachException) as excinfo:
            s.for_each_record("x", lambda x: x + " element")
        assert "unable to iterate through non-list object" in str(excinfo.value)

    def test_single_list_elem(self):
        s = Store()
        s.set_record("x", ["element"])

        s.for_each_record("x", lambda x: x + " element")
        
        record = s.read_record("x")
        assert len(record) == 1
        record[0] == "element element"