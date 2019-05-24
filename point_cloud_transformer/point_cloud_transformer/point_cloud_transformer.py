

import sys
import random
import os.path
import pandas as pd
from PyQt4 import QtGui, QtCore
from pyqtauto.widgets import Dialog, OrphanMessageBox


class PointCloudTransformer(object):
    """The PointCloudTransformer Class is an application that allows users to 
    transform noisey point cloud data into an Autodesk Inventor-friendly format.

    Cross-section points, which are exported as .txt files from PolyWorks 
    Inspector, cannot be used by Autodesk Inventor directly. Upon specifying an
    existing .txt file, this application will clean, subsample (if required), 
    and save the data in .xlsx format, which can be imported directly into 
    Autodesk Inventor sketches.

    """
    def __init__(self):
        super(PointCloudTransformer, self).__init__()
        self.points = []
        self.logic = Logic()
        self.select_file_view = SelectFileDialog()
        self.subsample_view = SubSampleDialog()
        self.start()

    def start(self):
        if self.select_file_view.exec_():
            # Get selected .txt file
            self.filepath = str(self.select_file_view.selectedFiles()[0])

            if self.subsample_view.exec_():
                # Validate user defined subsample
                self.value = self.logic.validate_subsample(
                    self.subsample_view.le.text()
                )

                if self.value:
                    # Transform raw point cloud data into 
                    # Autodesk Inventor-friendly .xlsx document
                    self.logic.transform(self.filepath, self.points, self.value)
                else:
                    self.subsample_view.input_error()


class SubSampleDialog(Dialog):
    """The SubSampleDialog Class queries the user for a value that lies between 
    0 and 1.

    Attributes
    ----------
    value : None or float
        Subsample defined by user.
    le : QLineEdit
    btn : QPushButton

    """
    _WIDTH = 80
    
    def __init__(self):
        super(SubSampleDialog, self).__init__('Settings', 'QFormLayout')
        self.le = QtGui.QLineEdit()
        self.le.setText('1.0')
        self.le.setFixedWidth(self._WIDTH)
        self.btn = QtGui.QPushButton('OK')
        self.btn.setFixedWidth(self._WIDTH)
        self.btn.clicked.connect(self.accept)
        self.le.returnPressed.connect(self.btn.click)
        self.layout.addRow('Subsample:', self.le)
        self.layout.addRow(None, self.btn)

    def input_error(self):
        """Notify user to redefine input correctly."""
        msg = OrphanMessageBox(
            'Warning',
            ['Subsample must be greater than 0 and less than or ',
            'equal to 1.']
            )
        msg.exec_()


class Logic(object):
    """The Logic Class provides the logical backend to the PointCloudTransformer
    Class.

    """
    def __init__(self):
        pass

    def validate_subsample(self, x):
        """
        Parameters
        ----------
        x : QString

		Returns
		-------
	    x : float
			Valid subsample.
		None
			Invalid subsample.
        
        """
        try:
            x = float(x)
        except ValueError:
            # No input received
            return

        if 0.0 < x <= 1.0:
            return x

    def _xlsx_path(self, filepath):
        """
        Parameters
        ----------
        filepath : str
            Valid absolute path to file containing raw point cloud data.

        Returns
        -------
        str
            `filepath` with extension .xlsx.

        """
        head, tail = os.path.split(filepath)
        filename = os.path.splitext(tail)[0]
        return os.path.join(head, filename + '.xlsx')

    def _create_xlsx(self, filepath, data, subsample):
        """Save a given dataset in .xlxs format.

        Parameters
        ----------
		filepath: str
			Valid absolute path to file containing raw point cloud data.
		data : list[list]
        subsample : float
			Fraction of data to retain.
        """
        df = pd.DataFrame(data)
        df = df.sample(frac=subsample, random_state=random.randint(0,10))
        df.to_excel(self._xlsx_path(filepath), header=False, index=False)        

    def _clean_cloud(self, filepath, container):
        """Fill a given container with refined point cloud data from a given 
        file.

        Parameters
        ----------
        filepath : str
            Valid absolute path to file containing raw data.
        container : list
            Empty object.

        Returns
        -------
        container : list[list]
            Contains refined data from `filepath`.
        """
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

    def transform(self, filepath, container, subsample):
        """Clean and save a dataset from a given file per a given subsample in 
        .xlsx format.

        Parameters
        ----------
        filepath : str
            Valid absolute path to file containing raw data.
        container : list
            Empty object.
        subsample: float
            Fraction of data to retain.

        """
        self._clean_cloud(filepath, container)
        self._create_xlsx(filepath, container, subsample)  


class SelectFileDialog(QtGui.QFileDialog):
    """The SelectFileDialog Class provides an interface for defining the .txt
    file which contains raw point cloud data.
    
    """
    def __init__(self):
        super(SelectFileDialog, self).__init__()
        self.setFileMode(QtGui.QFileDialog.AnyFile)
        self.setFilter('Text files (*.txt)')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    root = 'L:\\Division2\\DRAFTING\\PointCloudTransformer\\data\\images'
    icon_dir = os.path.join(root, 'sulzer.png')
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon_dir)))
    PointCloudTransformer()



    



