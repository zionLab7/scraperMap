# 🗺️ scraperMap - Google Maps Scraper

Este é um **web scraper** que coleta informações de empresas no **Google Maps**, sem necessidade da API, utilizando **Selenium e Python**. O usuário pode escolher **qual nicho (categoria)** deseja pesquisar, a **região** e **quantas empresas deseja coletar**.

---

## 🚀 Funcionalidades

✔ **Pesquisa empresas** no **Google Maps** com base na categoria e região fornecidas.

✔ Extrai **Nome, Telefone, Endereço, Website, E-mail e Categoria**.

✔ O usuário **define a quantidade de empresas** a coletar (ou sem limite se escolher `0`).

✔ **Exporta os dados para CSV** automaticamente.

✔ Suporte para **Windows, macOS e Linux**.

---

## 🛠️ Instalação

### 1️⃣ Instalar o Python (se ainda não tiver)

- **Windows**: Baixe e instale o [Python](https://www.python.org/downloads/). **Durante a instalação, marque a opção "Add Python to PATH"**.
- **macOS**: O Python já vem instalado, mas para atualizar, execute:
  ```bash
  brew install python3
  ```

### 2️⃣ Clonar o repositório

Abra o terminal (**Windows**: `cmd` ou `PowerShell`, **macOS/Linux**: `Terminal`) e execute:

```bash
git clone https://github.com/zionLab7/scraperMap.git
cd scraperMap
```

### 3️⃣ Criar um ambiente virtual (recomendado)

**Windows**:
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4️⃣ Instalar dependências

**Windows**:
```powershell
pip install -r requirements.txt
```

**macOS/Linux**:
```bash
pip3 install -r requirements.txt
```

---

## 🏃 Como Usar

Após instalar as dependências, execute o scraper com:
```bash
python scraperMaps.py
```

O script solicitará algumas informações:

1️⃣ **Categoria/Nicho** (Exemplo: `Restaurantes`, `Autoescola`, `Clínicas Médicas`).

2️⃣ **Região** (Exemplo: `São Paulo, SP`).

3️⃣ **Quantidade de empresas** (Digite `0` para coletar todas disponíveis).

Os resultados serão salvos automaticamente em **`resultados.csv`** no mesmo diretório do script.

---

## 🛑 Solução de Problemas

### ❌ Erro: "chromedriver não encontrado"

🔹 Certifique-se de ter o Google Chrome instalado e baixe o **ChromeDriver** correspondente à sua versão do Chrome:
👉 [Download ChromeDriver](https://chromedriver.chromium.org/downloads)

Depois, coloque o **chromedriver.exe** na pasta do script ou adicione ao **PATH do sistema**.

---

## 📜 Licença

Este projeto é **open-source** e está licenciado sob a **MIT License**.

---

✨ Agora você pode utilizar o **scraperMap - Google Maps Scraper** para extrair informações de negócios automaticamente! 🚀
