'''
Created on Oct 30, 2014

@author: rene
'''
import re
import string

from helper import DataObject, DataField, ListField


class IDDParser():

    def normalize_field_name(self, internal_name):
        name = internal_name.strip().replace('/', ' or ').lower()
        name = name.replace(' ', '_')
        name = name.replace('(', '')
        name = name.replace(')', '')
        return name

    def normalize_object_name(self, internal_name):
        name = internal_name.replace('/', ' or ').strip()
        name = string.capwords(name)
        name = name.replace(' ', '')
        return name

    def _is_new_field(self, line):
        return re.search(r"^\s*[AN]\d+\s*[,;]", line) is not None

    def _is_list(self, line):
        return re.search(r"^\s*L\d+\s*[,;]", line) is not None

    def _is_field_attribute(self, line):
        return re.search(r"^\s*\\", line) is not None

    def _is_new_object(self, line):
        if self._is_new_field(line) or self._is_field_attribute(line) or self._is_list(line):
            return False
        return re.search(r"^\s*(.*),", line) is not None

    def _parse_object_name(self, line):

        match_obj_name = re.search(r"^\s*(.*),", line)
        assert match_obj_name is not None

        internal_name = match_obj_name.group(1)

        name = self.normalize_object_name(internal_name)
        self.current_object = DataObject(name, internal_name)

    def _parse_field_name(self, line):
        # print "NewField:\t", line
        match_field_name = re.search(r"\\field\s(.*)$", line)
        match_field_type = re.search(r"^\s*([AN])", line)

        if match_field_name is None or match_field_type is None:
            print "Did not match field name: ", line, match_field_name, match_field_type
            return

        ftype = match_field_type.group(1)
        internal_name = match_field_name.group(1).strip()
        name = self.normalize_field_name(internal_name)
        self.current_object.fields.append(DataField(name, internal_name, ftype))

    def _parse_list(self, line):
        match_list_name = re.search(r"\\list\s(.*)$", line)

        if match_list_name is None:
            print "Did not match list name: ", line, match_list_name
            return

        internal_name = match_list_name.group(1).strip()
        object_name = self.normalize_object_name(internal_name)
        name = self.normalize_field_name(internal_name)
        df = ListField(name, internal_name, object_name)
        df.is_list = True
        self.current_object.fields.append(df)

    def _parse_field_attribute(self, line):
        last_field = self.current_object.fields[-1]

        match_attribute_name = re.match(r"\s*\\([^\s]+)", line)
        if match_attribute_name is not None:
            attribute_name = match_attribute_name.group(1).strip()

            no_value_attributes = ["required-field"]

            if attribute_name in no_value_attributes:
                last_field.attributes[attribute_name] = None

            match_value = re.search(r"\s*\\[^\s]+\s?(.*)", line)
            if match_value is not None:
                value = match_value.group(1).strip()

                multiple_value_attributes = ["key",
                                             "note"]

                if attribute_name in multiple_value_attributes:
                    if attribute_name not in last_field.attributes:
                        self.current_object.fields[-1].attributes[attribute_name] = []
                    last_field.attributes[attribute_name].append(value)
                else:
                    last_field.attributes[attribute_name] = value
            else:
                print "found no field value for: ", line, attribute_name, match_value
        else:
            print "found no field attribute for: ", line, match_attribute_name

    def __init__(self):
        self.current_object = None
        self.objects = []

    def parse(self, path):

        with open(path, mode='r') as f:
            for line in f:
                if line[0] == '!':
                    continue
                line = line.strip()
                print line

                if self._is_new_object(line):
                    # print "New Object! ", line
                    if self.current_object is not None:
                        self.objects.append(self.current_object)
                        self.current_object = None

                    self._parse_object_name(line)

                elif self._is_list(line):
                    self._parse_list(line)

                elif self._is_new_field(line):

                    assert self.current_object is not None

                    self._parse_field_name(line)

                elif self._is_field_attribute(line):
                    self._parse_field_attribute(line)
                else:
                    print "No detect:", line

        if self.current_object is not None:
            self.objects.append(self.current_object)
        return self.objects
#
#         for o in self.objects:
#             print o.name, len(o.fields), [i.name for i in o.fields]


if __name__ == '__main__':
    parser = IDDParser()
    objects = parser.parse("epw.idd")
