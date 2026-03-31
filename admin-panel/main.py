import customtkinter as ctk
import psycopg2
from psycopg2 import Error
from tkinter import messagebox
from tkinter import ttk

# Configuración Base de Tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ParkingAdmin(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Parking GTR - Admin Panel")
        self.geometry("1000x600")
        
        # Configurar conexión a la BD
        self.db_params = {
            "host": "192.168.100.61",
            "database": "parking_gtr",
            "user": "postgres",
            "password": "your_password_here",
            "port": "5432"
        }
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ---- SIDEBAR ----
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Parking GTR", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_refresh = ctk.CTkButton(self.sidebar_frame, text="⟳ Actualizar Datos", command=self.load_data)
        self.btn_refresh.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_complete = ctk.CTkButton(self.sidebar_frame, text="✅ Marcar Completado", fg_color="#2ecc71", hover_color="#27ae60", command=self.mark_completed)
        self.btn_complete.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_delete = ctk.CTkButton(self.sidebar_frame, text="🗑 Eliminar Registro", fg_color="#e74c3c", hover_color="#c0392b", command=self.delete_record)
        self.btn_delete.grid(row=3, column=0, padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Estado: Conectando...", text_color="gray")
        self.status_label.grid(row=5, column=0, padx=20, pady=20, sticky="s")
        
        # ---- MAIN CONTENT ----
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text="Reservaciones Activas", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Treeview for records
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=30, fieldbackground="#2b2b2b", bordercolor="#343638", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#414141", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#505050')])
        
        self.tree = ttk.Treeview(self.main_frame, columns=("ID", "Nombre", "Servicio", "Vehículo", "Fecha y Hora", "Estado"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Cliente")
        self.tree.heading("Servicio", text="Servicio")
        self.tree.heading("Vehículo", text="Vehículo")
        self.tree.heading("Fecha y Hora", text="Fecha de Llegada")
        self.tree.heading("Estado", text="Estado")
        
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Nombre", width=150)
        self.tree.column("Servicio", width=120)
        self.tree.column("Vehículo", width=100)
        self.tree.column("Fecha y Hora", width=150)
        self.tree.column("Estado", width=100, anchor="center")
        
        self.tree.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Cargar datos por primera vez
        self.load_data()

    def get_connection(self):
        try:
            return psycopg2.connect(**self.db_params)
        except Error as e:
            self.status_label.configure(text="Estado: Error de DB", text_color="#e74c3c")
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la Orange Pi.\n{e}")
            return None

    def load_data(self):
        self.status_label.configure(text="Actualizando...", text_color="yellow")
        self.update()
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status FROM reservations ORDER BY created_at DESC;")
                records = cursor.fetchall()
                
                for row in records:
                    date_time = f"{row[4]} {row[5]}" if row[4] and row[5] else "Pendiente"
                    estado = row[6] if row[6] else "pending"
                    
                    self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], date_time, estado))
                    
                self.status_label.configure(text="Estado: Conectado y Listo", text_color="#2ecc71")
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudieron leer los registros.\n{e}")
            finally:
                if cursor: cursor.close()
                if conn: conn.close()
                
    def mark_completed(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Por favor selecciona un registro de la tabla primero.")
            return
            
        record_id = self.tree.item(selected[0])["values"][0]
        
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Marcar como 'completed' en lugar de 'pending'
                cursor.execute("UPDATE reservations SET status = %s WHERE id = %s", ('completed', record_id))
                conn.commit()
                self.load_data()
                messagebox.showinfo("Éxito", f"Registro ID {record_id} marcado como completado.")
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudo actualizar el registro.\n{e}")
            finally:
                if cursor: cursor.close()
                if conn: conn.close()

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Por favor selecciona un registro de la tabla primero.")
            return
            
        record_id = self.tree.item(selected[0])["values"][0]
        cliente = self.tree.item(selected[0])["values"][1]
        
        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar la reservación de '{cliente}' permanentemente?")
        if confirm:
            conn = self.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM reservations WHERE id = %s", (record_id,))
                    conn.commit()
                    self.load_data()
                except Error as e:
                    messagebox.showerror("Error SQL", f"No se pudo eliminar el registro.\n{e}")
                finally:
                    if cursor: cursor.close()
                    if conn: conn.close()

if __name__ == "__main__":
    app = ParkingAdmin()
    app.mainloop()
