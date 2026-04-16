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
  cy.get('[name="nome_completo"]').type('Usuario Conta Cypress');
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();
};

describe('Autenticacao e conta', () => {
  it('registra, acessa a conta, faz logout e login novamente', () => {
    const user = buildUser('conta');

    registerUser(user);

    cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
    cy.contains('Sua conta').should('be.visible');
    cy.contains(user.username).should('be.visible');

    cy.get('[data-cy="nav-conta"]').click();
    cy.contains('Minha conta').should('be.visible');
    cy.contains(user.username).should('be.visible');
    cy.contains(user.email).should('be.visible');
    cy.get('[data-cy="account-athlete-link"]').should('contain', 'Criar perfil do atleta');

    cy.get('[data-cy="account-goals-link"]').click();
    cy.url().should('include', '/metas/');
    cy.contains('Criar meta').should('be.visible');

    cy.get('[data-cy="logout-link"]').click();
    cy.url().should('include', '/login/');
    cy.contains('Entrar').should('be.visible');

    cy.get('[name="username"]').type(user.username);
    cy.get('[name="password"]').type(user.password);
    cy.get('[data-cy="login-submit"]').click();

    cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
    cy.contains('Sua conta').should('be.visible');

    cy.get('[data-cy="home-account-link"]').click();
    cy.contains('Minha conta').should('be.visible');
  });
});
