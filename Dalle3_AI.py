import sys
import requests
import openai
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QStatusBar, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ImageGenerationThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, client, description):
        QThread.__init__(self)
        self.client = client
        self.description = description

    def run(self):
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=self.description,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
            self.finished.emit(image_url)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.openai_client = openai.Client(api_key="API KEY HERE")  # Initialize OpenAI client: Add OpenAI API key in this section
        self.current_image_url = None  # Variable to store the current image URL

    def initUI(self):
        self.setWindowTitle('AI Image Generator 2.0')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(20, 20, 20), stop:1 rgb(70, 70, 70));")

        main_layout = QHBoxLayout(central_widget)

        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("background-color: rgb(0, 55, 110); color: white;")  # Dark light blue background with white text
        chat_layout.addWidget(self.chat_display)

        self.image_description_box = QTextEdit(self)
        self.image_description_box.setFixedHeight(150)
        self.image_description_box.setStyleSheet("background-color: rgb(0, 55, 110); color: white;")  # Dark light blue background with white text
        chat_layout.addWidget(self.image_description_box)

        image_layout = QVBoxLayout()
        self.image_display = QLabel(self)
        self.image_display.setMinimumSize(400, 400)

        generate_image_button = QPushButton('Generate Image', self)
        generate_image_button.setStyleSheet("background-color: rgb(211, 211, 211);")  # Light gray background for the button
        generate_image_button.clicked.connect(self.generate_image)

        download_image_button = QPushButton('Download Image', self)
        download_image_button.setStyleSheet("background-color: rgb(211, 211, 211);")  # Light gray background for the button
        download_image_button.clicked.connect(self.download_image)

        image_layout.addWidget(self.image_display)
        image_layout.addWidget(generate_image_button)
        image_layout.addWidget(download_image_button)

        main_layout.addLayout(chat_layout)
        main_layout.addLayout(image_layout)

        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.showMessage('Ready')

    def generate_image(self):
        image_description = self.image_description_box.toPlainText()
        self.update_chat_display(f"User (Image Request): {image_description}")
        self.update_chat_display("Generating image, please wait...")
        self.thread = ImageGenerationThread(self.openai_client, image_description)
        self.thread.finished.connect(self.on_image_generated)
        self.thread.start()

    def on_image_generated(self, result):
        if "Error:" in result:
            self.update_chat_display(result)
        else:
            self.display_image(result)
        self.image_description_box.clear()

    def display_image(self, image_url):
        self.current_image_url = image_url
        response = requests.get(image_url)
        if response.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.image_display.setPixmap(pixmap.scaled(self.image_display.width(), self.image_display.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.chat_display.append("Error: Unable to load image from URL.\n")

    def update_chat_display(self, message):
        self.chat_display.append(message +"\n")

    def download_image(self):
        if self.current_image_url:
            options = QFileDialog.Options()
            filename, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg *.jpeg);;All Files (*)", options=options)
            if filename:
                with open(filename, 'wb') as file:
                    file.write(requests.get(self.current_image_url).content)
                self.chat_display.append(f"Image saved as {filename}\n")
        else:
            self.chat_display.append("No image to download.\n")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ChatApp()
    ex.show()
    sys.exit(app.exec_())
