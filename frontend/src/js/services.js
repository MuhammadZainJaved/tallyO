(function () {
  'use strict';

  angular.module('tallyO')
    .factory('Session', function ($window) {
      var key = 'tallyo.session';
      function read() {
        try { return JSON.parse($window.localStorage.getItem(key)) || {}; } catch (ignore) { return {}; }
      }
      var current = read();
      return {
        get: function () { return current; },
        set: function (value) { current = value || {}; $window.localStorage.setItem(key, JSON.stringify(current)); },
        clear: function () { current = {}; $window.localStorage.removeItem(key); },
        token: function () { return current.token; },
        authenticated: function () { return Boolean(current.token); },
        superAdmin: function () { return Boolean(current.user && current.user.is_superuser); }
      };
    })
    .factory('Api', function ($http) {
      var root = '/api/v1/';
      function url(path) { return root + path.replace(/^\//, ''); }
      function request(method, path, data, config) {
        return $http(angular.extend({ method: method, url: url(path), data: data }, config || {})).then(function (response) { return response.data; });
      }
      return {
        get: function (path, params) { return request('GET', path, undefined, { params: params }); },
        post: function (path, data, config) { return request('POST', path, data, config); },
        patch: function (path, data) { return request('PATCH', path, data); },
        remove: function (path) { return request('DELETE', path); }
      };
    })
    .factory('Notifier', function ($timeout) {
      var notices = [];
      var nextId = 1;
      function add(message, type) {
        var notice = { id: nextId++, message: message, type: type || 'info' };
        notices.push(notice);
        $timeout(function () { var i = notices.indexOf(notice); if (i >= 0) notices.splice(i, 1); }, 4500);
      }
      return { items: notices, success: function (m) { add(m, 'success'); }, error: function (m) { add(m, 'error'); }, info: add };
    })
    .factory('Cart', function ($window) {
      var prefix = 'tallyo.cart.';
      var metaPrefix = 'tallyo.cartmeta.';
      function read(slug) {
        try { return JSON.parse($window.localStorage.getItem(prefix + slug)) || {}; } catch (ignore) { return {}; }
      }
      function write(slug, cart) { $window.localStorage.setItem(prefix + slug, JSON.stringify(cart)); }
      function writeMeta(slug, store) {
        $window.localStorage.setItem(metaPrefix + slug, JSON.stringify({
          slug: slug,
          name: store.name,
          currency: store.currency,
          delivery_fee: store.delivery_fee
        }));
      }
      function readMeta(slug) {
        try { return JSON.parse($window.localStorage.getItem(metaPrefix + slug)) || {}; } catch (ignore) { return {}; }
      }
      function list(slug) {
        var cart = read(slug);
        return Object.keys(cart).map(function (id) { return cart[id]; });
      }
      return {
        items: list,
        add: function (slug, product, store) {
          var cart = read(slug); var item = cart[product.id] || { product: product, quantity: 0 };
          item.product = product; item.quantity += 1; cart[product.id] = item; write(slug, cart);
          if (store) writeMeta(slug, store);
        },
        update: function (slug, productId, quantity) {
          var cart = read(slug); var number = Math.max(0, Number(quantity) || 0);
          if (!number) delete cart[productId]; else if (cart[productId]) cart[productId].quantity = number;
          if (Object.keys(cart).length) write(slug, cart);
          else {
            $window.localStorage.removeItem(prefix + slug);
            $window.localStorage.removeItem(metaPrefix + slug);
          }
        },
        clear: function (slug) {
          $window.localStorage.removeItem(prefix + slug);
          $window.localStorage.removeItem(metaPrefix + slug);
        },
        otherCarts: function (currentSlug) {
          var carts = [];
          for (var index = 0; index < $window.localStorage.length; index += 1) {
            var key = $window.localStorage.key(index);
            if (!key || key.indexOf(prefix) !== 0) continue;
            var slug = key.slice(prefix.length);
            if (slug === currentSlug) continue;
            var items = list(slug);
            if (!items.length) continue;
            var meta = readMeta(slug);
            carts.push({
              slug: slug,
              name: meta.name || slug.replace(/-/g, ' '),
              currency: meta.currency || '',
              delivery_fee: meta.delivery_fee,
              item_count: items.reduce(function (total, item) { return total + item.quantity; }, 0)
            });
          }
          return carts;
        },
        count: function (slug) { return list(slug).reduce(function (sum, item) { return sum + item.quantity; }, 0); },
        subtotal: function (slug) { return list(slug).reduce(function (sum, item) { return sum + Number(item.product.price) * item.quantity; }, 0); }
      };
    })
    .factory('GoogleMaps', function ($q, $window, $document, Api) {
      var loading;
      return {
        load: function () {
          if ($window.google && $window.google.maps) return $q.resolve($window.google.maps);
          if (loading) return loading;
          loading = Api.get('config/public/').then(function (config) {
            if (!config.google_maps_enabled || !config.google_maps_browser_api_key) return null;
            var deferred = $q.defer();
            var callbackName = '__tallyoGoogleMapsReady';
            $window[callbackName] = function () {
              deferred.resolve($window.google.maps);
              delete $window[callbackName];
            };
            var script = $document[0].createElement('script');
            script.async = true;
            script.defer = true;
            script.src = 'https://maps.googleapis.com/maps/api/js?key=' +
              encodeURIComponent(config.google_maps_browser_api_key) +
              '&libraries=places,marker&v=weekly&loading=async&callback=' + callbackName;
            script.onerror = function () { deferred.reject(new Error('Google Maps could not be loaded.')); };
            $document[0].head.appendChild(script);
            return deferred.promise;
          });
          return loading;
        }
      };
    });
}());
