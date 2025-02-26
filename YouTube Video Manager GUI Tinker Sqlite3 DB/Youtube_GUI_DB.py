import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import webbrowser

class VideoManager:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Manager")
        self.conn = sqlite3.connect('youtube_videos.db')
        self.cursor = self.conn.cursor()
        self.create_table()
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                time TEXT NOT NULL,
                category TEXT,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def setup_gui(self):
        # Main Frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Treeview with Scrollbar
        self.tree = ttk.Treeview(main_frame, columns=('ID', 'Title', 'URL', 'Duration', 'Category', 'Views', 'Created At'), show='headings')
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        # Configure Columns
        columns = [
            ('ID', 50),
            ('Title', 200),
            ('URL', 250),
            ('Duration', 100),
            ('Category', 150),
            ('Views', 80),
            ('Created At', 150)
        ]
        for col, width in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_tree(c, False))
            self.tree.column(col, width=width, anchor=tk.CENTER)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        # Button Frame
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')

        # Buttons
        tk.Button(button_frame, text="Add Video", command=self.add_video_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Update Video", command=self.update_video_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete Video", command=self.delete_video).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Play Video", command=self.play_video).pack(side=tk.LEFT, padx=5)
        
        # Search Frame
        search_frame = tk.Frame(main_frame)
        search_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Go", command=self.search_videos).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Show All", command=self.refresh_treeview).pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.refresh_treeview()

    def sort_tree(self, col, reverse):
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        try:
            if col in ('ID', 'Views'):
                data.sort(key=lambda x: int(x[0]), reverse=reverse)
            else:
                data.sort(reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)

        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        self.tree.heading(col, command=lambda: self.sort_tree(col, not reverse))

    def refresh_treeview(self):
        self.cursor.execute("SELECT * FROM youtube_videos")
        rows = self.cursor.fetchall()
        self.update_treeview(rows)

    def update_treeview(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def add_video_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Video")
        
        fields = ['Title', 'URL', 'Duration', 'Category']
        entries = {}
        
        for i, field in enumerate(fields):
            tk.Label(dialog, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries[field] = entry

        def save():
            try:
                self.cursor.execute(
                    "INSERT INTO youtube_videos (title, url, time, category) VALUES (?, ?, ?, ?)",
                    (entries['Title'].get(), entries['URL'].get(), 
                     entries['Duration'].get(), entries['Category'].get())
                )
                self.conn.commit()
                self.refresh_treeview()
                dialog.destroy()
                messagebox.showinfo("Success", "Video added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add video: {str(e)}")

        tk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=1, sticky=tk.E, padx=5, pady=5)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=len(fields), column=0, sticky=tk.W, padx=5, pady=5)

    def update_video_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to update")
            return
        
        video_id = self.tree.item(selected[0])['values'][0]
        self.cursor.execute("SELECT * FROM youtube_videos WHERE id=?", (video_id,))
        video = self.cursor.fetchone()

        dialog = tk.Toplevel(self.root)
        dialog.title("Update Video")
        
        fields = ['Title', 'URL', 'Duration', 'Category']
        entries = {}
        
        for i, field in enumerate(fields):
            tk.Label(dialog, text=field).grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(dialog, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entry.insert(0, video[i+1])  # Skip ID (index 0)
            entries[field] = entry

        def save():
            try:
                self.cursor.execute(
                    "UPDATE youtube_videos SET title=?, url=?, time=?, category=? WHERE id=?",
                    (entries['Title'].get(), entries['URL'].get(),
                     entries['Duration'].get(), entries['Category'].get(), video_id)
                )
                self.conn.commit()
                self.refresh_treeview()
                dialog.destroy()
                messagebox.showinfo("Success", "Video updated successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update video: {str(e)}")

        tk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=1, sticky=tk.E, padx=5, pady=5)
        tk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=len(fields), column=0, sticky=tk.W, padx=5, pady=5)

    def delete_video(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to delete")
            return
        
        video_id = self.tree.item(selected[0])['values'][0]
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this video?"):
            try:
                self.cursor.execute("DELETE FROM youtube_videos WHERE id=?", (video_id,))
                self.conn.commit()
                self.refresh_treeview()
                messagebox.showinfo("Success", "Video deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete video: {str(e)}")

    def play_video(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a video to play")
            return
        
        video_id = self.tree.item(selected[0])['values'][0]
        url = self.tree.item(selected[0])['values'][2]
        
        try:
            self.cursor.execute("UPDATE youtube_videos SET views = views + 1 WHERE id=?", (video_id,))
            self.conn.commit()
            webbrowser.open(url)
            self.refresh_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {str(e)}")

    def search_videos(self):
        query = self.search_entry.get()
        if not query:
            self.refresh_treeview()
            return
        
        try:
            self.cursor.execute(
                "SELECT * FROM youtube_videos WHERE title LIKE ? OR category LIKE ?",
                (f'%{query}%', f'%{query}%')
            )
            results = self.cursor.fetchall()
            self.update_treeview(results)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def on_close(self):
        self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoManager(root)
    root.mainloop()