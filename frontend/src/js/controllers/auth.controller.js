(function () {
  'use strict';

  angular.module('tallyO').controller('LoginController', function ($location, Api, Session) {
    var vm = this;
    vm.credentials = { email: '', password: '' };
    if (Session.authenticated()) $location.path('/admin');
    vm.submit = function () {
      vm.loading = true; vm.error = '';
      Api.post('auth/login/', vm.credentials).then(function (data) {
        Session.set(data); $location.path('/admin');
      }).catch(function (error) {
        vm.error = TallyUtils.errorMessage(error, 'The email or password is incorrect.');
      }).finally(function () { vm.loading = false; });
    };
  });
}());
