
debuggerApp.controller('mainController', ['$scope','$location', function($scope) {
    $scope.$on('$routeChangeSuccess', function() {
        var loc = window.location.href.split('/');
        $(".menu-content li").removeClass("active");
        loc = loc[loc.length-1];
        var active = document.getElementById(loc+'Link');
        if (active != null) {
            active.classList.add('active');
        }
    });
}]);