var instanceService = angular.module('instanceService',[]);

instanceService.factory('Instance', ['$http', '$log', '$timeout', '$q','$location', function($http, $log, $timeout, $q, $location){

  var instances = {
    getInstanceTable: function(args){

      var body = {};
      for(k in args){
        if(args[k]) body[k] = args[k];

      }

      var url ="/instance/api/instancetable";

      $log.info(url);
      var deferred = $q.defer();
      $http.post(url, body).success(function (data) {
        $log.info("instance table data retrieved");
        deferred.resolve(data);
      }).error(function () {
        deferred.reject("error in retrieving instance table data");
      });
      return deferred.promise;
    },

    getMachineTypes: function(){
      var url = $location.absUrl()+"api/machinetypes";
      var deferred = $q.defer();

      $http.get(url).success(function (data){
        $log.info("machine types retrieved");
        deferred.resolve(data);
      }).error(function () {
        deferred.reject("error in retrieving machine types");
      });
      return deferred.promise;
    },

    getTags: function(){
      var url = "/instance/api/tags";
      var deferred = $q.defer();

      $http.get(url).success(function (data){
        $log.info("tags retrieved");
        deferred.resolve(data);
      }).error(function () {
        deferred.reject("error in retrieving tags");
      });
      return deferred.promise;
    }
  };

  return instances;

}]);
