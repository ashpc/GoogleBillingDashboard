var instanceController = angular.module('instanceController', []);

instanceController.controller('instanceController', ['$scope',  '$log', 'Instance', 'Usage', function($scope, $log, Instance, Usage){

  $scope.instanceTable = [];

  // lists used for dropdowns
  $scope.yearsList = [];
  $scope.machine_types = [];
  $scope.projectsList = [];
  $scope.tags = [];
  $scope.monthsList = [
      {'month':'January', 'num':1},   {'month':'February', 'num':2},
      {'month':'March', 'num':3},     {'month':'April', 'num':4},
      {'month':'May', 'num':5},       {'month':'June', 'num':6},
      {'month':'July', 'num':7},      {'month':'August', 'num':8},
      {'month':'September', 'num':9}, {'month':'October', 'num':10},
      {'month':'November', 'num':11}, {'month':'December', 'num':12}
    ];

  // query string values
  $scope.body = {
    'machine_type': null,
    'tags': null,
    'project': null,
    'month': null,
    'year': null

  }

  $scope.sortType = "name";
  $scope.sortReverse = false;
  $scope.allOpen = false;



  $scope.init = function(){
    var date = new Date();
    var yr = date.getFullYear();
    $scope.yearsList.push(yr);
    $scope.yearsList.push(yr-1);
    $scope.getProjectNames();
    $scope.getInstanceTable();
    $scope.getMachineTypes();
    $scope.getTags();

  };

  $scope.getInstanceTable = function(){
    if ($scope.body.tags) {
      if ($scope.body.tags.length > 0) {

        var tmp = [];
        for( var i = 0; i<$scope.body.tags.length; i++ ){
          tmp.push($scope.body.tags[i].name);
        }
        $scope.body.tags = tmp;
      } else {
      $scope.body.tags = null;
      }
    }

    Instance.getInstanceTable($scope.body).then(function(value){
      $scope.instanceTable = value;
      for(var i = 0; i<$scope.instanceTable.length; i++){
        $scope.instanceTable[i].open = false;
      }
    }, function(update){
      $log.info('Update ---', update);
    });
  };

  $scope.getProjectNames = function(){
    Usage.getProjectNames().then(function(value){
      $scope.projectsList = value;
    }, function(update){
      $log.info('Update ---', update);
    });
  };

  $scope.getMachineTypes = function(){
    Instance.getMachineTypes().then(function(value){
      $scope.machine_types = value;
    }, function (update){
      $log.info('Update ---', update);
    });
  };

  $scope.getTags = function(){
    Instance.getTags().then(function(value){
      for(var i=0; i<value.length; i++){
        $scope.tags.push({'name': value[i], 'ticked':false});
      }
    }, function (update){
      $log.info('Update ---', update);
    });
  };

  $scope.reset = function (){
    $scope.year = null;
    $scope.month= null;
    $scope.body.machine_type = null;
    $scope.body.project = null;
    $scope.body.tags = null;
    $scope.body.year = null;
    $scope.body.month = null;

    for (var i = 0; i < $scope.tags.length; i++ ){
      $scope.tags[i].ticked = false;
    }


    $scope.getInstanceTable();

  };

  $scope.openCloseAll = function () {
    $scope.allOpen = !$scope.allOpen;

    for (var i = 0; i < $scope.instanceTable.length; i++){
      $scope.instanceTable[i].open = $scope.allOpen;
    }

  };

  $scope.init();

}]);
