import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
from datetime import datetime
import threading  # ✅ Still used for DB tasks

# ---------- Database Connection ----------
def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="admin123",
        database="hostel_db"
    )

def execute(query, params=()):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        return str(e)

def fetch(query, params=()):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows
    except:
        return []

# ---------- Main Window ----------
root = tk.Tk()
root.title("Hostel Management System")
root.geometry("520x320")

ttk.Label(root, text="Student Hostel Tracker", font=("Helvetica", 16, "bold")).pack(pady=20)
ttk.Button(root, text="Admin", command=lambda: [root.withdraw(), open_admin_login()]).pack(pady=10)
ttk.Button(root, text="Student Going Out", command=lambda: [root.withdraw(), open_student_window()]).pack(pady=10)
ttk.Button(root, text="Student Coming In", command=lambda: [root.withdraw(), open_student_in_window()]).pack(pady=10)

# ---------- Admin Login ----------
def open_admin_login():
    login_win = tk.Toplevel(root)
    login_win.title("Admin Login")
    login_win.geometry("300x200")

    ttk.Label(login_win, text="Username").pack(pady=5)
    username_entry = ttk.Entry(login_win)
    username_entry.pack(pady=5)

    ttk.Label(login_win, text="Password").pack(pady=5)
    password_entry = ttk.Entry(login_win, show="*")
    password_entry.pack(pady=5)

    def check_login():
        if username_entry.get() == "admin" and password_entry.get() == "admin123":
            login_win.destroy()
            open_admin_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    ttk.Button(login_win, text="Login", command=check_login).pack(pady=10)
    ttk.Button(login_win, text="Back", command=lambda: [login_win.destroy(), root.deiconify()]).pack(pady=5)

# ---------- Admin Dashboard ----------
admin_students_tv = None
admin_outings_tv = None

def open_admin_dashboard():
    global admin_students_tv, admin_outings_tv
    dash = tk.Toplevel(root)
    dash.title("Admin Dashboard")
    dash.geometry("1000x700")

    # Left panel
    left = ttk.Frame(dash, padding=12)
    left.pack(side=tk.LEFT, fill=tk.Y)

    ttk.Label(left, text="Manage Students", font=("Helvetica", 12, "bold")).pack(pady=6)

    fields = {k: ttk.Entry(left) for k in ["Name", "Room", "Course", "Year", "Parent Phone"]}
    for k, e in fields.items():
        ttk.Label(left, text=k).pack(anchor=tk.W)
        e.pack(fill=tk.X, pady=4)

    def add_student():
        values = [e.get().strip() for e in fields.values()]
        if not values[0] or not values[-1]:
            return messagebox.showerror("Error", "Name & Parent Phone required")
        res = execute(
            "INSERT INTO students (name, room_no, course, year, parent_phone) VALUES (%s,%s,%s,%s,%s)",
            tuple(values)
        )
        if res == True:
            messagebox.showinfo("Success", f"Student {values[0]} added")
            refresh_admin_tables()
            for e in fields.values(): e.delete(0, tk.END)
        else:
            messagebox.showerror("DB Error", res)

    ttk.Label(left, text="Delete Student (Enter ID)").pack(anchor=tk.W, pady=(12,0))
    del_id_entry = ttk.Entry(left)
    del_id_entry.pack(fill=tk.X, pady=4)

    def delete_student():
        sid = del_id_entry.get().strip()
        if not sid.isdigit():
            return messagebox.showerror("Error", "Enter valid numeric ID")
        confirm = messagebox.askyesno("Confirm", f"Delete Student ID {sid}?")
        if not confirm:
            return
        execute("DELETE FROM outings WHERE student_id=%s", (sid,))
        res = execute("DELETE FROM students WHERE student_id=%s", (sid,))
        if res == True:
            messagebox.showinfo("Deleted", f"Student ID {sid} deleted")
            del_id_entry.delete(0, tk.END)
            refresh_admin_tables()
        else:
            messagebox.showerror("DB Error", res)

    # Buttons for Add/Delete
    btn_frame = ttk.Frame(left)
    btn_frame.pack(pady=10, fill=tk.X)
    ttk.Button(btn_frame, text="Add Student", command=add_student).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
    ttk.Button(btn_frame, text="Delete Student", command=delete_student).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    # Back button
    ttk.Button(left, text="Back", command=lambda: [dash.destroy(), root.deiconify()]).pack(pady=15, fill=tk.X)

    # Middle panel
    mid = ttk.Frame(dash, padding=8)
    mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ttk.Label(mid, text="Students", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
    admin_students_tv = ttk.Treeview(mid, columns=("ID","Name","Room","Course","Year","Parent"), show="headings", height=10)
    for c in admin_students_tv["columns"]:
        admin_students_tv.heading(c, text=c)
        admin_students_tv.column(c, width=120)
    admin_students_tv.pack(fill=tk.BOTH, expand=True, pady=6)

    ttk.Label(mid, text="Outings", font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=(12,0))
    outings_cols = ("OID","SID","Name","Room","Parent","Reason","Place","Out","In")
    admin_outings_tv = ttk.Treeview(mid, columns=outings_cols, show="headings", height=10)
    for c in outings_cols:
        admin_outings_tv.heading(c, text=c)
        admin_outings_tv.column(c, width=110)
    admin_outings_tv.pack(fill=tk.BOTH, expand=True, pady=6)

    refresh_admin_tables()

def refresh_admin_tables():
    global admin_students_tv, admin_outings_tv
    # Students
    admin_students_tv.delete(*admin_students_tv.get_children())
    for row in fetch("SELECT student_id, name, room_no, course, year, parent_phone FROM students"):
        admin_students_tv.insert("", tk.END, values=row)
    # Outings
    admin_outings_tv.delete(*admin_outings_tv.get_children())
    for row in fetch("""SELECT o.outing_id, s.student_id, s.name, s.room_no, s.parent_phone,
                        o.reason, o.place, o.time_out, o.time_in
                        FROM outings o JOIN students s ON o.student_id = s.student_id"""):
        admin_outings_tv.insert("", tk.END, values=row)

# ---------- Student Going Out ----------
def open_student_window():
    st = tk.Toplevel(root)
    st.title("Student Outing (Going Out)")
    st.geometry("420x380")

    ttk.Label(st, text="Student Outing Form", font=("Helvetica", 14, "bold")).pack(pady=8)
    ttk.Label(st, text="Student ID").pack(anchor=tk.W, padx=12)
    students_list = fetch("SELECT student_id,name,parent_phone FROM students")
    student_ids = [f"{r[0]} - {r[1]}" for r in students_list]
    sid_combo = ttk.Combobox(st, values=student_ids)
    sid_combo.pack(fill=tk.X, padx=12, pady=4)

    ttk.Label(st, text="Parent Phone").pack(anchor=tk.W, padx=12)
    parent_entry = ttk.Entry(st)
    parent_entry.pack(fill=tk.X, padx=12, pady=4)

    ttk.Label(st, text="Reason").pack(anchor=tk.W, padx=12)
    s_reason = ttk.Entry(st)
    s_reason.pack(fill=tk.X, padx=12, pady=4)

    ttk.Label(st, text="Place").pack(anchor=tk.W, padx=12)
    s_place = ttk.Entry(st)
    s_place.pack(fill=tk.X, padx=12, pady=4)

    def autofill_parent(event=None):
        sel = sid_combo.get().strip()
        if sel:
            sid = int(sel.split(" - ")[0])
            res = fetch("SELECT parent_phone FROM students WHERE student_id=%s", (sid,))
            if res:
                parent_entry.delete(0, tk.END)
                parent_entry.insert(0, res[0][0])

    sid_combo.bind("<<ComboboxSelected>>", autofill_parent)

    # ---------- Threaded Submit ----------
    def submit_outing():
        sel = sid_combo.get().strip()
        if not sel: return messagebox.showerror("Error", "Select Student ID")
        sid = int(sel.split(" - ")[0])
        reason, place, parent_phone = s_reason.get().strip(), s_place.get().strip(), parent_entry.get().strip()
        if not reason or not place or not parent_phone:
            return messagebox.showerror("Error", "All fields required")
        now = datetime.now()

        def db_task():
            res = execute("INSERT INTO outings (student_id, reason, place, time_out) VALUES (%s,%s,%s,%s)",
                          (sid, reason, place, now))
            if res == True:
                root.after(0, lambda: [
                    messagebox.showinfo("Success", "Outing recorded"),
                    s_reason.delete(0, tk.END),
                    s_place.delete(0, tk.END),
                    refresh_admin_tables()
                ])
            else:
                root.after(0, lambda: messagebox.showerror("DB Error", res))

        threading.Thread(target=db_task).start()

    ttk.Button(st, text="Submit Outing", command=submit_outing).pack(pady=6)
    ttk.Button(st, text="Back", command=lambda: [st.destroy(), root.deiconify()]).pack(pady=6)

# ---------- Student Coming In ----------
def open_student_in_window():
    st_in = tk.Toplevel(root)
    st_in.title("Student Returning (Coming In)")
    st_in.geometry("350x240")

    ttk.Label(st_in, text="Student Returning Form", font=("Helvetica", 14, "bold")).pack(pady=8)
    ttk.Label(st_in, text="Student ID").pack(anchor=tk.W, padx=12)

    students_list = fetch("SELECT student_id,name,parent_phone FROM students")
    student_ids = [f"{r[0]} - {r[1]}" for r in students_list]
    sid_combo = ttk.Combobox(st_in, values=student_ids)
    sid_combo.pack(fill=tk.X, padx=12, pady=6)

    def submit_return():
        sel = sid_combo.get().strip()
        if not sel:
            return messagebox.showerror("Error", "Select Student ID")
        sid = int(sel.split(" - ")[0])
        now = datetime.now()
        res = execute("UPDATE outings SET time_in=%s WHERE student_id=%s AND time_in IS NULL ORDER BY outing_id DESC LIMIT 1",
                      (now, sid))
        if res == True:
            messagebox.showinfo("Success", "Return time recorded")
            try: refresh_admin_tables()
            except: pass
        else:
            messagebox.showerror("DB Error", res)

    ttk.Button(st_in, text="Mark Return", command=submit_return).pack(pady=6)
    ttk.Button(st_in, text="Back", command=lambda: [st_in.destroy(), root.deiconify()]).pack(pady=6)

root.mainloop()
