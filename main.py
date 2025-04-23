import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QLabel, QApplication, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeyEvent
import sys

# import multi_agentic_chatbot as chat_bot  # Make sure this module exists
from rag import get_ready_with_pdf, query_function


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()

        # Load UI
        try:
            uic.loadUi('resources/rag.ui', self)
        except Exception as e:
            print(f"Error loading UI file: {e}")
            sys.exit(1)
        self.message_lbl.setText("🔴   Browse Pdf")

        self.browse_book_lbl.mousePressEvent = self.browse_pdf
        self.querry_lbl.mousePressEvent = self.call_llm
        # self.showFullScreen()  # This makes the window full screen
        self.setFixedSize(1920, 1080)  # Set the fixed size of the window

        self.show()


    def handle_key_press(self, event: QKeyEvent):
        """Handles key press events to trigger chatbot when Enter is pressed or insert new line with Shift+Enter"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() == Qt.ShiftModifier:
                # Allow Shift+Enter to insert a new line in QTextEdit
                QtWidgets.QTextEdit.keyPressEvent(self.user_prompt_txtedit, event)
            else:
                # Run chatbot on Enter without Shift
                self.call_llm()
        else:
            # Allow other key presses (like typing)
            QtWidgets.QTextEdit.keyPressEvent(self.user_prompt_txtedit, event)

    def call_llm(self, event):
        # Step 2: Ask your query
        user_prompt = self.user_prompt_txtedit.toPlainText().strip()
        answer = query_function(user_prompt)
        print("Answer:\n", answer)
        
        # Show response in the label
        self.response_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.response_lbl.setText(answer)

    def browse_pdf(self, event):
        self.message_lbl.setText("🔴   Compiling...")
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select a PDF file",
            "",
            "PDF Files (*.pdf)"
        )
        if file_path:
            get_ready_with_pdf(file_path)
        self.message_lbl.setText("🟢   Ready")
        




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle("Retrieval-Augmented Generation")
    sys.exit(app.exec_())
