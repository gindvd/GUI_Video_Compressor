import customtkinter as ctk
from typing import Any

class CTkScrollMsgbox(ctk.CTkToplevel):
  """ Top level popup for displaying text from text files """

  def __init__(self, master: Any, title: str, message: str, **kwargs: Any) -> None:
    super().__init__(master=master, **kwargs)

    self.title(title)
    self.geometry("475x700")
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._messagebox = ctk.CTkTextbox(self, wrap="word")
    self._messagebox.pack(expand=True, fill="both", padx=10, pady=10)

    self._messagebox.tag_config("center", justify="center")
    self._messagebox.insert("1.0", message)
    self._messagebox.configure(state="disabled")
    
    self._close_btn =ctk.CTkButton(self,
                                   text="Close",
                                   command=self.destroy)
    
    self._close_btn.pack(side="right", padx=10, pady=10)
