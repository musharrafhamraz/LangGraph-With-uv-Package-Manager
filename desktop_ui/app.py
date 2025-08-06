import sys
import json
import os
from datetime import datetime
import asyncio
import threading
from typing import Dict, List, Optional, Tuple, Any, Callable

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QTextEdit, QLineEdit, QScrollArea,
                             QFrame, QSplitter, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QMessageBox, QInputDialog, QMenu, QAction,
                             QListWidget, QListWidgetItem, QSizePolicy, QTabWidget)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QColor, QPalette

# Import MCP client
from mcp_client import MCPClientManager, run_async

class ServerConfig:
    """Class to manage MCP server configurations"""
    
    def __init__(self, config_file: str = "server_config.json"):
        self.config_file = config_file
        self.servers = self._load_config()
    
    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """Load server configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_config(self):
        """Save server configurations to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.servers, f, indent=4)
    
    def add_server(self, name: str, config: Dict[str, Any]):
        """Add or update a server configuration"""
        self.servers[name] = config
        self.save_config()
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            del self.servers[name]
            self.save_config()
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a server configuration by name"""
        return self.servers.get(name)
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all server configurations"""
        return self.servers

class ChatSession:
    """Class to manage a chat session"""
    
    def __init__(self, name: str):
        self.name = name
        self.messages = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to the session"""
        timestamp = datetime.now()
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        self.updated_at = timestamp
        return timestamp
    
    def get_messages(self):
        """Get all messages in the session"""
        return self.messages
    
    def to_dict(self):
        """Convert session to dictionary for serialization"""
        return {
            "name": self.name,
            "messages": [{
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"].isoformat()
            } for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create session from dictionary"""
        session = cls(data["name"])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        for msg in data["messages"]:
            timestamp = datetime.fromisoformat(msg["timestamp"])
            session.messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": timestamp
            })
        return session

class SessionManager:
    """Class to manage chat sessions"""
    
    def __init__(self, sessions_file: str = "chat_sessions.json"):
        self.sessions_file = sessions_file
        self.sessions = {}
        self.active_session = None
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from file"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    for session_data in data:
                        session = ChatSession.from_dict(session_data)
                        self.sessions[session.name] = session
            except (json.JSONDecodeError, KeyError):
                self.sessions = {}
    
    def save_sessions(self):
        """Save sessions to file"""
        with open(self.sessions_file, 'w') as f:
            json.dump([session.to_dict() for session in self.sessions.values()], f, indent=4)
    
    def create_session(self, name: str) -> ChatSession:
        """Create a new chat session"""
        if name in self.sessions:
            # Append a number to make the name unique
            i = 1
            while f"{name} ({i})" in self.sessions:
                i += 1
            name = f"{name} ({i})"
        
        session = ChatSession(name)
        self.sessions[name] = session
        self.active_session = session
        self.save_sessions()
        return session
    
    def get_session(self, name: str) -> Optional[ChatSession]:
        """Get a session by name"""
        return self.sessions.get(name)
    
    def set_active_session(self, name: str) -> Optional[ChatSession]:
        """Set the active session"""
        if name in self.sessions:
            self.active_session = self.sessions[name]
            return self.active_session
        return None
    
    def delete_session(self, name: str) -> bool:
        """Delete a session"""
        if name in self.sessions:
            if self.active_session and self.active_session.name == name:
                self.active_session = None
            del self.sessions[name]
            self.save_sessions()
            return True
        return False
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all sessions"""
        # Sort by updated_at (most recent first)
        return sorted(self.sessions.values(), key=lambda s: s.updated_at, reverse=True)

class HITLDialog(QDialog):
    """Human-in-the-Loop dialog for approving/denying/modifying AI responses"""
    
    def __init__(self, parent, title: str, message: str, callback: Callable[[str, bool], None]):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)
        self.callback = callback
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Label
        label = QLabel("Review AI Response:")
        layout.addWidget(label)
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setText(message)
        layout.addWidget(self.text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Approve button
        self.approve_btn = QPushButton("Approve")
        self.approve_btn.clicked.connect(self.on_approve)
        button_layout.addWidget(self.approve_btn)
        
        # Deny button
        self.deny_btn = QPushButton("Deny")
        self.deny_btn.clicked.connect(self.on_deny)
        button_layout.addWidget(self.deny_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Set focus
        self.text_edit.setFocus()
    
    def on_approve(self):
        message = self.text_edit.toPlainText().strip()
        self.callback(message, True)
        self.accept()
    
    def on_deny(self):
        self.callback("", False)
        self.accept()
    
    def on_cancel(self):
        self.callback(None, False)
        self.reject()

class ServerDialog(QDialog):
    """Dialog for adding/editing server configurations"""
    
    def __init__(self, parent, title: str, server_name: str = "", server_config: Dict = None, callback: Callable = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 300)
        
        self.server_name = server_name
        self.server_config = server_config or {}
        self.callback = callback
        
        # Create layout
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Server name
        self.name_edit = QLineEdit()
        if self.server_name:
            self.name_edit.setText(self.server_name)
        form_layout.addRow("Server Name:", self.name_edit)
        
        # Server type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["stdio", "streamable_http"])
        if "transport" in self.server_config:
            index = self.type_combo.findText(self.server_config["transport"])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        self.type_combo.currentTextChanged.connect(self.on_type_change)
        form_layout.addRow("Server Type:", self.type_combo)
        
        # Server URL (for HTTP)
        self.url_edit = QLineEdit()
        if "url" in self.server_config:
            self.url_edit.setText(self.server_config["url"])
        self.url_row = form_layout.addRow("Server URL:", self.url_edit)
        
        # Command (for stdio)
        self.command_edit = QLineEdit()
        if "command" in self.server_config:
            self.command_edit.setText(self.server_config["command"])
        self.command_row = form_layout.addRow("Command:", self.command_edit)
        
        # Args (for stdio)
        self.args_edit = QLineEdit()
        if "args" in self.server_config:
            self.args_edit.setText(", ".join(self.server_config["args"]))
        self.args_row = form_layout.addRow("Arguments:", self.args_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Show appropriate fields based on server type
        self.on_type_change(self.type_combo.currentText())
    
    def on_type_change(self, value):
        # Show/hide fields based on server type
        if value == "streamable_http":
            self.url_edit.setVisible(True)
            self.command_edit.setVisible(False)
            self.args_edit.setVisible(False)
        elif value == "stdio":
            self.url_edit.setVisible(False)
            self.command_edit.setVisible(True)
            self.args_edit.setVisible(True)
    
    def on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.critical(self, "Error", "Server name cannot be empty")
            return
        
        config = {"transport": self.type_combo.currentText()}
        
        if config["transport"] == "streamable_http":
            url = self.url_edit.text().strip()
            if not url:
                QMessageBox.critical(self, "Error", "Server URL cannot be empty")
                return
            config["url"] = url
        elif config["transport"] == "stdio":
            command = self.command_edit.text().strip()
            if not command:
                QMessageBox.critical(self, "Error", "Command cannot be empty")
                return
            config["command"] = command
            
            args = self.args_edit.text().strip()
            if args:
                config["args"] = [arg.strip() for arg in args.split(",")]
            else:
                config["args"] = []
        
        if self.callback:
            self.callback(name, config)
        
        self.accept()

class MessageWidget(QFrame):
    """Widget for displaying a chat message"""
    
    def __init__(self, role: str, content: str, timestamp: datetime, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.timestamp = timestamp
        
        # Set up styling based on role
        if role == "user":
            self.setStyleSheet(
                "QFrame { background-color: #e9f5ff; border-radius: 10px; margin: 5px; }"
                "QLabel { color: #000000; }"
            )
        else:
            self.setStyleSheet(
                "QFrame { background-color: #f0f0f0; border-radius: 10px; margin: 5px; }"
                "QLabel { color: #000000; }"
            )
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header layout
        header_layout = QHBoxLayout()
        
        # Role label
        role_label = QLabel(role.capitalize())
        role_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(role_label)
        
        # Timestamp label
        time_str = timestamp.strftime("%I:%M %p")
        time_label = QLabel(time_str)
        time_label.setFont(QFont("Arial", 8))
        time_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Content label
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(content_label)

class SessionListWidget(QListWidget):
    """Widget for displaying the list of chat sessions"""
    
    session_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.itemClicked.connect(self.on_item_clicked)
    
    def add_session(self, session: ChatSession, is_active: bool = False):
        item = QListWidgetItem(session.name)
        if is_active:
            item.setBackground(QColor(200, 200, 200))
        self.addItem(item)
    
    def clear_sessions(self):
        self.clear()
    
    def on_item_clicked(self, item):
        self.session_selected.emit(item.text())
    
    def set_active_session(self, session_name: str):
        for i in range(self.count()):
            item = self.item(i)
            if item.text() == session_name:
                item.setBackground(QColor(200, 200, 200))
            else:
                item.setBackground(QColor(255, 255, 255))

class ChatWidget(QWidget):
    """Widget for displaying chat messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scroll area for messages
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for messages
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(10)
        
        # Add stretch to push messages to the top
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)
    
    def add_message(self, role: str, content: str, timestamp: datetime):
        # Remove stretch
        if self.messages_layout.count() > 0:
            self.messages_layout.takeAt(self.messages_layout.count() - 1)
        
        # Create message widget
        message_widget = MessageWidget(role, content, timestamp)
        
        # Add message to layout
        self.messages_layout.addWidget(message_widget)
        
        # Add stretch back
        self.messages_layout.addStretch()
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def clear_messages(self):
        # Clear all messages
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add stretch back
        self.messages_layout.addStretch()

class ServerManagerDialog(QDialog):
    """Dialog for managing server configurations"""
    
    def __init__(self, parent, server_config: ServerConfig):
        super().__init__(parent)
        self.setWindowTitle("Manage Servers")
        self.resize(500, 400)
        self.server_config = server_config
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Servers list
        self.servers_list = QListWidget()
        self.servers_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.servers_list)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add button
        add_btn = QPushButton("Add Server")
        add_btn.clicked.connect(self.add_server)
        buttons_layout.addWidget(add_btn)
        
        # Edit button
        edit_btn = QPushButton("Edit Server")
        edit_btn.clicked.connect(self.edit_server)
        buttons_layout.addWidget(edit_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete Server")
        delete_btn.clicked.connect(self.delete_server)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # Load servers
        self.load_servers()
    
    def load_servers(self):
        # Clear list
        self.servers_list.clear()
        
        # Add servers
        servers = self.server_config.get_all_servers()
        for name, config in servers.items():
            transport = config.get("transport", "unknown")
            self.servers_list.addItem(f"{name} ({transport})")
    
    def add_server(self):
        # Show server dialog
        dialog = ServerDialog(self, "Add Server", callback=self.on_server_added)
        dialog.exec_()
    
    def on_server_added(self, name: str, config: Dict):
        # Add server to configuration
        self.server_config.add_server(name, config)
        
        # Reload servers
        self.load_servers()
    
    def edit_server(self):
        # Get selected server
        selected_items = self.servers_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a server to edit")
            return
        
        # Extract server name from item text
        item_text = selected_items[0].text()
        name = item_text.split(" (")[0]
        
        # Get server configuration
        config = self.server_config.get_server(name)
        if not config:
            QMessageBox.critical(self, "Error", f"Server configuration for '{name}' not found")
            return
        
        # Show server dialog
        dialog = ServerDialog(
            self, 
            "Edit Server", 
            server_name=name, 
            server_config=config, 
            callback=lambda new_name, new_config: self.on_server_edited(name, new_name, new_config)
        )
        dialog.exec_()
    
    def on_server_edited(self, old_name: str, new_name: str, new_config: Dict):
        # Remove old server
        self.server_config.remove_server(old_name)
        
        # Add server with new name and config
        self.server_config.add_server(new_name, new_config)
        
        # Reload servers
        self.load_servers()
    
    def delete_server(self):
        # Get selected server
        selected_items = self.servers_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a server to delete")
            return
        
        # Extract server name from item text
        item_text = selected_items[0].text()
        name = item_text.split(" (")[0]
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm", 
            f"Delete server '{name}'?", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove server
            self.server_config.remove_server(name)
            
            # Reload servers
            self.load_servers()

class ChatApp(QMainWindow):
    """Main chat application class"""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.setWindowTitle("MCP Chat Desktop")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        
        # Initialize managers
        self.session_manager = SessionManager()
        self.server_config = ServerConfig()
        self.mcp_client = MCPClientManager()
        
        # Create UI components
        self.create_menu()
        self.create_widgets()
        
        # Load initial data
        self.load_sessions()
        
        # Create a new session if none exists
        if not self.session_manager.active_session:
            self.create_new_session()
    
    def create_menu(self):
        # Create menubar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New session action
        new_session_action = QAction("New Session", self)
        new_session_action.triggered.connect(self.create_new_session)
        file_menu.addAction(new_session_action)
        
        # Delete session action
        delete_session_action = QAction("Delete Session", self)
        delete_session_action.triggered.connect(self.delete_current_session)
        file_menu.addAction(delete_session_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Server menu
        server_menu = menubar.addMenu("Servers")
        
        # Add server action
        add_server_action = QAction("Add Server", self)
        add_server_action.triggered.connect(self.add_server)
        server_menu.addAction(add_server_action)
        
        # Manage servers action
        manage_servers_action = QAction("Manage Servers", self)
        manage_servers_action.triggered.connect(self.manage_servers)
        server_menu.addAction(manage_servers_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_widgets(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (sessions list)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Sessions header
        sessions_header = QWidget()
        sessions_header_layout = QHBoxLayout(sessions_header)
        sessions_header_layout.setContentsMargins(0, 0, 0, 0)
        
        sessions_label = QLabel("Sessions")
        sessions_label.setFont(QFont("Arial", 12, QFont.Bold))
        sessions_header_layout.addWidget(sessions_label)
        
        new_session_btn = QPushButton("+")
        new_session_btn.setMaximumWidth(30)
        new_session_btn.clicked.connect(self.create_new_session)
        sessions_header_layout.addWidget(new_session_btn)
        
        left_layout.addWidget(sessions_header)
        
        # Sessions list
        self.sessions_list = SessionListWidget()
        self.sessions_list.session_selected.connect(self.load_session)
        left_layout.addWidget(self.sessions_list)
        
        # Add left panel to splitter
        splitter.addWidget(left_panel)
        
        # Right panel (chat)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # Chat header
        chat_header = QWidget()
        chat_header_layout = QHBoxLayout(chat_header)
        chat_header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.session_name_label = QLabel("No Session")
        self.session_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        chat_header_layout.addWidget(self.session_name_label)
        
        # Server selection
        server_frame = QWidget()
        server_layout = QHBoxLayout(server_frame)
        server_layout.setContentsMargins(0, 0, 0, 0)
        
        server_label = QLabel("Server:")
        server_layout.addWidget(server_label)
        
        self.server_combo = QComboBox()
        self.server_combo.addItem("None")
        self.server_combo.currentTextChanged.connect(self.on_server_change)
        server_layout.addWidget(self.server_combo)
        
        chat_header_layout.addWidget(server_frame)
        
        right_layout.addWidget(chat_header)
        
        # Chat messages
        self.chat_widget = ChatWidget()
        right_layout.addWidget(self.chat_widget)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        right_layout.addWidget(self.status_label)
        
        # Input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(60)
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.installEventFilter(self)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        right_layout.addWidget(input_widget)
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 800])
        
        # Load server configurations
        self.load_servers()
    
    def eventFilter(self, obj, event):
        # Handle Enter key in message input
        if obj is self.message_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def load_sessions(self):
        # Clear existing sessions
        self.sessions_list.clear_sessions()
        
        # Add sessions to the list
        for session in self.session_manager.get_all_sessions():
            is_active = (self.session_manager.active_session and 
                        self.session_manager.active_session.name == session.name)
            self.sessions_list.add_session(session, is_active)
        
        # Load active session if any
        if self.session_manager.active_session:
            self.load_session(self.session_manager.active_session.name)
    
    def load_session(self, name: str):
        # Set active session
        session = self.session_manager.set_active_session(name)
        if not session:
            return
        
        # Update session name label
        self.session_name_label.setText(session.name)
        
        # Highlight active session in list
        self.sessions_list.set_active_session(session.name)
        
        # Clear chat frame
        self.chat_widget.clear_messages()
        
        # Load messages
        for msg in session.get_messages():
            self.chat_widget.add_message(msg["role"], msg["content"], msg["timestamp"])
    
    def create_new_session(self):
        # Ask for session name
        name, ok = QInputDialog.getText(self, "New Session", "Enter session name:")
        if not ok or not name:
            return
        
        # Create new session
        session = self.session_manager.create_session(name)
        
        # Reload sessions
        self.load_sessions()
    
    def delete_current_session(self):
        if not self.session_manager.active_session:
            QMessageBox.information(self, "Info", "No active session to delete")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, 
            "Confirm", 
            f"Delete session '{self.session_manager.active_session.name}'?", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Delete session
            name = self.session_manager.active_session.name
            self.session_manager.delete_session(name)
            
            # Reload sessions
            self.load_sessions()
    
    def send_message(self):
        # Get message content
        content = self.message_input.toPlainText().strip()
        if not content:
            return
        
        # Clear input
        self.message_input.clear()
        
        # Check if we have an active session
        if not self.session_manager.active_session:
            self.create_new_session()
            if not self.session_manager.active_session:
                return
        
        # Add message to session
        timestamp = self.session_manager.active_session.add_message("user", content)
        self.session_manager.save_sessions()
        
        # Add message to chat
        self.chat_widget.add_message("user", content, timestamp)
        
        # Process message
        self.process_message(content)
    
    def process_message(self, content: str):
        # Get selected server
        server_name = self.server_combo.currentText()
        if server_name == "None":
            self.show_ai_response("Please select a server to process messages")
            return
        
        # Check if connected to server
        if not self.mcp_client.is_connected:
            self.show_ai_response("Not connected to server. Please reconnect.")
            return
        
        # Process message in a separate thread to avoid blocking UI
        threading.Thread(target=self.process_message_async, args=(content,)).start()
    
    def process_message_async(self, content: str):
        try:
            # Show thinking message
            self.show_thinking_indicator(True)
            
            # Process message
            response = run_async(self.mcp_client.process_message, content)
            
            # Hide thinking indicator
            self.show_thinking_indicator(False)
            
            # Show response with HITL approval
            self.show_hitl_dialog(response)
        except Exception as e:
            # Hide thinking indicator
            self.show_thinking_indicator(False)
            
            # Show error
            error_msg = f"Error processing message: {str(e)}"
            self.show_ai_response(error_msg)
    
    def show_thinking_indicator(self, show: bool):
        # Update status label
        if show:
            self.status_label.setText("Processing...")
        else:
            self.status_label.setText("")
    
    def show_hitl_dialog(self, response: str):
        # Show HITL dialog
        dialog = HITLDialog(self, "Approve AI Response", response, self.on_hitl_response)
        dialog.exec_()
    
    def on_hitl_response(self, response: str, approved: bool):
        if response is None:  # Cancelled
            return
        
        if approved and response:
            # Add approved response to chat
            self.show_ai_response(response)
        elif not approved:
            # Show denial message
            self.show_ai_response("Response was denied by user")
    
    def show_ai_response(self, response: str):
        if not self.session_manager.active_session:
            return
        
        # Add message to session
        timestamp = self.session_manager.active_session.add_message("assistant", response)
        self.session_manager.save_sessions()
        
        # Add message to chat
        self.chat_widget.add_message("assistant", response, timestamp)
    
    def load_servers(self):
        # Get all servers
        servers = self.server_config.get_all_servers()
        
        # Update dropdown values
        self.server_combo.clear()
        self.server_combo.addItem("None")
        for name in servers.keys():
            self.server_combo.addItem(name)
    
    def on_server_change(self, value):
        # Handle server change
        if value == "None":
            # Disconnect from server
            self.mcp_client.disconnect()
            return
        
        # Get server configuration
        server_config = self.server_config.get_server(value)
        if not server_config:
            QMessageBox.critical(self, "Error", f"Server configuration for '{value}' not found")
            return
        
        # Create server config dictionary for MCP client
        server_configs = {value: server_config}
        
        # Connect to server (in a separate thread to avoid blocking UI)
        threading.Thread(target=self.connect_to_server, args=(server_configs,)).start()
    
    def connect_to_server(self, server_configs):
        # Show connecting message
        self.show_ai_response("Connecting to server...")
        
        # Connect to server
        success = run_async(self.mcp_client.connect, server_configs)
        
        # Show result
        if success:
            self.show_ai_response("Connected to server successfully")
        else:
            self.show_ai_response("Failed to connect to server. Please check your configuration and try again.")
            # Reset server dropdown
            self.server_combo.setCurrentText("None")
    
    def add_server(self):
        # Show server dialog
        dialog = ServerDialog(self, "Add Server", callback=self.on_server_added)
        dialog.exec_()
    
    def on_server_added(self, name: str, config: Dict):
        # Add server to configuration
        self.server_config.add_server(name, config)
        
        # Reload servers
        self.load_servers()
        
        # Select the new server
        self.server_combo.setCurrentText(name)
    
    def manage_servers(self):
        # Show server manager dialog
        dialog = ServerManagerDialog(self, self.server_config)
        dialog.exec_()
        
        # Reload servers
        self.load_servers()
    
    def show_about(self):
        QMessageBox.information(
            self, 
            "About", 
            "MCP Chat Desktop\n\nA simple desktop UI for interacting with MCP servers.\n\nVersion 1.0"
        )

def main():
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()