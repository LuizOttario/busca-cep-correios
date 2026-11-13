"""
Busca de CEP no site dos Correios usando o Chrome oculto (headless).

O site pede um captcha de imagem em toda busca. O robô não tenta resolver
o captcha: ele tira um print da imagem e passa pra uma função que mostra
pra pessoa e devolve o texto digitado. Assim o Chrome continua oculto e
quem usa só precisa ler a imagem.
"""
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://buscacepinter.correios.com.br/app/endereco/index.php"


class CaptchaCancelado(Exception):
    pass


def limpar_cep(cep):
    return "".join(c for c in str(cep) if c.isdigit())


class BuscaCep:
    def __init__(self, oculto=True):
        opcoes = webdriver.ChromeOptions()
        if oculto:
            opcoes.add_argument("--headless=new")
        opcoes.add_argument("--window-size=1280,900")
        self.navegador = webdriver.Chrome(options=opcoes)
        self.espera = WebDriverWait(self.navegador, 20)

    def fechar(self):
        self.navegador.quit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()

    def _imagem_captcha(self):
        img = self.navegador.find_element(By.ID, "captcha_image")
        # espera a imagem terminar de carregar antes do print
        for _ in range(20):
            pronta = self.navegador.execute_script(
                "return arguments[0].complete && arguments[0].naturalWidth > 0", img
            )
            if pronta:
                break
            time.sleep(0.25)
        return img.screenshot_as_png

    def _resultado_da_tentativa(self):
        """Espera o site responder. Devolve None se deu certo ou a mensagem de erro."""
        # quando dá erro (captcha errado, por exemplo) o site mostra a mensagem
        # numa caixinha #alerta, por isso olho o texto dela
        def respondeu(nav):
            erro = nav.execute_script(
                "return document.querySelector('#alerta .msg').textContent.trim()"
            )
            if erro:
                return ("erro", erro)
            msg = nav.find_element(By.ID, "mensagem-resultado")
            if msg.get_attribute("hidden") is None:
                return ("ok", None)
            return False

        status, erro = self.espera.until(respondeu)
        return erro if status == "erro" else None

    def buscar(self, cep, pedir_captcha, tentativas=3):
        """
        Pesquisa um CEP e devolve uma lista de dicts com rua, bairro, cidade e cep.

        pedir_captcha recebe os bytes do PNG do captcha e precisa devolver o texto
        digitado (ou None pra desistir).
        """
        cep = limpar_cep(cep)
        if len(cep) != 8:
            raise ValueError(f"CEP inválido: {cep}")

        nav = self.navegador
        nav.get(URL)
        campo = self.espera.until(EC.presence_of_element_located((By.ID, "endereco")))
        campo.send_keys(cep)

        for tentativa in range(1, tentativas + 1):
            nav.execute_script("document.querySelector('#alerta .msg').textContent = ''")
            # quando o captcha erra o site troca a imagem, dou um tempo pra ela mudar
            if tentativa > 1:
                time.sleep(1.5)

            texto = pedir_captcha(self._imagem_captcha())
            if not texto:
                raise CaptchaCancelado()

            campo_captcha = nav.find_element(By.ID, "captcha")
            campo_captcha.clear()
            campo_captcha.send_keys(texto.strip())
            nav.execute_script("document.getElementById('btn_pesquisar').click()")

            erro = self._resultado_da_tentativa()
            if erro is None:
                return self._ler_tabela(cep)
            print(f"Site respondeu: {erro} (tentativa {tentativa} de {tentativas})")

        raise RuntimeError(f"Não consegui pesquisar o CEP {cep} depois de {tentativas} tentativas")

    def _ler_tabela(self, cep):
        linhas = self.navegador.find_elements(By.CSS_SELECTOR, "#resultado-DNEC tbody tr")
        enderecos = []
        for linha in linhas:
            colunas = [td.text.strip() for td in linha.find_elements(By.TAG_NAME, "td")]
            if len(colunas) < 4:
                continue
            enderecos.append({
                "Rua": colunas[0],
                "Bairro": colunas[1],
                "Cidade": colunas[2],
                "CEP": colunas[3],
            })
        if not enderecos:
            enderecos.append({"Rua": "", "Bairro": "", "Cidade": "", "CEP": f"{cep} (não encontrado)"})
        return enderecos
