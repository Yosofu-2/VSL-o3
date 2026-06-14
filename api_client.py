"""HTTP client for LitManager backend API."""

import os
import httpx
from typing import Any, Optional


class APIClient:
    """Synchronous HTTP client wrapping the FastAPI backend."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self._client = httpx.Client(timeout=30)

    def set_token(self, token: str):
        """Set JWT token for authenticated requests."""
        self.token = token
        if token:
            self._client.headers["Authorization"] = f"Bearer {token}"
        else:
            self._client.headers.pop("Authorization", None)

    def health(self) -> dict:
        r = self._client.get(f"{self.base_url}/api/health")
        r.raise_for_status()
        return r.json()

    def list_books(self, q=None, category_id=None, page=1, page_size=20):
        params = {"page": page, "page_size": page_size}
        if q:
            params["q"] = q
        if category_id is not None:
            params["category_id"] = category_id
        r = self._client.get(f"{self.base_url}/api/books", params=params)
        r.raise_for_status()
        data = r.json()
        print(f"[API] list_books: got {len(data.get('items', []))} items, total={data.get('total')}")
        return data

    def search_books_ai(self, query):
        """Smart search with LLM. Returns books matching natural language description."""
        r = self._client.post(f"{self.base_url}/api/books/search-ai", json={"query": query})
        r.raise_for_status()
        return r.json()

    def get_book_stats(self):
        """Get library statistics (total books, copies, available)."""
        r = self._client.get(f"{self.base_url}/api/books/stats")
        r.raise_for_status()
        return r.json()

    def get_book(self, book_id):
        r = self._client.get(f"{self.base_url}/api/books/{book_id}")
        r.raise_for_status()
        return r.json()

    def create_book(self, data):
        r = self._client.post(f"{self.base_url}/api/books", json=data)
        r.raise_for_status()
        return r.json()

    def update_book(self, book_id, data):
        r = self._client.put(f"{self.base_url}/api/books/{book_id}", json=data)
        r.raise_for_status()
        return r.json()

    def delete_book(self, book_id):
        r = self._client.delete(f"{self.base_url}/api/books/{book_id}")
        r.raise_for_status()

    def batch_delete_books(self, book_ids):
        """Delete multiple books by their IDs."""
        r = self._client.post(f"{self.base_url}/api/books/batch-delete", json={"book_ids": book_ids})
        r.raise_for_status()

    def list_categories(self):
        r = self._client.get(f"{self.base_url}/api/books/categories")
        r.raise_for_status()
        return r.json()

    def create_category(self, data):
        r = self._client.post(f"{self.base_url}/api/books/categories", json=data)
        r.raise_for_status()
        return r.json()

    def update_category(self, cat_id, data):
        r = self._client.put(f"{self.base_url}/api/books/categories/{cat_id}", json=data)
        r.raise_for_status()
        return r.json()

    def delete_category(self, cat_id):
        r = self._client.delete(f"{self.base_url}/api/books/categories/{cat_id}")
        r.raise_for_status()

    def list_readers(self):
        r = self._client.get(f"{self.base_url}/api/readers/")
        r.raise_for_status()
        return r.json()

    def create_reader(self, data):
        r = self._client.post(f"{self.base_url}/api/readers/", json=data)
        r.raise_for_status()
        return r.json()

    def update_reader(self, reader_id, data):
        r = self._client.put(f"{self.base_url}/api/readers/{reader_id}", json=data)
        r.raise_for_status()
        return r.json()

    def delete_reader(self, reader_id):
        r = self._client.delete(f"{self.base_url}/api/readers/{reader_id}")
        r.raise_for_status()

    def import_readers(self, filepath):
        """Import readers from Excel file."""
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            r = self._client.post(f"{self.base_url}/api/readers/import", files=files)
            r.raise_for_status()
            return r.json()

    def get_reader_profile(self, reader_id):
        """Get reader profile with statistics."""
        r = self._client.get(f"{self.base_url}/api/readers/{reader_id}/profile")
        r.raise_for_status()
        return r.json()

    def get_reader_borrowings(self, reader_id):
        """Get all borrowing records for a reader."""
        r = self._client.get(f"{self.base_url}/api/readers/{reader_id}/borrowings")
        r.raise_for_status()
        return r.json()

    def get_reader_overdue(self, reader_id):
        """Get overdue/active borrowing records for a reader."""
        r = self._client.get(f"{self.base_url}/api/readers/{reader_id}/overdue")
        r.raise_for_status()
        return r.json()

    def upload_avatar(self, reader_id, filepath):
        """Upload avatar image for a reader."""
        filename = os.path.basename(filepath)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
        content_type = f"image/{ext}" if ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp") else "image/png"
        with open(filepath, "rb") as f:
            files = {"avatar": (filename, f, content_type)}
            r = self._client.post(f"{self.base_url}/api/readers/{reader_id}/avatar", files=files)
            r.raise_for_status()
            return r.json()

    def login(self, username, password):
        """Authenticate admin credentials."""
        r = self._client.post(f"{self.base_url}/api/admins/login", json={
            "username": username,
            "password": password,
        })
        r.raise_for_status()
        data = r.json()
        if "token" in data:
            self.set_token(data["token"])
        return data

    def reader_login(self, card_number, password):
        """Authenticate reader credentials."""
        r = self._client.post(f"{self.base_url}/api/readers/login", json={
            "card_number": card_number,
            "password": password,
        })
        r.raise_for_status()
        data = r.json()
        if "token" in data:
            self.set_token(data["token"])
        return data

    def list_borrowing(self):
        r = self._client.get(f"{self.base_url}/api/borrowing/")
        r.raise_for_status()
        return r.json()

    def borrow_book(self, reader_id, copy_id=None, book_id=None, book_title=None):
        body = {"reader_id": reader_id}
        if copy_id is not None:
            body["copy_id"] = copy_id
        if book_id is not None:
            body["book_id"] = book_id
        if book_title is not None:
            body["book_title"] = book_title
        r = self._client.post(f"{self.base_url}/api/borrowing/borrow", json=body)
        r.raise_for_status()
        return r.json()

    def return_book(self, copy_id=None, book_id=None, book_title=None, reader_id=None):
        body = {}
        if copy_id is not None:
            body["copy_id"] = copy_id
        if book_id is not None:
            body["book_id"] = book_id
        if book_title is not None:
            body["book_title"] = book_title
        if reader_id is not None:
            body["reader_id"] = reader_id
        r = self._client.post(f"{self.base_url}/api/borrowing/return", json=body)
        r.raise_for_status()
        return r.json()

    def confirm_return(self, record_id):
        r = self._client.post(f"{self.base_url}/api/borrowing/confirm-return",
                              json={"record_id": record_id})
        r.raise_for_status()
        return r.json()

    def reject_return(self, record_id):
        r = self._client.post(f"{self.base_url}/api/borrowing/reject-return",
                              json={"record_id": record_id})
        r.raise_for_status()
        return r.json()

    def list_pending_returns(self):
        r = self._client.get(f"{self.base_url}/api/borrowing/pending")
        r.raise_for_status()
        return r.json()

    def get_borrowing_stats(self):
        r = self._client.get(f"{self.base_url}/api/borrowing/stats")
        r.raise_for_status()
        return r.json()

    def list_copies(self):
        r = self._client.get(f"{self.base_url}/api/copies/")
        r.raise_for_status()
        return r.json()

    def create_copy(self, data):
        r = self._client.post(f"{self.base_url}/api/copies/", json=data)
        r.raise_for_status()
        return r.json()

    def delete_copy(self, copy_id):
        r = self._client.delete(f"{self.base_url}/api/copies/{copy_id}")
        r.raise_for_status()
        return r.json()

    def list_models(self):
        r = self._client.get(f"{self.base_url}/api/models")
        r.raise_for_status()
        return r.json()

    def get_model(self, model_id):
        r = self._client.get(f"{self.base_url}/api/models/{model_id}")
        r.raise_for_status()
        return r.json()

    def create_model(self, data):
        r = self._client.post(f"{self.base_url}/api/models", json=data)
        r.raise_for_status()
        return r.json()

    def update_model(self, model_id, data):
        r = self._client.put(f"{self.base_url}/api/models/{model_id}", json=data)
        r.raise_for_status()
        return r.json()

    def delete_model(self, model_id):
        r = self._client.delete(f"{self.base_url}/api/models/{model_id}")
        r.raise_for_status()

    def fetch_ollama_models(self, api_base):
        """Fetch available models from a local Ollama instance."""
        r = self._client.get(f"{self.base_url}/api/models/ollama-list", params={"api_base": api_base})
        r.raise_for_status()
        return r.json()

    def list_conversations(self):
        r = self._client.get(f"{self.base_url}/api/conversations")
        r.raise_for_status()
        return r.json()

    def get_conversation(self, conv_id):
        r = self._client.get(f"{self.base_url}/api/conversations/{conv_id}")
        r.raise_for_status()
        return r.json()

    def delete_conversation(self, conv_id):
        r = self._client.delete(f"{self.base_url}/api/conversations/{conv_id}")
        r.raise_for_status()

    def chat(self, model_id, message, conversation_id=None, system_prompt=None, book_context_ids=None):
        body = {"model_id": model_id, "message": message}
        if conversation_id is not None:
            body["conversation_id"] = conversation_id
        if system_prompt:
            body["system_prompt"] = system_prompt
        if book_context_ids:
            body["book_context_ids"] = book_context_ids
        r = self._client.post(f"{self.base_url}/api/conversations/chat", json=body)
        r.raise_for_status()
        return r.json()

    def agent_execute(self, instruction, model_id):
        r = self._client.post(f"{self.base_url}/api/agent",
                              json={"instruction": instruction, "model_id": model_id})
        r.raise_for_status()
        return r.json()

    def agent_chat(self, message, model_id, conversation_id=None, system_prompt=None):
        """Multi-turn agent chat with conversation context."""
        body = {"message": message, "model_id": model_id}
        if conversation_id is not None:
            body["conversation_id"] = conversation_id
        if system_prompt:
            body["system_prompt"] = system_prompt
        r = self._client.post(f"{self.base_url}/api/agent/chat", json=body)
        r.raise_for_status()
        return r.json()

    def agent_chat_stream(self, message, model_id, conversation_id=None, system_prompt=None):
        """Multi-turn agent chat with streaming response (SSE).
        Yields chunks of text as they arrive from the server.
        """
        body = {"message": message, "model_id": model_id}
        if conversation_id is not None:
            body["conversation_id"] = conversation_id
        if system_prompt:
            body["system_prompt"] = system_prompt

        # Use streaming client with extended timeout for LLM responses
        with httpx.Client(timeout=300) as stream_client:
            with stream_client.stream(
                "POST",
                f"{self.base_url}/api/agent/chat-stream",
                json=body,
                headers=self._client.headers,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        yield line[6:]  # Remove "data: " prefix

    def list_agent_conversations(self):
        """List all agent conversations."""
        r = self._client.get(f"{self.base_url}/api/agent/conversations")
        r.raise_for_status()
        return r.json()

    def get_agent_conversation(self, conv_id):
        """Get a specific agent conversation with messages."""
        r = self._client.get(f"{self.base_url}/api/agent/conversations/{conv_id}")
        r.raise_for_status()
        return r.json()

    def delete_agent_conversation(self, conv_id):
        """Delete an agent conversation."""
        r = self._client.delete(f"{self.base_url}/api/agent/conversations/{conv_id}")
        r.raise_for_status()

    def test_model(self, model_id, test_message="Hello, are you working?"):
        """Test model connectivity."""
        r = self._client.post(f"{self.base_url}/api/models/{model_id}/test",
                              json={"test_message": test_message})
        r.raise_for_status()
        return r.json()

    def list_admins(self):
        r = self._client.get(f"{self.base_url}/api/admins/")
        r.raise_for_status()
        return r.json()

    def create_admin(self, data):
        r = self._client.post(f"{self.base_url}/api/admins/", json=data)
        r.raise_for_status()

    # ── Import / Export ────────────────────────────────

    def import_books(self, filepath):
        """Import books from Excel file. Returns dict with imported count and errors."""
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            r = self._client.post(f"{self.base_url}/api/books/import", files=files, timeout=300)
            r.raise_for_status()
            return r.json()

    def import_books_ai(self, filepath):
        """Import books from Excel with LLM auto-classification. Returns dict with imported count, errors, and classification results."""
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            files = {"file": (filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            r = self._client.post(f"{self.base_url}/api/books/import-ai", files=files)
            r.raise_for_status()
            return r.json()

    def download_template(self, save_path):
        """Download Excel import template and save to filepath."""
        r = self._client.get(f"{self.base_url}/api/books/template")
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

    def list_uncategorized_books(self):
        """List books without category."""
        r = self._client.get(f"{self.base_url}/api/books/uncategorized")
        r.raise_for_status()
        return r.json()

    def classify_uncategorized_books(self):
        """Batch classify uncategorized books using web search + LLM. Long-running."""
        r = self._client.post(f"{self.base_url}/api/books/classify", timeout=300)
        r.raise_for_status()
        return r.json()

    # ── Notifications ────────────────────────────────

    def list_notifications(self, user_id, user_type="reader", page=1, page_size=50):
        """List notifications for a user."""
        params = {"user_id": user_id, "user_type": user_type, "page": page, "page_size": page_size}
        r = self._client.get(f"{self.base_url}/api/notifications/", params=params)
        r.raise_for_status()
        return r.json()

    def get_unread_notification_count(self, user_id, user_type="reader"):
        """Get unread notification count for a user."""
        params = {"user_id": user_id, "user_type": user_type}
        r = self._client.get(f"{self.base_url}/api/notifications/unread-count", params=params)
        r.raise_for_status()
        return r.json()

    def mark_notification_read(self, notif_id):
        """Mark a notification as read."""
        r = self._client.put(f"{self.base_url}/api/notifications/{notif_id}/read")
        r.raise_for_status()
        return r.json()

    def mark_all_notifications_read(self, user_id, user_type="reader"):
        """Mark all notifications as read for a user."""
        params = {"user_id": user_id, "user_type": user_type}
        r = self._client.put(f"{self.base_url}/api/notifications/read-all", params=params)
        r.raise_for_status()
        return r.json()

    def delete_notification(self, notif_id):
        """Delete a notification."""
        r = self._client.delete(f"{self.base_url}/api/notifications/{notif_id}")
        r.raise_for_status()
        return r.json()

    # ── Audit Logs ────────────────────────────────

    def list_audit_logs(self, user_type=None, action=None, resource_type=None, start_date=None, end_date=None, page=1, page_size=20):
        """List audit logs with pagination and filters."""
        params = {"page": page, "page_size": page_size}
        if user_type:
            params["user_type"] = user_type
        if action:
            params["action"] = action
        if resource_type:
            params["resource_type"] = resource_type
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        r = self._client.get(f"{self.base_url}/api/audit/logs", params=params)
        r.raise_for_status()
        return r.json()

    # ── System / Backup ────────────────────────────────

    def list_backups(self):
        """List all database backups."""
        r = self._client.get(f"{self.base_url}/api/system/backups")
        r.raise_for_status()
        return r.json()

    def create_backup(self):
        """Create a database backup."""
        r = self._client.post(f"{self.base_url}/api/system/backup")
        r.raise_for_status()
        return r.json()

    def restore_backup(self, filename):
        """Restore database from backup."""
        r = self._client.post(f"{self.base_url}/api/system/restore/{filename}")
        r.raise_for_status()
        return r.json()

    def delete_backup(self, filename):
        """Delete a backup file."""
        r = self._client.delete(f"{self.base_url}/api/system/backups/{filename}")
        r.raise_for_status()
        return r.json()

    # ── Reader Password ────────────────────────────────

    def reset_reader_password(self, reader_id, new_password):
        """Admin resets a reader's password."""
        r = self._client.post(
            f"{self.base_url}/api/readers/{reader_id}/reset-password",
            json={"new_password": new_password},
        )
        r.raise_for_status()
        return r.json()

    def change_reader_password(self, reader_id, old_password, new_password):
        """Reader changes own password."""
        r = self._client.post(
            f"{self.base_url}/api/readers/{reader_id}/change-password",
            json={"old_password": old_password, "new_password": new_password},
        )
        r.raise_for_status()
        return r.json()

    def renew_book(self, record_id):
        """Renew a borrowing record."""
        r = self._client.post(f"{self.base_url}/api/borrowing/renew", json={"record_id": record_id})
        r.raise_for_status()
        return r.json()

    def get_my_reservations(self, reader_id):
        """Get reader's reservations."""
        r = self._client.get(f"{self.base_url}/api/reservations/my", params={"reader_id": reader_id})
        r.raise_for_status()
        return r.json()

    def create_reservation(self, reader_id, book_id):
        """Create a book reservation."""
        r = self._client.post(f"{self.base_url}/api/reservations", json={"reader_id": reader_id, "book_id": book_id})
        r.raise_for_status()
        return r.json()

    def cancel_reservation(self, reservation_id):
        """Cancel a reservation."""
        r = self._client.delete(f"{self.base_url}/api/reservations/{reservation_id}")
        r.raise_for_status()

    def get_reader_fines(self, reader_id):
        """Get reader's fines."""
        r = self._client.get(f"{self.base_url}/api/readers/{reader_id}/fines")
        r.raise_for_status()
        return r.json()

    def isbn_lookup(self, isbn):
        """Look up book info by ISBN."""
        r = self._client.get(f"{self.base_url}/api/books/isbn-lookup", params={"isbn": isbn})
        r.raise_for_status()
        return r.json()

    # ─ Statistics ────────────────────────────────

    def get_library_stats(self):
        """Get overall library statistics."""
        r = self._client.get(f"{self.base_url}/api/stats/library")
        r.raise_for_status()
        return r.json()

    def get_books_by_category(self):
        """Get book count by category."""
        r = self._client.get(f"{self.base_url}/api/stats/books-by-category")
        r.raise_for_status()
        return r.json()

    def get_books_by_year(self):
        """Get book count by publication year."""
        r = self._client.get(f"{self.base_url}/api/stats/books-by-year")
        r.raise_for_status()
        return r.json()

    def get_borrowing_trend(self):
        """Get monthly borrowing trend."""
        r = self._client.get(f"{self.base_url}/api/stats/borrowing-trend")
        r.raise_for_status()
        return r.json()

    def get_reader_activity(self):
        """Get top 20 most active readers."""
        r = self._client.get(f"{self.base_url}/api/stats/reader-activity")
        r.raise_for_status()
        return r.json()

    def get_top_books(self):
        """Get top 20 most borrowed books."""
        r = self._client.get(f"{self.base_url}/api/stats/top-books")
        r.raise_for_status()
        return r.json()

    def get_genre_distribution(self):
        """Get book count by genre."""
        r = self._client.get(f"{self.base_url}/api/stats/genre-distribution")
        r.raise_for_status()
        return r.json()

    def get_language_distribution(self):
        """Get book count by language."""
        r = self._client.get(f"{self.base_url}/api/stats/language-distribution")
        r.raise_for_status()
        return r.json()

    def get_overdue_analysis(self):
        """Get overdue borrowing analysis."""
        r = self._client.get(f"{self.base_url}/api/stats/overdue-analysis")
        r.raise_for_status()
        return r.json()

    def get_status_distribution(self):
        """Get borrowing status distribution."""
        r = self._client.get(f"{self.base_url}/api/stats/status-distribution")
        r.raise_for_status()
        return r.json()

    def export_books(self, save_path):
        """Export books to Excel file."""
        r = self._client.get(f"{self.base_url}/api/export/books")
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

    def export_readers(self, save_path):
        """Export readers to Excel file."""
        r = self._client.get(f"{self.base_url}/api/export/readers")
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

    def export_borrowings(self, save_path):
        """Export borrowing records to Excel file."""
        r = self._client.get(f"{self.base_url}/api/export/borrowings")
        r.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

