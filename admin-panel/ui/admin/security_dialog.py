"""
Parking GTR — Security Dialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana de datos sensibles para modificar contraseñas y matrículas.
"""

import customtkinter as ctk
from tkinter import messagebox

from config.theme import GOLD, GREEN, GREEN_HOVER
from core.crypto import hash_password
from services.member_service import get_vehicles_for_email, update_license_plate, update_password


class SecurityDialog(ctk.CTkToplevel):
    """Diálogo modal para edición de seguridad y accesos de un socio."""

    def __init__(self, master, email: str, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"Datos Sensibles - {email}")
        self.geometry("500x600")
        self.grab_set()

        self._email = email
        self._plate_entries: dict[int, ctk.CTkEntry] = {}

        container = ctk.CTkScrollableFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # ── Título ──
        ctk.CTkLabel(
            container,
            text="Modificar Seguridad y Accesos",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=GOLD,
        ).pack(anchor="w", pady=(0, 20))

        # ── Cambio de Contraseña ──
        ctk.CTkLabel(
            container,
            text="Nueva Contraseña Usuario:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w")

        self._pwd_entry = ctk.CTkEntry(
            container,
            placeholder_text="Mínimo 6 caracteres",
            width=300,
            show="*",
        )
        self._pwd_entry.pack(anchor="w", pady=(0, 20))

        # ── Vehículos (Matrículas) ──
        ctk.CTkLabel(
            container,
            text="Vehículos (Matrículas)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=GOLD,
        ).pack(anchor="w", pady=(10, 10))

        self._load_vehicles(container)

        # ── Botón Guardar ──
        ctk.CTkButton(
            container,
            text="Guardar Cambios",
            fg_color=GREEN,
            hover_color=GREEN_HOVER,
            command=self._save_changes,
        ).pack(pady=20)

    def _load_vehicles(self, container: ctk.CTkFrame) -> None:
        """Carga los vehículos del socio y crea entries para editar placas."""
        try:
            vehiculos = get_vehicles_for_email(self._email)

            for v in vehiculos:
                v_id = v[0]
                v_type = v[1].upper() if v[1] else "VEHICULO"
                v_plate = v[2] if v[2] else ""

                frame = ctk.CTkFrame(container, fg_color="#2b2b2b")
                frame.pack(fill="x", pady=5)

                ctk.CTkLabel(
                    frame,
                    text=f"Auto: {v_type} (ID: {v_id})",
                ).pack(side="left", padx=10, pady=10)

                entry = ctk.CTkEntry(frame, width=120)
                entry.insert(0, v_plate)
                entry.pack(side="right", padx=10, pady=10)

                self._plate_entries[v_id] = entry

        except Exception as exc:
            messagebox.showerror("Error", f"Error cargando vehículos: {exc}")

    def _save_changes(self) -> None:
        """Guarda cambios de placas y contraseña."""
        new_pwd = self._pwd_entry.get().strip()

        try:
            # Guardar placas
            for v_id, entry in self._plate_entries.items():
                placa = entry.get().strip()
                update_license_plate(v_id, placa)

            # Actualizar contraseña si se proporcionó
            if new_pwd:
                if len(new_pwd) < 4:
                    messagebox.showwarning("Inseguro", "La contraseña es muy corta.")
                    return
                hashed = hash_password(new_pwd)
                update_password(self._email, hashed)

            messagebox.showinfo(
                "Éxito", "Cambios guardados de forma segura en la Bóveda."
            )
            self.destroy()

        except Exception as exc:
            messagebox.showerror("Error SQL", f"No se pudo guardar: {exc}")
