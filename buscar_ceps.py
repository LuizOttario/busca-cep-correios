"""
Parte 1: lê os CEPs do ceps.txt (a primeira linha é o título e é pulada),
pesquisa um por um no site dos Correios e salva o resultado em enderecos.xlsx.

A cada CEP a imagem do captcha é aberta no visualizador de imagens e
o texto é digitado aqui no terminal.
"""
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from correios import BuscaCep, CaptchaCancelado

PASTA = Path(__file__).parent
ARQ_CEPS = PASTA / "ceps.txt"
ARQ_SAIDA = PASTA / "enderecos.xlsx"
ARQ_CAPTCHA = PASTA / "captcha.png"


def abrir_imagem(caminho):
    if sys.platform == "win32":
        os.startfile(caminho)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", caminho])
    else:
        subprocess.Popen(["xdg-open", caminho], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pedir_captcha_no_terminal(png):
    ARQ_CAPTCHA.write_bytes(png)
    abrir_imagem(ARQ_CAPTCHA)
    return input("Digite o texto do captcha (Enter vazio pula o CEP): ")


def ler_ceps(caminho):
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in linhas[1:] if l.strip()]


def main():
    ceps = ler_ceps(ARQ_CEPS)
    print(f"{len(ceps)} CEPs pra pesquisar\n")

    resultado = []
    with BuscaCep(oculto=True) as busca:
        for cep in ceps:
            print(f"Pesquisando {cep}...")
            try:
                enderecos = busca.buscar(cep, pedir_captcha_no_terminal)
            except CaptchaCancelado:
                print("Pulado\n")
                continue
            except Exception as erro:
                print(f"Erro: {erro}\n")
                continue

            for e in enderecos:
                print(f"  {e['Rua']} | {e['Bairro']} | {e['Cidade']} | {e['CEP']}")
            print()
            resultado.extend(enderecos)

    ARQ_CAPTCHA.unlink(missing_ok=True)

    if resultado:
        pd.DataFrame(resultado).to_excel(ARQ_SAIDA, index=False)
        print(f"Resultado salvo em {ARQ_SAIDA.name}")


if __name__ == "__main__":
    main()
