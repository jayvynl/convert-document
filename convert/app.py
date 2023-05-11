import logging
import tempfile
import warnings

from flask import Flask, request, send_file
from pantomime import FileName, normalize_mimetype, mimetype_extension
from pantomime.types import PDF

from convert.formats import load_mime_extensions
from convert.unoconv import UnoconvConverter
from convert.util import ConversionFailure

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("convert")
extensions = load_mime_extensions()
converter = UnoconvConverter()
app = Flask("convert")


@app.route("/", methods=["POST"])
def convert():
    try:
        timeout = int(request.args.get("timeout", 7200))
        upload = request.files.get("file")
        file_name = FileName(upload.filename)
        mime_type = normalize_mimetype(upload.mimetype)
        if not file_name.has_extension:
            file_name.extension = extensions.get(mime_type)
        if not file_name.has_extension:
            file_name.extension = mimetype_extension(mime_type)
        with tempfile.NamedTemporaryFile(suffix=file_name.extension) as i, \
                tempfile.NamedTemporaryFile(suffix='.pdf') as o:
            log.info("PDF convert: %s [%s]", i.name, mime_type)
            upload.save(i.name)
            out_file = converter.convert_file(i.name, o.name, timeout)
            return send_file(out_file, mimetype=PDF)
    except ConversionFailure as ex:
        converter.kill()
        return str(ex), 400
    except Exception as ex:
        converter.kill()
        log.error("Error: %s", ex)
        return str(ex), 500


@app.route("/healthy")
def check_health():
    try:
        if not converter.check_healthy():
            return "BUSY", 500
        return "OK", 200
    except:
        log.exception("Converter is not healthy.")
        return "DEAD", 500
