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
import xmlschema
from lxml import etree
from .qifsummary import QIFSummary

base_dir = os.path.join(os.getcwd(), "QIF3.0-2018-ANSI", "xsd", "QIFApplications")
schema_path = os.path.join(base_dir, "QIFDocument.xsd")

# schema_obj = xmlschema.XMLSchema(schema_path, base_url=base_dir)

schema_doc = etree.parse(schema_path)
schema_obj = etree.XMLSchema(schema_doc)

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
    qif_files = []
    for root, dirs, files in os.walk(upload_folder):
        for f in files:
            if f.lower().endswith(".qif"):
                location = os.path.join(root, f)
                relative_location = os.path.relpath(location, upload_folder)
                print(relative_location)
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
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)
    print(filepath)
    if not os.path.exists(filepath):
        abort(404, "File not found.")
    qif_summary = QIFSummary(filepath, schema_obj)
    metadata = qif_summary.get_summary()
    return render_template("qif_tools/qif_details.html", metadata=metadata)
