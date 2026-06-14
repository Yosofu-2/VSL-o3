"""Interactive matplotlib chart widget for tkinter with hover/zoom support."""
import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Chinese font support
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# Color palette
COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6']


class InteractiveChart(tk.Frame):
    """Interactive matplotlib chart with hover zoom and adaptive sizing."""
    
    def __init__(self, parent, chart_type='bar', title='', labels=None, values=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.chart_type = chart_type
        self.title = title
        self.labels = labels or []
        self.values = values or []
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor='#fafafa')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#fafafa')
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.canvas.mpl_connect('motion_notify_event', self._on_hover)
        self.canvas.mpl_connect('button_press_event', self._on_click)
        
        # Draw initial chart
        self._draw_chart()
        
        # Bind resize event
        self.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        """Handle window resize."""
        if event.widget == self:
            width = event.width / 100  # Convert to inches
            height = event.height / 100
            if width > 4 and height > 3:
                self.fig.set_size_inches(width, height)
                self.canvas.draw_idle()
    
    def _on_hover(self, event):
        """Handle mouse hover for tooltip."""
        if not event.inaxes:
            return
        
        if self.chart_type == 'bar':
            for i, bar in enumerate(self.ax.patches):
                if bar.contains(event)[0]:
                    # Highlight bar
                    for b in self.ax.patches:
                        b.set_alpha(0.3)
                    bar.set_alpha(1.0)
                    self.canvas.draw_idle()
                    
                    # Show tooltip
                    self._show_tooltip(event.xdata, event.ydata, self.labels[i], self.values[i])
                    return
        elif self.chart_type == 'pie':
            for i, wedge in enumerate(self.ax.patches):
                if wedge.contains(event)[0]:
                    # Explode wedge
                    for w in self.ax.patches:
                        w.set_alpha(0.3)
                    wedge.set_alpha(1.0)
                    self.canvas.draw_idle()
                    
                    self._show_tooltip(event.xdata, event.ydata, self.labels[i], self.values[i])
                    return
    
    def _on_click(self, event):
        """Handle click for zoom."""
        if event.button == 1:  # Left click to zoom in
            self.ax.set_xlim(event.xdata - 2, event.xdata + 2)
            self.canvas.draw_idle()
        elif event.button == 3:  # Right click to reset
            self._draw_chart()
    
    def _show_tooltip(self, x, y, label, value):
        """Show tooltip with data info."""
        # Create annotation
        self.ax.annotate(
            f'{label}: {value}',
            xy=(x, y),
            xytext=(10, 10),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0')
        )
        self.canvas.draw_idle()
        
        # Remove annotation after 2 seconds
        self.after(2000, lambda: self._clear_annotations())
    
    def _clear_annotations(self):
        """Clear all annotations."""
        for text in self.ax.texts:
            text.remove()
        self.canvas.draw_idle()
    
    def _draw_chart(self):
        """Draw chart based on type."""
        self.ax.clear()
        
        if not self.labels or not self.values:
            self.ax.text(0.5, 0.5, 'No data available', 
                        ha='center', va='center', fontsize=14, color='gray')
            self.canvas.draw_idle()
            return
        
        if self.chart_type == 'bar':
            self._draw_bar_chart()
        elif self.chart_type == 'line':
            self._draw_line_chart()
        elif self.chart_type == 'pie':
            self._draw_pie_chart()
        elif self.chart_type == 'horizontal_bar':
            self._draw_horizontal_bar_chart()
        
        self.canvas.draw_idle()
    
    def _draw_bar_chart(self):
        """Draw vertical bar chart."""
        n = len(self.labels)
        x = np.arange(n)
        width = 0.6
        
        # Limit to top 20 if too many
        if n > 20:
            x = x[:20]
            labels = self.labels[:20]
            values = self.values[:20]
        else:
            labels = self.labels
            values = self.values
        
        bars = self.ax.bar(x, values, width, color=COLORS[0], alpha=0.8)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value}', ha='center', va='bottom', fontsize=9)
        
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(labels, rotation=45, ha='right')
        self.ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)
        self.ax.set_ylabel('Count', fontsize=11)
        self.ax.grid(axis='y', alpha=0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
    
    def _draw_line_chart(self):
        """Draw line chart."""
        x = np.arange(len(self.labels))
        
        self.ax.plot(x, self.values, color=COLORS[0], linewidth=2, marker='o', markersize=6)
        self.ax.fill_between(x, self.values, alpha=0.3, color=COLORS[0])
        
        # Add value labels
        for i, v in enumerate(self.values):
            self.ax.text(i, v, str(v), ha='center', va='bottom', fontsize=9)
        
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(self.labels, rotation=45, ha='right')
        self.ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)
        self.ax.set_ylabel('Count', fontsize=11)
        self.ax.grid(alpha=0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
    
    def _draw_pie_chart(self):
        """Draw pie chart."""
        # Limit to top 10 if too many
        if len(self.labels) > 10:
            labels = self.labels[:9] + ['Others']
            values = self.values[:9] + [sum(self.values[9:])]
        else:
            labels = self.labels
            values = self.values
        
        wedges, texts, autotexts = self.ax.pie(
            values, 
            labels=labels,
            autopct='%1.1f%%',
            colors=COLORS[:len(labels)],
            startangle=90,
            pctdistance=0.85
        )
        
        # Make pie donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        self.ax.add_artist(centre_circle)
        
        self.ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)
    
    def _draw_horizontal_bar_chart(self):
        """Draw horizontal bar chart."""
        n = len(self.labels)
        y = np.arange(n)
        height = 0.6
        
        # Limit to top 20 if too many
        if n > 20:
            y = y[:20]
            labels = self.labels[:20]
            values = self.values[:20]
        else:
            labels = self.labels
            values = self.values
        
        bars = self.ax.barh(y, values, height, color=COLORS[0], alpha=0.8)
        
        # Add value labels
        for bar, value in zip(bars, values):
            width = bar.get_width()
            self.ax.text(width, bar.get_y() + bar.get_height()/2.,
                        f' {value}', ha='left', va='center', fontsize=9)
        
        self.ax.set_yticks(y)
        self.ax.set_yticklabels(labels)
        self.ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)
        self.ax.set_xlabel('Count', fontsize=11)
        self.ax.grid(axis='x', alpha=0.3)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
    
    def update_data(self, labels, values):
        """Update chart data and redraw."""
        self.labels = labels
        self.values = values
        self._draw_chart()
