(function () {
  'use strict';

  angular.module('tallyO').directive('googleMapPicker', function (GoogleMaps, $window) {
    return {
      restrict: 'E',
      scope: {
        latitude: '=',
        longitude: '=',
        address: '=',
        radius: '=',
        zoneLatitude: '<?',
        zoneLongitude: '<?',
        mode: '@'
      },
      template: '<div class="map-picker">' +
        '<div class="map-search-host" ng-show="mapsReady"></div>' +
        '<div class="map-canvas" ng-show="mapsReady"></div>' +
        '<div class="map-unavailable" ng-if="mapsUnavailable"><strong>Google Maps is not configured.</strong><span>You can still use browser location or enter coordinates manually.</span></div>' +
        '<p class="form-error" ng-if="mapError" ng-bind="mapError"></p>' +
        '<div class="map-actions"><button type="button" class="button button-secondary button-small" ng-click="useCurrentLocation()">Use current location</button><span ng-if="latitude && longitude">Selected: {{latitude}}, {{longitude}}</span></div>' +
      '</div>',
      link: function (scope, element) {
        var map;
        var marker;
        var circle;
        var geocoder;
        var maps;
        var canvas = element[0].querySelector('.map-canvas');
        var searchHost = element[0].querySelector('.map-search-host');
        var defaultCenter = { lat: 31.5204, lng: 74.3587 };

        function number(value) {
          var parsed = Number(value);
          return Number.isFinite(parsed) ? parsed : null;
        }

        function zoneCenter() {
          var lat = number(scope.mode === 'store' ? scope.latitude : scope.zoneLatitude);
          var lng = number(scope.mode === 'store' ? scope.longitude : scope.zoneLongitude);
          return lat === null || lng === null ? null : { lat: lat, lng: lng };
        }

        function selectedPoint() {
          var lat = number(scope.latitude);
          var lng = number(scope.longitude);
          return lat === null || lng === null ? null : { lat: lat, lng: lng };
        }

        function updateCircle() {
          if (!circle) return;
          var center = zoneCenter();
          if (center) circle.setCenter(center);
          circle.setRadius(Math.max(.1, number(scope.radius) || 1) * 1609.344);
          circle.setVisible(Boolean(center));
        }

        function setMarker(position) {
          if (!maps || !map || !position) return;
          if (!marker) {
            marker = new maps.marker.AdvancedMarkerElement({ map: map, position: position, gmpDraggable: true });
            marker.addListener('dragend', function (event) {
              choosePoint(event.latLng.lat(), event.latLng.lng(), true);
            });
          } else {
            marker.position = position;
          }
        }

        function reverseGeocode(position) {
          if (!geocoder) return;
          geocoder.geocode({ location: position }).then(function (response) {
            if (response.results && response.results[0]) {
              scope.$applyAsync(function () { scope.address = response.results[0].formatted_address; });
            }
          }).catch(function () {});
        }

        function choosePoint(latitude, longitude, lookupAddress, formattedAddress) {
          var position = { lat: latitude, lng: longitude };
          scope.$applyAsync(function () {
            scope.latitude = Number(latitude.toFixed(6));
            scope.longitude = Number(longitude.toFixed(6));
            if (formattedAddress) scope.address = formattedAddress;
          });
          setMarker(position);
          map.panTo(position);
          if (scope.mode === 'store') updateCircle();
          if (lookupAddress) reverseGeocode(position);
        }

        function initialize(googleMaps) {
          maps = googleMaps;
          var center = selectedPoint() || zoneCenter() || defaultCenter;
          map = new maps.Map(canvas, { center: center, zoom: zoneCenter() ? 14 : 11, mapId: 'DEMO_MAP_ID', streetViewControl: false });
          geocoder = new maps.Geocoder();
          circle = new maps.Circle({ map: map, strokeColor: '#2563eb', strokeOpacity: .8, strokeWeight: 2, fillColor: '#3b82f6', fillOpacity: .12 });
          updateCircle();
          setMarker(selectedPoint());
          map.addListener('click', function (event) { choosePoint(event.latLng.lat(), event.latLng.lng(), true); });

          var autocomplete = new maps.places.PlaceAutocompleteElement();
          autocomplete.placeholder = 'Search for an address or place';
          searchHost.appendChild(autocomplete);
          autocomplete.addEventListener('gmp-select', function (event) {
            var place = event.placePrediction.toPlace();
            place.fetchFields({ fields: ['formattedAddress', 'location'] }).then(function () {
              if (place.location) choosePoint(place.location.lat(), place.location.lng(), false, place.formattedAddress);
            });
          });
          scope.mapsReady = true;
        }

        scope.useCurrentLocation = function () {
          scope.mapError = '';
          if (!$window.navigator.geolocation) {
            scope.mapError = 'This browser does not support location services.';
            return;
          }
          $window.navigator.geolocation.getCurrentPosition(function (position) {
            scope.$applyAsync(function () {
              scope.latitude = Number(position.coords.latitude.toFixed(6));
              scope.longitude = Number(position.coords.longitude.toFixed(6));
            });
            if (map) choosePoint(position.coords.latitude, position.coords.longitude, true);
          }, function () {
            scope.$applyAsync(function () { scope.mapError = 'Location permission was denied or unavailable.'; });
          }, { enableHighAccuracy: true, timeout: 10000 });
        };

        GoogleMaps.load().then(function (googleMaps) {
          if (!googleMaps) { scope.mapsUnavailable = true; return; }
          initialize(googleMaps);
        }).catch(function () {
          scope.mapsUnavailable = true;
          scope.mapError = 'Google Maps could not be loaded. Check the API key and enabled APIs.';
        });

        scope.$watchGroup(['latitude', 'longitude', 'radius'], function () {
          if (!map) return;
          var point = selectedPoint();
          if (point) setMarker(point);
          updateCircle();
        });
      }
    };
  });
}());
