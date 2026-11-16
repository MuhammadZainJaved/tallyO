const test = require('node:test');
const assert = require('node:assert/strict');
const utils = require('../src/js/utils.js');

test('unwrap handles paginated and plain collections', () => {
  assert.deepEqual(utils.unwrap({ results: [{ id: 1 }] }), [{ id: 1 }]);
  assert.deepEqual(utils.unwrap([{ id: 2 }]), [{ id: 2 }]);
  assert.deepEqual(utils.unwrap(null), []);
});

test('slugify produces URL-safe store slugs', () => {
  assert.equal(utils.slugify('  Green & Fresh Store '), 'green-fresh-store');
});

test('errorMessage flattens API validation errors', () => {
  assert.equal(utils.errorMessage({ data: { error: { details: { phone: ['Invalid number'] } } } }), 'phone: Invalid number');
});

test('money safely formats a numeric amount', () => {
  assert.match(utils.money('12.50', 'USD'), /12\.50/);
});
