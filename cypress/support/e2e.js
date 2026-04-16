beforeEach(() => {
  cy.viewport(1440, 900);
  cy.on('window:confirm', () => true);
});
