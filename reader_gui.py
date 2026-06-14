# -*- coding: utf-8 -*-
"""Reader GUI - 普通用户界面，完全参考管理端UI风格与策略"""

import sys
import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from typing import Optional
from api_client import APIClient
from i18n import tr, set_language, get_language
from gui_utils import ToastNotification, LoadingOverlay, add_hover_effect

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

API = APIClient("http://127.0.0.1:8000")

# TRAE-Inspired Modern Color Scheme
C_SIDEBAR = "#f5f5f7"
C_SIDEBAR_HOVER = "#e8e8ed"
C_SIDEBAR_ACTIVE = "#d4d4db"
C_SIDEBAR_TEXT = "#1d1d1f"
C_HEADER = "#ffffff"
C_CONTENT = "#ffffff"
C_CARD = "#ffffff"
C_ACCENT = "#d4d4db"
C_ACCENT_HOVER = "#c0c0c8"
C_SUCCESS = "#a8d5ba"
C_SUCCESS_HOVER = "#96c4a8"
C_WARN = "#f5d76e"
C_DANGER = "#f4a0a0"
C_DANGER_HOVER = "#e89090"
C_TEXT = "#1d1d1f"
C_TEXT_SEC = "#86868b"
C_BORDER = "#e5e5e7"
C_INPUT_BG = "#fafafa"
C_BUTTON_BG = "#ffffff"
C_BUTTON_BORDER = "#d2d2d7"


class ReaderApp(ctk.CTk):
    """普通用户应用主窗口 - 完全参考管理端布局"""

    def __init__(self, reader_info: dict):
        super().__init__()
        self.title("LitManager")
        self.geometry("1200x760")
        self.minsize(1000, 600)

        self.reader_info = reader_info
        self.reader_id = reader_info.get("id")

        self._build_layout()

    def _build_layout(self):
        """构建主布局"""
        # ─ Sidebar ───────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # ── Main Content Area ─────────────────────────────
        self.main_area = ctk.CTkFrame(self, fg_color=C_CONTENT)
        self.main_area.pack(side="left", fill="both", expand=True)

        # Header (无搜索框，仅标题 + 通知铃铛 + 头像)
        self.header = ctk.CTkFrame(self.main_area, fg_color=C_HEADER, height=60, corner_radius=0)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        self._build_header()

        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_area, fg_color=C_CONTENT)
        self.content_frame.pack(side="top", fill="both", expand=True)

        # ── Views ─────────────────────────────────────────
        self.views = {}
        self.current_view = None
        self._init_views()
        self.switch_view("book_search")

    def _build_sidebar(self):
        """构建侧边栏导航"""
        # Logo/Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        logo_frame.pack(fill="x", pady=(16, 8))
        logo_frame.pack_propagate(False)
        logo_label = ctk.CTkLabel(
            logo_frame, text="LitManager",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=C_SIDEBAR_TEXT
        )
        logo_label.place(relx=0.5, rely=0.5, anchor="center")

        # Navigation Items: 图书搜索, 书架, 设置 (用户信息仅通过右上角头像访问)
        nav_items = [
            ("book_search", tr("Book Search"), ""),
            ("bookshelf", tr("Bookshelf"), ""),
            ("settings", tr("Settings"), ""),
        ]

        self.nav_buttons = []
        for view_id, label, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", text_color=C_SIDEBAR_TEXT,
                hover_color=C_SIDEBAR_HOVER, anchor="w",
                height=44, corner_radius=8,
                command=lambda vid=view_id: self.switch_view(vid)
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons.append((view_id, btn))
            
            # Add hover effect for visual feedback
            add_hover_effect(btn, hover_color=C_SIDEBAR_HOVER, original_color="transparent")

        # Bottom: Help button (参考管理端)
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=(0, 16))
        ctk.CTkButton(
            bottom_frame, text=f"  Help",
            font=ctk.CTkFont(size=12),
            fg_color="transparent", text_color=C_SIDEBAR_TEXT,
            hover_color=C_SIDEBAR_HOVER, anchor="w",
            height=36, corner_radius=8,
            command=self._show_help
        ).pack(fill="x")

    def _build_header(self):
        """构建顶部栏 - 无搜索框，仅标题 + 通知铃铛 + 头像"""
        # Center: Page Title
        self.page_title = ctk.CTkLabel(
            self.header, text=tr("Book Search"),
            font=ctk.CTkFont(size=18, weight="bold"), text_color=C_TEXT
        )
        self.page_title.place(relx=0.5, rely=0.5, anchor="center")

        # Right: Notification bell + User avatar (与管理端一致)
        actions_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        actions_frame.pack(side="right", fill="y", padx=16, pady=8)

        # Notification bell with badge
        self.notif_btn = ctk.CTkButton(
            actions_frame, text="🔔",
            font=ctk.CTkFont(size=18),
            fg_color=C_INPUT_BG, hover_color=C_BORDER,
            text_color=C_SIDEBAR_TEXT, width=40, height=40, corner_radius=12,
            command=self._show_notifications
        )
        self.notif_btn.pack(side="right", padx=(0, 8))

        self.notif_badge = ctk.CTkLabel(
            actions_frame, text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffffff", fg_color="#ef4444",
            width=18, height=18, corner_radius=9
        )
        self.notif_badge.place(relx=0.0, rely=0.0, anchor="ne", x=-4, y=4)
        self.notif_badge.lower(self.notif_btn)

        # User avatar
        ctk.CTkButton(
            actions_frame, text="👤",
            font=ctk.CTkFont(size=18),
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            text_color=C_SIDEBAR_TEXT, width=40, height=40, corner_radius=12,
            command=lambda: self.switch_view("user_profile")
        ).pack(side="right")

        # Load unread count
        self._refresh_notif_badge()

    def _init_views(self):
        """初始化所有视图"""
        self.views["book_search"] = ReaderBookSearchView(self.content_frame, self)
        self.views["bookshelf"] = ReaderBookshelfView(self.content_frame, self)
        self.views["user_profile"] = ReaderUserProfileView(self.content_frame, reader_id=self.reader_id, app_ref=self)
        self.views["settings"] = ReaderSettingsView(self.content_frame, app_ref=self)

    def switch_view(self, view_id, **kwargs):
        """切换视图 with smooth transition"""
        if self.current_view:
            self.current_view.pack_forget()

        self.current_view = self.views.get(view_id)
        if self.current_view:
            self.current_view.pack(fill="both", expand=True)
            
            # Smooth fade-in effect: raise widget after brief delay
            self.after(10, lambda: self.current_view.tkraise() if self.current_view else None)
            
            self.current_view.refresh(**kwargs) if kwargs else self.current_view.refresh()

            titles = {
                "book_search": tr("Book Search"),
                "bookshelf": tr("Bookshelf"),
                "user_profile": tr("User Profile"),
                "settings": tr("Settings"),
            }
            self.page_title.configure(text=titles.get(view_id, view_id))

        for vid, btn in self.nav_buttons:
            if vid == view_id:
                btn.configure(fg_color=C_SIDEBAR_ACTIVE, text_color=C_SIDEBAR_TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=C_SIDEBAR_TEXT)

    def _show_help(self):
        messagebox.showinfo("Help", "LitManager Reader\n\nSearch books, browse by category, borrow and return books.")

    def _refresh_notif_badge(self):
        """Refresh notification badge with unread count."""
        def _load():
            try:
                result = API.get_unread_notification_count(self.reader_id, user_type="reader")
                count = result.get("count", 0)
                self.after(0, lambda: self._update_badge(count))
            except Exception as e:
                print(f"Failed to load notification count: {e}")

        threading.Thread(target=_load, daemon=True).start()

    def _update_badge(self, count):
        """Update badge visibility and text."""
        if count > 0:
            self.notif_badge.configure(text=str(count) if count < 100 else "99+")
            self.notif_badge.lift(self.notif_btn)
        else:
            self.notif_badge.configure(text="")
            self.notif_badge.lower(self.notif_btn)

    def _show_notifications(self):
        """Show notification popup with list of notifications."""
        def _load():
            try:
                result = API.list_notifications(self.reader_id, user_type="reader", page=1, page_size=20)
                notifications = result.get("data", [])
                self.after(0, lambda: self._display_notifications(notifications))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _display_notifications(self, notifications):
        """Display notifications in a popup window."""
        if not notifications:
            messagebox.showinfo(tr("Notifications"), tr("No notifications"))
            return

        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title(tr("Notifications"))
        popup.geometry("500x600")
        popup.transient(self)
        popup.grab_set()

        # Title
        ctk.CTkLabel(
            popup, text=tr("Notifications"),
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 10))

        # Scrollable list
        scroll_frame = ctk.CTkScrollableFrame(popup, width=460, height=450)
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # Display each notification
        for notif in notifications:
            notif_frame = ctk.CTkFrame(scroll_frame, corner_radius=8)
            notif_frame.pack(fill="x", pady=5, padx=5)

            # Title with read indicator
            is_read = notif.get("is_read", 0)
            title_text = notif.get("title", "")
            if not is_read:
                title_text = f"● {title_text}"

            ctk.CTkLabel(
                notif_frame, text=title_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            ).pack(fill="x", padx=10, pady=(10, 5))

            # Content
            content = notif.get("content", "")
            if content:
                ctk.CTkLabel(
                    notif_frame, text=content,
                    font=ctk.CTkFont(size=12),
                    text_color=C_TEXT_SEC,
                    anchor="w", wraplength=420
                ).pack(fill="x", padx=10, pady=(0, 5))

            # Date
            created_at = notif.get("created_at", "")
            if created_at:
                ctk.CTkLabel(
                    notif_frame, text=created_at,
                    font=ctk.CTkFont(size=10),
                    text_color=C_TEXT_SEC,
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(0, 10))

            # Mark as read button (if unread)
            if not is_read:
                notif_id = notif.get("id")
                ctk.CTkButton(
                    notif_frame, text=tr("Mark as Read"),
                    font=ctk.CTkFont(size=11),
                    height=28, width=100,
                    command=lambda nid=notif_id: self._mark_notification_read(nid, popup)
                ).pack(anchor="e", padx=10, pady=(0, 10))

        # Mark all as read button
        ctk.CTkButton(
            popup, text=tr("Mark All as Read"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._mark_all_notifications_read(popup)
        ).pack(pady=(0, 20))

    def _mark_notification_read(self, notif_id, popup):
        """Mark a single notification as read."""
        def _mark():
            try:
                API.mark_notification_read(notif_id)
                self.after(0, lambda: self._on_notification_read(popup))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

        threading.Thread(target=_mark, daemon=True).start()

    def _mark_all_notifications_read(self, popup):
        """Mark all notifications as read."""
        def _mark():
            try:
                API.mark_all_notifications_read(self.reader_id, user_type="reader")
                self.after(0, lambda: self._on_notification_read(popup))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

        threading.Thread(target=_mark, daemon=True).start()

    def _on_notification_read(self, popup):
        """Callback after marking notifications as read."""
        popup.destroy()
        self._refresh_notif_badge()
        ToastNotification(self, tr("Notifications marked as read"), "success")

    def _logout(self):
        """退出登录"""
        if messagebox.askyesno(tr("Confirm"), tr("Are you sure you want to logout?")):
            self.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def rebuild_all_views(self):
        """Destroy and recreate all views to reflect language changes."""
        current_view = None
        for vid, v in self.views.items():
            if v == self.current_view:
                current_view = vid
                break

        try:
            self.sidebar.destroy()
        except Exception:
            pass
        try:
            self.main_area.destroy()
        except Exception:
            pass

        self.sidebar = ctk.CTkFrame(self, fg_color=C_SIDEBAR, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.main_area = ctk.CTkFrame(self, fg_color=C_CONTENT)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.header = ctk.CTkFrame(self.main_area, fg_color=C_HEADER, height=60, corner_radius=0)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        self._build_header()

        self.content_frame = ctk.CTkFrame(self.main_area, fg_color=C_CONTENT)
        self.content_frame.pack(side="top", fill="both", expand=True)

        self.views = {}
        self._init_views()

        if current_view:
            self.switch_view(current_view)
        else:
            self.switch_view("book_search")


# ══════════════════════════════════════════════════════════
# Views
# ═══════════════════════════════════════════════════════════


class ReaderBookSearchView(ctk.CTkFrame):
    """图书搜索视图 - 集成借阅和还书功能"""

    def __init__(self, master, app: ReaderApp, **kwargs):
        super().__init__(master, fg_color=C_CONTENT, **kwargs)
        self.app = app
        self.books = []
        self.borrowings = []
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=tr("Book Search"),
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(scroll, text=tr("Search, borrow or return books"),
                     font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC).pack(anchor="w", padx=24, pady=(0, 16))

        # ── Search Bar ──
        search_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        search_frame.pack(fill="x", padx=24, pady=10)
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=20, pady=16)

        self.search_entry = ctk.CTkEntry(
            search_inner, placeholder_text=tr("Enter book name, author, or ISBN..."),
            font=ctk.CTkFont(size=14), fg_color=C_INPUT_BG, border_width=0,
            corner_radius=10, height=40
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.search_btn = ctk.CTkButton(
            search_inner, text=tr("Search"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            text_color=C_SIDEBAR_TEXT, width=100, height=40, corner_radius=10,
            command=self._do_search
        )
        self.search_btn.pack(side="right")

        # ── Status ──
        self.status_label = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC)
        self.status_label.pack(pady=(10, 0))

        # ── Results Table ──
        table_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        table_frame.pack(fill="both", expand=True, padx=24, pady=16)

        columns = ("id", "title", "authors", "publisher", "year", "isbn", "available", "action")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        headings = {"id": "ID", "title": tr("Title"), "authors": tr("Author"),
                    "publisher": tr("Publisher"), "year": tr("Year"), "isbn": "ISBN",
                    "available": tr("Available"), "action": tr("Action")}
        widths = {"id": 60, "title": 280, "authors": 160, "publisher": 140,
                  "year": 60, "isbn": 130, "available": 80, "action": 80}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_double_click)

        # ── My Borrows Section (还书) ──
        borrow_section = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        borrow_section.pack(fill="both", padx=24, pady=16)

        ctk.CTkLabel(borrow_section, text=tr("My Borrows"),
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=C_TEXT
                     ).pack(anchor="w", padx=20, pady=(16, 8))

        borrow_inner = ctk.CTkFrame(borrow_section, fg_color="transparent")
        borrow_inner.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.borrow_tree_frame = ctk.CTkFrame(borrow_inner, fg_color="transparent")
        self.borrow_tree_frame.pack(fill="both", expand=True)

        self.borrow_empty_label = ctk.CTkLabel(
            self.borrow_tree_frame, text=tr("No borrowing records"),
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
        )
        self.borrow_empty_label.pack(pady=40)

    def refresh(self):
        """加载我的借阅记录"""
        def _load():
            try:
                borrowings = API.get_reader_borrowings(self.app.reader_id).get("data", [])
                self.borrowings = borrowings
                self.after(0, self._update_borrows)
            except Exception as e:
                print(f"加载借阅记录失败: {e}")

        threading.Thread(target=_load, daemon=True).start()

    def _update_borrows(self):
        for w in self.borrow_tree_frame.winfo_children():
            w.destroy()

        if not self.borrowings:
            ctk.CTkLabel(
                self.borrow_tree_frame, text=tr("No borrowing records"),
                font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
            ).pack(pady=40)
            return

        columns = ("book_title", "borrow_date", "due_date", "status", "action", "renew")
        tree = ttk.Treeview(self.borrow_tree_frame, columns=columns, show="headings", height=8)

        headings = {
            "book_title": tr("Book Title"), "borrow_date": tr("Borrow Date"),
            "due_date": tr("Due Date"), "status": tr("Status"), 
            "action": tr("Action"), "renew": tr("Renew")
        }
        widths = {"book_title": 300, "borrow_date": 110, "due_date": 110, "status": 90, "action": 90, "renew": 90}

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(self.borrow_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.bind("<Double-1>", lambda e: self._on_return_click(tree))
        tree.bind("<ButtonRelease-1>", lambda e: self._on_tree_click(tree))

        for b in self.borrowings:
            status = b.get("classified_status", b.get("status", ""))
            action = tr("Return") if status in ("借出", "临期未还", "逾期未还") else ""
            # Show renew option for borrowed books that haven't been renewed
            can_renew = tr("Renew") if status in ("借出", "临期未还") and not b.get("renewed") else ""
            tree.insert("", "end", values=(
                b.get("book_title", ""), b.get("borrow_date", ""),
                b.get("due_date", ""), status, action, can_renew,
            ))

    def _on_return_click(self, tree):
        """双击借阅记录还书"""
        selection = tree.selection()
        if not selection:
            return
        item = tree.item(selection[0])
        values = item["values"]
        status = values[3]
        if status not in (tr("Borrowed"), tr("Due Soon"), tr("Overdue"), "借出", "临期未还", "逾期未还"):
            return

        book_title = values[0]
        if messagebox.askyesno(tr("Return Book"), f"{tr('Return')} \"{book_title}\"?"):
            def _return():
                try:
                    result = API.return_book(book_title=book_title, reader_id=self.app.reader_id)
                    self.after(0, lambda: ToastNotification(self, result.get("message", tr("Return request submitted")), "success"))
                    self.refresh()
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

            threading.Thread(target=_return, daemon=True).start()

    def _on_tree_click(self, tree):
        """Handle single click on tree to detect renew button clicks."""
        region = tree.identify("region")
        if region != "cell":
            return
        
        column = tree.identify_column(tree.winfo_pointerx() - tree.winfo_rootx())
        # Column index 6 is "renew" (0-indexed: #6)
        if column == "#6":
            self._on_renew_click(tree)

    def _on_renew_click(self, tree):
        """Handle renew button click in borrowing table."""
        selection = tree.selection()
        if not selection:
            return
        item = tree.item(selection[0])
        values = item["values"]
        renew_text = values[5] if len(values) > 5 else ""
        if renew_text != tr("Renew"):
            return

        book_title = values[0]
        if messagebox.askyesno(tr("Renew Book"), f"{tr('Renew')} \"{book_title}\"?"):
            def _renew():
                try:
                    # Find the record_id from borrowings
                    record_id = None
                    for b in self.borrowings:
                        if b.get("book_title") == book_title:
                            record_id = b.get("id")
                            break
                    if not record_id:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), tr("Record not found")))
                        return
                    result = API.renew_book(record_id)
                    self.after(0, lambda: ToastNotification(self, result.get("message", tr("Renew successful")), "success"))
                    self.refresh()
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

            threading.Thread(target=_renew, daemon=True).start()

    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled", text=tr("Searching..."))
        self.status_label.configure(text=tr("Searching..."), text_color=C_TEXT_SEC)
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        try:
            result = API.list_books(q=query, page=1, page_size=50)
            self.books = result.get("items", [])
            total = result.get("total", 0)
            self.after(0, lambda: self._show_results(total))
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, total):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for b in self.books:
            available = b.get("available_copies", 0)
            available_text = f"{available}/{b.get('total_copies', 0)}"
            action = tr("Borrow") if available > 0 else tr("Reserve")
            self.tree.insert("", "end", values=(
                b.get("id", ""), b.get("title", ""), b.get("authors", ""),
                b.get("publisher", ""), b.get("publication_year", ""),
                b.get("isbn", ""), available_text, action,
            ))

        status_text = f"{total} {tr('results found')}"
        self.status_label.configure(text=status_text, text_color=C_SUCCESS)
        self.search_btn.configure(state="normal", text=tr("Search"))

    def _show_error(self, error):
        self.status_label.configure(text=f"{tr('Error')}: {error}", text_color="#ef4444")
        self.search_btn.configure(state="normal", text=tr("Search"))

    def _on_double_click(self, event=None):
        """双击搜索结果借书或预约"""
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]
        available = values[6]
        if "/" in str(available):
            avail_num = int(str(available).split("/")[0])
        else:
            avail_num = int(available) if str(available).isdigit() else 0

        book_id = int(values[0])
        title = values[1]

        if avail_num > 0:
            # Borrow
            if messagebox.askyesno(tr("Borrow Book"), f"{tr('Borrow')} \"{title}\"?"):
                def _borrow():
                    try:
                        result = API.borrow_book(self.app.reader_id, book_id=book_id)
                        self.after(0, lambda: ToastNotification(self.app, result.get("message", tr("Borrow successful")), "success"))
                        self._do_search()
                        self.refresh()
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

                threading.Thread(target=_borrow, daemon=True).start()
        else:
            # Reserve
            if messagebox.askyesno(tr("Reserve"), f"{tr('Reserve')} \"{title}\"?"):
                def _reserve():
                    try:
                        result = API.create_reservation(self.app.reader_id, book_id)
                        self.after(0, lambda: ToastNotification(self.app, result.get("message", tr("Reservation created")), "success"))
                        self._do_search()
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

                threading.Thread(target=_reserve, daemon=True).start()


class ReaderBookshelfView(ctk.CTkFrame):
    """书架视图 - 以表格形式按分类显示所有图书，支持借阅"""

    def __init__(self, master, app: ReaderApp, **kwargs):
        super().__init__(master, fg_color=C_CONTENT, **kwargs)
        self.app = app
        self.books = []
        self.categories = {}
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=tr("Bookshelf"),
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(scroll, text=tr("Browse books by category"),
                     font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC).pack(anchor="w", padx=24, pady=(0, 16))

        # Category filter bar
        filter_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        filter_frame.pack(fill="x", padx=24, pady=8)

        self.all_btn = ctk.CTkButton(
            filter_frame, text=tr("All Categories"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_ACCENT, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._filter_category(None)
        )
        self.all_btn.pack(side="left", padx=(0, 8))

        self.category_btns = {}
        self.cat_frame = filter_frame

        # Status bar
        self.status_label = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC)
        self.status_label.pack(pady=(10, 0))

        # Books table
        table_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        table_frame.pack(fill="both", expand=True, padx=24, pady=16)

        columns = ("id", "title", "authors", "category", "publisher", "year", "available", "action")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        headings = {"id": "ID", "title": tr("Title"), "authors": tr("Author"),
                    "category": tr("Category"), "publisher": tr("Publisher"),
                    "year": tr("Year"), "available": tr("Available"), "action": tr("Action")}
        widths = {"id": 60, "title": 260, "authors": 150, "category": 120,
                  "publisher": 130, "year": 60, "available": 80, "action": 80}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_double_click)

        self._current_category = None

    def refresh(self):
        """加载所有图书和分类"""
        def _load():
            try:
                # Backend limits page_size to 100, paginate to get all books
                all_books = []
                page = 1
                while True:
                    result = API.list_books(page=page, page_size=100)
                    items = result.get("items", [])
                    all_books.extend(items)
                    if len(items) < 100:
                        break
                    page += 1
                self.books = all_books
                print(f"[Bookshelf] Loaded {len(self.books)} books from API")
                categories = {}
                for b in self.books:
                    cat = b.get("category_name", "") or tr("Uncategorized")
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(b)
                self.categories = categories
                print(f"[Bookshelf] Categories: {list(categories.keys())}")
                self.after(0, self._build_categories)
            except Exception as e:
                print(f"[Bookshelf] 加载书架失败: {e}")
                import traceback
                traceback.print_exc()

        threading.Thread(target=_load, daemon=True).start()

    def _build_categories(self):
        for btn in self.category_btns.values():
            btn.destroy()
        self.category_btns = {}

        for cat in sorted(self.categories.keys()):
            btn = ctk.CTkButton(
                self.cat_frame, text=cat,
                font=ctk.CTkFont(size=13),
                fg_color=C_INPUT_BG, text_color=C_SIDEBAR_TEXT,
                height=36, corner_radius=10,
                command=lambda c=cat: self._filter_category(c)
            )
            btn.pack(side="left", padx=(0, 8))
            self.category_btns[cat] = btn

        self._filter_category(None)

    def _filter_category(self, category):
        self._current_category = category
        self.all_btn.configure(fg_color=C_ACCENT if category is None else C_INPUT_BG)
        for cat, btn in self.category_btns.items():
            btn.configure(fg_color=C_ACCENT if cat == category else C_INPUT_BG)

        # Filter and show books in table
        filtered = self.books
        if category:
            filtered = [b for b in self.books if (b.get("category_name", "") or tr("Uncategorized")) == category]

        for item in self.tree.get_children():
            self.tree.delete(item)

        for b in filtered:
            available = b.get("available_copies", 0)
            available_text = f"{available}/{b.get('total_copies', 0)}"
            action = tr("Borrow") if available > 0 else tr("Reserve")
            self.tree.insert("", "end", values=(
                b.get("id", ""), b.get("title", ""), b.get("authors", ""),
                b.get("category_name", "") or tr("Uncategorized"),
                b.get("publisher", ""), b.get("publication_year", ""),
                available_text, action,
            ))

        self.status_label.configure(text=f"{len(filtered)} {tr('results found')}", text_color=C_SUCCESS)

    def _on_double_click(self, event=None):
        """双击借书或预约"""
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]
        available = values[6]
        if "/" in str(available):
            avail_num = int(str(available).split("/")[0])
        else:
            avail_num = int(available) if str(available).isdigit() else 0

        book_id = int(values[0])
        title = values[1]

        if avail_num > 0:
            # Borrow
            if messagebox.askyesno(tr("Borrow Book"), f"{tr('Borrow')} \"{title}\"?"):
                def _borrow():
                    try:
                        result = API.borrow_book(self.app.reader_id, book_id=book_id)
                        self.after(0, lambda: ToastNotification(self.app, result.get("message", tr("Borrow successful")), "success"))
                        self.refresh()
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

                threading.Thread(target=_borrow, daemon=True).start()
        else:
            # Reserve
            if messagebox.askyesno(tr("Reserve"), f"{tr('Reserve')} \"{title}\"?"):
                def _reserve():
                    try:
                        result = API.create_reservation(self.app.reader_id, book_id)
                        self.after(0, lambda: ToastNotification(self.app, result.get("message", tr("Reservation created")), "success"))
                        self.refresh()
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

                threading.Thread(target=_reserve, daemon=True).start()


class ReaderUserProfileView(ctk.CTkFrame):
    """用户信息视图 - 完全参考管理端UserProfileView"""

    def __init__(self, master, reader_id=1, app_ref=None, **kwargs):
        super().__init__(master, fg_color=C_CONTENT, **kwargs)
        self.reader_id = reader_id
        self.app_ref = app_ref
        self.profile = {}
        self.borrowings = []
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ─ Profile Header Card ──
        header_card = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        header_card.pack(fill="x", padx=24, pady=(20, 12))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(fill="x", padx=24, pady=20)

        # Avatar circle
        self.avatar_frame = ctk.CTkFrame(
            header_inner, fg_color=C_INPUT_BG, width=80, height=80,
            corner_radius=40, border_width=2, border_color=C_BORDER
        )
        self.avatar_frame.pack(side="left", padx=(0, 20))
        self.avatar_frame.pack_propagate(False)

        self.avatar_label = ctk.CTkLabel(
            self.avatar_frame, text="👤",
            font=ctk.CTkFont(size=36), text_color=C_TEXT_SEC
        )
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # Name + identity
        info_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        self.name_label = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=22, weight="bold"), text_color=C_TEXT, anchor="w"
        )
        self.name_label.pack(anchor="w")

        self.identity_label = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC, anchor="w"
        )
        self.identity_label.pack(anchor="w", pady=(4, 0))

        self.status_badge = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=C_SIDEBAR_TEXT, fg_color=C_SUCCESS, corner_radius=8
        )
        self.status_badge.pack(anchor="w", pady=(8, 0))

        # ─ Stats Cards Row ──
        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.pack(fill="x", padx=24, pady=8)

        self.stat_total = self._make_stat_card(stats_row, "0", tr("Total Borrowed"), "#6366f1")
        self.stat_active = self._make_stat_card(stats_row, "0", tr("Currently Borrowed"), "#22c55e")
        self.stat_overdue = self._make_stat_card(stats_row, "0", tr("Overdue"), "#ef4444")
        self.stat_returned = self._make_stat_card(stats_row, "0", tr("Returned"), "#6b7280")

        # ── Tabs ──
        tab_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        tab_bar.pack(fill="x", padx=24, pady=(16, 0))

        self.tab_borrow = ctk.CTkButton(
            tab_bar, text=tr("Borrowing Records"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_ACCENT, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._switch_tab("borrow")
        )
        self.tab_borrow.pack(side="left", padx=(0, 8))

        self.tab_overdue = ctk.CTkButton(
            tab_bar, text=tr("Overdue Books"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_INPUT_BG, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._switch_tab("overdue")
        )
        self.tab_overdue.pack(side="left", padx=(0, 8))

        self.tab_settings = ctk.CTkButton(
            tab_bar, text=tr("Account Settings"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_INPUT_BG, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._switch_tab("settings")
        )
        self.tab_settings.pack(side="left", padx=(0, 8))

        self.tab_reservations = ctk.CTkButton(
            tab_bar, text=tr("My Reservations"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_INPUT_BG, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._switch_tab("reservations")
        )
        self.tab_reservations.pack(side="left", padx=(0, 8))

        self.tab_fines = ctk.CTkButton(
            tab_bar, text=tr("Fines"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_INPUT_BG, text_color=C_SIDEBAR_TEXT,
            height=36, corner_radius=10,
            command=lambda: self._switch_tab("fines")
        )
        self.tab_fines.pack(side="left")

        # Tab content containers
        self.borrow_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        self.overdue_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        self.settings_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        self.reservations_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        self.fines_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)

        self._build_borrow_tab()
        self._build_overdue_tab()
        self._build_settings_tab()
        self._build_reservations_tab()
        self._build_fines_tab()

        self._current_tab = "borrow"
        self._switch_tab("borrow")

    def _make_stat_card(self, parent, value, label, color):
        card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=12, border_width=1, border_color=C_BORDER)
        card.pack(side="left", fill="x", expand=True, padx=4)

        ctk.CTkFrame(card, fg_color=color, height=3, corner_radius=0).pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        val_label = ctk.CTkLabel(
            inner, text=str(value),
            font=ctk.CTkFont(size=24, weight="bold"), text_color=C_TEXT
        )
        val_label.pack(anchor="w")

        ctk.CTkLabel(
            inner, text=label,
            font=ctk.CTkFont(size=12), text_color=C_TEXT_SEC
        ).pack(anchor="w", pady=(4, 0))

        return {"card": card, "value": val_label}

    def _build_borrow_tab(self):
        inner = ctk.CTkFrame(self.borrow_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        self.borrow_tree_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.borrow_tree_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.borrow_tree_frame, text=tr("No borrowing records"),
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
        ).pack(pady=40)

    def _build_overdue_tab(self):
        inner = ctk.CTkFrame(self.overdue_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        self.overdue_tree_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.overdue_tree_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.overdue_tree_frame, text=tr("No overdue books"),
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
        ).pack(pady=40)

    def _build_reservations_tab(self):
        inner = ctk.CTkFrame(self.reservations_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        self.reservations_tree_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.reservations_tree_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.reservations_tree_frame, text=tr("No reservations"),
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
        ).pack(pady=40)

    def _build_fines_tab(self):
        inner = ctk.CTkFrame(self.fines_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        self.fines_tree_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.fines_tree_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.fines_tree_frame, text=tr("No fines"),
            font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
        ).pack(pady=40)

    def _build_settings_tab(self):
        inner = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            inner, text=tr("Profile Information"),
            font=ctk.CTkFont(size=16, weight="bold"), text_color=C_TEXT
        ).pack(anchor="w", pady=(0, 16))

        self.settings_info_labels = {}
        info_items = [
            ("name", tr("Name")),
            ("card_number", tr("Card Number")),
            ("identity_type", tr("Identity Type")),
            ("phone", tr("Phone")),
            ("register_date", tr("Register Date")),
            ("max_borrow", tr("Max Borrow")),
        ]

        for key, label in info_items:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13, weight="bold"),
                         width=120, anchor="w").pack(side="left")
            value_label = ctk.CTkLabel(row, text="", font=ctk.CTkFont(size=13), anchor="w")
            value_label.pack(side="left", padx=(8, 0))
            self.settings_info_labels[key] = value_label

        # ── Logout Button (集成在账户设置中) ──
        ctk.CTkFrame(inner, fg_color=C_BORDER, height=1).pack(fill="x", pady=(20, 16))

        ctk.CTkLabel(
            inner, text=tr("Account"),
            font=ctk.CTkFont(size=16, weight="bold"), text_color=C_TEXT
        ).pack(anchor="w", pady=(0, 16))

        # ── Change Password Section ──
        ctk.CTkLabel(
            inner, text=tr("Change Password"),
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C_TEXT
        ).pack(anchor="w", pady=(0, 8))

        pwd_frame = ctk.CTkFrame(inner, fg_color="transparent")
        pwd_frame.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            pwd_frame, text=tr("Old Password"),
            font=ctk.CTkFont(size=12), width=100, anchor="w"
        ).pack(side="left")
        self.old_pwd_entry = ctk.CTkEntry(
            pwd_frame, show="*", width=200, height=32, corner_radius=8
        )
        self.old_pwd_entry.pack(side="left", padx=(8, 0))

        pwd_frame2 = ctk.CTkFrame(inner, fg_color="transparent")
        pwd_frame2.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            pwd_frame2, text=tr("New Password"),
            font=ctk.CTkFont(size=12), width=100, anchor="w"
        ).pack(side="left")
        self.new_pwd_entry = ctk.CTkEntry(
            pwd_frame2, show="*", width=200, height=32, corner_radius=8
        )
        self.new_pwd_entry.pack(side="left", padx=(8, 0))

        pwd_frame3 = ctk.CTkFrame(inner, fg_color="transparent")
        pwd_frame3.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            pwd_frame3, text=tr("Confirm Password"),
            font=ctk.CTkFont(size=12), width=100, anchor="w"
        ).pack(side="left")
        self.confirm_pwd_entry = ctk.CTkEntry(
            pwd_frame3, show="*", width=200, height=32, corner_radius=8
        )
        self.confirm_pwd_entry.pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            inner, text=tr("Change Password"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            text_color=C_SIDEBAR_TEXT, height=36, corner_radius=8,
            command=self._change_password
        ).pack(fill="x", pady=(8, 16))

        ctk.CTkFrame(inner, fg_color=C_BORDER, height=1).pack(fill="x", pady=(0, 16))

        ctk.CTkButton(
            inner, text=tr("Logout"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=C_DANGER, hover_color=C_DANGER_HOVER,
            text_color=C_SIDEBAR_TEXT, height=44, corner_radius=10,
            command=self._logout
        ).pack(fill="x", pady=(0, 8))

    def _change_password(self):
        """Reader changes own password."""
        old_pwd = self.old_pwd_entry.get().strip()
        new_pwd = self.new_pwd_entry.get().strip()
        confirm_pwd = self.confirm_pwd_entry.get().strip()

        if not old_pwd or not new_pwd or not confirm_pwd:
            messagebox.showwarning(tr("Warning"), tr("All fields are required"))
            return

        if new_pwd != confirm_pwd:
            messagebox.showwarning(tr("Warning"), tr("New passwords do not match"))
            return

        if len(new_pwd) < 6:
            messagebox.showwarning(tr("Warning"), tr("Password must be at least 6 characters"))
            return

        def do_change():
            try:
                API.change_reader_password(self.reader_id, old_pwd, new_pwd)
                self.after(0, lambda: messagebox.showinfo(tr("Success"), tr("Password changed successfully")))
                self.after(0, lambda: self.old_pwd_entry.delete(0, "end"))
                self.after(0, lambda: self.new_pwd_entry.delete(0, "end"))
                self.after(0, lambda: self.confirm_pwd_entry.delete(0, "end"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

        threading.Thread(target=do_change, daemon=True).start()

    def _logout(self):
        if self.app_ref:
            self.app_ref._logout()

    def _switch_tab(self, tab_id):
        self.borrow_frame.pack_forget()
        self.overdue_frame.pack_forget()
        self.settings_frame.pack_forget()
        self.reservations_frame.pack_forget()
        self.fines_frame.pack_forget()

        for btn in (self.tab_borrow, self.tab_overdue, self.tab_settings, self.tab_reservations, self.tab_fines):
            btn.configure(fg_color=C_INPUT_BG)

        if tab_id == "borrow":
            self.borrow_frame.pack(fill="both", expand=True, padx=24, pady=12)
            self.tab_borrow.configure(fg_color=C_ACCENT)
        elif tab_id == "overdue":
            self.overdue_frame.pack(fill="both", expand=True, padx=24, pady=12)
            self.tab_overdue.configure(fg_color=C_ACCENT)
        elif tab_id == "settings":
            self.settings_frame.pack(fill="x", padx=24, pady=12)
            self.tab_settings.configure(fg_color=C_ACCENT)
        elif tab_id == "reservations":
            self.reservations_frame.pack(fill="both", expand=True, padx=24, pady=12)
            self.tab_reservations.configure(fg_color=C_ACCENT)
        elif tab_id == "fines":
            self.fines_frame.pack(fill="both", expand=True, padx=24, pady=12)
            self.tab_fines.configure(fg_color=C_ACCENT)

        self._current_tab = tab_id

    def refresh(self):
        def _load():
            try:
                profile = API.get_reader_profile(self.reader_id)
                borrowings = API.get_reader_borrowings(self.reader_id).get("data", [])
                reservations = API.get_my_reservations(self.reader_id).get("data", [])
                fines = API.get_reader_fines(self.reader_id).get("data", [])
                self.after(0, lambda: self._update_data(profile, borrowings, reservations, fines))
            except Exception as e:
                print(f"加载用户数据失败: {e}")

        threading.Thread(target=_load, daemon=True).start()

    def _update_data(self, profile: dict, borrowings: list, reservations: list = None, fines: list = None):
        self.profile = profile
        self.borrowings = borrowings

        name = profile.get("name", "")
        identity = profile.get("identity_type", "")
        status = profile.get("card_status", "")

        self.name_label.configure(text=name)
        self.identity_label.configure(text=f"{identity}  ·  {profile.get('card_number', '')}")
        self.status_badge.configure(text=status)

        total = len(borrowings)
        active = sum(1 for b in borrowings if b.get("classified_status") == "借出")
        returned = sum(1 for b in borrowings if b.get("classified_status") == "已归还")
        overdue = sum(1 for b in borrowings if b.get("classified_status") in ("逾期未还", "临期未还"))

        self.stat_total["value"].configure(text=str(total))
        self.stat_active["value"].configure(text=str(active))
        self.stat_overdue["value"].configure(text=str(overdue))
        self.stat_returned["value"].configure(text=str(returned))

        self._update_borrow_tab(borrowings)
        overdue_list = [b for b in borrowings if b.get("classified_status") in ("逾期未还", "临期未还")]
        self._update_overdue_tab(overdue_list)

        if reservations is not None:
            self._update_reservations_tab(reservations)
        if fines is not None:
            self._update_fines_tab(fines)

        for key, label in self.settings_info_labels.items():
            value = profile.get(key, "")
            label.configure(text=str(value) if value else "-")

    def _update_borrow_tab(self, borrowings):
        for w in self.borrow_tree_frame.winfo_children():
            w.destroy()

        if not borrowings:
            ctk.CTkLabel(
                self.borrow_tree_frame, text=tr("No borrowing records"),
                font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
            ).pack(pady=40)
            return

        columns = ("book_title", "borrow_date", "due_date", "status")
        tree = ttk.Treeview(self.borrow_tree_frame, columns=columns, show="headings", height=10)

        headings = {
            "book_title": tr("Book Title"), "borrow_date": tr("Borrow Date"),
            "due_date": tr("Due Date"), "status": tr("Status")
        }
        widths = {"book_title": 320, "borrow_date": 120, "due_date": 120, "status": 100}

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(self.borrow_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for b in borrowings:
            tree.insert("", "end", values=(
                b.get("book_title", ""), b.get("borrow_date", ""),
                b.get("due_date", ""), b.get("classified_status", b.get("status", "")),
            ))

    def _update_overdue_tab(self, overdue_list):
        for w in self.overdue_tree_frame.winfo_children():
            w.destroy()

        if not overdue_list:
            ctk.CTkLabel(
                self.overdue_tree_frame, text=tr("No overdue books"),
                font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
            ).pack(pady=40)
            return

        columns = ("book_title", "due_date", "overdue_days")
        tree = ttk.Treeview(self.overdue_tree_frame, columns=columns, show="headings", height=10)

        headings = {
            "book_title": tr("Book Title"), "due_date": tr("Due Date"),
            "overdue_days": tr("Overdue Days")
        }
        widths = {"book_title": 320, "due_date": 120, "overdue_days": 100}

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(self.overdue_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for b in overdue_list:
            tree.insert("", "end", values=(
                b.get("book_title", ""), b.get("due_date", ""), b.get("overdue_days", 0),
            ))

    def _update_reservations_tab(self, reservations):
        for w in self.reservations_tree_frame.winfo_children():
            w.destroy()

        if not reservations:
            ctk.CTkLabel(
                self.reservations_tree_frame, text=tr("No reservations"),
                font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
            ).pack(pady=40)
            return

        columns = ("id", "book_title", "status", "created_at", "action")
        tree = ttk.Treeview(self.reservations_tree_frame, columns=columns, show="headings", height=10)

        headings = {
            "id": "ID", "book_title": tr("Book Title"), "status": tr("Status"),
            "created_at": tr("Created At"), "action": tr("Action")
        }
        widths = {"id": 60, "book_title": 300, "status": 100, "created_at": 120, "action": 100}

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(self.reservations_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for r in reservations:
            status = r.get("status", "")
            action = tr("Cancel Reservation") if status in ("waiting", "等待中") else ""
            tree.insert("", "end", values=(
                r.get("id", ""), r.get("book_title", ""), status,
                r.get("created_at", ""), action,
            ))

        tree.bind("<Double-1>", lambda e: self._on_reservation_double_click(tree))

    def _on_reservation_double_click(self, tree):
        """双击取消预约"""
        selection = tree.selection()
        if not selection:
            return
        item = tree.item(selection[0])
        values = item["values"]
        reservation_id = values[0]
        status = values[2]
        action = values[4]

        if action == tr("Cancel Reservation"):
            if messagebox.askyesno(tr("Cancel Reservation"), f"{tr('Cancel Reservation')} (ID: {reservation_id})?"):
                def _cancel():
                    try:
                        API.cancel_reservation(reservation_id)
                        self.after(0, lambda: ToastNotification(self.app_ref, tr("Reservation cancelled"), "success"))
                        self.refresh()
                    except Exception as e:
                        self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))

                threading.Thread(target=_cancel, daemon=True).start()

    def _update_fines_tab(self, fines):
        for w in self.fines_tree_frame.winfo_children():
            w.destroy()

        if not fines:
            ctk.CTkLabel(
                self.fines_tree_frame, text=tr("No fines"),
                font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC
            ).pack(pady=40)
            return

        columns = ("id", "reason", "amount", "status", "created_at")
        tree = ttk.Treeview(self.fines_tree_frame, columns=columns, show="headings", height=10)

        headings = {
            "id": "ID", "reason": tr("Reason"), "amount": tr("Amount"),
            "status": tr("Status"), "created_at": tr("Created At")
        }
        widths = {"id": 60, "reason": 280, "amount": 100, "status": 100, "created_at": 120}

        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])

        vsb = ttk.Scrollbar(self.fines_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for f in fines:
            tree.insert("", "end", values=(
                f.get("id", ""), f.get("reason", ""), f.get("amount", 0),
                f.get("status", ""), f.get("created_at", ""),
            ))


class ReaderSettingsView(ctk.CTkFrame):
    """设置视图 - 完全参考管理端SettingsView"""

    def __init__(self, master, app_ref=None, **kwargs):
        super().__init__(master, fg_color=C_CONTENT, **kwargs)
        self.app_ref = app_ref
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text=tr("Settings"),
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(scroll, text=tr("Your profile and preferences"),
                     font=ctk.CTkFont(size=13), text_color=C_TEXT_SEC).pack(anchor="w", padx=24, pady=(0, 16))

        # ── Appearance Section ──
        appearance_card = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        appearance_card.pack(fill="x", padx=24, pady=8)

        ctk.CTkLabel(appearance_card, text=tr("Appearance"),
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=C_TEXT
                     ).pack(anchor="w", padx=20, pady=(16, 8))

        theme_row = ctk.CTkFrame(appearance_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(theme_row, text=tr("Theme"), font=ctk.CTkFont(size=14)).pack(side="left")
        self.theme_var = ctk.StringVar(value=tr("System"))
        theme_menu = ctk.CTkOptionMenu(theme_row, variable=self.theme_var,
                                       values=[tr("System"), tr("Light"), tr("Dark")],
                                       fg_color=C_INPUT_BG, button_color=C_ACCENT,
                                       text_color=C_TEXT, corner_radius=10, height=36,
                                       command=self._set_theme)
        theme_menu.pack(side="right")

        lang_row = ctk.CTkFrame(appearance_card, fg_color="transparent")
        lang_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(lang_row, text=tr("Language"), font=ctk.CTkFont(size=14)).pack(side="left")
        self.lang_var = ctk.StringVar(value="中文" if get_language() == "zh" else "English")
        lang_menu = ctk.CTkOptionMenu(lang_row, variable=self.lang_var,
                                     values=["中文", "English"],
                                     fg_color=C_INPUT_BG, button_color=C_ACCENT,
                                     text_color=C_TEXT, corner_radius=10, height=36,
                                     command=self._set_language)
        lang_menu.pack(side="right")

        # ── About Section ──
        about_card = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=16, border_width=1, border_color=C_BORDER)
        about_card.pack(fill="x", padx=24, pady=8)

        ctk.CTkLabel(about_card, text=tr("About"),
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=C_TEXT
                     ).pack(anchor="w", padx=20, pady=(16, 8))

        about_items = [
            (tr("LitManager"), tr("Library Management System")),
            (tr("Version"), "0.1.0"),
            (tr("Backend"), tr("FastAPI + SQLite")),
            (tr("Frontend"), tr("Modern Tkinter GUI")),
        ]
        for label, value in about_items:
            row = ctk.CTkFrame(about_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=13, weight="bold"),
                         width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=13),
                         anchor="w").pack(side="left", padx=(8, 0))

    def _set_theme(self, choice):
        mapping = {"System": "System", "Light": "Light", "Dark": "Dark"}
        ctk.set_appearance_mode(mapping.get(choice, "System"))

    def _set_language(self, choice):
        lang = "zh" if choice == "中文" else "en"
        set_language(lang)
        if self.app_ref:
            self.app_ref.after(100, self.app_ref.rebuild_all_views)

    def refresh(self):
        pass


def start_reader_app(reader_info: dict):
    """启动读者应用"""
    app = ReaderApp(reader_info)
    app.mainloop()


if __name__ == "__main__":
    set_language("zh")
    test_reader = {"id": 1, "card_number": "R001", "name": "测试读者", "role": "reader"}
    start_reader_app(test_reader)
