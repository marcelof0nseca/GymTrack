#  GymTrack
![Logo](assets/gymtrack.png)

> Sistema Web para Gerenciamento de Treinos de Academia

---

##   Sobre o Projeto

O **GymTrack** é uma aplicação web desenvolvida para auxiliar praticantes de academia a organizarem, registrarem e acompanharem seus treinos de forma estruturada e eficiente.

---

##  Integrantes

* João Mafra  jcmsn@cesar.school
* Marcelo Fonseca  maf@cesar.school
* João Cláudio Beltrão  jccbf@cesar.school
* Vinícius Cezar  vcrc@cesar.school
* Mateus Reinaux  mrbm@cesar.school
* Arthur Rodrigues de Andrade ara@cesar.school
* João Lucas jlogb@cesar.school

---

## Links Úteis

- **Jira (Gerenciamento do Projeto)**  
[Quadro do Jira](https://gymtrackteam.atlassian.net/jira/software/projects/SCRUM/boards/1?atlOrigin=eyJpIjoiZDc0NzljNTI3MzI0NDMyNjhkYTE3MWZlMjY5Y2FkNzIiLCJwIjoiaiJ9)

-  **Protótipo no Figma**  
[Figma](https://www.figma.com/files/team/1540039649788931211/project/572415580?fuid=1540039646964877001)

---

##  Entregas do Projeto

<details>
<summary> Entrega 1 — Kickoff</summary>

## Histórias de Usuário
O projeto está sendo gerenciado utilizando a metodologia Scrum.

Backlog do Produto:
![historia](assets/Historias.png)

Quadro da Sprint 1:
![Sprint](assets/Sprint.png)
<details>
<summary>Ver histórias</summary>

### 1. Criar treino

**Descrição**

Como usuário do sistema,  
eu quero criar um treino,  
para organizar meus exercícios por categoria ou objetivo.

**BDD**

Given que estou na tela de treinos  
When eu preencho o nome do treino e clico em "Criar treino"  
Then o sistema deve salvar o treino e exibi-lo na lista de treinos cadastrados.

---

### 2. Adicionar exercícios ao treino

**Descrição**

Como usuário,  
eu quero adicionar exercícios a um treino,  
para montar a sequência de exercícios que devo realizar.

**BDD**

Given que já existe um treino criado  
When eu informo o nome do exercício, número de séries e repetições  
Then o sistema deve adicionar o exercício ao treino selecionado.

---

### 3. Criar atleta

**Descrição**

Como usuário,  
eu quero cadastrar um atleta,  
para registrar suas informações físicas e objetivos de treino.

**BDD**

Given que estou na tela de cadastro de atleta  
When eu preencho os dados obrigatórios e clico em "Cadastrar atleta"  
Then o sistema deve salvar o atleta e exibir seu perfil no sistema.

---

### 4. Registrar medidas

**Descrição**

Como usuário,  
eu quero registrar medidas físicas,  
para acompanhar a evolução corporal ao longo do tempo.

**BDD**

Given que existe um atleta cadastrado  
When eu informo valores como peso, braço ou cintura e clico em salvar  
Then o sistema deve registrar as medidas no histórico do atleta.

---

### 5. Criar lembretes

**Descrição**

Como usuário,  
eu quero criar lembretes,  
para ser avisado sobre treinos ou atividades importantes.

**BDD**

Given que estou na tela de lembretes  
When eu informo o título, data e horário do lembrete  
Then o sistema deve salvar o lembrete e exibi-lo na lista de lembretes.

---

### 6. Definir metas

**Descrição**

Como usuário,  
eu quero definir metas de treino ou evolução,  
para ter objetivos claros dentro da minha rotina de treino.

**BDD**

Given que estou na tela de metas  
When eu informo o nome da meta, valor objetivo e prazo  
Then o sistema deve salvar a meta e exibi-la na lista de metas.

---

### 7. Registrar execução do treino

**Descrição**

Como usuário,  
eu quero registrar a execução de um treino,  
para marcar os exercícios que já foram concluídos.

**BDD**

Given que existe um treino com exercícios cadastrados  
When eu marco os exercícios como concluídos e finalizo o treino  
Then o sistema deve registrar que o treino foi realizado.

</details>

###  Screencast
[Link](https://youtu.be/zOUuL4RQky8)

</details>

---

<details>
<summary> Entrega 2 — Protótipo</summary>

Conteúdo da segunda entrega.

- Protótipo de interface  
- Modelagem inicial do sistema  
- Atualização das histórias de usuário  

</details>

---

<details>
<summary> Entrega 3 — Implementação</summary>

Conteúdo da terceira entrega.

- Implementação das funcionalidades principais  
- Integração com banco de dados  
- Testes iniciais  

</details>

---

<details>
<summary> Entrega 4 — Versão Final</summary>

Conteúdo da entrega final.

- Sistema completo  
- Melhorias de interface  
- Apresentação final  

</details>

---

## Licença

Projeto acadêmico desenvolvido para fins educacionais.  
Disciplina: **Fundamentos de Software**
