import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from .base_view import BaseView

class AnalyticsView(BaseView):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button frame at top
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)
        
        # Exit button
        ttk.Button(
            button_frame,
            text="Close",
            command=self.master.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Top stats panel
        stats_frame = ttk.LabelFrame(container, text="Password Statistics")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_labels = {}
        stats = [
            ("Total Accounts", "total"),
            ("Average Strength", "avg_strength"),
            ("Weak Passwords", "weak"),
            ("Medium Passwords", "medium"),
            ("Strong Passwords", "strong")
        ]
        
        for i, (label, key) in enumerate(stats):
            ttk.Label(stats_frame, text=label).grid(row=0, column=i, padx=10, pady=5)
            self.stats_labels[key] = ttk.Label(stats_frame, text="0")
            self.stats_labels[key].grid(row=1, column=i, padx=10, pady=5)
            
        # Graph panel
        graph_frame = ttk.LabelFrame(container, text="Password Strength History")
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(
            container,
            text="Refresh Analytics",
            command=self.refresh_analytics
        ).pack(pady=10)
        
    def update_stats(self, data):
        """Update statistics display"""
        try:
            for key, label in self.stats_labels.items():
                value = data.get(key, 'N/A')
                if isinstance(value, (int, float)):
                    value = f"{value:.1f}" if isinstance(value, float) else str(value)
                label.config(text=value)
        except Exception as e:
            print(f"Error updating stats: {e}")
            for label in self.stats_labels.values():
                label.config(text="Error")

    def plot_history(self, dates, values):
        """Plot password strength history"""
        try:
            if not dates or not values:
                self.ax.clear()
                self.ax.text(0.5, 0.5, 'No historical data available', 
                           ha='center', va='center')
                self.canvas.draw()
                return
                
            self.ax.clear()
            self.ax.plot(dates, values, marker='o')
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('Average Password Strength')
            self.ax.set_title('Password Strength Over Time')
            self.ax.tick_params(axis='x', rotation=45)
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as e:
            print(f"Error plotting history: {e}")
            self.ax.clear()
            self.ax.text(0.5, 0.5, f'Error plotting data: {str(e)}', 
                       ha='center', va='center')
            self.canvas.draw()
        
    def refresh_analytics(self):
        """Refresh analytics data"""
        self.controller.refresh_analytics()
