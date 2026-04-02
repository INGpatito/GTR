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
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # ---- TABVIEW ----
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew")
        self.tabview.add("Registro de Actividad")
        self.tabview.add("Directorio de Socios")
        
        # --- TAB 1: RESERVACIONES ---
        self.tab1 = self.tabview.tab("Registro de Actividad")
        self.tab1.grid_rowconfigure(1, weight=1)
        self.tab1.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self.tab1, text="Reservaciones Activas", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Estilos aplicados de manera general al Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", rowheight=30, fieldbackground="#2b2b2b", bordercolor="#343638", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#414141", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#505050')])
        
        self.tree = ttk.Treeview(self.tab1, columns=("ID", "Nombre", "Servicio", "Vehículo", "Fecha y Hora", "Estado"), show="headings")
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
        
        # --- TAB 2: SOCIOS (USUARIOS) ---
        self.tab2 = self.tabview.tab("Directorio de Socios")
        self.tab2.grid_rowconfigure(1, weight=1)
        self.tab2.grid_columnconfigure(0, weight=1)
        
        self.users_title = ctk.CTkLabel(self.tab2, text="Directorio de Socios", font=ctk.CTkFont(size=24, weight="bold"))
        self.users_title.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Split frame
        self.users_split = ctk.CTkFrame(self.tab2, fg_color="transparent")
        self.users_split.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.users_split.grid_rowconfigure(0, weight=1)
        self.users_split.grid_columnconfigure(0, weight=3) # Treeview
        self.users_split.grid_columnconfigure(1, weight=2) # Panel

        self.tree_users = ttk.Treeview(self.users_split, columns=("Email", "Nombre", "Vehículos", "Suscripción Mayor"), show="headings")
        self.tree_users.heading("Email", text="Email (Cuenta)")
        self.tree_users.heading("Nombre", text="Último Nombre")
        self.tree_users.heading("Vehículos", text="Total Vehículos")
        self.tree_users.heading("Suscripción Mayor", text="Suscripción")
        
        self.tree_users.column("Email", width=180)
        self.tree_users.column("Nombre", width=150)
        self.tree_users.column("Vehículos", width=80, anchor="center")
        self.tree_users.column("Suscripción Mayor", width=120)
        self.tree_users.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.tree_users.bind("<<TreeviewSelect>>", self.show_user_details)

        # Detail Panel
        self.user_detail_frame = ctk.CTkScrollableFrame(self.users_split, corner_radius=10)
        self.user_detail_frame.grid(row=0, column=1, sticky="nsew")
        
        self.ud_title = ctk.CTkLabel(self.user_detail_frame, text="Detalles del Socio", font=ctk.CTkFont(size=18, weight="bold"))
        self.ud_title.pack(pady=15, padx=10)
        
        self.ud_info = ctk.CTkLabel(self.user_detail_frame, text="Selecciona un correo en la\ntabla para ver información.", justify="left", wraplength=250)
        self.ud_info.pack(pady=10, fill="x", padx=15)
        
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
        
        # Limpiar ambas tablas
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.tree_users.get_children():
            self.tree_users.delete(item)
            
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Cargar TAB 1 (Reservaciones)
                cursor.execute("SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status FROM reservations ORDER BY created_at DESC;")
                records = cursor.fetchall()
                for row in records:
                    date_time = f"{row[4]} {row[5]}" if row[4] and row[5] else "Pendiente"
                    estado = row[6] if row[6] else "pending"
                    self.tree.insert("", "end", values=(row[0], row[1], row[2], row[3], date_time, estado))
                    
                # Cargar TAB 2 (Usuarios/Socios agrupadros)
                cursor.execute("""
                    SELECT email, MAX(full_name), COUNT(id), MAX(service)
                    FROM reservations 
                    WHERE email IS NOT NULL AND email != ''
                    GROUP BY email
                    ORDER BY MAX(created_at) DESC;
                """)
                users = cursor.fetchall()
                for u in users:
                    self.tree_users.insert("", "end", values=(u[0], u[1], u[2], u[3]))
                    
                self.status_label.configure(text="Estado: Conectado y Listo", text_color="#2ecc71")
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudieron leer los registros.\n{e}")
            finally:
                if cursor: cursor.close()
                if conn: conn.close()
                
    def show_user_details(self, event):
        selected = self.tree_users.selection()
        if not selected:
            return
            
        email = self.tree_users.item(selected[0])["values"][0]
        
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Obtener detalles completos de este usuario buscando todos sus historiales
                cursor.execute("""
                    SELECT full_name, phone, service, vehicle, status, created_at
                    FROM reservations
                    WHERE email = %s
                    ORDER BY created_at DESC
                """, (email,))
                historial = cursor.fetchall()
                
                if not historial:
                    self.ud_info.configure(text="No hay datos para este usuario.")
                    return
                
                # Datos principales del perfil (del registro más reciente)
                latest = historial[0]
                total_coches = len(historial)
                
                info_text = (
                    f"👤 Socio: {latest[0]}\n"
                    f"✉️ Email: {email}\n"
                    f"📞 Teléfono: {latest[1] if latest[1] else 'No provisto'}\n"
                    f"⭐ Nivel Principal: {latest[2].upper()}\n"
                    f"🚗 Total Vehículos: {total_coches}\n"
                    f"{'-'*30}\n"
                    f"📋 Historico de Registro:\n"
                )
                
                for idx, r in enumerate(historial):
                    info_text += f"\n  [{idx+1}] {r[3].upper()} ({r[4]})\n      Servicio: {r[2]}"
                    
                self.ud_info.configure(text=info_text)
                
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudo cargar detalles del socio.\n{e}")
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
