(function () {
  'use strict';

  var app = angular.module('tallyO');

  function storeBase($routeParams) { return 'stores/' + $routeParams.storeId + '/'; }
  function loadStore(Api, id, vm) {
    return Api.get('stores/' + id + '/').then(function (store) { vm.store = store; return store; });
  }
  function fail(vm, error, fallback) { vm.error = TallyUtils.errorMessage(error, fallback); }

  app.controller('AdminDashboardController', function (Api, Session, Notifier) {
    var vm = this;
    vm.isSuperAdmin = Session.superAdmin();
    vm.form = { timezone: 'Asia/Karachi', currency: 'PKR', delivery_fee: 0 };
    vm.slugFromName = function () { if (!vm.slugEdited) vm.form.slug = TallyUtils.slugify(vm.form.name); };
    vm.load = function () {
      vm.loading = true;
      Api.get('stores/').then(function (data) { vm.stores = TallyUtils.unwrap(data); }).catch(function (e) { fail(vm, e, 'Could not load stores.'); }).finally(function () { vm.loading = false; });
    };
    vm.create = function () {
      vm.saving = true; vm.error = '';
      Api.post('stores/', vm.form).then(function () {
        Notifier.success('Store created.'); vm.form = { timezone: 'Asia/Karachi', currency: 'PKR', delivery_fee: 0 }; vm.load();
      }).catch(function (e) { fail(vm, e, 'Could not create the store.'); }).finally(function () { vm.saving = false; });
    };
    vm.load();
  });

  app.controller('StoreSettingsController', function ($routeParams, Api, Session, Notifier) {
    var vm = this; var base = storeBase($routeParams);
    vm.isSuperAdmin = Session.superAdmin();
    function load() {
      vm.loading = true;
      loadStore(Api, $routeParams.storeId, vm).then(function (store) {
        vm.form = {
          name: store.name, timezone: store.timezone, currency: store.currency, delivery_fee: Number(store.delivery_fee),
          location_address: store.location_address,
          latitude: store.latitude === null ? null : Number(store.latitude),
          longitude: store.longitude === null ? null : Number(store.longitude),
          delivery_radius_miles: Number(store.delivery_radius_miles),
          delivery_radius_enabled: store.delivery_radius_enabled,
          branding: angular.extend({ logo_url: '', banner_url: '', primary_color: '#2563eb', secondary_color: '#0f172a', footer_text: '' }, store.branding || {})
        };
      }).catch(function (e) { fail(vm, e, 'Could not load store settings.'); }).finally(function () { vm.loading = false; });
      Api.get(base + 'memberships/').then(function (data) { vm.memberships = TallyUtils.unwrap(data); });
      if (vm.isSuperAdmin) Api.get('users/').then(function (data) { vm.users = TallyUtils.unwrap(data); });
    }
    vm.save = function () {
      vm.saving = true; vm.error = '';
      Api.patch('stores/' + $routeParams.storeId + '/', vm.form).then(function () { Notifier.success('Store settings saved.'); load(); })
        .catch(function (e) { fail(vm, e, 'Could not save settings.'); }).finally(function () { vm.saving = false; });
    };
    vm.addMember = function () {
      Api.post(base + 'memberships/', { user_id: vm.memberUserId, is_active: true }).then(function () { vm.memberUserId = ''; Notifier.success('Store administrator assigned.'); load(); })
        .catch(function (e) { fail(vm, e, 'Could not assign administrator.'); });
    };
    vm.toggleMember = function (member) {
      Api.patch(base + 'memberships/' + member.id + '/', { is_active: !member.is_active }).then(function () { Notifier.success('Membership updated.'); load(); })
        .catch(function (e) { fail(vm, e, 'Could not update membership.'); });
    };
    load();
  });

  app.controller('CatalogController', function ($routeParams, Api, Notifier) {
    var vm = this; var base = storeBase($routeParams);
    vm.categoryForm = { display_order: 0, is_active: true };
    vm.productForm = { price: '0.00', is_active: true, track_inventory: false, stock_quantity: 0, category: null };
    function load() {
      vm.loading = true;
      loadStore(Api, $routeParams.storeId, vm);
      return Api.get(base + 'categories/').then(function (data) { vm.categories = TallyUtils.unwrap(data); })
        .then(function () { return Api.get(base + 'products/'); }).then(function (data) { vm.products = TallyUtils.unwrap(data); })
        .catch(function (e) { fail(vm, e, 'Could not load the catalog.'); }).finally(function () { vm.loading = false; });
    }
    vm.categorySlug = function () { if (!vm.categoryForm.id) vm.categoryForm.slug = TallyUtils.slugify(vm.categoryForm.name); };
    vm.productSlug = function () { if (!vm.productForm.id) vm.productForm.slug = TallyUtils.slugify(vm.productForm.name); };
    vm.editCategory = function (item) { vm.categoryForm = angular.copy(item); };
    vm.cancelCategory = function () { vm.categoryForm = { display_order: 0, is_active: true }; };
    vm.saveCategory = function () {
      var form = angular.copy(vm.categoryForm); var call = form.id ? Api.patch(base + 'categories/' + form.id + '/', form) : Api.post(base + 'categories/', form);
      call.then(function () { Notifier.success('Category saved.'); vm.cancelCategory(); load(); }).catch(function (e) { fail(vm, e, 'Could not save category.'); });
    };
    vm.deleteCategory = function (item) {
      if (!window.confirm('Delete category "' + item.name + '"? Products remain uncategorized.')) return;
      Api.remove(base + 'categories/' + item.id + '/').then(function () { Notifier.success('Category deleted.'); load(); }).catch(function (e) { fail(vm, e, 'Could not delete category.'); });
    };
    vm.editProduct = function (item) { vm.productForm = angular.copy(item); vm.productForm.category = item.category || null; };
    vm.cancelProduct = function () { vm.productForm = { price: '0.00', is_active: true, track_inventory: false, stock_quantity: 0, category: null }; };
    vm.saveProduct = function () {
      var form = angular.copy(vm.productForm); form.category = form.category || null; delete form.category_name; delete form.is_available; var call = form.id ? Api.patch(base + 'products/' + form.id + '/', form) : Api.post(base + 'products/', form);
      call.then(function () { Notifier.success('Product saved.'); vm.cancelProduct(); load(); }).catch(function (e) { fail(vm, e, 'Could not save product.'); });
    };
    vm.deleteProduct = function (item) {
      if (!window.confirm('Delete product "' + item.name + '"?')) return;
      Api.remove(base + 'products/' + item.id + '/').then(function () { Notifier.success('Product deleted.'); load(); }).catch(function (e) { fail(vm, e, 'Could not delete product.'); });
    };
    load();
  });

  app.controller('OrdersController', function ($routeParams, Api, Notifier) {
    var vm = this; var base = storeBase($routeParams);
    vm.statuses = ['', 'pending', 'confirmed', 'preparing', 'ready', 'out_for_delivery', 'completed', 'cancelled'];
    vm.transitions = { pending: ['confirmed', 'cancelled'], confirmed: ['preparing', 'cancelled'], preparing: ['ready', 'cancelled'], ready: ['out_for_delivery', 'completed', 'cancelled'], out_for_delivery: ['completed', 'cancelled'] };
    vm.money = TallyUtils.money;
    vm.load = function () {
      vm.loading = true; loadStore(Api, $routeParams.storeId, vm);
      Api.get(base + 'orders/', vm.status ? { status: vm.status } : {}).then(function (data) { vm.orders = TallyUtils.unwrap(data); })
        .catch(function (e) { fail(vm, e, 'Could not load orders.'); }).finally(function () { vm.loading = false; });
    };
    vm.transition = function (order, status) {
      if (!status) return;
      Api.post(base + 'orders/' + order.id + '/transition/', { status: status }).then(function () { Notifier.success('Order moved to ' + status.replace(/_/g, ' ') + '.'); vm.load(); })
        .catch(function (e) { fail(vm, e, 'Could not update the order.'); });
    };
    vm.load();
  });

  app.controller('CustomersController', function ($routeParams, Api, Notifier) {
    var vm = this; var base = storeBase($routeParams);
    function load() {
      vm.loading = true; loadStore(Api, $routeParams.storeId, vm);
      Api.get(base + 'customers/').then(function (data) { vm.customers = TallyUtils.unwrap(data); })
        .catch(function (e) { fail(vm, e, 'Could not load customers.'); }).finally(function () { vm.loading = false; });
    }
    vm.edit = function (customer) { vm.editing = angular.copy(customer); };
    vm.cancel = function () { vm.editing = null; };
    vm.save = function () {
      vm.saving = true; vm.error = '';
      Api.patch(base + 'customers/' + vm.editing.id + '/', {
        name: vm.editing.name,
        email: vm.editing.email,
        last_delivery_address: vm.editing.last_delivery_address
      }).then(function () { Notifier.success('Customer updated.'); vm.cancel(); load(); })
        .catch(function (e) { fail(vm, e, 'Could not update customer.'); })
        .finally(function () { vm.saving = false; });
    };
    load();
  });

  app.controller('UsersController', function (Api, Notifier) {
    var vm = this; vm.form = { is_superuser: false };
    function load() { Api.get('users/').then(function (data) { vm.users = TallyUtils.unwrap(data); }).catch(function (e) { fail(vm, e, 'Could not load users.'); }); }
    vm.create = function () {
      vm.saving = true; vm.error = '';
      Api.post('users/', vm.form).then(function () { vm.form = { is_superuser: false }; Notifier.success('Staff user created.'); load(); })
        .catch(function (e) { fail(vm, e, 'Could not create user.'); }).finally(function () { vm.saving = false; });
    };
    vm.toggle = function (user) {
      Api.patch('users/' + user.id + '/', { full_name: user.full_name, is_active: !user.is_active }).then(function () { Notifier.success('User updated.'); load(); })
        .catch(function (e) { fail(vm, e, 'Could not update user.'); });
    };
    load();
  });

  app.controller('ReportsController', function (Api) {
    var vm = this;
    vm.loading = true;
    Api.get('reports/daily-orders/').then(function (data) { vm.reports = TallyUtils.unwrap(data); })
      .catch(function (e) { fail(vm, e, 'Could not load reports.'); }).finally(function () { vm.loading = false; });
  });
}());
