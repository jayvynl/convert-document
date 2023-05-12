import logging
import tempfile
import warnings
import zipfile

from flask import Flask, request, send_file
from pantomime import FileName, normalize_mimetype, mimetype_extension
from pantomime.types import PDF

from convert.formats import load_mime_extensions
from convert.unoconv import UnoconvConverter

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(process)s] [%(name)s:%(lineno)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("convert")
extensions = load_mime_extensions()
converter = UnoconvConverter()
app = Flask("convert")


@app.route("/", methods=["POST"])
def convert():
    upload = request.files.get("file")
    update = request.form.get("update")
    timeout = int(request.form.get("timeout", 7200))
    file_name = FileName(upload.filename)
    mime_type = normalize_mimetype(upload.mimetype)
    if not file_name.has_extension:
        file_name.extension = extensions.get(mime_type)
    if not file_name.has_extension:
        file_name.extension = mimetype_extension(mime_type)
    with tempfile.NamedTemporaryFile(suffix=f'.{file_name.extension}') as i, \
            tempfile.NamedTemporaryFile(suffix='.pdf') as o:
        log.info("PDF convert: %s [%s]", i.name, mime_type)
        upload.save(i.name)
        out_file = converter.convert_file(i.name, o.name, timeout)
        if update in ["True", "true", "on", "yes", "1"]:
            with tempfile.NamedTemporaryFile(suffix='.zip') as z:
                with zipfile.ZipFile(z.file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(i.name, f'in.{file_name.extension}')
                    zf.write(o.name, 'out.pdf')
                return send_file(z.name)
        return send_file(out_file, mimetype=PDF)


@app.route("/healthy")
def check_health():
    if not converter.check_healthy():
        return "BUSY", 500
    return "OK", 200
