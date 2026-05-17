# Guia de Contribuicao

Obrigado por considerar contribuir com o GymTrack! Este guia resume o fluxo recomendado para preparar o ambiente, desenvolver mudancas e validar o projeto antes de abrir um Pull Request.

## Como contribuir

1. Faca um fork do repositorio e crie uma branch a partir da `main`.
2. Abra uma issue antes de implementar mudancas grandes ou que alterem regras de negocio.
3. Mantenha o escopo da branch pequeno e descreva claramente o que foi alterado no Pull Request.
4. Inclua prints, videos curtos ou passos de validacao quando a mudanca afetar telas ou fluxos de usuario.

## Preparando o ambiente

1. Clone o repositorio:

   ```bash
   git clone https://github.com/marcelof0nseca/GymTrack.git
   cd GymTrack
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Instale as dependencias do backend:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Instale as dependencias do frontend/testes E2E:

   ```bash
   npm install
   ```

5. Aplique as migracoes:

   ```bash
   python manage.py migrate
   ```

6. Opcionalmente, carregue os exercicios iniciais:

   ```bash
   python manage.py popular_exercicios
   ```

## Rodando o projeto

Para iniciar o servidor local:

```bash
python manage.py runserver
```

Depois, acesse `http://127.0.0.1:8000/` no navegador.

## Padrao de codigo

- Siga o padrao PEP 8 em arquivos Python.
- Use nomes descritivos para variaveis, funcoes, classes e templates.
- Prefira mudancas pequenas e coesas, alinhadas ao estilo ja usado no projeto.
- Evite commitar arquivos gerados localmente, bancos SQLite, caches, logs ou artefatos de teste.
- Adicione ou atualize testes quando criar funcionalidades, corrigir bugs ou alterar regras de negocio.

## Testes

Execute os testes unitarios e de integracao do Django:

```bash
npm test
```

Ou, diretamente pelo Django:

```bash
python manage.py test --exclude-tag=e2e
```

Para rodar os testes E2E com Cypress:

```bash
npm run cy:run
```

Para abrir o Cypress em modo interativo:

```bash
npm run cy:open
```

## Antes de abrir um Pull Request

- Confirme que os testes relevantes passam.
- Revise o diff para remover alteracoes acidentais.
- Atualize documentacao, migrations ou fixtures quando necessario.
- Explique no Pull Request o problema resolvido, a solucao adotada e como a mudanca foi testada.

## Reportando bugs e sugerindo melhorias

Abra uma issue em:

https://github.com/marcelof0nseca/GymTrack/issues

Inclua, quando possivel:

- Passos para reproduzir o problema.
- Resultado esperado e resultado obtido.
- Prints, mensagens de erro ou logs relevantes.
- Informacoes do ambiente, como navegador, sistema operacional e versao do Python.

## Duvidas e contato

Tem duvidas ou precisa de ajuda?

- Abra uma issue com a tag `question`.
- Entre em contato com o mantenedor: maf@cesar.school, jcmsn@cesar.school

---

Obrigado por contribuir! Seu esforco ajuda este projeto a crescer e impactar mais pessoas.
