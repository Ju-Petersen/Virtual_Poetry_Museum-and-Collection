# Museu Virtual de Poesia

Este projeto é uma aplicação web em Streamlit para criar um museu/coleção virtual de poesia e textos, com foco em descoberta, leitura, publicação e autoria.

## Visão geral

A plataforma tem três pilares principais:

- Descobrir: galeria em grade com cards de poemas
- Ler: página dedicadas ao texto, com preservação de estrofes e quebras de linha
- Publicar: usuários enviam seus próprios textos e também podem gerenciar rascunhos e publicações

Além disso, o sistema inclui:

- cadastro e login de usuários
- histórico de leitura
- tags e filtros
- páginas de autor
- painel de moderação com denúncias
- suporte a SQLite para desenvolvimento e MySQL para produção

## Stack

- Python 3.12+
- Streamlit
- SQLAlchemy
- SQLite e MySQL
- uv como gerenciador de pacotes

## Estrutura do projeto

```text
.
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   └── models.py
├── tests/
│   └── test_smoke.py
├── .gitignore
├── pyproject.toml
├── README.md
├── instructions.txt
└── poetry_museum.db
```

## Instalação

```bash
uv sync --group dev
```

## Execução local

```bash
uv run streamlit run src/app.py
```

## Banco de dados

O sistema usa SQLite por padrão para desenvolvimento local.

Para produção, configure a variável de ambiente `MYSQL_DATABASE_URL`:

```bash
export MYSQL_DATABASE_URL="mysql+pymysql://usuario:senha@host:3306/nome_do_banco"
```

No PowerShell:

```powershell
$env:MYSQL_DATABASE_URL = "mysql+pymysql://usuario:senha@host:3306/nome_do_banco"
```

## Dados iniciais

Ao iniciar a aplicação, o sistema cria as tabelas e insere alguns dados demonstração para permitir uma experiência inicial útil.

## Considerações

A aplicação foi pensada para seguir as diretrizes do projeto: museu virtual de poesia, com foco em autorias, direitos, moderação e divulgação de textos.
