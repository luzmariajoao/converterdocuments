# Document Processor App

Uma aplicação Streamlit para processamento e conversão de documentos com suporte para múltiplos clientes.

## Funcionalidades

- **Converter**: Processa PDFs e Excel para formato PHC
- **Financial Control**: Agrupa dados por CPO/SPO com resumo financeiro
- **Suporte para 4 clientes**: Customer A, B, C, D (com nomes genéricos para portfólio)

## Dependências

```
streamlit==1.28.0
pandas==2.0.0
openpyxl==3.10.0
pdfplumber==0.9.0
```

## Instalação Local

```bash
# 1. Clone o repositório
git clone https://github.com/luzmariaoao/document-processor.git
cd document-processor

# 2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run document_processor_app.py
```

A aplicação abrirá em `http://localhost:8501`

---

## OPÇÃO 1: Deploy no Streamlit Cloud ⭐ RECOMENDADO

### Passo 1: Prepare o GitHub

1. **Crie um novo repositório público** em `github.com/luzmariaoao/document-processor`

2. **Faça upload dos arquivos**:
   - `document_processor_app.py` (código principal)
   - `requirements.txt` (dependências)
   - `README.md` (este arquivo)

3. **Estrutura do repositório**:
   ```
   document-processor/
   ├── document_processor_app.py
   ├── requirements.txt
   └── README.md
   ```

### Passo 2: Configure no Streamlit Cloud

1. Aceda a https://share.streamlit.io

2. Clique em **"New app"**

3. Preencha:
   - **GitHub repo**: `luzmariaoao/document-processor`
   - **Branch**: `main`
   - **Main file path**: `document_processor_app.py`

4. Clique em **"Deploy"** 🚀

5. **URL pública** gerada automaticamente:
   ```
   https://document-processor-[random].streamlit.app
   ```

### Vantagens do Streamlit Cloud:
✅ Deploy em 2 minutos
✅ URL automática e HTTPS
✅ Atualizações automáticas com git push
✅ Grátis até 3 aplicações
✅ Logs e monitoring inclusos

---

## OPÇÃO 2: Deploy com GitHub + Cloudflare

### Passo 1: Crie um servidor Python com Gunicorn

1. **Crie um arquivo `wsgi.py`**:
```python
import streamlit.web.cli as stcli
import sys
from pathlib import Path

def run():
    sys.argv = ["streamlit", "run", "document_processor_app.py", "--server.port=8000"]
    stcli.main()

if __name__ == "__main__":
    run()
```

2. **Atualize `requirements.txt`**:
```
streamlit==1.28.0
pandas==2.0.0
openpyxl==3.10.0
pdfplumber==0.9.0
gunicorn==21.0.0
```

### Passo 2: Deploy com Cloudflare Pages + Workers

**Opção A: Usar Railway (mais fácil)**

1. Aceda a https://railway.app
2. Clique em **"Deploy"**
3. Selecione o repositório GitHub
4. Railway detecta automaticamente que é Streamlit
5. Expõe a aplicação com domínio automático

**Opção B: Usar Render (alternativa)**

1. Aceda a https://render.com
2. Clique em **"New +"** → **"Web Service"**
3. Selecione o repositório GitHub
4. Preencha:
   - **Name**: `document-processor`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run document_processor_app.py --server.port=8000`
5. Deploy automático

### Vantagens desta abordagem:
✅ Controlo total da infraestrutura
✅ Cloudflare cache + CDN
✅ Domínio customizado (com pagamento)
⚠️ Mais complexo de configurar

---

## RECOMENDAÇÃO FINAL

Para o teu CV online, **recomendo OPÇÃO 1 (Streamlit Cloud)** porque:

1. **Mais rápido**: Deploy em 2 minutos
2. **Profissional**: URL limpa e stável
3. **Sem custos**: Gratuito até 3 apps
4. **Menos manutenção**: Atualizações automáticas com git
5. **Melhor performance**: Otimizado para Streamlit nativo

---

## Como Atualizar a Aplicação

Após fazer deploy no Streamlit Cloud, qualquer `git push` para `main` atualiza automaticamente a app:

```bash
git add .
git commit -m "Atualizar documento processador"
git push origin main
```

A aplicação será redeployada em segundos! 🚀

---

## Para Adicionar ao CV

Adicione esta secção ao teu CV online:

```
Demo App: Document Processor
🔗 https://document-processor-[your-id].streamlit.app
GitHub: https://github.com/luzmariaoao/document-processor

Desenvolvido com Streamlit | Python | Pandas | PyPDF
Funcionalidades: PDF parsing, Excel conversion, Financial reporting
```

---

## Troubleshooting

**Erro "ModuleNotFoundError"?**
- Verifique se `requirements.txt` tem todas as dependências
- No Streamlit Cloud: Settings → Advanced Settings → Python version = 3.11

**App lenta no início?**
- Streamlit Cloud faz cold start em 30s (normal)
- Depois fica rápido

**Quer domínio próprio?**
- Streamlit Cloud: Settings → Custom Domain (pago)
- Render: integra com qualquer domínio via DNS

---

Qualquer dúvida, avisa! 💪
