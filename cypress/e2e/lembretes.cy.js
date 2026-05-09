const buildUser = (prefix) => {
  const suffix = `${Date.now()}_${Cypress._.random(1000, 9999)}`;
  const username = `${prefix}_${suffix}`;

  return {
    username,
    email: `${username}@example.com`,
    password: 'SenhaForte123',
  };
};

const registerUser = (user) => {
  cy.visit('/register/');
  cy.get('[name="nome_completo"]').type('Usuario Lembretes Cypress');
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();

  cy.location('pathname', { timeout: 10000 }).should('eq', '/');
};

const formatDateTime = (offsetDays) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  const pad = (value) => String(value).padStart(2, '0');

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

describe('Fluxo de lembretes', () => {
  it('cria lembrete com sucesso', () => {
    const user = buildUser('lembrete');
    const reminderName = `Lembrete Cypress ${Date.now()}`;

    registerUser(user);

    cy.visit('/lembretes/');
    cy.contains('Criar lembrete').should('be.visible');

    cy.get('[name="titulo"]').type(reminderName);
    cy.get('[name="data_hora"]').type(formatDateTime(1));
    cy.get('[data-cy="create-reminder"]').click();

    cy.contains('Lembrete criado com sucesso!').should('be.visible');
    cy.contains(reminderName).should('be.visible');
    cy.contains('Agendado').should('be.visible');

    cy.get('[data-cy="nav-home"]').click();
    cy.contains(/Lembretes pr.ximos/).should('be.visible');
    cy.contains(reminderName).should('be.visible');
  });

  it('impede cadastro com data no passado', () => {
    const user = buildUser('lembrete-passado');

    registerUser(user);

    cy.visit('/lembretes/');
    cy.contains('Criar lembrete').should('be.visible');

    cy.get('[name="titulo"]').type('Lembrete antigo');
    cy.get('[name="data_hora"]').type('2000-01-01T10:00');
    cy.get('[data-cy="create-reminder"]').click();

    cy.contains(/A data e o hor.rio do lembrete n.o podem estar no passado/).should('be.visible');
    cy.contains('Lembrete criado com sucesso!').should('not.exist');
    cy.contains(/Nenhum lembrete cadastrado at. o momento/).should('be.visible');
    cy.contains('Lembrete antigo').should('not.exist');
  });

  it('exibe erro quando campos obrigatÃ³rios ficam vazios', () => {
    const user = buildUser('lembrete-vazio');

    registerUser(user);

    cy.visit('/lembretes/');
    cy.contains('Criar lembrete').should('be.visible');

    cy.get('[data-cy="create-reminder"]').click();

    cy.contains(/Este campo . obrigat.rio/).should('be.visible');
    cy.contains('Lembrete criado com sucesso!').should('not.exist');
    cy.contains(/Nenhum lembrete cadastrado at. o momento/).should('be.visible');
  });
});
