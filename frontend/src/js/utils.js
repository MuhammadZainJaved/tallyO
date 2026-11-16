(function (root, factory) {
  var utilities = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = utilities;
  } else {
    root.TallyUtils = utilities;
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function unwrap(payload) {
    return payload && Array.isArray(payload.results) ? payload.results : (Array.isArray(payload) ? payload : []);
  }

  function slugify(value) {
    return String(value || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  function errorMessage(error, fallback) {
    var data = error && error.data;
    var details = data && data.error && data.error.details;
    if (typeof details === 'string') return details;
    if (details && typeof details === 'object') {
      return Object.keys(details).map(function (key) {
        var value = Array.isArray(details[key]) ? details[key].join(', ') : details[key];
        return key + ': ' + value;
      }).join(' · ');
    }
    return fallback || 'Something went wrong. Please try again.';
  }

  function money(value, currency) {
    var amount = Number(value || 0);
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency: currency || 'USD' }).format(amount);
    } catch (ignore) {
      return (currency || 'USD') + ' ' + amount.toFixed(2);
    }
  }

  function idempotencyKey() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
    return 'order-' + Date.now() + '-' + Math.random().toString(16).slice(2);
  }

  return { unwrap: unwrap, slugify: slugify, errorMessage: errorMessage, money: money, idempotencyKey: idempotencyKey };
}));
