import sys
import os
import subprocess
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QTableWidget, QTableWidgetItem, QProgressBar, 
                            QMessageBox, QLineEdit, QSplitter, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QCursor

class ADBWorker(QThread):
    deviceFound = pyqtSignal(list)
    transferComplete = pyqtSignal(bool, str)
    fileListComplete = pyqtSignal(list)
    operationComplete = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.mode = "scan"  # scan, transfer, list_files, delete
        self.transfer_data = None
        self.current_device = None
        self.target_path = None
        self.file_to_delete = None
        
    def run(self):
        if self.mode == "scan":
            self.scan_devices()
        elif self.mode == "transfer":
            self.transfer_file()
        elif self.mode == "list_files":
            self.list_files()
        elif self.mode == "delete":
            self.delete_file()
    
    def scan_devices(self):
        try:
            result = subprocess.check_output(['adb', 'devices']).decode('utf-8')
            devices = []
            for line in result.split('\n')[1:]:
                if '\t' in line:
                    device_id, status = line.split('\t')
                    if status.strip() == 'device':
                        devices.append(device_id)
            self.deviceFound.emit(devices)
        except Exception as e:
            self.deviceFound.emit([])
            
    def transfer_file(self):
        try:
            device_id, src_path, dest_path = self.transfer_data
            command = ['adb', '-s', device_id, 'push', src_path, dest_path]
            result = subprocess.check_output(command).decode('utf-8')
            self.transferComplete.emit(True, "Dosya başarıyla transfer edildi!")
        except Exception as e:
            self.transferComplete.emit(False, f"Hata: {str(e)}")
            
    def list_files(self):
        try:
            command = ['adb', '-s', self.current_device, 'shell', 'ls', '-la', self.target_path]
            result = subprocess.check_output(command).decode('utf-8')
            files = []
            for line in result.split('\n'):
                if line.strip():
                    # ls -la çıktısını daha doğru parse edelim
                    try:
                        parts = line.split()
                        if len(parts) >= 8:  # en az 8 parça olmalı (izinler, boyut, tarih, saat ve dosya adı)
                            perms = parts[0]
                            size = parts[4]
                            date = parts[5]
                            # Dosya adını kalan tüm parçaları birleştirerek alalım
                            name = ' '.join(parts[7:])  # Saat kısmından sonraki tüm parçaları birleştir
                            if name not in [".", ".."]:
                                files.append({
                                    'name': name,
                                    'size': size,
                                    'date': date,
                                    'permissions': perms
                                })
                    except Exception as e:
                        print(f"Line parse error: {e}")
                
            self.fileListComplete.emit(files)
        except Exception as e:
            print(f"List files error: {e}")
            self.fileListComplete.emit([])
            
    def delete_file(self):
        try:
            # Sadece dosya adını kullanarak silme işlemi yap
            file_path = os.path.join(self.target_path, self.file_to_delete)
            file_path = file_path.replace('\\', '/').replace('//', '/')
            
            # Debug için komut çıktısını yazdır
            print(f"Delete command: rm -f '{file_path}'")
            
            command = ['adb', '-s', self.current_device, 'shell', f"rm -f '{file_path}'"]
            result = subprocess.check_output(command, stderr=subprocess.STDOUT)
            print(f"Delete result: {result.decode('utf-8')}")
            
            self.operationComplete.emit(True, "Dosya başarıyla silindi!")
        except Exception as e:
            print(f"Delete error: {e}")
            self.operationComplete.emit(False, f"Silme hatası: {str(e)}")

class FileManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adb Dosya Yöneticisi")
        self.setMinimumSize(1000, 600)
        self.selected_file = ""
        self.current_device = None
        self.initUI()
        
        self.worker = ADBWorker()
        self.worker.deviceFound.connect(self.update_device_list)
        self.worker.transferComplete.connect(self.transfer_completed)
        self.worker.fileListComplete.connect(self.update_file_list)
        self.worker.operationComplete.connect(self.operation_completed)
        
        self.scan_devices()
        
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Üst bölüm - Dosya seçimi ve hedef yol
        top_layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        file_layout.addWidget(QLabel("PC'den Yüklenecek Dosya:"))
        file_layout.addWidget(self.file_path_label)
        select_file_btn = QPushButton("Dosya Seç")
        select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_file_btn)
        top_layout.addLayout(file_layout)
        
        dest_layout = QHBoxLayout()
        self.dest_path_edit = QLineEdit("/storage/emulated/0/")
        dest_layout.addWidget(QLabel("Hedef Yol:"))
        dest_layout.addWidget(self.dest_path_edit)
        refresh_path_btn = QPushButton("Klasörü Yenile")
        refresh_path_btn.clicked.connect(self.refresh_file_list)
        dest_layout.addWidget(refresh_path_btn)
        top_layout.addLayout(dest_layout)
        
        main_layout.addLayout(top_layout)
        
        # Alt bölüm - Cihazlar ve dosya listesi
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Cihaz listesi
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)
        device_layout.addWidget(QLabel("Bağlı Cihazlar"))
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(3)
        self.device_table.setHorizontalHeaderLabels(["Cihaz ID", "Durum", "İşlem"])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        device_layout.addWidget(self.device_table)
        splitter.addWidget(device_widget)
        
        # Dosya listesi
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.addWidget(QLabel("Hedef Klasördeki Dosyalar"))

        # Dosya aktarma butonu ekleniyor
        transfer_button = QPushButton("Seçili Dosyayı Aktar")
        transfer_button.clicked.connect(lambda: self.start_transfer(self.current_device))
        file_layout.addWidget(transfer_button)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Dosya Adı", "Boyut", "Tarih", "İzinler"])
        self.file_table.horizontalHeader().setStretchLastSection(True)
        self.file_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_context_menu)
        file_layout.addWidget(self.file_table)
        splitter.addWidget(file_widget)
        
        
        main_layout.addWidget(splitter)
        
        # Alt butonlar
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton("Cihazları Yenile")
        refresh_btn.clicked.connect(self.scan_devices)
        button_layout.addWidget(refresh_btn)
        main_layout.addLayout(button_layout)
        
        # Durum çubuğu
        self.status_bar = self.statusBar()
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
        
        
    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = QAction("Sil", self)
        delete_action.triggered.connect(self.delete_selected_file)
        menu.addAction(delete_action)
        
        download_action = QAction("PC'ye İndir", self)
        download_action.triggered.connect(self.download_selected_file)
        menu.addAction(download_action)
        
        menu.exec(self.file_table.mapToGlobal(position))
        
    def delete_selected_file(self):
        if not self.current_device:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cihaz seçin!")
            return
            
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            file_name = self.file_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Onay", 
                                       f"{file_name} dosyasını silmek istediğinizden emin misiniz?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.mode = "delete"
                self.worker.current_device = self.current_device
                self.worker.target_path = self.dest_path_edit.text()
                self.worker.file_to_delete = file_name
                self.worker.start()
                
    def download_selected_file(self):
        if not self.current_device:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cihaz seçin!")
            return
            
        current_row = self.file_table.currentRow()
        if current_row >= 0:
            file_name = self.file_table.item(current_row, 0).text()
            save_path, _ = QFileDialog.getSaveFileName(self, "Dosyayı Kaydet", file_name)
            if save_path:
                try:
                    source_path = os.path.join(self.dest_path_edit.text(), file_name)
                    command = ['adb', '-s', self.current_device, 'pull', source_path, save_path]
                    subprocess.check_output(command)
                    QMessageBox.information(self, "Başarılı", "Dosya başarıyla indirildi!")
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"İndirme hatası: {str(e)}")
        
    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Dosya Seç")
        if file_name:
            self.selected_file = file_name
            self.file_path_label.setText(file_name)
            
    def scan_devices(self):
        self.status_bar.showMessage("Cihazlar taranıyor...")
        self.worker.mode = "scan"
        self.worker.start()
        
    def refresh_file_list(self):
        if not self.current_device:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cihaz seçin!")
            return
            
        self.worker.mode = "list_files"
        self.worker.current_device = self.current_device
        self.worker.target_path = self.dest_path_edit.text()
        self.worker.start()
        
    def update_device_list(self, devices):
        self.device_table.setRowCount(0)
        for device_id in devices:
            row_position = self.device_table.rowCount()
            self.device_table.insertRow(row_position)
            
            # Cihaz ID
            self.device_table.setItem(row_position, 0, QTableWidgetItem(device_id))
            
            # Durum
            self.device_table.setItem(row_position, 1, QTableWidgetItem("Hazır"))
            
            # İşlem butonu
            select_btn = QPushButton("Seç ve Listele")
            select_btn.clicked.connect(lambda checked, d=device_id: self.select_device(d))
            self.device_table.setCellWidget(row_position, 2, select_btn)
            
        self.status_bar.showMessage(f"{len(devices)} cihaz bulundu")
        
    def select_device(self, device_id):
        self.current_device = device_id
        self.status_bar.showMessage(f"Seçili cihaz: {device_id}")
        self.refresh_file_list()
        
    def update_file_list(self, files):
        self.file_table.setRowCount(0)
        for file_info in files:
            row_position = self.file_table.rowCount()
            self.file_table.insertRow(row_position)
            
            # Dosya adını olduğu gibi göster
            name_item = QTableWidgetItem(file_info['name'])
            self.file_table.setItem(row_position, 0, name_item)
            self.file_table.setItem(row_position, 1, QTableWidgetItem(file_info['size']))
            self.file_table.setItem(row_position, 2, QTableWidgetItem(file_info['date']))
            self.file_table.setItem(row_position, 3, QTableWidgetItem(file_info['permissions']))
            
    def operation_completed(self, success, message):
        if success:
            QMessageBox.information(self, "Başarılı", message)
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "Hata", message)
            
    def start_transfer(self, device_id):
        if not self.selected_file:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir dosya seçin!")
            return
            
        dest_path = self.dest_path_edit.text()
        if not dest_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen hedef yolu belirtin!")
            return
            
        self.worker.mode = "transfer"
        self.worker.transfer_data = (device_id, self.selected_file, dest_path)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.worker.start()
        
    def transfer_completed(self, success, message):
        self.progress_bar.hide()
        if success:
            QMessageBox.information(self, "Başarılı", message)
            self.refresh_file_list()
        else:
            QMessageBox.critical(self, "Hata", message)
    def start_transfer(self, device_id):
        if not device_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir cihaz seçin!")
            return
            
        if not self.selected_file:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir dosya seçin!")
            return
            
        dest_path = self.dest_path_edit.text()
        if not dest_path:
            QMessageBox.warning(self, "Uyarı", "Lütfen hedef yolu belirtin!")
            return
            
        self.worker.mode = "transfer"
        self.worker.transfer_data = (device_id, self.selected_file, dest_path)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.worker.start()

def main():
    app = QApplication(sys.argv)
    window = FileManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()