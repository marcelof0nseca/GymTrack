describe('Fluxo de treino e execucao', () => {
  it('cria conta, cadastra treino, adiciona exercicio e conclui a execucao', () => {
    const suffix = Date.now();
    const username = `cypress_${suffix}`;
    const email = `${username}@example.com`;
    const treino = `Treino Cypress ${suffix}`;

    cy.visit('/register/');
    cy.get('[name="nome_completo"]').type('Usuario Cypress');
    cy.get('[name="username"]').type(username);
    cy.get('[name="email"]').type(email);
    cy.get('[name="password1"]').type('SenhaForte123');
    cy.get('[name="password2"]').type('SenhaForte123');
    cy.get('[data-cy="register-submit"]').click();

    cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
    cy.contains('Sua conta').should('be.visible');

    cy.visit('/treinos/');
    cy.get('[name="nome"]').type(treino);
    cy.get('[data-cy="create-training"]').click();
    cy.contains(treino).should('be.visible');

    cy.visit('/exercicios/');
    cy.get('[name="treino"]').select(treino);
    cy.get('[name="exercicio_base"] option').then(($options) => {
      const firstExercise = [...$options].find((option) => option.value);
      expect(firstExercise, 'first exercise option').to.exist;

      const exerciseName = firstExercise.text.trim().split(' (')[0];

      cy.get('[name="exercicio_base"]').select(firstExercise.value);
      cy.get('[name="series"]').clear().type('4');
      cy.get('[name="repeticoes"]').clear().type('10');
      cy.get('[data-cy="add-exercise"]').click();

      cy.contains(exerciseName).should('be.visible');
      cy.contains(treino).should('be.visible');

      cy.visit('/execucao/');
      cy.get('[name="treino"]').select(treino);
      cy.get('[data-cy="start-training"]').click();

      cy.url().should('match', /\/execucao\/\d+\/$/);
      cy.contains(exerciseName).should('be.visible');
      cy.get('[data-cy="complete-exercise"]').first().click();

      cy.contains('1/1').should('be.visible');
      cy.get('[data-cy="training-completed"]').should('be.visible');
    });
  });
});
