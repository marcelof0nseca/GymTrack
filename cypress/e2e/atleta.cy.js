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
  cy.get('[name="nome_completo"]').type('Usuario Atleta Cypress');
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();

  cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
};

describe('Perfil do atleta', () => {
  it('valida campos obrigatórios e dados inválidos no cadastro do atleta', () => {
    const user = buildUser('atleta-validacao');

    registerUser(user);

    cy.get('[data-cy="home-create-athlete"]').click();
    cy.url().should('include', '/atleta/');

    cy.get('[data-cy="create-athlete-profile"]').click();
    cy.contains('Este campo é obrigatório.').should('be.visible');
    cy.contains('Criar perfil do atleta').should('be.visible');

    cy.get('[name="objetivo_principal"]').select('ganho_massa');
    cy.get('[name="altura_cm"]').type('-170.00');
    cy.get('[name="peso_kg"]').type('-82.00');
    cy.get('[name="braco_cm"]').type('-33.00');
    cy.get('[name="cintura_cm"]').type('0');
    cy.get('[name="peito_cm"]').type('95.00');
    cy.get('[name="coxa_cm"]').type('55.00');
    cy.get('[data-cy="create-athlete-profile"]').click();

    cy.contains('A altura deve ser maior que zero.').should('be.visible');
    cy.contains('O peso deve ser maior que zero.').should('be.visible');
    cy.contains('O braço deve ser maior que zero.').should('be.visible');
    cy.contains('A cintura deve ser maior que zero.').should('be.visible');
  });

  it('cria o perfil, atualiza dados e registra novas medicoes', () => {
    const user = buildUser('atleta');

    registerUser(user);

    cy.get('[data-cy="home-create-athlete"]').click();
    cy.url().should('include', '/atleta/');

    cy.get('[name="objetivo_principal"]').select('emagrecimento');
    cy.get('[name="objetivo_descricao"]').type('Perder gordura e acompanhar a evolucao fisica.');
    cy.get('[name="altura_cm"]').type('172.00');
    cy.get('[name="peso_kg"]').type('84.50');
    cy.get('[name="braco_cm"]').type('33.00');
    cy.get('[name="cintura_cm"]').type('88.00');
    cy.get('[name="peito_cm"]').type('97.00');
    cy.get('[name="coxa_cm"]').type('57.00');
    cy.get('[data-cy="create-athlete-profile"]').click();

    cy.contains('Perfil do atleta criado com sucesso!').should('be.visible');
    cy.contains('Emagrecimento').should('be.visible');
    cy.contains('84,50 kg').should('be.visible');

    cy.get('[data-cy="nav-home"]').click();
    cy.contains('Perfil do atleta').should('be.visible');
    cy.get('[data-cy="home-athlete-link"]').should('be.visible');
    cy.contains('84,50 kg').should('be.visible');

    cy.get('[data-cy="nav-conta"]').click();
    cy.get('[data-cy="account-athlete-link"]').should('contain', 'Abrir perfil do atleta');
    cy.get('[data-cy="account-athlete-link"]').click();

    cy.get('[name="objetivo_descricao"]').clear().type('Acompanhar medidas e manter consistencia no treino.');
    cy.get('[name="altura_cm"]').clear().type('173.00');
    cy.get('[data-cy="save-athlete-data"]').click();

    cy.contains('Perfil do atleta atualizado com sucesso!').should('be.visible');
    cy.get('[name="altura_cm"]').should('have.value', '173.00');

    cy.get('[name="peso_kg"]').clear().type('82.00');
    cy.get('[name="braco_cm"]').clear().type('33.50');
    cy.get('[name="cintura_cm"]').clear().type('84.00');
    cy.get('[name="peito_cm"]').clear().type('96.50');
    cy.get('[name="coxa_cm"]').clear().type('56.50');
    cy.get('[data-cy="register-measurement"]').click();

    cy.contains('Parab').should('be.visible');
    cy.contains('Historico de medicoes').should('be.visible');
    cy.contains('82,00 kg').should('be.visible');
    cy.get('.athlete-history-item').should(($items) => {
      expect($items.length).to.be.gte(2);
    });

    cy.get('[data-cy="nav-home"]').click();
    cy.contains('82,00 kg').should('be.visible');
    cy.get('[data-cy="home-athlete-link"]').should('be.visible');
  });
});
