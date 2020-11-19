#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import random
import os.path
import pandas as pd
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import Dialog, OrphanMessageBox, DialogButtonBox


__author__ = 'Brandon McCleary'



# Pulled from Nucleus app, consider adding to pyqtauto.
def update_feedback_label(label, text=None, valid=False):
	"""Change the appearance of a ``QLabel`` that displays input feedback.

	If `valid` is False, `text` is ignored and the `label` text will default 
	to an error message.

	Parameters
	----------
	label : QLabel
		``QLabel`` whose text will display feedback.
	text : None or str, optional
		Feedback value, only needed if `valid` is True.
	valid : {False, True}, optional
		Specifies whether the update is a response to valid input.

	"""
	if valid:
		# Set color to black and show text
		label.setStyleSheet('color : rgb(0,0,0)')
		label.setText(text)
	else:
		# Set color to red and show error 
		label.setStyleSheet('color : rgb(255,0,0)')
		label.setText('***')


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS,
        # and places our data files in a folder relative to that temp
        # folder named as specified in the datas tuple in the spec file
        base_path = os.path.join(sys._MEIPASS, 'data')
    except Exception:
        # sys._MEIPASS is not defined, so use the original path
        base_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'data', 
                'images'
        )
    return os.path.join(base_path, relative_path)


class PointCloudConverter(object):
    """
    PointCloudConverter is an application that allows users to transform 
    noisey point cloud data into an Autodesk Inventor-friendly format.
    Cross-section points, which are exported as TXT files from PolyWorks 
    Inspector, cannot be used by Autodesk Inventor directly. Upon specifying an
    existing TXT file, this application will clean, subsample (if required), 
    and save the data in XLSX format, which can be imported directly into 
    Autodesk Inventor 2D sketches.

    """
    def __init__(self):
        super(PointCloudConverter, self).__init__()
        self.logic = Logic()
        self.select_view = SelectFileDialog()
        self.sub_view = SubSampleDialog()
        self.sub_view.le.textChanged.connect(self.update_hint)
        self.start()

    def start(self):
        """Run program."""
        if self.select_view.exec_():
            # Get selected TXT file
            self.filepath = str(self.select_view.selectedFiles()[0])

            self.update_hint()

            if self.sub_view.exec_():
                if self.logic.validate_sub(self.sub_view.subsample) is not None:
                    # Transform raw point cloud data into Autodesk 
                    # Inventor-friendly XLSX document
                    self.logic.transform(self.filepath, self.sub_view.subsample)
                else:
                    self.sub_view.input_error()

    def update_hint(self):
        """Show subsample point count feedback."""
        try:
            count = self.logic.preview(self.filepath, self.sub_view.subsample)
            update_feedback_label(
                self.sub_view.point_count_lb, '%s points' % str(count), 
                True
            )
        except ValueError:
            update_feedback_label(self.sub_view.point_count_lb)


class SubSampleDialog(Dialog):
    """
    Prompts the user for a value that lies between 0 and 1.

    Attributes
    ----------
    subsample
    point_cloud_lb : QLabel

    """
    def __init__(self):
        super(SubSampleDialog, self).__init__('Settings', 'QVBoxLayout')
        self.le = QtGui.QLineEdit()
        self.le.setText('1.0')
        self.point_count_lb = QtGui.QLabel()
        self._wid_layout = QtGui.QHBoxLayout()
        self._wid_layout.addWidget(QtGui.QLabel('Subsample:'))
        self._wid_layout.addWidget(self.le)
        self._wid_layout.addWidget(self.point_count_lb)
        self.layout.addLayout(self._wid_layout)
        self._btn = DialogButtonBox(self.layout)
        self._btn.accepted.connect(self.accept)
        self.le.returnPressed.connect(self._btn.accepted)

    @property
    def subsample(self):
        """float: The user-defined subsample value."""
        return float(self.le.text())

    def input_error(self):
        """Prompt user to redefine input correctly."""
        msg = OrphanMessageBox(
            'Warning',
            ['Subsample must be greater than 0 and less than or ',
            'equal to 1.']
            )
        msg.exec_()


class Logic(object):
    """
    The ``PointCloudConverter`` logic layer.

    """
    def __init__(self):
        pass

    def validate_sub(self, x):
        """
        Parameters
        ----------
        x : str

        Returns
        -------
        x : float
            A validated subsample value.
        None
            If subsample value is invalid.
        
        """
        try:
            x = float(x)
        except ValueError:
            # No input received
            return

        if 0.0 < x <= 1.0:
            return x

    def _xlsx_path(self, filepath):
        """Modify a filepath to have an XLSX extension.

        Parameters
        ----------
        filepath : str
            A valid absolute path to the file containing raw point cloud data.

        Returns
        -------
        str
            `filepath` with extension .xlsx.

        """
        head, tail = os.path.split(filepath)
        filename = os.path.splitext(tail)[0]
        return os.path.join(head, filename + '.xlsx')

    def preview(self, filepath, subsample):
        """Get the number of point pairs after subsampling a dataset.

        Parameters
        ----------
        filepath : str
            A valid absolute path to the raw data file.
        subsample : float
            The fraction of data to retain.

        Returns
        -------
        point_count : int

        """
        points = self.cleaned_cloud(filepath)
        point_count = self.point_data(points, subsample)[0]
        return point_count

    def point_data(self, data, subsample):
        """Subsample a DataFrame and count the number of point pairs.

        Parameters
        ----------
        data : list
            Contains lists of X, Y, Z coordinate values.
        subsample : float
            The fraction of data to retain.

        Returns
        -------
        int
            The number of point pairs.
        df : DataFrame
            A subsampled ``DataFrame`` derived from `data`.

        """
        df = pd.DataFrame(data)
        df = df.sample(frac=subsample, random_state=random.randint(0,10))
        return len(df.index), df

    def _create_xlsx(self, filepath, data, subsample):
        """Save a given dataset in XLSX format.

        Parameters
        ----------
        filepath: str
            A valid absolute path to the file containing raw point cloud data.
        data : list
            Contains lists of X, Y, Z coordinate values.
        subsample : float
            The fraction of data to retain.
            
        """
        df = self.point_data(data, subsample)[1]
        df.to_excel(self._xlsx_path(filepath), header=False, index=False)        

    def cleaned_cloud(self, filepath):
        """Get a refined point cloud dataset.

        Parameters
        ----------
        filepath : str
            A valid absolute path to the raw data file.

        Returns
        -------
        container : list
            Contains lists of X, Y, Z coordinate values.
            
        """
        container = []
        with open(filepath, 'rb') as f:
            for line in f:
                if line[0] == '#':
                    # Ignore indication of noisey data
                    pass
                else:
                    row = line.split(',')
                    # Remove the unnecessary string from the Z value that is 
                    # inherited through this string manipulation.
                    row[2] = row[2].replace('\r\n', '')
                    container.append(row)
        return container

    def transform(self, filepath, subsample):
        """Clean and save a TXT dataset in XLSX format.

        Parameters
        ----------
        filepath : str
            A valid absolute path to the raw data file.
        subsample: float
            The fraction of data to retain.

        """
        data = self.cleaned_cloud(filepath)
        self._create_xlsx(filepath, data, subsample)  


class SelectFileDialog(QtGui.QFileDialog):
    """
    Prompts the user to select the TXT file that contains raw point cloud data.
    
    """
    def __init__(self):
        super(SelectFileDialog, self).__init__()
        self.setFileMode(QtGui.QFileDialog.AnyFile)
        self.setFilter('Text files (*.txt)')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(resource_path('sulzer.png'))))
    PointCloudConverter()



    



