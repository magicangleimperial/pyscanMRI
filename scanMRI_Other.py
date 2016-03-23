from os import path
from datetime import date
from time import time
from PyQt5.QtWidgets import QFileDialog
from numpy import absolute, uint16, save
from dicom.dataset import Dataset, FileDataset

'''                 Class to save image
########################################################################
PNG or Dicom can be used
########################################################################
'''


def Save_Image(self):
    title = 'Save Image'
    files_types = "PNG (*.png);;DICOM (*.dcm)"
    pathd = path.dirname(path.abspath(__file__)) + "/Image"
    filename = QFileDialog.getSaveFileName(self, title, pathd, files_types)[0]
    canvas = self.ui.matplotwidget.canvas
    if filename.find(".png") != -1:
        canvas.fig.savefig(filename, bbox_inches='tight', pad_inches=0)
    if filename.find(".dcm") != -1:
        if canvas.data is not None:
            number_slice = len(canvas.data[0, 0, :])
            for i in range(number_slice):
                data_abs = absolute(canvas.data[:, :, i])
                pix_ar = data_abs / data_abs.max() * 65385.0
                if pix_ar.dtype != uint16:
                    pix_ar = pix_ar.astype(uint16)
                if number_slice > 1:
                    filename_dicom = filename[:-4] + " - %i" % i + ".dcm"
                    write_dicom(pix_ar, filename_dicom)
                    save(filename_dicom[:-4] + "-kspace", canvas.kspace_data)
                else:
                    write_dicom(pix_ar, filename)
                    save(filename[:-4] + "-kspace", canvas.kspace_data)


'''                 Class to define DICOM metadata
########################################################################
Only some metadata are implemented, to show the principle.
########################################################################
'''


def write_dicom(pixel_array, filename):
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
    file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684'
    file_meta.MediaStorageSOPInstanceUID += '411017669021768385720736873780'
    file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0"*128)
    ds.Modality = 'MR'
    ds.ContentDate = str(date.today()).replace('-', '')
    ds.ContentTime = str(time())
    ds.StudyInstanceUID = '1.3.6.1.4.1.9590.100.1.1.1243139774123601752342712'
    ds.StudyInstanceUID += '87472804872093'
    ds.SeriesInstanceUID = '1.3.6.1.4.1.9590.100.1.1.369231118011061003403421'
    ds.SeriesInstanceUID += '859172643143649'
    ds.SOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385'
    ds.SOPInstanceUID += '720736873780'
    ds.SOPClassUID = 'Secondary Capture Image Storage'
    ds.SecondaryCaptureDeviceManufctur = 'Python 3.3.5'
    # Options
    ds.InstitutionName = "Imperial College London"
    ds.RepetitionTime = 300
    # These are the necessary imaging components of the FileDataset object.
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0
    ds.HighBit = 15
    ds.BitsStored = 16
    ds.BitsAllocated = 16
    ds.Columns = pixel_array.shape[1]
    ds.Rows = pixel_array.shape[0]
    ds.PixelData = pixel_array.tostring()
    ds.save_as(filename)

    return 0
