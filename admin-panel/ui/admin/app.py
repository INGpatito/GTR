"""
Parking GTR — Admin Panel Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana principal del panel de administración.
Coordina sidebar, tabs, y operaciones de datos.
"""

import datetime

import customtkinter as ctk
from tkinter import messagebox

from config.theme import setup_ctk_theme, GREEN, RED, AMBER
from core.email_service import send_approval_email
from services import reservation_service, member_service
from ui.admin.sidebar import AdminSidebar
from ui.admin.activity_tab import ActivityTab
from ui.admin.members_tab import MembersTab
from ui.admin.security_dialog import SecurityDialog

# Configurar tema global
setup_ctk_theme()


class ParkingAdmin(ctk.CTk):
    """Ventana principal del panel de administración de Parking GTR."""

    def __init__(self):
        super().__init__()
        self.title("Parking GTR - Admin Panel")
        self.geometry("1000x600")

        # ── Layout Grid ──
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──
        self.sidebar = AdminSidebar(
            self,
            callbacks={
                "refresh":  self.load_data,
                "complete": self._mark_completed,
                "delete":   self._delete_record,
            },
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main Content ──
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # ── Tabview ──
        tabview = ctk.CTkTabview(main_frame)
        tabview.grid(row=0, column=0, sticky="nsew")
        tabview.add("Registro de Actividad")
        tabview.add("Directorio de Socios")

        # ── Tabs ──
        self.activity_tab = ActivityTab(
            tabview.tab("Registro de Actividad"),
            on_filter_change=self.load_data,
        )

        self.members_tab = MembersTab(
            tabview.tab("Directorio de Socios"),
            on_select_member=self._on_member_selected,
            on_delete_member=self._delete_member,
            on_security=self._prompt_security,
        )

        # ── Carga inicial ──
        self.load_data()

    # ══════════════════════════════════════════════════
    #  DATA LOADING
    # ══════════════════════════════════════════════════
    def load_data(self) -> None:
        """Carga datos desde la DB y llena ambas tablas."""
        self.sidebar.status.set_status("Actualizando...", "yellow")
        self.update()

        self.activity_tab.clear()
        self.members_tab.clear()

        try:
            # Tab 1: Reservaciones
            records = reservation_service.get_all_reservations(
                pending_only=self.activity_tab.is_pending_only
            )
            for row in records:
                date_time = (
                    f"{row[4]} {row[5]}" if row[4] and row[5] else "Pendiente"
                )
                estado = row[6] if row[6] else "pending"
                self.activity_tab.insert_row(
                    (row[0], row[1], row[2], row[3], date_time, estado)
                )

            # Tab 2: Socios
            users = member_service.get_members_summary()
            for u in users:
                self.members_tab.insert_row((u[0], u[1], u[2], u[3]))

            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.sidebar.status.set_status(f"Estado: Listo ({now})", GREEN)

        except Exception as exc:
            self.sidebar.status.set_status("Estado: Error de DB", RED)
            messagebox.showerror("Error de Conexión", f"No se pudo conectar.\n{exc}")

    # ══════════════════════════════════════════════════
    #  MEMBER DETAILS
    # ══════════════════════════════════════════════════
    def _on_member_selected(self, email: str) -> None:
        """Callback cuando se selecciona un socio en la tabla."""
        try:
            historial = member_service.get_member_details(email)
            if not historial:
                self.members_tab.show_empty_details()
                return

            latest = historial[0]
            self.members_tab.show_member_details(
                email=email,
                nombre=latest[0] if latest[0] else "Socio Sin Nombre",
                telefono=latest[1] if latest[1] else "No provisto",
                sub_nivel=latest[2].upper() if latest[2] else "NINGUNO",
                total_coches=len(historial),
                historial=historial,
            )
        except Exception as exc:
            messagebox.showerror(
                "Error SQL", f"No se pudo cargar detalles del socio.\n{exc}"
            )

    # ══════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════
    def _mark_completed(self) -> None:
        """Marca la reservación seleccionada como completada."""
        values = self.activity_tab.get_selected_values()
        if not values:
            messagebox.showwarning(
                "Atención", "Por favor selecciona un registro de la tabla primero."
            )
            return

        record_id = values[0]

        try:
            user_info = reservation_service.get_user_info_for_approval(record_id)
            reservation_service.mark_completed(record_id)
            self.load_data()

            # Ofrecer envío de correo
            if user_info and user_info[1]:
                nombre = user_info[0] or "Socio"
                email = user_info[1]
                servicio = (user_info[2] or "valet").upper()

                if messagebox.askyesno(
                    "Enviar Notificación",
                    f"Registro ID {record_id} aprobado.\n\n"
                    f"¿Deseas enviar correo de aprobación a {email}?",
                ):
                    self._send_email(nombre, email, servicio)
            else:
                messagebox.showinfo(
                    "Éxito",
                    f"Registro ID {record_id} marcado como completado "
                    "(sin email para notificar).",
                )
        except Exception as exc:
            messagebox.showerror(
                "Error SQL", f"No se pudo actualizar el registro.\n{exc}"
            )

    def _send_email(self, nombre: str, email: str, servicio: str) -> None:
        """Envía correo de aprobación con feedback en la UI."""
        self.sidebar.status.set_status("Enviando correo...", AMBER)
        self.update()

        def on_success():
            self.after(0, lambda: [
                self.sidebar.status.set_status("Estado: Correo enviado ✅", GREEN),
                messagebox.showinfo(
                    "Éxito", f"Correo de aprobación enviado a:\n{email}"
                ),
            ])

        def on_error(msg):
            self.after(0, lambda: [
                self.sidebar.status.set_status("Estado: Error de correo", RED),
                messagebox.showwarning("Error EmailJS", f"No se pudo enviar el correo.\n{msg}"),
            ])

        send_approval_email(nombre, email, servicio, on_success, on_error)

    def _delete_record(self) -> None:
        """Elimina la reservación seleccionada."""
        values = self.activity_tab.get_selected_values()
        if not values:
            messagebox.showwarning(
                "Atención", "Por favor selecciona un registro de la tabla primero."
            )
            return

        record_id = values[0]
        cliente = values[1]

        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la reservación "
            f"de '{cliente}' permanentemente?",
        ):
            try:
                reservation_service.delete_reservation(record_id)
                self.load_data()
            except Exception as exc:
                messagebox.showerror(
                    "Error SQL", f"No se pudo eliminar el registro.\n{exc}"
                )

    def _delete_member(self) -> None:
        """Elimina un socio y todas sus reservaciones."""
        email = self.members_tab.get_selected_email()
        if not email:
            messagebox.showwarning(
                "Atención", "Por favor selecciona un socio de la tabla primero."
            )
            return

        if messagebox.askyesno(
            "Confirmar Eliminación de Socio",
            f"🚨 ATENCIÓN 🚨\n\n"
            f"¿Estás completamente seguro de que quieres eliminar al socio con email:\n"
            f"'{email}'\n\n"
            "Esto borrará TODAS sus reservaciones, vehículos y acceso al portal. "
            "Esta acción no se puede deshacer.",
        ):
            try:
                deleted_count = member_service.delete_member(email)
                self.load_data()
                self.members_tab.show_empty_details()
                messagebox.showinfo(
                    "Éxito",
                    f"Socio eliminado.\n"
                    f"Se eliminaron {deleted_count} registros asociados a {email}.",
                )
            except Exception as exc:
                messagebox.showerror(
                    "Error SQL", f"No se pudo eliminar el socio.\n{exc}"
                )

    # ══════════════════════════════════════════════════
    #  SECURITY
    # ══════════════════════════════════════════════════
    def _prompt_security(self, email: str) -> None:
        """Solicita contraseña de admin antes de abrir datos sensibles."""
        from config.settings import ADMIN_UNLOCK_PASS

        dialog = ctk.CTkInputDialog(
            text="Introduce la contraseña de desbloqueo de administrador:",
            title="Acceso Protegido",
        )
        pwd = dialog.get_input()
        if pwd is None:
            return
        if pwd == ADMIN_UNLOCK_PASS:
            SecurityDialog(self, email)
        else:
            messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.")
