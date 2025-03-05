import os
from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    flash,
    redirect,
    url_for,
    current_app,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET
import re

qif_bp = Blueprint("qif", __name__)


# Helper function to check allowed file types
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@qif_bp.route("/", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            flash(f"File '{filename}' uploaded successfully!", "success")
            return redirect(url_for("qif.start"))

        flash("Invalid file type!", "error")

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    files = os.listdir(upload_folder)

    return render_template("qif_tools/start.html", files=files)


@qif_bp.route("/download/<filename>")
def download_file(filename):
    """Serve a file for download."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)


def remove_namespace(tag):
    """Removes the XML namespace from a tag."""
    return re.sub(r"\{.*\}", "", tag)  # Removes {namespace} from tag names


def traverse_xml(element):
    """Recursively converts an XML element into a dictionary."""
    tag_name = remove_namespace(element.tag)
    node_dict = {}

    # If the element has text, store it as a value
    text = element.text.strip() if element.text and element.text.strip() else None

    # Iterate over child elements
    children = [traverse_xml(child) for child in element]

    if children:
        # If there are multiple children with the same tag, store as a list
        grouped_children = {}
        for child in children:
            for key, value in child.items():
                if key in grouped_children:
                    grouped_children[key].append(value)
                else:
                    grouped_children[key] = [value]

        # Store the grouped children
        node_dict[tag_name] = grouped_children
    else:
        # If there are no children, store only text content
        node_dict[tag_name] = text if text else {}

    return node_dict


def remove_namespace(tag):
    """Removes the XML namespace from a tag."""
    return re.sub(r"\{.*\}", "", tag)


def normalize_units(data):
    """Flattens nested FileUnits data into a structured table format with dynamic keys."""
    rows = []
    all_columns = set()  # Tracks all possible column names

    def extract_units(category, unit_data):
        """Extracts unit details dynamically and builds table rows."""
        for unit_type, unit_list in unit_data.items():
            for unit in unit_list:
                row = {"Category": category, "Unit Type": unit_type}

                # Extract all available keys dynamically
                for key, value in unit.items():
                    if isinstance(value, list) and value:  # Handle lists correctly
                        if isinstance(value[0], dict):
                            if len(value[0].keys()) == 1:
                                subvalue = value[0][list(value[0].keys())[0]]
                                if (isinstance(subvalue, list) and len(subvalue) == 1):
                                    row[key] = subvalue[0]
                                else:
                                    row[key] = value[0][list(value[0].keys())[0]]
                        else:
                            row[key] = value[0] if isinstance(value[0], str) else str(value[0])
                                
                        # has to happen here
                    else:
                        row[key] = value

                    all_columns.add(key)  # Track all discovered columns

                rows.append(row)

    # Process PrimaryUnits and OtherUnits
    if "FileUnits" in data:
        for section, units in data["FileUnits"].items():
            if isinstance(units, list):
                for unit_data in units:
                    extract_units(section, unit_data)

    return rows, sorted(all_columns)  # Return rows + sorted column headers for consistency


def parse_qif_metadata(filepath):
    """Extracts QIF metadata and normalizes FileUnits into a dynamic structured table."""
    metadata = {
        "filename": os.path.basename(filepath),
        "filesize": round(os.path.getsize(filepath) / 1024, 2),  # KB
        "qif_version": "Unknown",
        "file_units": {},
        "normalized_units": [],
        "unit_columns": []  # Dynamically extracted table headers
    }

    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        for elem in root:
            print(f"- {remove_namespace(elem.tag)}")

        # Store QIF version
        metadata["qif_version"] = root.attrib.get("versionQIF") or root.attrib.get("version", "Unknown")

        # Extract structured FileUnits
        file_units_element = root.find(".//{http://qifstandards.org/xsd/qif3}FileUnits")
        if file_units_element is not None:
            metadata["file_units"] = traverse_xml(file_units_element)

        # Normalize units dynamically
        metadata["normalized_units"], metadata["unit_columns"] = normalize_units(metadata["file_units"])

        features = root.find(".//{http://qifstandards.org/xsd/qif3}Features")
        feature_defs = features.findall(".//{http://qifstandards.org/xsd/qif3}FeatureDefinition")   

        for feature in feature_defs:
            print(f"  - {remove_namespace(feature.tag)}")

    except Exception as e:
        metadata["error"] = f"Error parsing QIF file: {str(e)}"

    return metadata


@qif_bp.route("/qif/<filename>")
def qif_details(filename):
    """Displays QIF file metadata and logs all nested elements."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)

    if not os.path.exists(filepath):
        abort(404, "File not found.")

    metadata = parse_qif_metadata(filepath)
    return render_template("qif_tools/qif_details.html", metadata=metadata)
