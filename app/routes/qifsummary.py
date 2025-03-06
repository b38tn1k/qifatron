import os
import re
from lxml import etree
from xmldiff import main
import logging
import difflib
import json

logger = logging.getLogger(__name__)


def recursive_diff(d1, d2, base_path=""):
    """
    Compare two nested dictionaries (which may include a special '_path' key)
    and collect the differences. Each difference entry can also include the
    original XML '_path' (if present).

    Args:
        d1 (dict): First nested dictionary.
        d2 (dict): Second nested dictionary.
        base_path (str): A prefix to apply to the 'path' for these keys.

    Returns:
        list of dict: Each dict describes a difference with these fields:
                    - "path": combined path of parent + this key
                    - "element_path_in_file1": the '_path' from d1 if present
                    - "element_path_in_file2": the '_path' from d2 if present
                    - "file1": the value from d1
                    - "file2": the value from d2
    """
    # We generally want to skip comparing special keys like '_path' to avoid false diffs.
    ignore_keys = {"_path"}
    all_keys = (set(d1.keys()) - ignore_keys) | (set(d2.keys()) - ignore_keys)

    differences = []
    for key in all_keys:
        path = f"{base_path}/{key}" if base_path else key

        if key not in d1:
            # Present in d2, missing in d1
            differences.append(
                {
                    "path": path,
                    "element_path_in_file1": d1.get("_path"),
                    "element_path_in_file2": d2.get("_path"),
                    "file1": None,
                    "file2": d2[key],
                }
            )
        elif key not in d2:
            # Present in d1, missing in d2
            differences.append(
                {
                    "path": path,
                    "element_path_in_file1": d1.get("_path"),
                    "element_path_in_file2": d2.get("_path"),
                    "file1": d1[key],
                    "file2": None,
                }
            )
        else:
            v1, v2 = d1[key], d2[key]

            # If both are dicts, recurse
            if isinstance(v1, dict) and isinstance(v2, dict):
                differences.extend(recursive_diff(v1, v2, base_path=path))

            # If both are lists, we can compare them directly or build a more complex matching system
            elif isinstance(v1, list) and isinstance(v2, list):
                if v1 != v2:
                    differences.append(
                        {
                            "path": path,
                            "element_path_in_file1": d1.get("_path"),
                            "element_path_in_file2": d2.get("_path"),
                            "file1": v1,
                            "file2": v2,
                        }
                    )

            # Otherwise do a direct comparison (final scalar, or unmatched types)
            else:
                if v1 != v2:
                    differences.append(
                        {
                            "path": path,
                            "element_path_in_file1": d1.get("_path"),
                            "element_path_in_file2": d2.get("_path"),
                            "file1": v1,
                            "file2": v2,
                        }
                    )

    return differences


class QIFSummary:
    def __init__(self, filepath, schema_obj):
        """
        Initialize by parsing the QIF XML file using lxml and storing a preloaded XMLSchema object.

        Args:
            filepath (str): Path to the QIF XML file.
            schema_obj (xmlschema.XMLSchema): A preloaded XMLSchema object for validation.
        """
        self.filepath = filepath
        self.name = os.path.basename(filepath)
        self.ns = {"qif": "http://qifstandards.org/xsd/qif3"}
        logger.debug("Initializing QIFSummary for file: %s", filepath)
        self.basic_xml_errors = []
        try:
            with open(self.filepath, "rb") as f:
                xml_content = f.read()

            if b"##other" in xml_content:
                xml_content = xml_content.replace(
                    b"##other", b"http://example.com/other"
                )
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
        features_section = self.root.find(
            ".//{http://qifstandards.org/xsd/qif3}Features"
        )
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
        file_units_element = self.root.find(
            ".//{http://qifstandards.org/xsd/qif3}FileUnits"
        )
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
                                        row[f"{key} {sub_key}"] = (
                                            sub_value[0]
                                            if (
                                                isinstance(sub_value, list)
                                                and sub_value
                                            )
                                            else sub_value
                                        )
                                        all_columns.add(f"{key} {sub_key}")
                            else:
                                row[key] = (
                                    value[0]
                                    if isinstance(value[0], str)
                                    else str(value[0])
                                )
                                all_columns.add(key)
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                row[f"{key} {sub_key}"] = (
                                    sub_value[0]
                                    if (isinstance(sub_value, list) and sub_value)
                                    else sub_value
                                )
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
        normalized_units, unit_columns = self.normalize_units(
            self.get_file_units_dict()
        )
        organised_units = {}
        for item in normalized_units:
            if "UnitConversion Factor" in item.keys():
                if item["SIUnitName"] not in organised_units:
                    organised_units[item["SIUnitName"]] = {}
                organised_units[item["SIUnitName"]][item["UnitName"]] = item[
                    "UnitConversion Factor"
                ]

        summary = {
            "filename": os.path.basename(self.filepath),
            "file_size": round(os.path.getsize(self.filepath) / 1024, 2),
            "qif_version": self.root.attrib.get("versionQIF")
            or self.root.attrib.get("version", "Unknown"),
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

    def traverse_xml(self, element, current_path=""):
        """
        Recursively converts an XML element into a dictionary, storing a '_path'
        key so you can correlate each dictionary node to its original XML node.

        Args:
            element (lxml.etree._Element): The current XML element to traverse.
            current_path (str): The hierarchical path to this element so far.

        Returns:
            dict: A nested dictionary that represents this element and its children.
                Includes a special "_path" key for debugging/traceback.
        """
        tag_name = self.remove_namespace(element.tag)
        # Build a hierarchical path to this element
        # For uniqueness, you might also include an index if there are multiple siblings with the same tag.
        new_path = f"{current_path}/{tag_name}".rstrip("/")

        node_dict = {"_path": new_path}  # store the path for reference
        text = (element.text or "").strip() or None

        children = list(element)  # get all immediate children
        if children:
            grouped_children = {}
            # Recursively build dictionaries for all children
            for child in children:
                child_dict = self.traverse_xml(child, current_path=new_path)
                # child_dict might look like: {"_path": "...", "ChildTag": {...}}
                # We need to fold this into grouped_children by "ChildTag".
                # We'll also skip merging the "_path" into grouped_children to avoid clutter.
                for key, value in child_dict.items():
                    if key == "_path":
                        continue  # skip the special path key
                    if key in grouped_children:
                        grouped_children[key].append(value)
                    else:
                        grouped_children[key] = [value]
            node_dict[tag_name] = grouped_children
        else:
            # Leaf node: store text or an empty dict
            node_dict[tag_name] = text if text else {}

        return node_dict

    def traverse_xml(self, element, current_path=""):
        """
        Recursively converts an XML element into a dictionary, storing a '_path'
        key so you can correlate each dictionary node to its original XML node.

        Args:
            element (lxml.etree._Element): The current XML element to traverse.
            current_path (str): The hierarchical path to this element so far.

        Returns:
            dict: A nested dictionary that represents this element and its children.
                Includes a special "_path" key for debugging/traceback.
        """
        tag_name = self.remove_namespace(element.tag)
        # Build a hierarchical path to this element
        # For uniqueness, you might also include an index if there are multiple siblings with the same tag.
        new_path = f"{current_path}/{tag_name}".rstrip("/")

        node_dict = {"_path": new_path}  # store the path for reference
        text = (element.text or "").strip() or None

        children = list(element)  # get all immediate children
        if children:
            grouped_children = {}
            # Recursively build dictionaries for all children
            for child in children:
                child_dict = self.traverse_xml(child, current_path=new_path)
                # child_dict might look like: {"_path": "...", "ChildTag": {...}}
                # We need to fold this into grouped_children by "ChildTag".
                # We'll also skip merging the "_path" into grouped_children to avoid clutter.
                for key, value in child_dict.items():
                    if key == "_path":
                        continue  # skip the special path key
                    if key in grouped_children:
                        grouped_children[key].append(value)
                    else:
                        grouped_children[key] = [value]
            node_dict[tag_name] = grouped_children
        else:
            # Leaf node: store text or an empty dict
            node_dict[tag_name] = text if text else {}

        return node_dict

    def compare_to(self, other):
        """
        Compare key parts of the QIF summary dictionaries for self and other.
        Differences are aggregated into a single list (all_diffs).
        Each difference can optionally include the '_path' trace from the original XML.

        Returns:
            dict with:
                "differences": list of difference entries (dictionaries)
                "name1": filename for self
                "name2": filename for other
        """

        # res = self.compare_full_tree(other)

        # for k in res:
        #     print(k)
        #     print(res[k])
        #     print()

        def dict_from_top_section_summary(obj):
            # Helper to put top_section_summary in a dict with the name "top_sections"
            return {"top_sections": obj.get_top_section_summary()}

        def dict_from_feature_summary(obj):
            return {"feature_summary": obj.get_feature_summary()}

        def dict_from_fileunits_summary(obj):
            return {"fileunits_repetition": obj.get_repeated_section_summary()}

        # We'll gather dictionaries from each side
        d1 = {}
        d2 = {}

        # Merge in top-sections, features, repeated FileUnits, etc.
        d1.update(dict_from_top_section_summary(self))
        d2.update(dict_from_top_section_summary(other))

        d1.update(dict_from_feature_summary(self))
        d2.update(dict_from_feature_summary(other))

        d1.update(dict_from_fileunits_summary(self))
        d2.update(dict_from_fileunits_summary(other))

        # Compare QIF version as well
        v1 = self.root.attrib.get("versionQIF") or self.root.attrib.get(
            "version", "Unknown"
        )
        v2 = other.root.attrib.get("versionQIF") or other.root.attrib.get(
            "version", "Unknown"
        )
        d1["qif_version"] = v1
        d2["qif_version"] = v2

        all_diffs = recursive_diff(d1, d2)

        return {"differences": all_diffs, "name1": self.name, "name2": other.name}

    def compare_full_tree(self, other):
        """
        Compare the entire XML tree of self vs. other, returning a list of differences.
        Uses traverse_xml(...) on each root to build a dictionary representation,
        then calls recursive_diff(...) to find differences.

        Returns:
            dict with keys:
            - "differences": list of difference details
            - "name1": filename for self
            - "name2": filename for other
        """
        # 1) Build dictionary from entire XML tree
        d1 = self.traverse_xml(self.root)
        d2 = other.traverse_xml(other.root)

        # 2) Compare those dictionaries
        differences = recursive_diff(d1, d2)

        return {"differences": differences, "name1": self.name, "name2": other.name}

    def chase_feature(self, feature_name):
        """
        Searches for a CharacteristicNominal with <Name>==feature_name,
        and gathers downward references (FeatureNominalIds) plus upward references
        (CharacteristicItems referencing the nominal, PMIDisplay referencing ID).
        """
        result = {
            "feature_name": feature_name,
            "nominal_id": None,
            "down_chain": {},
            "up_chain": {},
            "details": {},
        }

        # 1) Find the relevant CharacteristicNominal by name
        char_nom = self._find_characteristic_nominal_by_name(feature_name)
        if char_nom is None:
            result["error"] = (
                f"No CharacteristicNominal found with <Name>{feature_name}</Name>"
            )
            return result

        # Basic info about the nominal
        nominal_id = char_nom.get("id")
        result["nominal_id"] = nominal_id
        # Possibly gather details on this nominal element
        result["details"]["characteristic_nominal"] = self._element_summary(char_nom)

        # 2) Trace down: from <FeatureNominalIds> or etc.
        result["down_chain"] = self._trace_down_nominal(char_nom)

        # 3) Trace up: find CharacteristicItem referencing nominal, plus PMIDisplay references
        result["up_chain"] = self._trace_up_nominal(nominal_id)

        return result

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------

    def _find_characteristic_nominal_by_name(self, feature_name):
        """
        Finds <CharacteristicNominal> with <Name>==feature_name. Returns the element or None.
        """
        nominal_tags = [
            "DiameterCharacteristicNominal",
            "FlatnessCharacteristicNominal",
            "PositionCharacteristicNominal",
            "ProfileCharacteristicNominal",
            "SurfaceProfileCharacteristicNominal",
            "AngularityCharacteristicNominal",
            "ParallelismCharacteristicNominal",
            "PerpendicularityCharacteristicNominal",
        ]
        for tag in nominal_tags:
            nominals = self.root.findall(".//{http://qifstandards.org/xsd/qif3}" + tag)

            for nom in nominals:
                name_elem = nom.find("{http://qifstandards.org/xsd/qif3}Name")
                if name_elem is not None and name_elem.text == feature_name:
                    return nom
        return None

    def _trace_down_nominal(self, char_nom_element):
        """
        Collects references from a <CharacteristicNominal> downward, e.g.
        <FeatureNominalIds> => <Id> => actual FeatureNominal element(s).
        """
        down_data = {}

        fn_ids_elem = char_nom_element.find(
            "{http://qifstandards.org/xsd/qif3}FeatureNominalIds"
        )
        if fn_ids_elem is not None:
            # Gather all <Id> sub-elements
            id_elems = fn_ids_elem.findall("{http://qifstandards.org/xsd/qif3}Id")
            ids_list = [ielem.text for ielem in id_elems]
            down_data["feature_nominal_ids"] = ids_list

            # Optionally fetch the actual FeatureNominal elements
            # e.g. <FeatureNominal id="32243">
            feature_nominals = []
            for fid in ids_list:
                f_nom = self._find_element_by_id("FeatureNominal", fid)
                if f_nom is not None:
                    feature_nominals.append(self._element_summary(f_nom))
            down_data["feature_nominals"] = feature_nominals

        return down_data

    def _trace_up_nominal(self, nominal_id):
        """
        Finds <CharacteristicItem> referencing <CharacteristicNominalId>==nominal_id.
        Then also checks for <PMIDisplay><Reference><Id> => nominal_id.
        """
        up_data = {}

        # 1) Find all CharacteristicItems referencing nominal_id
        char_items = self.root.findall(
            ".//{http://qifstandards.org/xsd/qif3}CharacteristicItem"
        )
        referencing_items = []
        for item in char_items:
            cnom_id_elem = item.find(
                "{http://qifstandards.org/xsd/qif3}CharacteristicNominalId"
            )
            if cnom_id_elem is not None and cnom_id_elem.text == nominal_id:
                referencing_items.append(item)
        up_data["characteristic_items"] = [
            self._element_summary(ci) for ci in referencing_items
        ]

        # 2) Also find if there's any <PMIDisplay> referencing that nominal
        # e.g. <PMIDisplay>...<Reference><Id>24844</Id></Reference> ...
        pmi_displays = self.root.findall(
            ".//{http://qifstandards.org/xsd/qif3}PMIDisplay"
        )
        referencing_pmis = []
        for pmi in pmi_displays:
            ref_elem = pmi.find(
                "{http://qifstandards.org/xsd/qif3}Reference/{http://qifstandards.org/xsd/qif3}Id"
            )
            if ref_elem is not None and ref_elem.text == nominal_id:
                referencing_pmis.append(pmi)

        up_data["pmi_displays"] = [self._element_summary(pd) for pd in referencing_pmis]

        return up_data

    def _find_element_by_id(self, tag_name, elem_id):
        """
        Finds an element of type <tag_name> with @id == elem_id.
        Example: <FeatureNominal id="32243">...
        """
        path = f".//{{http://qifstandards.org/xsd/qif3}}{tag_name}"
        candidates = self.root.findall(path)
        for c in candidates:
            if c.get("id") == elem_id:
                return c
        return None

    def _element_summary(self, elem):
        """
        Returns a minimal dictionary describing an element: tag, id, name (if any),
        plus a formatted snippet of the element's XML content.
        """
        info = {
            "tag": self.remove_namespace(elem.tag),
            "id": elem.get("id"),
        }

        # If there's a <Name> child, include it
        name_elem = elem.find("{http://qifstandards.org/xsd/qif3}Name")
        if name_elem is not None:
            info["name"] = name_elem.text

        # Convert this element to a nicely formatted XML string.
        # Make sure pretty_print=True for readable indentation, 
        # and decode from bytes to get a Python string.
        try:
            info["xml_snippet"] = etree.tostring(elem, pretty_print=True).decode("utf-8")
        except Exception as e:
            # If there's some reason serialization fails, store an error message 
            # (should be unlikely unless there's invalid data).
            info["xml_snippet"] = f"<serialization error: {e}>"

        return info
    
    def get_raw_xml(self):
        """
        Reads and returns the *entire* QIF XML file as a raw Unicode string.
        Useful if you need to serve or inspect the original XML contents directly.
        """
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.read()

    def as_dict(self):
        """
        Builds and returns a full dictionary representation of this QIF file
        by recursively traversing the entire XML tree.

        Note: This can be very large if the QIF is huge. Consider partial traversal or
        streaming approaches for extremely large files.
        """
        # Leverage the self.traverse_xml(...) method defined in QIFSummary
        return self.traverse_xml(self.root, current_path="")