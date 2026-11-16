(function () {
  'use strict';

  var app = angular.module('tallyO');

  app.controller('DiscoveryController', function (Api) {
    var vm = this;
    vm.money = TallyUtils.money;
    vm.searchStores = function () {
      vm.loadingStores = true; vm.storeError = '';
      Api.get('storefronts/', vm.storeQuery ? { q: vm.storeQuery } : {}).then(function (data) {
        vm.stores = TallyUtils.unwrap(data);
      }).catch(function (error) {
        vm.storeError = TallyUtils.errorMessage(error, 'Could not load stores.');
      }).finally(function () { vm.loadingStores = false; });
    };
    vm.searchProducts = function () {
      vm.loadingProducts = true; vm.productError = '';
      Api.get('products/search/', vm.productQuery ? { q: vm.productQuery } : {}).then(function (data) {
        vm.products = TallyUtils.unwrap(data);
      }).catch(function (error) {
        vm.productError = TallyUtils.errorMessage(error, 'Could not load products.');
      }).finally(function () { vm.loadingProducts = false; });
    };
    vm.searchStores();
    vm.searchProducts();
  });

  app.controller('StorefrontController', function ($routeParams, $location, Api, Cart, Notifier) {
    var vm = this; var slug = $routeParams.storeSlug;
    vm.money = TallyUtils.money; vm.checkout = { customer_name: '', phone: '', email: '', delivery_address: '', notes: '' };
    vm.brandStyle = function () {
      var brand = vm.store && vm.store.branding;
      return brand ? { '--brand-primary': brand.primary_color || '#2563eb', '--brand-secondary': brand.secondary_color || '#0f172a' } : {};
    };
    vm.loadProducts = function () {
      var params = {}; if (vm.category) params.category = vm.category; if (vm.query) params.q = vm.query;
      Api.get('storefront/' + slug + '/products/', params).then(function (data) { vm.products = TallyUtils.unwrap(data); })
        .catch(function (e) { vm.error = TallyUtils.errorMessage(e, 'Could not load products.'); });
    };
    vm.refreshCart = function () { vm.cart = Cart.items(slug); vm.cartCount = Cart.count(slug); vm.subtotal = Cart.subtotal(slug); };
    function addToCurrentStore(product) {
      Cart.add(slug, product, vm.store); vm.refreshCart(); Notifier.success(product.name + ' added to cart.');
    }
    vm.add = function (product) {
      var otherCarts = Cart.otherCarts(slug);
      if (!vm.cartCount && otherCarts.length) {
        vm.pendingProduct = product;
        vm.deliveryConflict = { otherCarts: otherCarts, other: otherCarts[0] };
        return;
      }
      addToCurrentStore(product);
    };
    vm.confirmSeparateBasket = function () {
      if (vm.pendingProduct) addToCurrentStore(vm.pendingProduct);
      vm.pendingProduct = null; vm.deliveryConflict = null;
    };
    vm.cancelSeparateBasket = function () { vm.pendingProduct = null; vm.deliveryConflict = null; };
    vm.updateQuantity = function (item) { Cart.update(slug, item.product.id, item.quantity); vm.refreshCart(); };
    vm.remove = function (item) { Cart.update(slug, item.product.id, 0); vm.refreshCart(); };
    vm.total = function () { return vm.subtotal + Number((vm.store && vm.store.delivery_fee) || 0); };
    vm.placeOrder = function () {
      if (!vm.cart.length) return;
      vm.placing = true; vm.checkoutError = '';
      var payload = angular.extend({}, vm.checkout, { items: vm.cart.map(function (item) { return { product_id: item.product.id, quantity: item.quantity }; }) });
      Api.post('storefront/' + slug + '/orders/', payload, { headers: { 'Idempotency-Key': TallyUtils.idempotencyKey() } }).then(function (order) {
        Cart.clear(slug); vm.refreshCart(); $location.path('/shop/' + slug + '/order/' + order.public_token);
      }).catch(function (e) { vm.checkoutError = TallyUtils.errorMessage(e, 'Could not place your order.'); }).finally(function () { vm.placing = false; });
    };
    vm.loading = true;
    Api.get('storefront/' + slug + '/').then(function (store) { vm.store = store; return Api.get('storefront/' + slug + '/categories/'); })
      .then(function (categories) { vm.categories = TallyUtils.unwrap(categories); vm.loadProducts(); })
      .catch(function (e) { vm.error = TallyUtils.errorMessage(e, 'This store is unavailable.'); }).finally(function () { vm.loading = false; });
    vm.refreshCart();
  });

  app.controller('OrderStatusController', function ($routeParams, $interval, Api) {
    var vm = this; var path = 'storefront/' + $routeParams.storeSlug + '/orders/' + $routeParams.token + '/';
    vm.storeSlug = $routeParams.storeSlug;
    vm.money = TallyUtils.money;
    vm.load = function () {
      vm.loading = true;
      Api.get(path).then(function (order) {
        vm.order = order; vm.error = '';
        if (['completed', 'cancelled'].indexOf(order.status) >= 0) vm.stopPolling();
      }).catch(function (e) { vm.error = TallyUtils.errorMessage(e, 'Could not find this order.'); }).finally(function () { vm.loading = false; });
    };
    var poll = $interval(vm.load, 30000);
    vm.stopPolling = function () { if (poll) { $interval.cancel(poll); poll = null; } };
    vm.isTerminal = function () { return vm.order && ['completed', 'cancelled'].indexOf(vm.order.status) >= 0; };
    vm.load();
    vm.$onDestroy = vm.stopPolling;
  });
}());
