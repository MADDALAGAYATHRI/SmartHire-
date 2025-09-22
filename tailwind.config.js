// tailwind.config.js
module.exports = {
  content: [
    "./backend/templates/**/*.html",   // all your Jinja/FastAPI templates
    "./backend/static/js/**/*.js",     // if you use JS with Tailwind
    "./*.html",                        // root HTML files
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
