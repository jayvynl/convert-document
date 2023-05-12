import logging
import os
import subprocess
import time
from threading import Timer

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
from com.sun.star.lang import DisposedException, IllegalArgumentException

from convert.common import Converter
from convert.util import INSTANCE_DIR
from convert.util import SystemFailure, ConversionFailure

DESKTOP = "com.sun.star.frame.Desktop"
RESOLVER = "com.sun.star.bridge.UnoUrlResolver"
CONNECTION = (
    "socket,host=localhost,port=2002,tcpNoDelay=1;urp;StarOffice.ComponentContext"
)
COMMAND = [
    "/usr/bin/soffice",
    "-env:UserInstallation=file:///%s" % INSTANCE_DIR,
    "-env:JFW_PLUGIN_DO_NOT_CHECK_ACCESSIBILITY=1",
    "--nologo",
    "--headless",
    "--nocrashreport",
    "--nodefault",
    "--norestore",
    "--accept=%s" % CONNECTION,
]

log = logging.getLogger(__name__)


class UnoconvConverter(Converter):
    """Launch a background instance of LibreOffice and convert documents
    to PDF using its filters.
    """

    PDF_FILTERS = (
        ("com.sun.star.text.GenericTextDocument", "writer_pdf_Export"),
        ("com.sun.star.text.WebDocument", "writer_web_pdf_Export"),
        ("com.sun.star.presentation.PresentationDocument", "impress_pdf_Export"),
        ("com.sun.star.drawing.DrawingDocument", "draw_pdf_Export"),
    )

    def start(self):
        with self.lock:
            if self.get_proc():
                log.debug("office is running")
                return
            log.info("Starting LibreOffice: %s", " ".join(COMMAND))
            proc = subprocess.Popen(COMMAND, close_fds=True)
            time.sleep(2)
            log.info("PID: %s; return: %s", proc.pid, proc.returncode)

    def _svc_create(self, ctx, clazz):
        return ctx.ServiceManager.createInstanceWithContext(clazz, ctx)

    def connect(self):
        proc = self.get_proc()
        if proc is None:
            self.start()

        for attempt in range(15):
            try:
                context = uno.getComponentContext()
                resolver = self._svc_create(context, RESOLVER)
                context = resolver.resolve("uno:%s" % CONNECTION)
                return self._svc_create(context, DESKTOP)
            except NoConnectException:
                log.warning("No connection to LibreOffice (%s)", attempt)
                time.sleep(2)
            except DisposedException:
                raise SystemFailure("Bridge is disposed.")
        raise SystemFailure("No connection to LibreOffice")

    def check_healthy(self):
        return self.get_proc() is not None

    def on_timeout(self):
        self.kill()
        raise SystemFailure("LibreOffice timed out.")

    def convert_file(self, infile, outfile, timeout):
        timer = Timer(timeout, self.on_timeout)
        timer.start()
        try:
            return self._timed_convert_file(infile, outfile)
        finally:
            timer.cancel()

    def _timed_convert_file(self, infile, outfile):
        desktop = self.connect()
        try:
            url = uno.systemPathToFileUrl(infile)
            props = self.property_tuple(
                {
                    "Hidden": True,
                    "MacroExecutionMode": 0,
                    "Overwrite": True,
                    "OpenNewView": True,
                    "StartPresentation": False,
                    "RepairPackage": False,
                }
            )
            doc = desktop.loadComponentFromURL(url, "_blank", 0, props)
        except IllegalArgumentException:
            raise ConversionFailure("Cannot open document.")
        except DisposedException:
            raise SystemFailure("Bridge is disposed.")

        if doc is None:
            raise ConversionFailure("Cannot open document.")

        try:
            # Update document indexes
            for ii in range(2):
                # At first, update Table-of-Contents.
                # ToC grows, so page numbers grow too.
                # On second turn, update page numbers in ToC.
                try:
                    doc.refresh()
                    indexes = doc.getDocumentIndexes()
                except AttributeError:
                    # The document doesn't implement the XRefreshable and/or
                    # XDocumentIndexesSupplier interfaces
                    break
                else:
                    for i in range(0, indexes.getCount()):
                        indexes.getByIndex(i).update()

            # save original file.
            prop_dic = {}
            _, ext = os.path.splitext(infile)
            if ext == ".docx":
                prop_dic["FilterName"] = "MS Word 2007 XML"
            doc.storeToURL(url, self.property_tuple(prop_dic))

            output_url = uno.systemPathToFileUrl(outfile)
            prop = self.get_output_properties(doc)
            # log.debug("[%s] refreshed.", file_name)
            doc.storeToURL(output_url, prop)
        except Exception:
            self.kill()
            self.start()
            raise
        finally:
            doc.dispose()
            doc.close(True)
            del doc

        return outfile

    def get_output_properties(self, doc):
        # https://github.com/unoconv/unoconv/blob/master/doc/filters.adoc
        filter_name = "writer_pdf_Export"
        for (service, pdf) in self.PDF_FILTERS:
            if doc.supportsService(service):
                filter_name = pdf
        return self.property_tuple(
            {
                "FilterName": filter_name,
                "Overwrite": True,
                "ReduceImageResolution": True,
                "MaxImageResolution": 300,
                "SelectPdfVersion": 1,
            }
        )

    def property_tuple(self, propDict):
        properties = []
        for k, v in propDict.items():
            prop = PropertyValue()
            prop.Name = k
            prop.Value = v
            properties.append(prop)
        return tuple(properties)
