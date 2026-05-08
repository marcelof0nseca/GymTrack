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

  cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
};

const formatDateTime = (offsetDays) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  const pad = (value) => String(value).padStart(2, '0');

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

describe('Fluxo de lembretes', () => {
  it('valida data passada e cria lembrete com sucesso', () => {
    const user = buildUser('lembrete');
    const reminderName = `Lembrete Cypress ${Date.now()}`;

    registerUser(user);

    cy.visit('/lembretes/');
    cy.contains('Criar lembrete').should('be.visible');

    cy.get('[name="titulo"]').type(reminderName);
    cy.get('[name="data_hora"]').type('2000-01-01T10:00');
    cy.get('[data-cy="create-reminder"]').click();

    cy.contains('A data e o horário do lembrete não podem estar no passado.').should('be.visible');

    cy.get('[name="data_hora"]').clear().type(formatDateTime(1));
    cy.get('[data-cy="create-reminder"]').click();

    cy.contains('Lembrete criado com sucesso!').should('be.visible');
    cy.contains(reminderName).should('be.visible');

    cy.get('[data-cy="nav-home"]').click();
    cy.contains('Lembretes próximos').should('be.visible');
    cy.contains(reminderName).should('be.visible');
  });
});
