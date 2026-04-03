import customtkinter as ctk
import psycopg2
from psycopg2 import Error
from tkinter import messagebox
from tkinter import ttk
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración Base de Tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ParkingAdmin(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Parking GTR - Admin Panel")
        self.geometry("1000x600")
        
        # Configurar conexión a la BD (desde variables de entorno)
        self.db_params = {
            "host": os.getenv("DB_HOST", "192.168.100.61"),
            "database": os.getenv("DB_NAME", "parking_gtr"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "port": os.getenv("DB_PORT", "5432")
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
        
        # Auto-refresh toggle
        self.auto_refresh = False
        self.auto_refresh_id = None
        self.btn_auto = ctk.CTkButton(self.sidebar_frame, text="🔄 Auto-Refresh: OFF", fg_color="#555555", hover_color="#666666", command=self.toggle_auto_refresh)
        self.btn_auto.grid(row=4, column=0, padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Estado: Conectando...", text_color="gray")
        self.status_label.grid(row=6, column=0, padx=20, pady=20, sticky="s")
        
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
        style.configure("Treeview", 
                        background="#1a1a1a", 
                        foreground="#e0e0e0", 
                        rowheight=35, 
                        fieldbackground="#1a1a1a", 
                        bordercolor="#2b2b2b", 
                        borderwidth=0,
                        font=("Helvetica", 10))
        style.map('Treeview', background=[('selected', '#d4af37')], foreground=[('selected', '#000000')])
        style.configure("Treeview.Heading", background="#2a2a2a", foreground="#d4af37", relief="flat", font=("Helvetica", 10, "bold"))
        style.map("Treeview.Heading", background=[('active', '#3a3a3a')])
        
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
        self.user_detail_frame = ctk.CTkScrollableFrame(self.users_split, corner_radius=10, fg_color="#1e1e1e")
        self.user_detail_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        self.show_empty_details()
        
        # Cargar datos por primera vez
        self.load_data()

    def toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.btn_auto.configure(text="🔄 Auto-Refresh: ON", fg_color="#1f538d", hover_color="#1a4570")
            self._auto_refresh_tick()
        else:
            self.btn_auto.configure(text="🔄 Auto-Refresh: OFF", fg_color="#555555", hover_color="#666666")
            if self.auto_refresh_id:
                self.after_cancel(self.auto_refresh_id)
                self.auto_refresh_id = None

    def _auto_refresh_tick(self):
        if not self.auto_refresh:
            return
        self.load_data()
        self.auto_refresh_id = self.after(30000, self._auto_refresh_tick)  # 30 seconds

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
                
    def show_empty_details(self):
        for w in self.user_detail_frame.winfo_children():
            w.destroy()
        
        lbl_icon = ctk.CTkLabel(self.user_detail_frame, text="👤", font=ctk.CTkFont(size=40))
        lbl_icon.pack(pady=(40, 10))
        lbl_text = ctk.CTkLabel(self.user_detail_frame, text="Selecciona un socio\nen la tabla para ver\nsu información.", font=ctk.CTkFont(size=14), text_color="gray")
        lbl_text.pack()
                
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
                    self.show_empty_details()
                    return
                
                # Limpiar el frame derecho (borrar todo antes de renderizar info nueva)
                for w in self.user_detail_frame.winfo_children():
                    w.destroy()
                
                # Datos principales del perfil (del registro más reciente)
                latest = historial[0]
                total_coches = len(historial)
                nombre = latest[0] if latest[0] else "Socio Sin Nombre"
                telefono = latest[1] if latest[1] else "No provisto"
                sub_nivel = latest[2].upper() if latest[2] else "NINGUNO"
                
                # Header del Socio
                hdr_frame = ctk.CTkFrame(self.user_detail_frame, fg_color="transparent")
                hdr_frame.pack(fill="x", pady=(10, 20), padx=10)
                
                name_lbl = ctk.CTkLabel(hdr_frame, text=nombre, font=ctk.CTkFont(size=22, weight="bold"), text_color="#d4af37")
                name_lbl.pack(anchor="w")
                email_lbl = ctk.CTkLabel(hdr_frame, text=email, font=ctk.CTkFont(size=13), text_color="#a0a0a0")
                email_lbl.pack(anchor="w")
                
                # Stats grid
                stats_frame = ctk.CTkFrame(self.user_detail_frame, fg_color="#2b2b2b", corner_radius=8)
                stats_frame.pack(fill="x", padx=10, pady=(0, 20))
                
                ctk.CTkLabel(stats_frame, text="Suscripción:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#d4af37").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
                ctk.CTkLabel(stats_frame, text=sub_nivel, font=ctk.CTkFont(size=14)).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
                
                ctk.CTkLabel(stats_frame, text="Teléfono:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#d4af37").grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
                ctk.CTkLabel(stats_frame, text=telefono, font=ctk.CTkFont(size=14)).grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")
                
                ctk.CTkLabel(stats_frame, text="Vehículos:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#d4af37").grid(row=0, column=2, padx=10, pady=(10, 0), sticky="w")
                ctk.CTkLabel(stats_frame, text=str(total_coches), font=ctk.CTkFont(size=14)).grid(row=1, column=2, padx=10, pady=(0, 10), sticky="w")
                
                # Historial de Vehículos Registrados (Tarjetas)
                title_veh = ctk.CTkLabel(self.user_detail_frame, text="Historial de Vehículos", font=ctk.CTkFont(size=16, weight="bold"))
                title_veh.pack(anchor="w", padx=10, pady=(0, 10))
                
                for r in historial:
                    v_type = r[3].upper() if r[3] else "DESCONOCIDO"
                    v_status = r[4] if r[4] else "pending"
                    v_service = r[2] if r[2] else "N/A"
                    date_str = r[5].strftime("%Y-%m-%d") if r[5] else ""
                    
                    card = ctk.CTkFrame(self.user_detail_frame, fg_color="#242424", corner_radius=8, border_width=1, border_color="#3a3a3a")
                    card.pack(fill="x", padx=10, pady=5)
                    
                    header = ctk.CTkFrame(card, fg_color="transparent")
                    header.pack(fill="x", padx=10, pady=(10, 5))
                    
                    lbl_ti = ctk.CTkLabel(header, text=f"🚘 {v_type}", font=ctk.CTkFont(size=14, weight="bold"))
                    lbl_ti.pack(side="left")
                    
                    # Status badge
                    color_status = "#2ecc71" if v_status == "completed" else "#f39c12"
                    lbl_st = ctk.CTkLabel(header, text=v_status.upper(), text_color=color_status, font=ctk.CTkFont(size=10, weight="bold"))
                    lbl_st.pack(side="right")
                    
                    # Info sub-label
                    lbl_sub = ctk.CTkLabel(card, text=f"Servicio Registrado: {v_service}", text_color="#b0b0b0", font=ctk.CTkFont(size=12))
                    lbl_sub.pack(anchor="w", padx=15, pady=(0, 10))
                
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