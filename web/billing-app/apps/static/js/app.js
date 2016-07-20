'use strict';


/* App Module  that includes all the modules needed for this cu.App module
 ngRoute --- for routing
 ui.bootstrap --- for all bootstrap funcitionalities
 cu.Animations  -- custom module for animation that uses ngAnimate module
 controllers -- controller module that has all the controllers used

 */

/**
 * Based on the url load the dependencies for the angular app
 */

if (document.URL.indexOf('billing') != -1) {
  var cuApp = angular.module('cuApp', [
    'ngRoute',
    'ngCookies',
    'ui.bootstrap',
    'angular.filter',
    'cuControllers',
    'loginService',
    'cuBillingControllers',
    'cuProjectsControllers',
    'cuDirectorsControllers',
    'billingService',
    'exportImportController',
    'cuFilters'
  ]);

} else if (document.URL.indexOf('quota') != -1) {
  var cuApp = angular.module('cuApp', [
    'ngRoute',
    'ngCookies',
    'ui.bootstrap',
    'angular.filter',
    'cuControllers',
    'loginService',
    'cuQuotaControllers',
    'cuDirectorsControllers',
    'quotaService',
    'billingService',
    'cuFilters'
  ]);

} else {
  var cuApp = angular.module('cuApp', [
    'ngRoute',
    'ngCookies',
    'ui.bootstrap',
    'angular.filter',
    'cuControllers',
    'usageController',
    'usageService',
    'loginService'
  ]);
}
/*
 Define all the routing used for this app
 templateUrl --> have the partial url defined
 controller --> what controller to use

 */

cuApp.run(function ($rootScope, $cookies) {
  $rootScope.login_cookie = $cookies.get('cloudAdminCookie');
  $rootScope.user = $cookies.get('cloudUser');
  $rootScope.isLogged = function () {
    if ($cookies.get('cloudAdminCookie') && $cookies.get('cloudAdminCookie') != '') {
      return true;
    } else {
      return false;
    }
  };

});
