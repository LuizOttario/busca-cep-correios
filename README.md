# Busca de CEP nos Correios

Projeto da seção 23 do curso de Python + RPA.

Robô em Selenium que pesquisa CEPs no [Busca CEP dos Correios](https://buscacepinter.correios.com.br/app/endereco/index.php) com o Chrome oculto e traz rua, bairro, cidade e CEP.

## Sobre o captcha

Quando o curso foi gravado o site não tinha captcha. Hoje toda busca pede um captcha de imagem. O robô não tenta adivinhar: ele tira um print só da imagem do captcha e mostra pra você digitar. O resto (abrir o site, preencher o CEP, clicar em buscar e ler a tabela) continua automático e com o Chrome oculto.

Se o captcha estiver errado o site avisa "Captcha Inválido!", troca a imagem e o robô pede de novo (até 3 vezes por CEP).

## Parte 1: vários CEPs do bloco de notas

`buscar_ceps.py` lê o `ceps.txt`, pula a primeira linha (é o título) e pesquisa os CEPs um por um. A imagem do captcha abre no visualizador de imagens do sistema e você digita o texto no terminal. Deixar em branco pula o CEP. No fim tudo é salvo em `enderecos.xlsx`.

```bash
python buscar_ceps.py
```

## Parte 2: tela em Tkinter

`tela.py` abre uma janela de 950x350 com o campo de CEP e o botão Pesquisar. O captcha aparece numa janelinha por cima e o endereço encontrado vai pra TreeView. Dá pra pesquisar vários CEPs seguidos, eles vão se acumulando na lista.

A pesquisa roda numa thread separada pra janela não travar enquanto o Chrome está trabalhando.

```bash
python tela.py
```

## Arquivos

- `correios.py`: a parte do Selenium, usada pelos dois scripts
- `buscar_ceps.py`: parte 1
- `tela.py`: parte 2
- `ceps.txt`: CEPs de exemplo

## Instalação

```bash
pip install -r requirements.txt
```

Precisa do Google Chrome instalado. No Linux o Tkinter às vezes vem separado (`sudo apt install python3-tk` no Ubuntu, `sudo pacman -S tk` no Arch).
