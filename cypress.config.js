const { defineConfig } = require('cypress');

module.exports = defineConfig({
  video: true,
  allowCypressEnv: false,
  screenshotsFolder: 'cypress/screenshots',
  videosFolder: 'cypress/videos',
  viewportWidth: 1440,
  viewportHeight: 900,
  e2e: {
    baseUrl: 'http://127.0.0.1:8000',
    specPattern: 'cypress/e2e/**/*.cy.js',
    supportFile: 'cypress/support/e2e.js',
  },
});
