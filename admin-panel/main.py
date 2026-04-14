import customtkinter as ctk
import psycopg2
from psycopg2 import Error
from tkinter import messagebox, simpledialog
from tkinter import ttk
import os
import bcrypt
import requests
import threading
import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde admin-panel/.env
_script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_script_dir, ".env"))

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
        self.admin_unlock_pass = os.getenv("ADMIN_UNLOCK_PASS", "admin123")
        
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
        
        self.tab1_header = ctk.CTkFrame(self.tab1, fg_color="transparent")
        self.tab1_header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.tab1_header.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(self.tab1_header, text="Registro de Actividad", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        
        self.filter_pending_var = ctk.BooleanVar(value=False)
        self.chk_filter = ctk.CTkCheckBox(
            self.tab1_header,
            text="🚨 Mostrar SÓLO Pendientes",
            variable=self.filter_pending_var,
            command=self.load_data,
            fg_color="#d4af37",
            hover_color="#b5952f"
        )
        self.chk_filter.grid(row=0, column=2, sticky="e")
        
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
        
        self.tab2_header = ctk.CTkFrame(self.tab2, fg_color="transparent")
        self.tab2_header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.tab2_header.grid_columnconfigure(0, weight=1)
        
        self.users_title = ctk.CTkLabel(self.tab2_header, text="Directorio de Socios", font=ctk.CTkFont(size=24, weight="bold"))
        self.users_title.grid(row=0, column=0, sticky="w")
        
        self.btn_delete_member = ctk.CTkButton(self.tab2_header, text="🗑 Eliminar Socio", fg_color="#e74c3c", hover_color="#c0392b", width=140, command=self.delete_member)
        self.btn_delete_member.grid(row=0, column=1, sticky="e")

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
                if hasattr(self, 'filter_pending_var') and self.filter_pending_var.get():
                    cursor.execute("SELECT id, full_name, service, vehicle, arrival_date, arrival_time, status FROM reservations WHERE status = 'pending' OR status IS NULL ORDER BY created_at DESC;")
                else:
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
                    
                now = datetime.datetime.now().strftime("%H:%M:%S")
                self.status_label.configure(text=f"Estado: Listo ({now})", text_color="#2ecc71")
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
                    SELECT full_name, phone, service, vehicle, status, created_at, id, license_plate
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
                hdr_frame.grid_columnconfigure(0, weight=1)
                
                info_f = ctk.CTkFrame(hdr_frame, fg_color="transparent")
                info_f.grid(row=0, column=0, sticky="w")
                
                name_lbl = ctk.CTkLabel(info_f, text=nombre, font=ctk.CTkFont(size=22, weight="bold"), text_color="#d4af37")
                name_lbl.pack(anchor="w")
                email_lbl = ctk.CTkLabel(info_f, text=email, font=ctk.CTkFont(size=13), text_color="#a0a0a0")
                email_lbl.pack(anchor="w")
                
                btn_security = ctk.CTkButton(hdr_frame, text="🔒 Seguridad", width=100, fg_color="#c0392b", hover_color="#922b21", command=lambda: self.prompt_security(email))
                btn_security.grid(row=0, column=1, sticky="e")
                
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
                # Obtener datos del usuario antes de aprobar
                cursor.execute("SELECT full_name, email, service FROM reservations WHERE id = %s", (record_id,))
                user_row = cursor.fetchone()
                
                # Marcar como 'completed'
                cursor.execute("UPDATE reservations SET status = %s WHERE id = %s", ('completed', record_id))
                conn.commit()
                self.load_data()
                
                # Enviar correo de aprobación
                if user_row and user_row[1]:  # Si tiene email
                    nombre = user_row[0] or "Socio"
                    email = user_row[1]
                    servicio = (user_row[2] or "valet").upper()
                    
                    send_email = messagebox.askyesno(
                        "Enviar Notificación",
                        f"Registro ID {record_id} aprobado.\n\n¿Deseas enviar correo de aprobación a {email}?"
                    )
                    if send_email:
                        self.send_approval_email(nombre, email, servicio)
                else:
                    messagebox.showinfo("Éxito", f"Registro ID {record_id} marcado como completado (sin email para notificar).")
                    
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudo actualizar el registro.\n{e}")
            finally:
                if cursor: cursor.close()
                if conn: conn.close()

    def send_approval_email(self, to_name, to_email, membership_type):
        """Envía correo de aprobación via EmailJS REST API en un hilo separado."""
        self.status_label.configure(text="Enviando correo...", text_color="#f39c12")
        self.update()
        
        def _send():
            try:
                payload = {
                    "service_id": "service_h4dij37",
                    "template_id": "template_r4gkv6g",
                    "user_id": "BaTFzWtSBU0bZ_lKj",
                    "accessToken": "oXznojZUyeBLPnRk_GqNj",
                    "template_params": {
                        "to_name": to_name,
                        "to_email": to_email,
                        "membership_type": membership_type
                    }
                }
                
                response = requests.post(
                    "https://api.emailjs.com/api/v1.0/email/send",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    self.after(0, lambda: [
                        self.status_label.configure(text="Estado: Correo enviado ✅", text_color="#2ecc71"),
                        messagebox.showinfo("Éxito", f"Correo de aprobación enviado a:\n{to_email}")
                    ])
                else:
                    self.after(0, lambda: [
                        self.status_label.configure(text="Estado: Error de correo", text_color="#e74c3c"),
                        messagebox.showwarning("Error EmailJS", f"No se pudo enviar el correo.\nCódigo: {response.status_code}\n{response.text}")
                    ])
            except Exception as e:
                self.after(0, lambda: [
                    self.status_label.configure(text="Estado: Error de red", text_color="#e74c3c"),
                    messagebox.showerror("Error de Red", f"No se pudo conectar a EmailJS:\n{e}")
                ])
        
        # Ejecutar en hilo separado para no congelar la UI
        threading.Thread(target=_send, daemon=True).start()

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
                    
    def delete_member(self):
        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Atención", "Por favor selecciona un socio de la tabla primero.")
            return
            
        email = self.tree_users.item(selected[0])["values"][0]
        
        confirm = messagebox.askyesno("Confirmar Eliminación de Socio", f"🚨 ATENCIÓN 🚨\n\n¿Estás completamente seguro de que quieres eliminar al socio con email:\n'{email}'\n\nEsto borrará TODAS sus reservaciones, vehículos y acceso al portal. Esta acción no se puede deshacer.")
        if confirm:
            conn = self.get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # Delete all rows matching this email
                    cursor.execute("DELETE FROM reservations WHERE email = %s", (email,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    self.load_data()
                    self.show_empty_details()  # Clear the panel just in case
                    messagebox.showinfo("Éxito", f"Socio eliminado.\nSe eliminaron {deleted_count} registros asociados a {email}.")
                except Error as e:
                    messagebox.showerror("Error SQL", f"No se pudo eliminar el socio.\n{e}")
                finally:
                    if cursor: cursor.close()
                    if conn: conn.close()

    def prompt_security(self, email):
        dialog = ctk.CTkInputDialog(text="Introduce la contraseña de desbloqueo de administrador:", title="Acceso Protegido")
        pwd = dialog.get_input()
        if pwd is None:
            return
        if pwd == self.admin_unlock_pass:
            self.open_security_window(email)
        else:
            messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.")
            
    def open_security_window(self, email):
        toplevel = ctk.CTkToplevel(self)
        toplevel.title(f"Datos Sensibles - {email}")
        toplevel.geometry("500x600")
        toplevel.grab_set()
        
        container = ctk.CTkScrollableFrame(toplevel)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(container, text="Modificar Seguridad y Accesos", font=ctk.CTkFont(size=20, weight="bold"), text_color="#d4af37").pack(anchor="w", pady=(0, 20))
        
        # Cambio de contraseña
        ctk.CTkLabel(container, text="Nueva Contraseña Usuario:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        pwd_entry = ctk.CTkEntry(container, placeholder_text="Mínimo 6 caracteres", width=300, show="*")
        pwd_entry.pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(container, text="Vehículos (Matrículas)", font=ctk.CTkFont(size=16, weight="bold"), text_color="#d4af37").pack(anchor="w", pady=(10, 10))
        
        # Obtener todas las reservaciones (coches del usuario) para editar matrícula
        conn = self.get_connection()
        plate_entries = {} # record_id -> CTkEntry
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, vehicle, license_plate, service FROM reservations WHERE email = %s ORDER BY created_at DESC", (email,))
                vehiculos = cursor.fetchall()
                
                for v in vehiculos:
                    v_id = v[0]
                    v_type = v[1].upper() if v[1] else "VEHICULO"
                    v_plate = v[2] if v[2] else ""
                    
                    frame = ctk.CTkFrame(container, fg_color="#2b2b2b")
                    frame.pack(fill="x", pady=5)
                    
                    ctk.CTkLabel(frame, text=f"Auto: {v_type} (ID: {v_id})").pack(side="left", padx=10, pady=10)
                    
                    entry = ctk.CTkEntry(frame, width=120)
                    entry.insert(0, v_plate)
                    entry.pack(side="right", padx=10, pady=10)
                    
                    plate_entries[v_id] = entry
                    
            except Error as e:
                messagebox.showerror("Error", f"Error cargando vehículos: {e}")
            finally:
                if cursor: cursor.close()
                if conn: conn.close()
                
        def save_changes():
            new_pwd = pwd_entry.get().strip()
            
            save_conn = self.get_connection()
            if not save_conn: return
            
            try:
                cur = save_conn.cursor()
                
                # Guardar placas
                for v_id, entry in plate_entries.items():
                    placa = entry.get().strip()
                    cur.execute("UPDATE reservations SET license_plate = %s WHERE id = %s", (placa, v_id))
                
                # Actualizar password si hay
                if new_pwd:
                    if len(new_pwd) < 4:
                        messagebox.showwarning("Inseguro", "La contraseña es muy corta.")
                        return
                    salt = bcrypt.gensalt(rounds=12)
                    hashed = bcrypt.hashpw(new_pwd.encode('utf-8'), salt).decode('utf-8')
                    # Actualiza en todas las reservaciones ligadas a este email para consistencia de inicio de sesión
                    cur.execute("UPDATE reservations SET password_hash = %s WHERE email = %s", (hashed, email))
                
                save_conn.commit()
                messagebox.showinfo("Éxito", "Cambios guardados de forma segura en la Bóveda.")
                toplevel.destroy()
                
            except Error as e:
                messagebox.showerror("Error SQL", f"No se pudo guardar: {e}")
            finally:
                if cur: cur.close()
                if save_conn: save_conn.close()
                
        # Boton Guardar
        btn_save = ctk.CTkButton(container, text="Guardar Cambios", fg_color="#2ecc71", hover_color="#27ae60", command=save_changes)
        btn_save.pack(pady=20)

if __name__ == "__main__":
    app = ParkingAdmin()
    app.mainloop()