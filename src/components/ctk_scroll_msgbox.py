import customtkinter as ctk

class CTkScrollMsgbox(ctk.CTkToplevel):
  def __init__(self, master, title: str, message: str, justify: str = "center",  **kwargs):
    super().__init__(master=master, **kwargs)

    self.title(title)
    self.geometry("700x450")
    
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")

    self._messagebox_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
    self._messagebox_frame.pack(expand=True, fill='both')

    self._messagebox = ctk.CTkLabel(self._messagebox_frame,
                                    wraplength=400,
                                    text=message,
                                    justify=justify)
    
    self._messagebox.pack(padx=10, pady=10, expand=True, fill='both')
    
    self._close_btn =ctk.CTkButton(self,
                                   text="Close",
                                   command=self.destroy)
    
    self._close_btn.pack(side="right", padx=10, pady=10)
