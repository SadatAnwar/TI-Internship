var debuggerApp = angular.module('debuggerApp', ['ngRoute']);

debuggerApp.config(function($routeProvider){
    $routeProvider.
            when('/', {
                templateUrl: '/pages/views/home.html',
                controller: 'mainController'
            }).
            when('/home', {
                templateUrl: '/pages/views/home.html',
                controller: 'mainController'
            }).
            when('/fram', {
                templateUrl: '/pages/views/fram.html',
            controller: 'mainController'
            }).
            when('/help', {
                templateUrl: '/pages/views/help.html'
            }).
            when('/setup', {
                templateUrl: '/pages/views/setup.html'
            }).
            when('/wip', {
                templateUrl: '/pages/views/wip.html'
            }).
            otherwise({
                redirectTo: '/home'
            });
    });