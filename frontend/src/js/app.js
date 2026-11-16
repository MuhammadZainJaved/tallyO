(function () {
  'use strict';

  angular.module('tallyO')
    .config(function ($routeProvider, $httpProvider) {
      $routeProvider
        .when('/', { templateUrl: '/templates/discovery.html', controller: 'DiscoveryController', controllerAs: 'vm' })
        .when('/login', { templateUrl: '/templates/login.html', controller: 'LoginController', controllerAs: 'vm' })
        .when('/admin', { templateUrl: '/templates/admin-dashboard.html', controller: 'AdminDashboardController', controllerAs: 'vm', auth: true })
        .when('/admin/stores/:storeId/settings', { templateUrl: '/templates/store-settings.html', controller: 'StoreSettingsController', controllerAs: 'vm', auth: true })
        .when('/admin/stores/:storeId/catalog', { templateUrl: '/templates/catalog.html', controller: 'CatalogController', controllerAs: 'vm', auth: true })
        .when('/admin/stores/:storeId/orders', { templateUrl: '/templates/orders.html', controller: 'OrdersController', controllerAs: 'vm', auth: true })
        .when('/admin/stores/:storeId/customers', { templateUrl: '/templates/customers.html', controller: 'CustomersController', controllerAs: 'vm', auth: true })
        .when('/admin/users', { templateUrl: '/templates/users.html', controller: 'UsersController', controllerAs: 'vm', auth: true, superAdmin: true })
        .when('/admin/reports', { templateUrl: '/templates/reports.html', controller: 'ReportsController', controllerAs: 'vm', auth: true, superAdmin: true })
        .when('/shop/:storeSlug', { templateUrl: '/templates/storefront.html', controller: 'StorefrontController', controllerAs: 'vm' })
        .when('/shop/:storeSlug/order/:token', { templateUrl: '/templates/order-status.html', controller: 'OrderStatusController', controllerAs: 'vm' })
        .otherwise({ redirectTo: '/' });

      $httpProvider.interceptors.push(function ($q, $location, Session) {
        return {
          request: function (config) {
            if (config.url.indexOf('/api/v1/') === 0 && Session.token()) {
              config.headers = config.headers || {};
              config.headers.Authorization = 'Token ' + Session.token();
            }
            return config;
          },
          responseError: function (response) {
            if (response.status === 401 && Session.authenticated()) {
              Session.clear();
              if ($location.path().indexOf('/admin') === 0) $location.path('/login');
            }
            return $q.reject(response);
          }
        };
      });
    })
    .run(function ($rootScope, $location, Session) {
      $rootScope.$on('$routeChangeStart', function (event, next) {
        if (next && next.auth && !Session.authenticated()) {
          event.preventDefault(); $location.path('/login');
        } else if (next && next.superAdmin && !Session.superAdmin()) {
          event.preventDefault(); $location.path('/admin');
        }
      });
    })
    .controller('ShellController', function ($location, Api, Session, Notifier) {
      var vm = this;
      vm.notices = Notifier.items;
      vm.showAdminNav = function () { return Session.authenticated() && $location.path().indexOf('/admin') === 0; };
      vm.isSuperAdmin = Session.superAdmin;
      vm.userName = function () { var user = Session.get().user || {}; return user.full_name || user.email || ''; };
      vm.logout = function () {
        Api.post('auth/logout/', {}).finally(function () { Session.clear(); $location.path('/login'); });
      };
    });
}());
