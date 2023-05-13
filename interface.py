import os
import sys
from PyQt5 import QtWidgets, uic, QtCore

class UpscaleThread(QtCore.QThread):
    progress_update = QtCore.pyqtSignal(int)

    def __init__(self, image_path, model, scale, output_path):
        super().__init__()
        self.image_path = image_path
        self.model = model
        self.scale = scale
        self.output_path = output_path

    def run(self):
        command = f'realesrgan-ncnn-vulkan.exe -i "{self.image_path}" -o "{self.output_path}" -s {self.scale} -g 0 -n {self.model} -x -f png'
        process = QtCore.QProcess()
        process.startDetached(command)

        while process.state() == QtCore.QProcess.Running:
            progress = int(process.readAllStandardOutput().split(b'progress: ')[-1].split(b'%')[0])
            self.progress_update.emit(progress)

        if process.exitCode() != 0:
            self.progress_update.emit(-1)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('interface.ui', self)
        self.select_image_button.clicked.connect(self.select_image)
        self.process_image_button.clicked.connect(self.process_image)
        self.progress_dialog = QtWidgets.QProgressDialog(self)
        self.progress_dialog.setLabelText('Processando imagem...')
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.setMinimum(0)
        self.progress_dialog.setMaximum(100)
        self.progress_dialog.setValue(0)

    def select_image(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Selecionar imagem", "",
                                                             "Imagens (*.png *.jpg *.jpeg *.bmp)", options=options)
        if file_name:
            self.image_path.setText(file_name)

    def process_image(self):
        image_path = self.image_path.text()
        if not os.path.isfile(image_path):
            QtWidgets.QMessageBox.warning(self, "Erro", "Selecione uma imagem válida.")
            return
        model = "realesrgan-x4plus-anime"
        scale = "4"
        output_path = os.path.splitext(image_path)[0] + "_upscaled.png"

        # Cria uma nova thread para executar o processo de upscaling
        self.thread = UpscaleThread(image_path, model, scale, output_path)
        self.thread.progress_update.connect(self.update_progress)
        self.progress_dialog.show()
        self.thread.start()

    def update_progress(self, progress):
        if progress == -1:
            QtWidgets.QMessageBox.warning(self, "Erro", "Ocorreu um erro durante o processamento da imagem.")
            self.progress_dialog.close()
            return
        self.progress_dialog.setValue(progress)
        if progress == 100:
            self.status_label.setText('Status: Imagem processada com sucesso.')
            self.progress_dialog.close()

    def closeEvent(self, event):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
