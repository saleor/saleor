from xml.dom import minidom
from datetime import datetime
from braintree.util.datetime_parser import parse_datetime
import re
import sys

if sys.version_info[0] == 2:
    binary_type = str
else:
    binary_type = bytes

class Parser(object):
    def __init__(self, xml):
        if isinstance(xml, binary_type):
            xml = xml.decode('utf-8')
        self.doc = minidom.parseString("><".join(re.split(">\s+<", xml)).strip())

    def parse(self):
        return {self.__underscored(self.doc.documentElement.tagName): self.__parse_node(self.doc.documentElement)}

    def __parse_node(self, root):
        child = root.firstChild
        if self.__get_node_attribute(root, "type") == "array":
            return self.__build_list(child)
        elif not child:
            return self.__node_content(root, None)
        elif (child.nodeType == minidom.Node.TEXT_NODE):
            return self.__node_content(root, child.nodeValue)
        else:
            return self.__build_dict(child)

    def __convert_to_boolean(self, value):
        if value == "true" or value == "1":
            return True
        else:
            return False

    def __convert_to_date(self, value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    def __convert_to_datetime(self, value):
        return parse_datetime(value)

    def __convert_to_list(self, dict, key):
        val = dict[key]
        if not isinstance(val, list):
            dict[key] = [val]

    def __build_list(self, child):
        l = []
        while child is not None:
            if (child.nodeType == minidom.Node.ELEMENT_NODE):
                l.append(self.__parse_node(child))
            child = child.nextSibling
        return l

    def __build_dict(self, child):
        d = {}
        while child is not None:
            if (child.nodeType == minidom.Node.ELEMENT_NODE):
                child_tag = self.__underscored(child.tagName)
                if self.__get_node_attribute(child, "type") == "array" or child.firstChild and child.firstChild.nodeType == minidom.Node.TEXT_NODE:
                    d[child_tag] = self.__parse_node(child)
                else:
                    if not d.get(child_tag):
                        d[child_tag] = self.__parse_node(child)
                    else:
                        self.__convert_to_list(d, child_tag)
                        d[child_tag].append(self.__parse_node(child))

            child = child.nextSibling
        return d

    def __get_node_attribute(self, node, attribute):
        attribute_node = node.attributes.get(attribute)
        return attribute_node and attribute_node.value

    def __node_content(self, parent, content):
        parent_type = self.__get_node_attribute(parent, "type")
        parent_nil = self.__get_node_attribute(parent, "nil")

        if parent_type == "integer":
            return int(content)
        elif parent_type == "boolean":
            return self.__convert_to_boolean(content)
        elif parent_type == "datetime":
            return self.__convert_to_datetime(content)
        elif parent_type == "date":
            return self.__convert_to_date(content)
        elif parent_nil == "true":
            return None
        else:
            return content or ""

    def __underscored(self, string):
        return string.replace("-", "_")
