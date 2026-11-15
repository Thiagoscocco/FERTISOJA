# FertiSoja

Aplicativo desktop em Python e CustomTkinter para interpretação de análises de solo e recomendações de adubação e calagem para soja. Gera laudos em PNG A4.

## Instalação e execução

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 fertisoja.py
```

No Windows, ative o ambiente com `.venv\Scripts\activate` e use `python` no lugar de `python3`.

## Estrutura

- `fertisoja.py`: entrada e montagem das abas.
- `fertilizacao.py` e `core/`: cálculos, interface e geração do laudo PNG.
- `assets/Logo Thiago.png` e `imagem.png`: imagens usadas na interface e no laudo.
- `novo.ico` e `FertiSoja.spec`: ícone e configuração de empacotamento.
- `docs/`: documentação de design e da lógica de adubação.

O envio de laudos por e-mail é opcional. Para habilitá-lo, copie `modelo_mail/.env.example` para `modelo_mail/.env` e preencha os dados SMTP. O arquivo `.env` é ignorado pelo Git.

Caches de Python, ambientes virtuais e arquivos gerados pelo aplicativo também são ignorados pelo Git.
