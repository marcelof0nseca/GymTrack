describe('Fluxo de metas', () => {
  it('cria e confirma uma meta no sistema', () => {
    const suffix = Date.now();
    const username = `meta_${suffix}`;
    const email = `${username}@example.com`;
    const nomeMeta = `Meta Cypress ${suffix}`;
    const hoje = new Date();
    const dataInicio = hoje.toISOString().split('T')[0];
    const prazo = new Date(hoje.getTime() + (7 * 24 * 60 * 60 * 1000)).toISOString().split('T')[0];

    cy.visit('/register/');
    cy.get('[name="nome_completo"]').type('Usuario Metas Cypress');
    cy.get('[name="username"]').type(username);
    cy.get('[name="email"]').type(email);
    cy.get('[name="password1"]').type('SenhaForte123');
    cy.get('[name="password2"]').type('SenhaForte123');
    cy.get('[data-cy="register-submit"]').click();

    cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
    cy.contains('Sua conta').should('be.visible');

    cy.visit('/metas/');
    cy.url().should('include', '/metas/');
    cy.get('[data-cy="create-meta"]').should('be.visible');
    cy.get('[name="nome"]').type(nomeMeta);
    cy.get('[name="valor"]').type('5.00');
    cy.get('[name="data_inicio"]').type(dataInicio);
    cy.get('[name="prazo"]').type(prazo);
    cy.get('[data-cy="create-meta"]').click();

    cy.contains(nomeMeta).should('be.visible');
    cy.contains('Em andamento').should('be.visible');
    cy.get('[data-cy="confirm-meta"]').first().click();

    cy.contains('Meta confirmada com sucesso!').should('be.visible');
    cy.get('[data-cy="meta-status"]').first().should('contain', 'Conclu');
    cy.get('[data-cy="confirm-meta"]').should('not.exist');
  });
});
