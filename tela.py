"""
Parte 2: tela em Tkinter pra pesquisar um CEP por vez.

A pesquisa roda numa thread separada pra tela não travar enquanto o
Chrome trabalha. Quando o site pede o captcha, a imagem aparece numa
janelinha e o texto digitado volta pro robô.
"""
import base64
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from correios import BuscaCep, CaptchaCancelado, limpar_cep

COLUNAS = ["Rua", "Bairro", "Cidade", "CEP"]


class Tela:
    def __init__(self, root):
        self.root = root
        self.busca = None
        self.fila = queue.Queue()

        root.title("Busca CEP")
        root.geometry("950x350")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.sair)

        topo = ttk.Frame(root)
        topo.pack(fill="x", padx=10, pady=10)

        ttk.Label(topo, text="CEP:").pack(side="left")
        self.entrada = ttk.Entry(topo, width=15, font=("TkDefaultFont", 11))
        self.entrada.pack(side="left", padx=5)
        self.entrada.bind("<Return>", lambda e: self.pesquisar())
        self.entrada.focus()

        self.botao = ttk.Button(topo, text="Pesquisar", command=self.pesquisar)
        self.botao.pack(side="left", padx=5)

        ttk.Button(topo, text="Limpar", command=self.limpar).pack(side="left", padx=5)

        self.status = ttk.Label(topo, text="")
        self.status.pack(side="left", padx=15)

        quadro = ttk.Frame(root)
        quadro.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.arvore = ttk.Treeview(quadro, columns=COLUNAS, show="headings")
        larguras = {"Rua": 330, "Bairro": 200, "Cidade": 220, "CEP": 120}
        for c in COLUNAS:
            self.arvore.heading(c, text=c)
            self.arvore.column(c, width=larguras[c])
        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.arvore.yview)
        self.arvore.configure(yscrollcommand=barra.set)
        self.arvore.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.verificar_fila()

    def limpar(self):
        self.arvore.delete(*self.arvore.get_children())
        self.entrada.delete(0, "end")
        self.entrada.focus()

    def pesquisar(self):
        cep = limpar_cep(self.entrada.get())
        if len(cep) != 8:
            messagebox.showwarning("CEP inválido", "Digite um CEP com 8 números")
            return

        self.botao.config(state="disabled")
        self.status.config(text="Pesquisando...")
        threading.Thread(target=self._pesquisar, args=(cep,), daemon=True).start()

    def _pesquisar(self, cep):
        # roda fora da thread da tela, então não mexe em widget nenhum aqui:
        # só manda recados pela fila e a tela lê eles no verificar_fila
        try:
            if self.busca is None:
                self.busca = BuscaCep(oculto=True)
            enderecos = self.busca.buscar(cep, self.pedir_captcha)
            self.fila.put((self._mostrar, (enderecos,)))
        except CaptchaCancelado:
            self.fila.put((self._fim, ("Pesquisa cancelada",)))
        except Exception as erro:
            self.fila.put((self._erro, (str(erro),)))

    def verificar_fila(self):
        while not self.fila.empty():
            funcao, argumentos = self.fila.get()
            funcao(*argumentos)
        self.root.after(100, self.verificar_fila)

    def _mostrar(self, enderecos):
        for e in enderecos:
            self.arvore.insert("", "end", values=[e[c] for c in COLUNAS])
        self._fim("")
        self.entrada.delete(0, "end")

    def _erro(self, mensagem):
        self._fim("")
        messagebox.showerror("Erro", mensagem)

    def _fim(self, texto):
        self.status.config(text=texto)
        self.botao.config(state="normal")

    def pedir_captcha(self, png):
        """Chamado pela thread da busca. Abre a janela na thread da tela e espera a resposta."""
        resposta = queue.Queue()
        self.fila.put((self._janela_captcha, (png, resposta)))
        return resposta.get()

    def _janela_captcha(self, png, resposta):
        janela = tk.Toplevel(self.root)
        janela.title("Captcha")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        imagem = tk.PhotoImage(data=base64.b64encode(png))
        rotulo = ttk.Label(janela, image=imagem)
        rotulo.image = imagem  # sem isso a imagem some
        rotulo.pack(padx=10, pady=10)

        ttk.Label(janela, text="Digite o texto da imagem:").pack()
        campo = ttk.Entry(janela, width=20, font=("TkDefaultFont", 12))
        campo.pack(pady=5)
        campo.focus()

        respondido = False

        def responder(valor):
            nonlocal respondido
            if respondido:
                return
            respondido = True
            resposta.put(valor)
            janela.destroy()

        botoes = ttk.Frame(janela)
        botoes.pack(pady=(0, 10))
        ttk.Button(botoes, text="OK", command=lambda: responder(campo.get())).pack(side="left", padx=5)
        ttk.Button(botoes, text="Cancelar", command=lambda: responder(None)).pack(side="left", padx=5)
        campo.bind("<Return>", lambda e: responder(campo.get()))
        janela.protocol("WM_DELETE_WINDOW", lambda: responder(None))

    def sair(self):
        if self.busca is not None:
            try:
                self.busca.fechar()
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    Tela(root)
    root.mainloop()
