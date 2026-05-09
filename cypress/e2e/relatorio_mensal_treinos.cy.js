const buildUser = (prefix) => {
  const suffix = `${Date.now()}_${Cypress._.random(1000, 9999)}`;
  const username = `${prefix}_${suffix}`;

  return {
    username,
    email: `${username}@example.com`,
    password: 'SenhaForte123',
  };
};

const registerUser = (user, fullName = 'Usuario Relatorio Cypress') => {
  cy.visit('/register/');
  cy.get('[name="nome_completo"]').type(fullName);
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();

  cy.location('pathname', { timeout: 10000 }).should('eq', '/');
  cy.contains('Sua conta').should('be.visible');
};

const fillInput = (selector, value) => {
  cy.get(selector)
    .should('be.visible')
    .invoke('val', '')
    .trigger('input')
    .type(String(value));
};

const pad = (value) => String(value).padStart(2, '0');

const formatMonth = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}`;

const monthOffset = (offset) => {
  const date = new Date();
  date.setDate(1);
  date.setMonth(date.getMonth() + offset);

  return formatMonth(date);
};

const currentMonth = () => monthOffset(0);
const previousMonth = () => monthOffset(-1);
const nextMonth = () => monthOffset(1);

const createTraining = (trainingName) => {
  cy.visit('/treinos/');
  fillInput('[name="nome"]', trainingName);
  cy.get('[data-cy="create-training"]').click();

  cy.contains('Treino criado com sucesso').should('be.visible');
  cy.contains(trainingName).should('be.visible');
};

const exerciseLabel = (option) => option.text.trim().split(' (')[0];

const addFirstExerciseToTraining = (trainingName) => {
  cy.visit('/exercicios/');

  cy.get('[name="exercicio_base"] option').then(($options) => {
    const firstExercise = [...$options].find((option) => option.value);
    expect(firstExercise, 'first exercise option').to.exist;

    cy.get('[name="treino"]').should('be.enabled').select(trainingName);
    cy.get('[name="exercicio_base"]').should('be.enabled').select(firstExercise.value);
    fillInput('[name="series"]', 4);
    fillInput('[name="repeticoes"]', 10);
    cy.get('[data-cy="add-exercise"]').click();

    cy.contains('adicionado com sucesso').should('be.visible');
    cy.contains(trainingName).should('be.visible');
    cy.contains(exerciseLabel(firstExercise)).should('be.visible');
  });
};

const startTraining = (trainingName) => {
  cy.visit('/execucao/');
  cy.get('[name="treino"]').should('be.enabled').select(trainingName);
  cy.get('[data-cy="start-training"]').click();

  cy.location('pathname').should('match', /\/execucao\/\d+\/$/);
};

const createCompletedExecution = (trainingName) => {
  createTraining(trainingName);
  addFirstExerciseToTraining(trainingName);
  startTraining(trainingName);

  cy.get('[data-cy="complete-exercise"]').first().click();
  cy.get('[data-cy="training-completed"]').should('be.visible');
  cy.contains('1/1').should('be.visible');
};

const createInProgressExecution = (trainingName) => {
  createTraining(trainingName);
  addFirstExerciseToTraining(trainingName);
  startTraining(trainingName);

  cy.contains(trainingName).should('be.visible');
  cy.contains('0/1').should('be.visible');
};

describe('Relatorio mensal de treinos', () => {
  it('exibe treinos do mes, total e permite filtrar por treino e status', () => {
    const user = buildUser('relatorio-com-treinos');
    const completedTraining = `Treino Concluido ${Date.now()}`;
    const inProgressTraining = `Treino Andamento ${Date.now()}`;

    registerUser(user);
    createCompletedExecution(completedTraining);
    createInProgressExecution(inProgressTraining);

    cy.visit(`/relatorios/treinos/?mes=${currentMonth()}`);

    cy.contains(/Relat.rio mensal de treinos/).should('be.visible');
    cy.get('[name="mes"]').should('have.value', currentMonth());
    cy.get('.report-total strong').should('contain', '2');
    cy.get('[data-cy="monthly-report-list"] .item').should('have.length', 2);
    cy.get('[data-cy="monthly-report-list"]').within(() => {
      cy.contains(completedTraining).should('be.visible');
      cy.contains(inProgressTraining).should('be.visible');
      cy.contains('Conclu').should('be.visible');
      cy.contains('Em andamento').should('be.visible');
    });

    cy.get('[name="treino"]').select(inProgressTraining);
    cy.get('[name="status"]').select('em_andamento');
    cy.get('[data-cy="filter-monthly-report"]').click();

    cy.get('[name="mes"]').should('have.value', currentMonth());
    cy.get('[name="treino"] option:selected').should('contain', inProgressTraining);
    cy.get('[name="status"]').should('have.value', 'em_andamento');
    cy.get('.report-total strong').should('contain', '1');
    cy.get('[data-cy="monthly-report-list"] .item').should('have.length', 1);
    cy.get('[data-cy="monthly-report-list"]').within(() => {
      cy.contains(inProgressTraining).should('be.visible');
      cy.contains(completedTraining).should('not.exist');
      cy.contains('Em andamento').should('be.visible');
    });
  });

  it('informa quando mes valido nao possui treinos registrados', () => {
    const user = buildUser('relatorio-vazio');

    registerUser(user);

    cy.visit(`/relatorios/treinos/?mes=${nextMonth()}`);

    cy.contains(/Relat.rio mensal de treinos/).should('be.visible');
    cy.get('[name="mes"]').should('have.value', nextMonth());
    cy.get('.report-total strong').should('contain', '0');
    cy.get('[data-cy="report-empty-month"]').should('be.visible');
    cy.contains(/N.o houve treinos registrados/).should('be.visible');
    cy.contains(/Nenhuma execu..o foi encontrada no per.odo selecionado/).should('be.visible');
    cy.get('[data-cy="monthly-report-list"]').should('not.exist');
  });

  it('informa indisponibilidade para mes anterior ao cadastro do usuario', () => {
    const user = buildUser('relatorio-antes-cadastro');

    registerUser(user);

    cy.visit(`/relatorios/treinos/?mes=${previousMonth()}`);

    cy.contains(/Relat.rio mensal de treinos/).should('be.visible');
    cy.get('[name="mes"]').should('have.value', previousMonth());
    cy.get('.report-total strong').should('contain', '0');
    cy.get('[data-cy="report-before-registration"]').should('be.visible');
    cy.contains(/N.o h. dados dispon.veis/).should('be.visible');
    cy.contains(/O m.s selecionado . anterior ao cadastro da sua conta/).should('be.visible');
    cy.get('[data-cy="monthly-report-list"]').should('not.exist');
    cy.get('[data-cy="report-empty-month"]').should('not.exist');
  });
});
