# -*- coding: utf-8 -*-
"""GUI utility classes for visual effects: Toast notifications, Loading overlay, Hover effects."""

import customtkinter as ctk


class ToastNotification:
    """Temporary popup notification at top-right of window."""

    def __init__(self, parent, message, msg_type="info", duration=3000):
        """
        Args:
            parent: Parent CTk window
            message: Notification text
            msg_type: "success" (green), "error" (red), "warning" (yellow), "info" (blue)
            duration: Auto-dismiss time in milliseconds
        """
        self.parent = parent
        self.duration = duration

        # Color mapping
        colors = {
            "success": ("#a8d5ba", "#1d1d1f"),  # bg, text
            "error": ("#f4a0a0", "#1d1d1f"),
            "warning": ("#f5d76e", "#1d1d1f"),
            "info": ("#a0c4f4", "#1d1d1f"),
        }
        bg_color, text_color = colors.get(msg_type, colors["info"])

        # Create toast window
        self.toast = ctk.CTkToplevel(parent)
        self.toast.overrideredirect(True)  # Remove window decorations
        self.toast.attributes("-topmost", True)

        # Calculate position (top-right of parent)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        toast_width = 300
        toast_height = 60
        x = parent_x + parent_width - toast_width - 20
        y = parent_y + 20
        self.toast.geometry(f"{toast_width}x{toast_height}+{x}+{y}")

        # Toast content
        frame = ctk.CTkFrame(self.toast, fg_color=bg_color, corner_radius=12)
        frame.pack(fill="both", expand=True)

        # Icon
        icons = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
        icon = icons.get(msg_type, "ℹ")

        ctk.CTkLabel(
            frame,
            text=f"{icon}  {message}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=text_color,
            wraplength=260
        ).pack(expand=True, padx=16, pady=12)

        # Auto-dismiss
        self.toast.after(duration, self._dismiss)

    def _dismiss(self):
        """Close the toast notification."""
        try:
            self.toast.destroy()
        except Exception:
            pass


class LoadingOverlay:
    """Semi-transparent overlay with spinning indicator during async operations."""

    def __init__(self, parent, message="加载中..."):
        """
        Args:
            parent: Parent widget to overlay
            message: Loading text
        """
        self.parent = parent
        self.message = message
        self.overlay = None
        self._animating = False
        self._anim_id = None

    def show(self):
        """Display the loading overlay."""
        if self.overlay:
            return

        # Create overlay frame
        self.overlay = ctk.CTkFrame(self.parent, fg_color=("white", "#1a1a1a"))
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift()

        # Spinner label with animated characters
        self.spinner_chars = ["⏳", "⌛", "⏳", "⌛"]
        self.spinner_idx = 0
        self.spinner_label = ctk.CTkLabel(
            self.overlay,
            text=self.spinner_chars[0],
            font=ctk.CTkFont(size=32)
        )
        self.spinner_label.pack(expand=True)

        # Message label
        ctk.CTkLabel(
            self.overlay,
            text=self.message,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1d1d1f", "#e5e5e7")
        ).pack(pady=(0, 20))

        # Start animation
        self._animating = True
        self._animate()

    def _animate(self):
        """Animate the spinner."""
        if not self._animating:
            return
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
        self.spinner_label.configure(text=self.spinner_chars[self.spinner_idx])
        self._anim_id = self.parent.after(300, self._animate)

    def hide(self):
        """Remove the loading overlay."""
        self._animating = False
        if self._anim_id:
            try:
                self.parent.after_cancel(self._anim_id)
            except Exception:
                pass
        if self.overlay:
            try:
                self.overlay.destroy()
            except Exception:
                pass
            self.overlay = None


def add_hover_effect(button, hover_color=None, original_color=None):
    """
    Add hover effect to a CTk button.

    Args:
        button: CTkButton widget
        hover_color: Color on hover (darker shade)
        original_color: Original color to restore on leave
    """
    if original_color is None:
        original_color = button.cget("fg_color")
    if hover_color is None:
        # Default darker shade
        hover_color = button.cget("hover_color")

    def on_enter(event):
        try:
            button.configure(fg_color=hover_color)
        except Exception:
            pass

    def on_leave(event):
        try:
            button.configure(fg_color=original_color)
        except Exception:
            pass

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
