"""Statistics view with interactive matplotlib charts."""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import threading
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import numpy as np
from api_client import APIClient
from i18n import tr

# Create API client instance
API = APIClient("http://127.0.0.1:8000")

# Chinese font support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Color palette
COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#06b6d4']


class StatisticsView(ctk.CTkFrame):
    """Interactive statistics dashboard with matplotlib charts."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#ffffff", **kwargs)
        self.current_chart = None
        self._build()
        self.refresh()
    
    def _build(self):
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=24, pady=(20, 0))
        
        ctk.CTkLabel(
            title_frame,
            text=tr("Library Statistics"),
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#1d1d1f"
        ).pack(side="left")
        
        ctk.CTkButton(
            title_frame,
            text=tr("Refresh"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366f1",
            hover_color="#4f46e5",
            text_color="white",
            height=36,
            corner_radius=10,
            command=self.refresh
        ).pack(side="right")
        
        # Summary cards
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=24, pady=(16, 8))
        
        # Chart selector
        selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        selector_frame.pack(fill="x", padx=24, pady=(8, 8))
        
        ctk.CTkLabel(
            selector_frame,
            text=tr("Chart Type:"),
            font=ctk.CTkFont(size=13),
            text_color="#86868b"
        ).pack(side="left", padx=(0, 8))
        
        self.chart_var = ctk.StringVar(value="category")
        chart_types = [
            ("category", tr("By Category")),
            ("genre", tr("By Genre")),
            ("language", tr("By Language")),
            ("year", tr("By Year")),
            ("status", tr("By Status")),
            ("reader", tr("Top Readers")),
            ("book", tr("Top Books")),
        ]
        
        for value, label in chart_types:
            ctk.CTkRadioButton(
                selector_frame,
                text=label,
                variable=self.chart_var,
                value=value,
                font=ctk.CTkFont(size=12),
                command=self._on_chart_type_change
            ).pack(side="left", padx=4)
        
        # Chart container
        self.chart_container = ctk.CTkFrame(self, fg_color="#fafafa", corner_radius=16, border_width=1, border_color="#e5e7eb")
        self.chart_container.pack(fill="both", expand=True, padx=24, pady=(8, 24))
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.chart_container,
            text=tr("Loading statistics..."),
            font=ctk.CTkFont(size=14),
            text_color="#86868b"
        )
        self.placeholder.pack(expand=True)
    
    def _on_chart_type_change(self):
        """Handle chart type selection change."""
        self._load_chart(self.chart_var.get())
    
    def refresh(self):
        """Refresh all statistics."""
        self._load_summary_cards()
        self._load_chart(self.chart_var.get())
    
    def _load_summary_cards(self):
        """Load summary statistics cards."""
        # Clear existing cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        
        # Configure grid
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=1)
        
        def _fetch():
            try:
                stats = API.get_library_stats()
                self.after(0, lambda: self._update_cards(stats))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(tr("Error"), str(e)))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def _update_cards(self, stats):
        """Update summary cards with data."""
        cards = [
            (tr("Total Books"), str(stats.get("total_books", 0)), "#6366f1", "📚"),
            (tr("Total Readers"), str(stats.get("total_readers", 0)), "#22c55e", "👥"),
            (tr("Borrowed"), str(stats.get("borrowed", 0)), "#f59e0b", "📖"),
            (tr("Overdue"), str(stats.get("overdue", 0)), "#ef4444", "⚠️"),
        ]
        
        for i, (label, value, color, icon) in enumerate(cards):
            card = ctk.CTkFrame(self.cards_frame, fg_color="#f8f9fa", corner_radius=12, border_width=1, border_color="#e5e7eb")
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            
            # Color strip
            ctk.CTkFrame(card, fg_color=color, height=4, corner_radius=0).pack(fill="x")
            
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color="#1d1d1f"
            ).pack(pady=(12, 4))
            
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color="#86868b"
            ).pack(pady=(0, 12))
    
    def _load_chart(self, chart_type):
        """Load chart based on type."""
        # Clear existing chart
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        # Show loading
        loading = ctk.CTkLabel(
            self.chart_container,
            text=tr("Loading chart..."),
            font=ctk.CTkFont(size=14),
            text_color="#86868b"
        )
        loading.pack(expand=True)
        
        def _fetch():
            try:
                if chart_type == "category":
                    data = API.get_books_by_category()
                    title = tr("Books by Category")
                    chart_type_actual = "bar"
                elif chart_type == "genre":
                    data = API.get_genre_distribution()
                    title = tr("Books by Genre")
                    chart_type_actual = "pie"
                elif chart_type == "language":
                    data = API.get_language_distribution()
                    title = tr("Books by Language")
                    chart_type_actual = "pie"
                elif chart_type == "year":
                    data = API.get_books_by_year()
                    title = tr("Books by Publication Year")
                    chart_type_actual = "line"
                elif chart_type == "status":
                    data = API.get_status_distribution()
                    title = tr("Borrowing Status Distribution")
                    chart_type_actual = "pie"
                elif chart_type == "reader":
                    data = API.get_reader_activity()
                    title = tr("Top 20 Most Active Readers")
                    chart_type_actual = "horizontal_bar"
                elif chart_type == "book":
                    data = API.get_top_books()
                    title = tr("Top 20 Most Borrowed Books")
                    chart_type_actual = "horizontal_bar"
                else:
                    data = API.get_books_by_category()
                    title = tr("Books by Category")
                    chart_type_actual = "bar"
                
                self.after(0, lambda: self._render_chart(data, title, chart_type_actual))
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "No data" in error_msg:
                    self.after(0, lambda: self._show_no_data())
                else:
                    self.after(0, lambda: messagebox.showerror(tr("Error"), error_msg))
        
        threading.Thread(target=_fetch, daemon=True).start()
    
    def _render_chart(self, data, title, chart_type):
        """Render matplotlib chart."""
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not labels or not values:
            self._show_no_data()
            return
        
        # Create figure
        fig = Figure(figsize=(10, 6), dpi=100, facecolor='#fafafa')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#fafafa')
        
        if chart_type == "bar":
            self._draw_bar_chart(ax, labels, values, title)
        elif chart_type == "line":
            self._draw_line_chart(ax, labels, values, title)
        elif chart_type == "pie":
            self._draw_pie_chart(ax, labels, values, title)
        elif chart_type == "horizontal_bar":
            self._draw_horizontal_bar_chart(ax, labels, values, title)
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.chart_container)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind hover events
        canvas.mpl_connect('motion_notify_event', lambda event: self._on_hover(event, ax, labels, values))
    
    def _draw_bar_chart(self, ax, labels, values, title):
        """Draw vertical bar chart."""
        # Limit to top 20 if too many
        if len(labels) > 20:
            labels = labels[:20]
            values = values[:20]
        
        x = np.arange(len(labels))
        bars = ax.bar(x, values, color=COLORS[0], alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#1d1d1f')
        ax.set_ylabel(tr("Count"), fontsize=11, color='#86868b')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e5e7eb')
        ax.spines['bottom'].set_color('#e5e7eb')
    
    def _draw_line_chart(self, ax, labels, values, title):
        """Draw line chart."""
        x = np.arange(len(labels))
        
        ax.plot(x, values, color=COLORS[0], linewidth=2.5, marker='o', markersize=6, markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(x, values, alpha=0.2, color=COLORS[0])
        
        # Add value labels
        for i, v in enumerate(values):
            ax.text(i, v, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#1d1d1f')
        ax.set_ylabel(tr("Count"), fontsize=11, color='#86868b')
        ax.grid(alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e5e7eb')
        ax.spines['bottom'].set_color('#e5e7eb')
    
    def _draw_pie_chart(self, ax, labels, values, title):
        """Draw pie chart."""
        # Limit to top 10 if too many
        if len(labels) > 10:
            labels = labels[:9] + [tr("Others")]
            values = values[:9] + [sum(values[9:])]
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            colors=COLORS[:len(labels)],
            startangle=90,
            pctdistance=0.85,
            textprops={'fontsize': 10}
        )
        
        # Make pie donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#1d1d1f')
    
    def _draw_horizontal_bar_chart(self, ax, labels, values, title):
        """Draw horizontal bar chart."""
        # Limit to top 20 if too many
        if len(labels) > 20:
            labels = labels[:20]
            values = values[:20]
        
        y = np.arange(len(labels))
        bars = ax.barh(y, values, color=COLORS[0], alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Add value labels
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {value}', ha='left', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color='#1d1d1f')
        ax.set_xlabel(tr("Count"), fontsize=11, color='#86868b')
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e5e7eb')
        ax.spines['bottom'].set_color('#e5e7eb')
    
    def _on_hover(self, event, ax, labels, values):
        """Handle mouse hover for tooltip."""
        if not event.inaxes:
            return
        
        # Find nearest data point
        if hasattr(event, 'xdata') and event.xdata is not None:
            idx = int(round(event.xdata))
            if 0 <= idx < len(labels):
                # Clear previous annotations
                for text in ax.texts:
                    if hasattr(text, '_tooltip'):
                        text.remove()
                
                # Add tooltip
                tooltip = ax.annotate(
                    f'{labels[idx]}: {values[idx]}',
                    xy=(event.xdata, event.ydata),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.9),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    fontsize=10,
                    fontweight='bold'
                )
                tooltip._tooltip = True
                event.canvas.draw_idle()
    
    def _show_no_data(self):
        """Show no data message."""
        for widget in self.chart_container.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.chart_container,
            text=tr("No data available for this dimension"),
            font=ctk.CTkFont(size=16),
            text_color="#86868b"
        ).pack(expand=True)
