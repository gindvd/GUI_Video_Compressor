import customtkinter as ctk

class CTkScrollMsgbox(ctk.CTkToplevel):
  def __init__(self, master, title: str, message: str, **kwargs):
    super().__init__(master=master, **kwargs)

    self.title(title)
    self.geometry("600x400")

    self._messagebox = ctk.CTkTextbox(self, wrap="word")
    self._messagebox.pack(expand=True,fill="both", padx=10, pady=10)

    self._messagebox.insert("1.0", message)
    self._messagebox.configure(state="disabled")
    
    self._close_btn =ctk.CTkButton(self,
                                   text="Close",
                                   command=self.destroy)
    
    self._close_btn.pack(side="right", padx=10, pady=10)
