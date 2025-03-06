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
    Response,
)
from werkzeug.utils import secure_filename
import xmlschema
from lxml import etree
from .qifsummary import QIFSummary
import logging

base_dir = os.path.join(os.getcwd(), "QIF3.0-2018-ANSI", "xsd", "QIFApplications")
schema_path = os.path.join(base_dir, "QIFDocument.xsd")

# schema_obj = xmlschema.XMLSchema(schema_path, base_url=base_dir)

schema_doc = etree.parse(schema_path)
schema_obj = etree.XMLSchema(schema_doc)

qif_bp = Blueprint("qif", __name__)

logger = logging.getLogger(__name__)


def load_qif_summary(filename):
    """
    Helper function to:
     1) Build the full path to the QIF file
     2) Load / create the schema object from QIFDocument.xsd (or some location)
     3) Construct a QIFSummary instance
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)
    if not os.path.exists(filepath):
        abort(404, f"File not found: {filename}")

    # Create a QIFSummary instance:
    try:
        qif_summary = QIFSummary(filepath, schema_obj)
        return qif_summary
    except Exception as e:
        logger.error("Failed to init QIFSummary: %s", e)
        abort(500, f"QIFSummary init error: {e}")


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
    qif_files = []
    for root, dirs, files in os.walk(upload_folder):
        for f in files:
            if f.lower().endswith(".qif"):
                location = os.path.join(root, f)
                relative_location = os.path.relpath(location, upload_folder)
                qif_files.append(relative_location)

    return render_template("qif_tools/start.html", files=qif_files)


@qif_bp.route("/download/<path:filename>")
def download_file(filename):
    """Serve a file for download."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)


@qif_bp.route("/details/<path:filename>")
def qif_details(filename):
    """
    Uses the QIFSummary class to extract all metadata from the QIF file,
    then passes this data to the template for display.
    """
    qif_summary = load_qif_summary(filename)
    metadata = qif_summary.get_summary()

    return render_template("qif_tools/qif_details.html", metadata=metadata)


@qif_bp.route("/compare", methods=["POST"])
def compare_files():
    # Get file names from the form
    file1 = request.form.get("file1")
    file2 = request.form.get("file2")

    logger.debug("Comparing files: %s and %s", file1, file2)
    # Create QIFSummary instances for both files.
    try:
        qif_summary1 = load_qif_summary(file1)
        qif_summary2 = load_qif_summary(file2)
    except Exception as e:
        logger.error("Error creating QIFSummary: %s", e)
        abort(500, f"Error processing files: {e}")

    # Compare the two summaries.
    differences = qif_summary1.compare_to(qif_summary2)
    print(differences)
    logger.debug("Differences: %s", differences)

    # Return the differences as a JSON response.
    return render_template("qif_tools/qiff_diff_results.html", diff=differences)


@qif_bp.route("/search-feature", methods=["POST"])
def search_feature():
    filename = request.form.get("qif_file")
    feature_name = request.form.get("feature_name")

    qif_summary = load_qif_summary(filename)
    chase_result = qif_summary.chase_feature(feature_name)
    print(chase_result)

    # Render a new template that presents chase_result
    return render_template(
        "qif_tools/search_results.html",
        file=filename,
        feature_name=feature_name,
        chase_result=chase_result,
    )


@qif_bp.route("/rawxml/<path:filename>")
def serve_raw_qif_xml(filename):
    """
    Returns the QIF file's raw XML content as text/xml.
    Example usage:
      GET /rawxml/SomeFile.qif
    """
    qif_summary = load_qif_summary(filename)
    # Return the raw XML
    raw_xml = qif_summary.get_raw_xml()
    return Response(raw_xml, mimetype="text/xml")


@qif_bp.route("/dictxml/<path:filename>")
def serve_qif_dict(filename):
    """
    Returns the *entire* QIF XML as a fully traversed nested dict (converted to JSON).
    Potentially large for big QIF files, so use with caution.
    Example usage:
      GET /dictxml/SomeFile.qif
    """
    qif_summary = load_qif_summary(filename)
    data_dict = qif_summary.as_dict()  # full dictionary of the XML
    return jsonify(data_dict)


@qif_bp.route("/summary/<path:filename>")
def serve_qif_summary(filename):
    """
    Returns a 'high-level summary' dict (filename, size, version, top sections, etc.)
    as JSON. This is smaller and faster to generate than the entire dict.

    Example usage:
      GET /summary/SomeFile.qif
    """
    qif_summary = load_qif_summary(filename)
    summary_data = qif_summary.get_summary()
    return jsonify(summary_data)

@qif_bp.route("/visualize/<path:filename>")
def visualize_qif(filename):
    """
    Renders an HTML page running p5.js that fetches the QIF dictionary data
    and does a simple or 'artistic' visualization.
    """
    return render_template("qif_tools/qif_visualize.html", filename=filename)
