// Re-export the app-local Tailwind config so editor tooling at the repository root
// can discover Tailwind settings (content paths, plugins) used by the app.
module.exports = require('./apps/web/tailwind.config.js');
