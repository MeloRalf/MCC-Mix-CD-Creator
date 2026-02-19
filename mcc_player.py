import sys
import os
import pygame
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QFrame, QFileDialog, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class MCCFinal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MCC - Digital Mix CD Master")
        self.resize(1000, 700)
        
        # --- ICON PROTECTION ---
        # If the icon exists, use it. If not, don't crash.
        icon_path = os.path.join(os.getcwd(), "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Folder Setup
        self.mix_folder = os.path.join(os.getcwd(), "My_DMC_Mixes")
        if not os.path.exists(self.mix_folder):
            os.makedirs(self.mix_folder)

        pygame.mixer.init()
        self.playlist = []
        self.current_index = -1
        self.is_paused = False

        # --- Y2K Glossy Skin ---
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8dbbe0, stop:1 #d7e8f5); }
            #LibraryArea { 
                background-color: black; 
                border: 2px solid #333; 
                border-radius: 10px; 
                color: #00ff00;
                font-size: 16px;
            }
            #Sidebar { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #c9e0f2); border-left: 2px solid #a0b0c0; }
            QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fcfcfc, stop:1 #d0d0d0); 
                border: 1px solid #777; border-radius: 10px; padding: 8px; font-weight: bold; 
            }
            QPushButton:hover { background: #e5f1fb; border-color: #0078d7; }
            #PlayBtn { background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #5db1ff, stop:1 #004a8d); color: white; border-radius: 25px; min-width: 50px; min-height: 50px; font-size: 18px; }
            #PauseBtn { background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #ffb347, stop:1 #ff6600); color: white; border-radius: 25px; min-width: 50px; min-height: 50px; font-size: 18px; }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- UI Construction ---
        self.top_menu = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 REFRESH LIBRARY")
        self.btn_refresh.clicked.connect(self.load_installed_mixes)
        self.btn_save = QPushButton("💾 SAVE CURRENT DMC")
        self.btn_save.clicked.connect(self.save_current_mix)
        self.top_menu.addWidget(self.btn_refresh)
        self.top_menu.addWidget(self.btn_save)
        self.top_menu.addStretch()
        self.main_layout.addLayout(self.top_menu)

        self.mid_layout = QHBoxLayout()
        self.library_widget = QListWidget(); self.library_widget.setObjectName("LibraryArea")
        self.library_widget.itemDoubleClicked.connect(self.load_selected_mix)
        
        self.lib_container = QVBoxLayout()
        self.lib_label = QLabel("INSTALLED MIXES (.mix)")
        self.lib_label.setStyleSheet("color: white; background: black; font-weight: bold; padding: 5px;")
        self.lib_container.addWidget(self.lib_label)
        self.lib_container.addWidget(self.library_widget)
        
        self.mid_layout.addLayout(self.lib_container, 3)

        self.sidebar = QFrame(); self.sidebar.setObjectName("Sidebar")
        self.side_layout = QVBoxLayout(self.sidebar)
        self.track_list_widget = QListWidget()
        self.side_layout.addWidget(QLabel("<b>CURRENT MIX CONTENT</b>"))
        self.side_layout.addWidget(self.track_list_widget)
        
        self.btn_add = QPushButton("+ ADD TRACKS")
        self.btn_add.clicked.connect(self.add_songs)
        self.side_layout.addWidget(self.btn_add)
        self.mid_layout.addWidget(self.sidebar, 1)
        self.main_layout.addLayout(self.mid_layout)

        self.ctrl_layout = QHBoxLayout()
        self.btn_prev = QPushButton("⏮"); self.btn_prev.clicked.connect(self.prev_song)
        self.btn_play = QPushButton("▶"); self.btn_play.setObjectName("PlayBtn"); self.btn_play.clicked.connect(self.play_song)
        self.btn_pause = QPushButton("⏸"); self.btn_pause.setObjectName("PauseBtn"); self.btn_pause.clicked.connect(self.pause_song)
        self.btn_next = QPushButton("⏭"); self.btn_next.clicked.connect(self.next_song)
        
        self.ctrl_layout.addStretch()
        self.ctrl_layout.addWidget(self.btn_prev)
        self.ctrl_layout.addWidget(self.btn_play)
        self.ctrl_layout.addWidget(self.btn_pause)
        self.ctrl_layout.addWidget(self.btn_next)
        self.ctrl_layout.addStretch()
        self.main_layout.addLayout(self.ctrl_layout)

        self.load_installed_mixes()

    # --- THE FIXED LOGIC ---
    def load_installed_mixes(self):
        self.library_widget.clear()
        if not os.path.exists(self.mix_folder): return
        for file in os.listdir(self.mix_folder):
            if file.endswith(".mix"):
                self.library_widget.addItem(file)

    def save_current_mix(self):
        if not self.playlist:
            QMessageBox.warning(self, "Oops!", "The track list is empty. Add songs first!")
            return
        
        name, ok = QInputDialog.getText(self, "Save Mix", "Name your Mix CD:")
        if ok and name:
            file_name = f"{name}.mix" if not name.endswith(".mix") else name
            file_path = os.path.join(self.mix_folder, file_name)
            
            try:
                # FIXED: Added encoding and immediate disk flushing
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.playlist, f)
                    f.flush()
                    os.fsync(f.fileno()) 
                
                QMessageBox.information(self, "Saved", f"'{file_name}' saved to Library!")
                self.load_installed_mixes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def load_selected_mix(self, item):
        file_path = os.path.join(self.mix_folder, item.text())
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.playlist = json.load(f)
            
            self.track_list_widget.clear()
            for path in self.playlist:
                self.track_list_widget.addItem(os.path.basename(path))
            self.current_index = -1
            self.is_paused = False
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"File is empty or corrupted: {e}")

    def add_songs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Music", "", "Audio Files (*.mp3 *.wav)")
        if files:
            for f in files:
                self.playlist.append(f)
                self.track_list_widget.addItem(os.path.basename(f))

    def play_song(self):
        if not self.playlist: return
        if self.current_index == -1: self.current_index = 0
        
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.load(self.playlist[self.current_index])
                pygame.mixer.music.play()
            self.track_list_widget.setCurrentRow(self.current_index)
        except Exception as e:
            QMessageBox.warning(self, "Play Error", f"Could not play file: {e}")

    def pause_song(self):
        if pygame.mixer.music.get_busy() and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
        elif self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False

    def next_song(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.is_paused = False
            self.play_song()

    def prev_song(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.is_paused = False
            self.play_song()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MCCFinal()
    window.show()
    sys.exit(app.exec())