import os
import re
from lxml import etree
import xmlschema  # pip install xmlschema
import logging

logger = logging.getLogger(__name__)

class QIFSummary:
    def __init__(self, filepath, schema_obj):
        """
        Initialize by parsing the QIF XML file using lxml and storing a preloaded XMLSchema object.
        
        Args:
            filepath (str): Path to the QIF XML file.
            schema_obj (xmlschema.XMLSchema): A preloaded XMLSchema object for validation.
        """
        self.filepath = filepath
        self.ns = {"qif": "http://qifstandards.org/xsd/qif3"}
        logger.debug("Initializing QIFSummary for file: %s", filepath)
        self.basic_xml_errors = []
        try:
            with open(self.filepath, 'rb') as f:
                xml_content = f.read()

            if b'##other' in xml_content:
                xml_content = xml_content.replace(b'##other', b'http://example.com/other')
                self.basic_xml_errors.append("Replaced b'##other' with a valid URI.")
            self.tree = etree.fromstring(xml_content, parser=etree.XMLParser())
            self.root = self.tree
            logger.debug("Parsed XML tree successfully using lxml.")
        except Exception as e:
            logger.error("Failed to parse XML tree using lxml: %s", e)
            raise
        self.schema = schema_obj

    def remove_namespace(self, tag):
        """Remove any XML namespace from the tag name."""
        result = re.sub(r"\{.*\}", "", tag)
        logger.debug("Removed namespace from tag: '%s' -> '%s'", tag, result)
        return result

    def get_schema_validation(self):
        """
        Uses the provided lxml XMLSchema object to validate the QIF file.
        
        Returns:
            dict: Contains keys "schema_valid" (bool) and "errors" (None or error details).
        """
        logger.debug("Performing schema validation using lxml XMLSchema.")
        try:
            valid = self.schema.validate(self.tree)
            if not valid:
                # lxml error log is available as self.schema.error_log
                errors = [e.message for e in self.schema.error_log]
                print(errors)
                logger.debug("Schema validation failed with errors: %s", errors)
                return {"schema_valid": valid, "errors": errors}
            logger.debug("Schema validation successful.")
            return {"schema_valid": valid, "errors": None}
        except Exception as e:
            logger.error("Exception in get_schema_validation: %s", e)
            return {"schema_valid": False, "errors": str(e)}

    def get_top_section_summary(self):
        """Returns a dictionary with counts for each top-level element."""
        logger.debug("Calculating top section summary.")
        summary = {}
        for child in self.root:
            tag = self.remove_namespace(child.tag)
            summary[tag] = summary.get(tag, 0) + 1
        logger.debug("Top section summary: %s", summary)
        return summary

    def get_feature_summary(self):
        """
        Returns a summary (count) of feature-related elements.
        It finds the Features section (using the namespace) and recursively counts
        elements (ignoring the top-level 'Features' container).
        """
        logger.debug("Calculating feature summary.")
        summary = {}
        features_section = self.root.find(".//{http://qifstandards.org/xsd/qif3}Features")
        if features_section is None:
            logger.debug("No Features section found.")
            return summary
        for feature in features_section.iter():
            tag = self.remove_namespace(feature.tag)
            if tag != "Features":
                summary[tag] = summary.get(tag, 0) + 1
        logger.debug("Feature summary: %s", summary)
        return summary

    def get_repeated_section_summary(self):
        """
        Returns a summary for the FileUnits section.
        For example, counts of unit groups (e.g. PrimaryUnits, OtherUnits).
        """
        logger.debug("Calculating repeated section summary for FileUnits.")
        summary = {}
        file_units = self.root.find(".//{http://qifstandards.org/xsd/qif3}FileUnits")
        if file_units is not None:
            for section in file_units:
                section_name = self.remove_namespace(section.tag)
                summary[section_name] = len(list(section))
        logger.debug("Repeated section summary: %s", summary)
        return summary

    def traverse_xml(self, element):
        """Recursively converts an XML element into a dictionary."""
        tag_name = self.remove_namespace(element.tag)
        node_dict = {}
        text = element.text.strip() if element.text and element.text.strip() else None
        children = [self.traverse_xml(child) for child in element]
        if children:
            grouped_children = {}
            for child in children:
                for key, value in child.items():
                    if key in grouped_children:
                        grouped_children[key].append(value)
                    else:
                        grouped_children[key] = [value]
            node_dict[tag_name] = grouped_children
        else:
            node_dict[tag_name] = text if text else {}
        logger.debug("Traversed element '%s': %s", tag_name, node_dict[tag_name])
        return node_dict

    def get_file_units_dict(self):
        """Extracts the FileUnits section as a dictionary."""
        logger.debug("Extracting FileUnits section.")
        file_units_element = self.root.find(".//{http://qifstandards.org/xsd/qif3}FileUnits")
        if file_units_element is not None:
            file_units_dict = self.traverse_xml(file_units_element)
            logger.debug("Extracted FileUnits dictionary.")
            return file_units_dict
        logger.debug("No FileUnits section found.")
        return {}

    def normalize_units(self, data):
        """
        Flattens nested FileUnits data into a structured table format with dynamic keys.
        Returns a tuple: (list of rows, sorted list of column headers).
        """
        logger.debug("Normalizing units from FileUnits data.")
        rows = []
        all_columns = set()

        def extract_units(category, unit_data):
            for unit_type, unit_list in unit_data.items():
                for unit in unit_list:
                    row = {"category": category, "unit type": unit_type}
                    for key, value in unit.items():
                        if isinstance(value, list) and value:
                            if isinstance(value[0], dict):
                                if len(value[0].keys()) == 1:
                                    sub_key = list(value[0].keys())[0]
                                    subvalue = value[0][sub_key]
                                    if isinstance(subvalue, list) and subvalue:
                                        row[f"{key} {sub_key}"] = subvalue[0]
                                    else:
                                        row[f"{key} {sub_key}"] = subvalue
                                    all_columns.add(f"{key} {sub_key}")
                                else:
                                    for sub_key, sub_value in value[0].items():
                                        row[f"{key} {sub_key}"] = (sub_value[0] if (isinstance(sub_value, list) and sub_value) else sub_value)
                                        all_columns.add(f"{key} {sub_key}")
                            else:
                                row[key] = value[0] if isinstance(value[0], str) else str(value[0])
                                all_columns.add(key)
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                row[f"{key} {sub_key}"] = (sub_value[0] if (isinstance(sub_value, list) and sub_value) else sub_value)
                                all_columns.add(f"{key} {sub_key}")
                        else:
                            row[key] = value
                            all_columns.add(key)
                    rows.append(row)
                    logger.debug("Extracted row: %s", row)

        file_units_dict = self.get_file_units_dict()
        if "FileUnits" in file_units_dict:
            for section, units in file_units_dict["FileUnits"].items():
                if isinstance(units, list):
                    for unit_data in units:
                        extract_units(section, unit_data)
        logger.debug("Normalized units rows: %s", rows)
        return rows, sorted(all_columns)

    def get_summary(self):
        """
        Returns a high-level summary dictionary containing:
          - filename, file size, qif version,
          - summaries for top sections, features, and repeated FileUnits,
          - schema validation results,
          - normalized units table (rows and column headers).
        """
        logger.debug("Generating complete summary for file: %s", self.filepath)
        normalized_units, unit_columns = self.normalize_units(self.get_file_units_dict())
        organised_units = {}
        for item in normalized_units:
            if 'UnitConversion Factor' in item.keys():
                if item['SIUnitName'] not in organised_units:
                    organised_units[item['SIUnitName']] = {}
                organised_units[item['SIUnitName']][item['UnitName']] = item['UnitConversion Factor']
        
        summary = {
            "filename": os.path.basename(self.filepath),
            "file_size": round(os.path.getsize(self.filepath) / 1024, 2),
            "qif_version": self.root.attrib.get("versionQIF") or self.root.attrib.get("version", "Unknown"),
            "top_sections": self.get_top_section_summary(),
            "feature_summary": self.get_feature_summary(),
            "fileunits_repetition": self.get_repeated_section_summary(),
            "validation": self.get_schema_validation(),
            "xml_errors": self.basic_xml_errors,
            "normalized_units": normalized_units,
            "organised_units": organised_units,
            "unit_columns": unit_columns,
        }
        logger.debug("Final summary: %s", summary)
        return summary