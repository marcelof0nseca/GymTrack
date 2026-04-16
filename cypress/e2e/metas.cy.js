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
  cy.get('[name="nome_completo"]').type('Usuario Metas Cypress');
  cy.get('[name="username"]').type(user.username);
  cy.get('[name="email"]').type(user.email);
  cy.get('[name="password1"]').type(user.password);
  cy.get('[name="password2"]').type(user.password);
  cy.get('[data-cy="register-submit"]').click();

  cy.url().should('eq', `${Cypress.config('baseUrl')}/`);
};

const formatDate = (offsetDays) => {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split('T')[0];
};

const fillGoalForm = (goalName, value, startDate, endDate) => {
  cy.get('[name="nome"]').clear().type(goalName);
  cy.get('[name="valor"]').clear().type(value);
  cy.get('[name="data_inicio"]').clear().type(startDate);
  cy.get('[name="prazo"]').clear().type(endDate);
  cy.get('[data-cy="create-meta"]').click();
};

describe('Fluxo de metas', () => {
  it('valida valor inválido e data final anterior à data inicial', () => {
    const user = buildUser('meta-validacao');
    const nomeMetaInvalida = `Meta Invalida ${Date.now()}`;
    const nomeMetaDatas = `Meta Datas ${Date.now()}`;
    const dataInicioHoje = formatDate(0);
    const dataInicioFutura = formatDate(5);
    const prazoAntes = formatDate(3);

    registerUser(user);

    cy.visit('/metas/');

    fillGoalForm(nomeMetaInvalida, '0', dataInicioHoje, formatDate(7));
    cy.contains('O valor da meta deve ser maior que zero.').should('be.visible');

    fillGoalForm(nomeMetaDatas, '10.00', dataInicioFutura, prazoAntes);
    cy.contains('A data de término não pode ser anterior à data de início.').should('be.visible');
  });

  it('cria, confirma, acompanha na home e remove metas', () => {
    const user = buildUser('meta');
    const nomeMetaConcluida = `Meta Confirmada ${Date.now()}`;
    const nomeMetaPendente = `Meta Pendente ${Date.now()}`;
    const dataInicio = formatDate(0);
    const prazoCurto = formatDate(4);
    const prazoMaior = formatDate(7);

    registerUser(user);

    cy.visit('/metas/');
    cy.get('[data-cy="create-meta"]').should('be.visible');

    fillGoalForm(nomeMetaConcluida, '5.00', dataInicio, prazoCurto);
    cy.contains(nomeMetaConcluida).should('be.visible');

    cy.contains('.meta-item-card', nomeMetaConcluida).within(() => {
      cy.get('[data-cy="meta-status"]').should('contain', 'Em andamento');
      cy.get('[data-cy="confirm-meta"]').click();
    });

    cy.contains('Meta confirmada com sucesso!').should('be.visible');
    cy.contains('.meta-item-card', nomeMetaConcluida).within(() => {
      cy.get('[data-cy="meta-status"]').should('contain', 'Conclu');
      cy.get('[data-cy="confirm-meta"]').should('not.exist');
    });

    fillGoalForm(nomeMetaPendente, '8.00', dataInicio, prazoMaior);
    cy.contains(nomeMetaPendente).should('be.visible');

    cy.get('[data-cy="nav-home"]').click();
    cy.contains(nomeMetaPendente).should('be.visible');

    cy.get('[data-cy="nav-metas"]').click();
    cy.contains('.meta-item-card', nomeMetaPendente).within(() => {
      cy.get('[data-cy="remove-meta-trigger"]').click();
    });

    cy.get('[data-cy="confirm-remove-meta"]').click();
    cy.contains('Meta removida com sucesso!').should('be.visible');
    cy.contains(nomeMetaPendente).should('not.exist');
    cy.contains(nomeMetaConcluida).should('be.visible');
  });
});
