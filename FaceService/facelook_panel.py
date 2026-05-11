import tkinter as tk
from tkinter import messagebox, ttk
import cv2
import face_recognition
import subprocess
import time
from db_manager import init_db, add_user, get_all_users, delete_user

class FacelookPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FACELOOK – User Management")
        self.root.geometry("600x480")
        self.root.resizable(False, False)

        # ----- Enroll Section -----
        enroll_frame = tk.LabelFrame(self.root, text="Enroll New User", padx=10, pady=10)
        enroll_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(enroll_frame, text="Windows Username:").grid(row=0, column=0, sticky="w")
        self.username_entry = tk.Entry(enroll_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5)

        tk.Label(enroll_frame, text="Windows Password:").grid(row=1, column=0, sticky="w")
        self.password_entry = tk.Entry(enroll_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=5)

        enroll_btn = tk.Button(enroll_frame, text="Enroll Face", command=self.enroll)
        enroll_btn.grid(row=2, column=0, columnspan=2, pady=10)

        tk.Label(enroll_frame, text="(Service will be paused during capture)",
                 fg="gray").grid(row=3, column=0, columnspan=2)

        # ----- User List Section -----
        list_frame = tk.LabelFrame(self.root, text="Enrolled Users", padx=10, pady=10)
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.user_list = ttk.Treeview(list_frame, columns=("GUID", "Username"), show="headings", height=8)
        self.user_list.heading("GUID", text="GUID")
        self.user_list.heading("Username", text="Username")
        self.user_list.column("GUID", width=280)
        self.user_list.column("Username", width=120)
        self.user_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.user_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.user_list.configure(yscrollcommand=scrollbar.set)

        delete_btn = tk.Button(self.root, text="Delete Selected User", command=self.delete_selected)
        delete_btn.pack(pady=5)

        # Load users at startup
        self.refresh_list()

    def stop_service(self):
        try:
            subprocess.run(["net", "stop", "FACELOOKService"], capture_output=True,
                           timeout=10, check=False)
            time.sleep(1)   # allow the camera to be released
        except:
            pass

    def start_service(self):
        try:
            subprocess.run(["net", "start", "FACELOOKService"], capture_output=True,
                           timeout=10, check=False)
        except:
            pass

    def enroll(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both fields.")
            return

        # Stop the main service to free the camera
        messagebox.showinfo("Service", "Stopping FACELOOKService briefly to use the camera...")
        self.stop_service()

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)   # DirectShow backend may be more tolerant
        if not cap.isOpened():
            self.start_service()
            messagebox.showerror("Error", "Camera not found!")
            return

        messagebox.showinfo("Capture", "Press SPACE to capture your face.")
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            cv2.imshow("Enrollment - press SPACE", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                break
        cv2.destroyAllWindows()

        if frame is None:
            cap.release()
            self.start_service()
            messagebox.showerror("Error", "Failed to capture frame.")
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        if not boxes:
            cap.release()
            self.start_service()
            messagebox.showerror("Error", "No face detected. Try again.")
            return

        encodings = face_recognition.face_encodings(rgb, boxes)
        if not encodings:
            cap.release()
            self.start_service()
            messagebox.showerror("Error", "Failed to generate embedding.")
            return

        cap.release()
        # Restart the service
        self.start_service()

        guid = add_user(username, password, encodings[0])
        messagebox.showinfo("Success", f"User enrolled!\nGUID: {guid}")
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.refresh_list()

    def delete_selected(self):
        selected = self.user_list.selection()
        if not selected:
            messagebox.showerror("Error", "Select a user to delete.")
            return
        item = self.user_list.item(selected[0])
        guid = item["values"][0]
        username = item["values"][1]
        confirm = messagebox.askyesno("Confirm", f"Delete user {username} ({guid})?")
        if confirm:
            delete_user(guid)
            self.refresh_list()
            messagebox.showinfo("Deleted", f"User {username} removed.")

    def refresh_list(self):
        for row in self.user_list.get_children():
            self.user_list.delete(row)
        init_db()
        for user in get_all_users():
            self.user_list.insert("", "end", values=(user["guid"], user["username"]))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    panel = FacelookPanel()
    panel.run()