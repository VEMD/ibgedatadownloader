"""
/***************************************************************************
        begin                : 2021-11-17
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Vinicius Etchebeur Medeiros Dória
        email                : vinicius_etchebeur@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import tarfile
import urllib
import zipfile

from qgis.core import Qgis, QgsProject, QgsTask
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QIcon


class WorkerDownloadManager(QgsTask):
    """Downloads and extracts files from
    zip or tar file in background"""

    # Signals emitted
    textProgress = pyqtSignal(str)  # text for progress dialog
    processResult = pyqtSignal(list)  # process result
    barMax = pyqtSignal(float)  # max number of progress bar

    def __init__(self, iface, desc, listUrls, dirPad, listUnzipOptions):
        """Constructor."""

        # Mother class constructor QgsTask (subclass)
        super(WorkerDownloadManager, self).__init__(desc, flags=QgsTask.CanCancel)

        # Saving references
        self.iface = iface
        self.project = QgsProject.instance()
        self.msgBar = self.iface.messageBar()
        self.listUrls = listUrls
        self.totalUrls = len(self.listUrls)
        self.dirPad = dirPad
        self.pluginIcon = QIcon(":/plugins/ibgedatadownloader/icon.png")
        self.unzip = listUnzipOptions[1] if listUnzipOptions[0] else False
        self.exception = []

    def getFileSize(self, url):
        """Returns file size of the url"""

        u = urllib.request.urlopen(url)
        meta = u.headers
        fileSize = int(meta.get("Content-Length"))
        return fileSize

    def finished(self, result):
        """This function is called automatically when the task is completed and is
        called from the main thread so it is safe to interact with the GUI etc here"""

        if result is False:
            self.msgBar.pushMessage(
                self.tr("Error"),
                self.tr("Oops, something went wrong! Please, contact the developer by e-mail."),
                Qgis.Critical,
                duration=0,
            )
        elif self.exception != []:
            self.msgBar.pushMessage(
                self.tr("Warning"), self.tr("Process partially completed."), Qgis.Warning, duration=0
            )
        else:
            self.msgBar.pushMessage(self.tr("Success"), self.tr("Process completed."), Qgis.Success, duration=0)

    def run(self):
        """Principal method that is automatically called when the task runs."""

        fails = 0
        for n, u in enumerate(self.listUrls):
            url = u[1]
            fileSize = self.getFileSize(url)

            # Adjusting progress bar
            self.barMax.emit(100)

            fileName = os.path.basename(url)
            outFile = os.path.join(self.dirPad, fileName)
            try:
                u = urllib.request.urlopen(url)
            except Exception as e:
                msg = self.tr("Failed to open url {}.").format(url)
                # return False
                self.exception.append(n, url, msg, e)
                fails += 1
                continue

            # Creates directory for product, if it doesn't exists
            if not os.path.isdir(self.dirPad):
                os.makedirs(self.dirPad)

            # Downloading file
            f = open(outFile, "wb")
            msg = self.tr("{n}/{total} - Downloading {file}...").format(n=n + 1, total=self.totalUrls, file=fileName)
            self.textProgress.emit(msg)
            # print "Downloading: %s Bytes: %s" % (outFile, file_size)
            file_size_dl = 0
            block_sz = 8192
            while True:
                # Check if task was canceled by the user
                if self.isCanceled():
                    self.processResult.emit(
                        [
                            self.tr("The process was canceled by the user."),
                            Qgis.Critical,
                            self.exception,
                            url,
                            "download",
                        ]
                    )
                    return True

                buffer = u.read(block_sz)
                if not buffer:
                    break
                file_size_dl += len(buffer)
                f.write(buffer)
                self.setProgress(file_size_dl * 100 / fileSize)
                # status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                # status = status + chr(8)*(len(status)+1)
                # print status,
            f.close()

            # Extracting downloaded files
            if self.unzip and any(fileName.endswith(ext) for ext in (".zip", ".tar")):
                msg = self.tr("{n}/{total} - Extracting files from {file}...").format(
                    n=n + 1, total=self.totalUrls, file=fileName
                )
                self.textProgress.emit(msg)
                if fileName.endswith("zip"):
                    # Extract zip file
                    with zipfile.ZipFile(os.path.join(self.dirPad, fileName), "r") as zip_ref:
                        zip_ref.extractall(self.dirPad)
                else:
                    # Extract tar file
                    with tarfile.open(os.path.join(self.dirPad, fileName), "r") as tar_ref:
                        tar_ref.extractall(self.dirPad)

        self.processResult.emit(
            [
                self.tr(
                    'Process completed with {fails} fails. Check your file(s) at <a href="{saida}">{saida}</a>.'
                ).format(fails=fails, saida=self.dirPad),
                Qgis.Success,
                self.exception,
                self.listUrls,
                "download",
            ]
        )
        return True
