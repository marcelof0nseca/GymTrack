const buildUser = (prefix) => {
  const suffix = `${Date.now()}_${Cypress._.random(1000, 9999)}`;
  const username = `${prefix}_${suffix}`;

  return {
    username,
    email: `${username}@example.com`,
    password: 'SenhaForte123',
  };
};

const registerUser = (user, fullName = 'Usuario Cypress') => {
  cy.visit('/register/');
  cy.get('[name="nome_completo"]').type(fullName);
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();

  cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
  cy.contains('Sua conta').should('be.visible');
};

const fillInput = (selector, value) => {
  cy.get(selector)
    .should('be.visible')
    .invoke('val', '')
    .trigger('input')
    .type(String(value));
};

const createTraining = (trainingName) => {
  cy.visit('/treinos/');
  fillInput('[name="nome"]', trainingName);
  cy.get('[data-cy="create-training"]').click();
  cy.contains('Treino criado com sucesso').should('be.visible');
  cy.contains(trainingName).should('be.visible');
};

const assertTrainingCount = (trainingName, expectedCount) => {
  cy.get('.items-list .item strong').then(($titles) => {
    const matches = [...$titles].filter((title) => title.innerText.trim() === trainingName);
    expect(matches).to.have.length(expectedCount);
  });
};

const exerciseLabel = (option) => option.text.trim().split(' (')[0];

const addExerciseToTraining = (trainingName, exerciseValue, exerciseName, series, repetitions) => {
  cy.location('pathname').should('eq', '/exercicios/');
  cy.get('[name="treino"]').should('be.enabled').select(trainingName);
  cy.get('[name="exercicio_base"]').should('be.enabled').select(exerciseValue);
  fillInput('[name="series"]', series);
  fillInput('[name="repeticoes"]', repetitions);
  cy.get('[data-cy="add-exercise"]').click();

  cy.location('pathname').should('eq', '/exercicios/');
  cy.contains('adicionado com sucesso').should('be.visible');
  cy.contains(trainingName).should('be.visible');
  cy.contains(exerciseName).should('be.visible');
};

describe('Fluxos de treino, exercicios e execucao', () => {
  it('valida treino obrigatório e impede duplicidade', () => {
    const user = buildUser('treino-validacao');
    const treino = `Treino Unico ${Date.now()}`;

    registerUser(user);

    cy.visit('/treinos/');
    cy.get('[data-cy="create-training"]').click();
    cy.contains('O nome do treino é obrigatório.').should('be.visible');

    fillInput('[name="nome"]', treino);
    cy.get('[data-cy="create-training"]').click();
    cy.contains('Treino criado com sucesso').should('be.visible');
    assertTrainingCount(treino, 1);

    fillInput('[name="nome"]', treino);
    cy.get('[data-cy="create-training"]').click();
    cy.contains('Você já possui um treino com esse nome.').should('be.visible');
    assertTrainingCount(treino, 1);
  });

  it('valida campos obrigatórios e bloqueia exercício duplicado', () => {
    const user = buildUser('exercicio-validacao');
    const treino = `Treino Exercicios ${Date.now()}`;

    registerUser(user);
    createTraining(treino);

    cy.visit('/exercicios/');
    cy.get('[data-cy="add-exercise"]').click();
    cy.contains('Este campo é obrigatório.').should('be.visible');

    cy.get('[name="exercicio_base"] option').then(($options) => {
      const firstExercise = [...$options].find((option) => option.value);
      expect(firstExercise, 'first exercise option').to.exist;

      const firstExerciseValue = firstExercise.value;
      const firstExerciseName = exerciseLabel(firstExercise);

      addExerciseToTraining(treino, firstExerciseValue, firstExerciseName, 4, 10);

      cy.get('[name="treino"]').should('be.enabled').select(treino);
      cy.get('[name="exercicio_base"]').should('be.enabled').select(firstExerciseValue);
      fillInput('[name="series"]', 4);
      fillInput('[name="repeticoes"]', 10);
      cy.get('[data-cy="add-exercise"]').click();

      cy.contains('Esse exercício já foi adicionado a este treino.').should('be.visible');
      cy.contains(firstExerciseName).should('be.visible');
    });
  });

  it('cria conta, cadastra treino, adiciona exercicio e conclui a execucao automaticamente', () => {
    const user = buildUser('treino');
    const treino = `Treino Cypress ${Date.now()}`;

    registerUser(user);
    createTraining(treino);

    cy.visit('/exercicios/');
    cy.get('[name="exercicio_base"] option').then(($options) => {
      const firstExercise = [...$options].find((option) => option.value);
      expect(firstExercise, 'first exercise option').to.exist;

      const firstExerciseValue = firstExercise.value;
      const firstExerciseName = exerciseLabel(firstExercise);

      addExerciseToTraining(treino, firstExerciseValue, firstExerciseName, 4, 10);

      cy.visit('/execucao/');
      cy.get('[name="treino"]').should('be.enabled').select(treino);
      cy.get('[data-cy="start-training"]').click();

      cy.url().should('match', /\/execucao\/\d+\/$/);
      cy.contains(firstExerciseName).should('be.visible');
      cy.get('[data-cy="complete-exercise"]').first().click();

      cy.contains('1/1').should('be.visible');
      cy.get('[data-cy="training-completed"]').should('be.visible');
    });
  });

  it('impede iniciar a execução de um treino sem exercícios', () => {
    const user = buildUser('execucao-vazia');
    const treino = `Treino Vazio ${Date.now()}`;

    registerUser(user);
    createTraining(treino);

    cy.visit('/execucao/');
    cy.get('[name="treino"]').should('be.enabled').select(treino);
    cy.get('[data-cy="start-training"]').click();

    cy.contains('Esse treino ainda não possui exercícios cadastrados').should('be.visible');
    cy.url().should('include', '/execucao/');
  });

  it('edita treino, remove e adiciona exercicios, finaliza parcialmente e exclui o treino', () => {
    const user = buildUser('gerenciar');
    const treinoOriginal = `Treino Gerenciamento ${Date.now()}`;
    const treinoEditado = `${treinoOriginal} Editado`;

    registerUser(user);
    createTraining(treinoOriginal);

    cy.visit('/exercicios/');
    cy.get('[name="exercicio_base"] option').then(($options) => {
      const exerciseOptions = [...$options].filter((option) => option.value);
      expect(exerciseOptions.length, 'available exercise options').to.be.gte(2);

      const firstExerciseValue = exerciseOptions[0].value;
      const firstExerciseName = exerciseLabel(exerciseOptions[0]);
      const secondExerciseValue = exerciseOptions[1].value;
      const secondExerciseName = exerciseLabel(exerciseOptions[1]);

      addExerciseToTraining(treinoOriginal, firstExerciseValue, firstExerciseName, 3, 12);

      cy.visit('/treinos/');
      cy.contains('.item', treinoOriginal).within(() => {
        cy.get('[data-cy="edit-training"]').click();
      });

      cy.location('pathname').should('match', /\/treinos\/editar\/\d+\/$/);
      fillInput('[name="nome"]', treinoEditado);
      cy.get('[data-cy="save-training-changes"]').click();
      cy.contains('Treino atualizado com sucesso').should('be.visible');
      cy.contains(treinoEditado).should('be.visible');

      cy.get('[data-cy="delete-exercise"]').click();
      cy.location('pathname').should('match', /\/treinos\/editar\/\d+\/$/);
      cy.contains('sucesso').should('be.visible');
      cy.contains(firstExerciseName).should('not.exist');

      cy.get('[data-cy="go-add-exercise"]').click();
      addExerciseToTraining(treinoEditado, firstExerciseValue, firstExerciseName, 4, 10);
      addExerciseToTraining(treinoEditado, secondExerciseValue, secondExerciseName, 4, 8);

      cy.visit('/execucao/');
      cy.get('[name="treino"]').should('be.enabled').select(treinoEditado);
      cy.get('[data-cy="start-training"]').click();

      cy.url().should('match', /\/execucao\/\d+\/$/);
      cy.contains(firstExerciseName).should('be.visible');
      cy.contains(secondExerciseName).should('be.visible');
      cy.get('[data-cy="complete-exercise"]').first().click();

      cy.contains('1/2').should('be.visible');
      cy.get('[data-cy="open-partial-confirm"]').click();
      cy.get('[data-cy="confirm-partial-training"]').click();

      cy.contains('Treino finalizado com exerc').should('be.visible');
      cy.contains('pendente').should('be.visible');
      cy.get('[data-cy="training-completed"]').should('be.visible');

      cy.visit('/treinos/');
      cy.contains('.item', treinoEditado).within(() => {
        cy.get('[data-cy="delete-training"]').click();
      });

      cy.contains(treinoEditado).should('not.exist');
    });
  });
});
