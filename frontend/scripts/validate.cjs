const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const source = path.join(root, 'src');
const app = fs.readFileSync(path.join(source, 'js', 'app.js'), 'utf8');
const index = fs.readFileSync(path.join(source, 'index.html'), 'utf8');
const templatePattern = /templateUrl:\s*['"]\/([^'"]+)['"]/g;
const missing = [];
let match;
while ((match = templatePattern.exec(app))) {
  if (!fs.existsSync(path.join(source, match[1]))) missing.push(match[1]);
}
['app.css', 'js/utils.js', 'js/module.js', 'js/services.js', 'js/maps.directive.js', 'js/app.js'].forEach((asset) => {
  if (!index.includes('/' + asset)) missing.push(asset);
});
if (missing.length) throw new Error('Missing referenced frontend files: ' + missing.join(', '));
console.log('Frontend references are valid.');
