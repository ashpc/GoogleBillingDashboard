/**
 * Created by ashwini on 3/9/16.
 */
'use strict';

/* Controllers */

var cuQuotaControllers = angular.module('cuQuotaControllers', []);

cuQuotaControllers.controller('CPUQuotaListController', ['$scope', '$log', '$sce', 'Quota', '$location',
  'UsageCost', '$filter', '$http',
  function ($scope, $log, $sce, Quota, $location, UsageCost, $filter, $http) {

    var init = function init() {
      $log.info('----- CPU Controller INIT --- ');

      $scope.centerSelected = 'all';
      $scope.regionSelected = '';
      $scope.metricSelected = 'CPUS';
      $scope.projectSelected = 'all';

      $scope.costCenterList = [];
      $scope.projectList = [];
      $scope.regionsList = [];
      $scope.metricsList = [];
      $scope.regionList = [];
      $scope.failedList = '';
      $scope.metric = {
        total: '',
        totalUsed: ''
      };
      // get the url params
      $scope.getURLParams();
    };

    /**
     * get the url params to match the filter
     */
    $scope.getURLParams = function getURLParams() {
      var params = $location.search();
      //if params not found then first time get the center list and set it to all
      if (!params.cost_center) {
        $scope.centerSelected = 'all';
        $scope.projectSelected = 'all';
      } else if (!params.project) {
        $scope.projectSelected = 'all';
        $scope.centerSelected = params.cost_center;
      } else {
        $scope.centerSelected = params.cost_center;
        $scope.projectSelected = params.project;
      }
      $location.search('cost_center', $scope.centerSelected);
      $location.search('project', $scope.projectSelected);
      getCostCenterList();
    };
    /* on location change call filter change with the updated params
     * */
    $scope.$on('$locationChangeSuccess', function (next, current) {
      var params = $location.search();
      $log.info('Location Change Called');
      $log.info(params);
      $log.info($scope.centerSelected);
      $log.info($scope.projectSelected);

      if (params.cost_center && !params.project) {
        $log.info('Project Not There');

        $scope.centerSelected = params.cost_center;
        $scope.projectSelected = 'all';
        $scope.setDefaults($scope.projectSelected);
        if ($scope.costCenterList.length == 0) {
          getCostCenterList();
        }
      } else if (params.cost_center && params.project != 'all') {
        $scope.centerSelected = params.cost_center;
        $scope.projectSelected = params.project;
        $scope.setDefaults($scope.projectSelected);
      }

      if ($scope.projectList.length != 0) {
        $scope.getProjectList();
      }
    });

    $scope.updateURLParams = function updateURLParams(center, project) {

      if (!project || project == 'all') {
        $location.search('cost_center', center);
        $location.search('project', 'all');
        $scope.projectSelected = 'all';
        $scope.fail = false;
        //$scope.getProjectList();
      } else {
        $location.search('cost_center', center);
        $location.search('project', project);
        //$scope.getCPUQuota();
      }

    };
    $scope.setDefaults = function setDefaults(project) {

      $scope.projectSelected = project;
      $scope.regionsList = [];
      $scope.metricsList = [];
      $scope.regionList = [];
      $scope.loading = true;
      $scope.fail = false;

    };
    var getCostCenterList = function getCostCenterList() {
      UsageCost.getCostCenterList(true).then(function (value) {

        $log.info(value);
        $scope.costCenterList = value.cost_center_list;
        $scope.setDefaults($scope.projectSelected);
        $scope.getProjectList();

      }, function (reason) {
        var msg = (reason.data && reason.data.message) ? reason.data.message : CU.usage_error_msg;
        $log.error('Reason for Failure ---', msg);
        $scope.fail = true;
        $scope.class_name = 'red';
        $('#container').html('');
        $scope.message = $sce.trustAsHtml('Reason for Failure ---' + msg);

      }, function (update) {
        $log.info('Update  ---', update);
      });

    };
    /**
     *
     * @param center
     * @returns {boolean}
     * based on the center value get the list of projects and update the url as well
     */

    $scope.getProjectList = function getProjectList() {
      $scope.projectList = [];
      $scope.loading = true;
      $scope.setDefaults($scope.projectSelected);
      UsageCost.getProjectList($scope.centerSelected).then(function (value) {
        $log.info(value);
        $scope.loading = false;
        $scope.projectList = value;
        $scope.getCPUQuota();

      }, function (reason) {
        var msg = (reason.data && reason.data.message) ? reason.data.message : CU.error_msg;
        $log.error('Reason for Failure ---', msg);
        $scope.fail = true;
        $scope.loading = false;
        $scope.class_name = 'red';
        $('#container').html('');
        $scope.message = $sce.trustAsHtml('Reason for Failure ---' + msg);

      }, function (update) {
        $log.info('Update  ---', update);
      });
    };
    /**
     * get the CPU data based on the project selected
     */

    $scope.getCPUQuota = function getCPUQuota() {
      $scope.setDefaults($scope.projectSelected);
      $scope.failedList = '';
      if ($scope.projectSelected == 'all') {
        $.each($scope.projectList, function (key, value) {
          $scope.currentProject = value;
          $scope.getQuota(value, 'all');
        });
      } else {
        $scope.currentProject = '';
        $scope.getQuota($scope.projectSelected);
      }


    };
    /**
     * QuotaListing Api call for single or multiple calls
     *
     */
    $scope.getQuota = function (project, type) {

      UsageCost.getQuota(project).then(function (value) {
        $log.debug($scope.regionsList);
        $scope.loading = $scope.getStatus();
        $scope.regionsList = $scope.regionsList.concat(value);

        $scope.getUniqueLists(project);
        $scope.getTotal();
      }, function (reason) {
        if (typeof(type) != 'undefined' && type == 'all') {
          $scope.fail = true;
          $scope.class_name = 'red';
          $scope.failedList += project + ' , ';
          $scope.loading = $scope.getStatus();

          var msg = '<div class="panel-body region_error"><span>Failed projects are : <b> ' + $scope.failedList +
            '</b> </span></div>';

          // if ($scope.regionsList.length == 0) {
          $scope.message = $sce.trustAsHtml(msg);
          //}
        } else {
          var msg = (reason.data && reason.data.message) ? reason.data.message : CU.error_msg;
          $log.error('Reason for Failure ---', msg);
          $scope.fail = true;
          $scope.loading = $scope.getStatus();
          $scope.class_name = 'red';
          $('#container').html('');
          $scope.message = $sce.trustAsHtml('Reason for Failure ---' + msg);

        }


      }, function (update) {
        $log.info('Update  ---', update);
      });
    };
    $scope.getStatus = function () {
      if (!$http.pendingRequests.length > 0) {
        $scope.failedList = $scope.failedList.slice(0, $scope.failedList.lastIndexOf(","));
      }
      return $http.pendingRequests.length > 0;
    };
    /**
     * get total cpu usage when metricSelected == CPUS
     */

    $scope.getTotal = function getTotal() {

      // if ($scope.metricSelected == 'CPUS') {
      if ($scope.metricSelected != 'all') {
        $scope.hideTotal = false;
        $scope.queryData = [];
        $scope.total = 0;
        $scope.totalUsed = 0;
        var region = $filter('filter')($scope.regionList, $scope.regionSelected);
        $.each($scope.regionsList, function (key, item) {
          if (region.indexOf(item['name']) != -1) {
            $scope.queryData.push($filter('filter')(item['quotas'], $scope.metricSelected));
          }
        });

        $.each($scope.queryData, function (key, value) {
          $scope.total += parseInt(value[0].limit);
          $scope.totalUsed += parseInt(value[0].usage);
        });
        $scope.metric = {
          total: $scope.total,
          totalUsed: $scope.totalUsed
        };
      } else {
        $scope.hideTotal = true;

      }


      //}
    };

    /**
     * get unique region list and metrics list
     */
    $scope.getUniqueLists = function getUniqueLists(project) {

      $log.debug('UNIQUE');
      $log.debug(project);

      angular.forEach($scope.regionsList, function (key, val) {
        if (project) {
          if (!key.hasOwnProperty('project')) {
            key['project'] = project;
          }
        }
        if ($scope.regionList.indexOf(key['name']) == -1) {

          $scope.regionList.push(key['name']);
        }
        angular.forEach(key['quotas'], function (k, value) {
          if ($scope.metricsList.indexOf(k['metric']) == -1) {

            $scope.metricsList.push(k['metric']);
          }
        });
      });
    };
    /**
     * add class basedon status
     */
    $scope.regionStatus = function regionStatus(status) {
      if (status == 'UP') {
        return 'fa fa-arrow-up text-success';
      } else if (status == 'DOWN') {
        return 'fa fa-arrow-up text-danger';
      }
    };
    /**
     * get usage %
     */
    $scope.getUsage = function getUsage(usage, limit, metric) {
      metric.usage_percent = parseFloat(((usage / limit) * 100).toFixed(2));
      metric.width = metric.usage_percent + '%';
      if (metric.usage_percent <= 50) {
        return 'progress-bar progress-bar-success';

      } else if (metric.usage_percent > 51 && metric.usage_percent <= 70) {
        return 'progress-bar progress-bar-warning';

      } else if (metric.usage_percent > 71) {
        return 'progress-bar progress-bar-danger';
      }

    };


    init();
  }
])
;
