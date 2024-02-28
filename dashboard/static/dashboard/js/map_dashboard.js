// Initialize and add the map
let map;
//var markers = [];
var data_prev = [];
var data_new = [];
var data_backup = [];
var bounds;
var legend;

var marker_property = {
    'is_new': {
        'title': 'NEW',
        'markerColor': '#0000ff', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "white",
        'glyphColor': "#0000ff",
        'glyphBorder': "white",
        'glyphScale': 1.2,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'is_show': true,
        'is_cluster': false,
        //'count': 0,
    },
    'is_online': {
        'title': 'ONLINE',
        'markerColor': '#009900', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "white",
        'glyphColor': "#009900",
        'glyphBorder': "white",
        'glyphScale': 1.0,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'is_show': true,
        'is_cluster': true,
        //'count': 0,
    },
    'is_offline': {
        'title': 'OFFLINE',
        'markerColor': '#ff0000', // Yellow
        'glyph': "/static/dashboard/images/backone-white-trans.svg",
        //'glyphColor': "black",
        'glyphColor': "#ff0000",
        'glyphBorder': "white",
        'glyphScale': 1.1,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'is_show': true,
        'is_cluster': true,
        //'count': 0,
    },
    'is_problem': {
        'title': 'PROBLEM',
        'markerColor': '#ffc300', // Yellow
        'glyph': "/static/dashboard/images/backone-black-trans.svg",
        //'glyph': backoneTrans,
        //'glyphColor': "black",
        'glyphColor': "#ffc300",
        'glyphBorder': "black",
        'glyphScale': 1.3,
        'map': null,
        'data': [],
        'markers': [],
        'markersCluster': null,
        'is_show': true,
        'is_cluster': false,
        //'count': 0,
    },
};

const intersectionObserverDrop = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("drop");
      intersectionObserverDrop.unobserve(entry.target);
    }
  }
});


const intersectionObserverBounce = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (entry.isIntersecting) {
      entry.target.classList.add("bounce");
      intersectionObserverBounce.unobserve(entry.target);
    }
  }
});

// Sets the map on all markers in the array.
function setMapOnAll(key, map) {
    for (let i = 0; i < marker_property[key].markers.length; i++) {
        marker_property[key].markers[i].setMap(map);
    }
}

function setClusterOnAll(key, is_show) {
    if (marker_property[key].markersCluster != null) {
        //console.log(marker_property[key].markersCluster);
        if (is_show) {
            marker_property[key].markersCluster.addMarkers(marker_property[key].markers);
            marker_property[key].markersCluster.render();
        }
        else
            marker_property[key].markersCluster.clearMarkers();
    }
}

// Removes the markers from the map, but keeps them in the array.
function hideMarkers(key) {
  setMapOnAll(key, null);
  setClusterOnAll(key, false);
}

// Shows any markers currently in the array.
function showMarkers(key) {
  if (marker_property[key].is_show)
    if (marker_property[key].is_cluster)
        setClusterOnAll(key, true);
    else
        setMapOnAll(key, map);
}

function showMarkersData(data) {


}

// Deletes all markers in the array by removing references to them.
function deleteMarkers(key) {
  hideMarkers(key);
  //for (let key in marker_property) {
      marker_property[key].markers = [];
      marker_property[key].markersCluster = null;
  //}
}


function drawMarker(key) {

    var infowindow = new google.maps.InfoWindow();
    var marker, i;
    var pinGlyph, markerColor;
    var data_marker = [];
    var return_renderer;
    var problem_link;

    // Reset Markers
    marker_property[key].markers = [];
    marker_property[key].markersCluster = [];

    //if (key == 'is_new' || key == 'is_problem')
    if (! marker_property[key].is_cluster)
        marker_property[key].map = map;

    if (! marker_property[key].is_show)
        marker_property[key].map = null;

    for (i = 0; i < marker_property[key].data.length; i++) {  

      data_marker = marker_property[key].data[i];

      markerColor = marker_property[key].markerColor;
      if (key == 'is_problem') {
        if (data_marker['is_online'])
            markerColor = marker_property['is_online'].markerColor;
            //marker_property[key].markerColor = marker_property['is_online'].markerColor;
        else
            markerColor = marker_property['is_offline'].markerColor;
            //marker_property[key].markerColor = marker_property['is_offline'].markerColor;
      }

      if (key == 'is_offline') {
        if (!data_marker['is_authorized'])
          markerColor = 'grey';
      }

      const glyphImg = document.createElement("img");
      glyphImg.src = marker_property[key].glyph;

      pinGlyph = new google.maps.marker.PinElement({
          background: markerColor,
          //background: marker_property[key].markerColor,
          borderColor: marker_property[key].glyphBorder,
          glyphColor: marker_property[key].glyphColor,
          glyph: glyphImg,
          scale: marker_property[key].glyphScale
      });

      marker = new google.maps.marker.AdvancedMarkerElement({
          position: new google.maps.LatLng(data_marker['lat'], data_marker['lng']),
          content: pinGlyph.element,
          map: marker_property[key].map,
          title: data_marker['name']
      });

      const content = marker.content;
      // Start - Animation Drop
      content.style.opacity = "0";
      content.addEventListener("animationend", (event) => {
          content.classList.remove("drop");
          content.style.opacity = "1";
          if (key == 'is_problem') {
              const time = 5 + Math.random(); // 2s delay for easy to see the animation
              content.style.setProperty("--bounce-delay-time", time + "s");
              intersectionObserverBounce.observe(content);
          }
      });

      const time = 1 + Math.random(); // 2s delay for easy to see the animation
      //const time = Math.random(); // 2s delay for easy to see the animation

      content.style.setProperty("--delay-time", time + "s");
      intersectionObserverDrop.observe(content);
      // End - Animation Drop

      // Start - Content InfoWindow

      problem_link = ''; 
      if (data_marker['is_problem']) {
        problem_link = '<a href="/problems/memberproblems/?q=' + data_marker['member_id'] + '">PROBLEM</a>&nbsp;&nbsp;&nbsp;';
      }

      let contentString =
            '<div id="content">' +
            '<div id="siteNotice"></div>' +
            '<h2 id="firstHeading" class="firstHeading">' + data_marker['name'] + '</h2>' +
            '<div id="bodyContent">' +
            '<p style="color: black;">' + data_marker['address'] + '</p>' +
            '<p style="color: black;">' + data_marker['network'] + '</p>' +
            '<p style="color: black;">' + data_marker['services'] + '</p>' +
            '<a href="/members/members/?q=' + data_marker['member_id'] + '">CHECK</a>' +
            '</div>' +
            '</div>';

      google.maps.event.addListener(marker, 'click', (function(marker, i) {
        return function() {
          infowindow.setContent(contentString);
          infowindow.open(map, marker);
        }
      })(marker, i));
      // End - Content InfoWindow

      //if (key == 'is_online' || key == 'is_offline') {
        marker_property[key].markers.push(marker);
      //}
    }

    // Start - Renderer
    let customRenderer = new markerClusterer.DefaultRenderer();
    customRenderer.render = function({ count, position }, stats, map) {
        //const color = markerColor;
        const color = marker_property[key].markerColor;
        // create svg literal with fill color
        const svg = `<svg fill="${color}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="50" height="50">
<circle cx="120" cy="120" opacity=".6" r="70" />
<circle cx="120" cy="120" opacity=".3" r="90" />
<circle cx="120" cy="120" opacity=".2" r="110" />
<text x="50%" y="50%" style="fill:#fff" text-anchor="middle" font-size="50" dominant-baseline="middle" font-family="roboto,arial,sans-serif">${count}</text>
</svg>`;

        const title = `Cluster of ${count} markers`;
        // adjust zIndex to be above other markers
        zIndex = Number(google.maps.Marker.MAX_ZINDEX) + count;

        if (map.getMapCapabilities().isAdvancedMarkersAvailable) {
            // create cluster SVG element
            const div = document.createElement("div");
            div.innerHTML = svg;
            const svgEl = div.firstElementChild;
            svgEl.setAttribute("transform", "translate(0 25)");
            const clusterOptions = {
                map,
                position,
                zIndex,
                title,
                content: svgEl,
            };
            
            return new google.maps.marker.AdvancedMarkerElement(clusterOptions);
        }
        const clusterOptions = {
            position,
            zIndex,
            title,
            icon: {
                url: `data:image/svg+xml;base64,${btoa(svg)}`,
                anchor: new google.maps.Point(25, 25),
            },
        };

        return new google.maps.Marker(clusterOptions);
    }

    // Add a marker clusterer to manage the markers.
    if (marker_property[key].is_cluster) {
        let markersCluster = new markerClusterer.MarkerClusterer({ 
            map: map,
            markers: marker_property[key].markers,
            renderer: customRenderer
        });
        marker_property[key].markersCluster = markersCluster;
        if (! marker_property[key].is_show) {
            markersCluster.clearMarkers();
        }
    }
    else {
        marker_property[key].markersCluster = null;
    }
}


async function get_api(base_api, is_all, is_no_org, query_id) {

    var api_url;

    api_url = base_api + '/api/members/get_by_user/' + query_id;

    /*
    if (is_all)
        api_url = base_api + '/api/members/get_all';
    else
        if (is_no_org)
            api_url = base_api + '/api/members/get_by_user/' + query_id;
        else
            api_url = base_api + '/api/members/get_by_org/' + query_id;
    */

    // Storing response
    const response = await fetch(api_url);
   
    // Storing data in form of JSON
    var data = await response.json();

    //console.log(data);
    return data;
}

function arraysEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;

  // If you don't care about the order of the elements inside
  // the array, you should sort both arrays here.
  // Please note that calling sort on an array will modify that array.
  // you might want to clone your array first.

  for (var i = 0; i < a.length; ++i) {
    if (JSON.stringify(a[i]) != JSON.stringify(b[i])) {
        return false;
    }
  }
  return true;
}

function setCenterZoom() {

    map.setCenter(bounds.getCenter()); //or use custom center
    map.fitBounds(bounds);

    if(map.getZoom() > 15){
        map.setZoom(15);
    }
}

function toggleMarkers(key) {
    let keyElement = document.getElementById(key);
    let keyElementText = keyElement.textContent;
    //let keyElementText = document.getElementById(key).textContent;

    if (marker_property[key].is_show) {
        marker_property[key].is_show = false;
        hideMarkers(key);
        keyElement.innerHTML = keyElementText.strike();
    }
    else {
        marker_property[key].is_show = true;
        showMarkers(key);
        keyElement.innerHTML = keyElementText;
    }
}

function resetMarkersData(data) {
    marker_property.is_new.data = [];
    marker_property.is_online.data = [];
    marker_property.is_offline.data = [];
    marker_property.is_problem.data = [];

    for (i = 0; i < data.length; i++) {  
        if (data[i]['is_new'])
            marker_property.is_new.data.push(data[i]);
        else
            if (data[i]['is_problem'])
                marker_property.is_problem.data.push(data[i]);
            else
                if (data[i]['is_online'])
                    marker_property.is_online.data.push(data[i]);
                else
                    marker_property.is_offline.data.push(data[i]);
    }
    data_prev = data;
}

function refreshMarkersAfterReset() {
    let total_sites = 0;

    for (let key in marker_property) {
        deleteMarkers(key);
        drawMarker(key);

        total_sites += marker_property[key].data.length;

        // Remove Elements
        let divRemove = document.getElementById(key);
        if (divRemove)
            divRemove.remove()

        // Create Legend
        if (marker_property[key].data.length > 0) {
            let div = document.createElement('div');
            div.innerHTML =  '<button id="' + key + '"' +
                ' style="background-color: white;"' + 
                ' onclick="toggleMarkers(\'' + key + '\');">' +
                marker_property[key].title + 
                ': ' + marker_property[key].data.length + '</button>';
            legend.appendChild(div);

            if (! marker_property[key].is_show) {
                let keyElement = document.getElementById(key);
                let keyElementText = keyElement.textContent;
                keyElement.innerHTML = keyElementText.strike();
            }
        }
    }

    let divTotalRemove = document.getElementById('total_sites');
    if (divTotalRemove)
        divTotalRemove.remove()

    let div = document.createElement('div');
    div.innerHTML =  '<button id="total_sites"' +
        ' style="background-color: white; margin-top: 5px;"' +
        ' onclick="showAllSites()">TOTAL: ' + 
        total_sites + '</button>';
    legend.appendChild(div);

}

function calculateMapCenter(data) {
    var latlngList = [];
    for (i = 0; i < data.length; i++) {  
        latlngList.push(new google.maps.LatLng(data[i]['lat'], data[i]['lng']));

        bounds = new google.maps.LatLngBounds();
        latlngList.forEach(function(n) {
            bounds.extend(n);
        });
    }
}

async function redrawMarkers() {
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    var data;
    var is_equal;

    is_equal = false;

    if (api_params.new_query) {
        data_new = await get_api(
            api_params.api_url, api_params.is_all, 
            api_params.is_no_org, api_params.query_id);

        is_equal = arraysEqual(data_prev, data_new);
    }

    //console.log('is_equal', is_equal);

    if (! is_equal) {

        //data_prev = data_new;
        //data = data_new;

        calculateMapCenter(data_new);
        /*
        var latlngList = [];
        for (i = 0; i < data.length; i++) {  
            latlngList.push(new google.maps.LatLng(data[i]['lat'], data[i]['lng']));

            bounds = new google.maps.LatLngBounds();
            latlngList.forEach(function(n) {
                bounds.extend(n);
            });
        }
        */

        if (! data_prev.length)
            setCenterZoom();

        //data_prev = data_new;

        resetMarkersData(data_new);
        refreshMarkersAfterReset();
        /*
        marker_property.is_new.data = [];
        marker_property.is_online.data = [];
        marker_property.is_offline.data = [];
        marker_property.is_problem.data = [];

        for (i = 0; i < data.length; i++) {  
            if (data[i]['is_new'])
                marker_property.is_new.data.push(data[i]);
            else
                if (data[i]['is_problem'])
                    marker_property.is_problem.data.push(data[i]);
                else
                    if (data[i]['is_online'])
                        marker_property.is_online.data.push(data[i]);
                    else
                        marker_property.is_offline.data.push(data[i]);
        }
        */

        //deleteMarkers();
        /*
        let total_sites = 0;

        for (let key in marker_property) {
            deleteMarkers(key);
            drawMarker(key);

            total_sites += marker_property[key].data.length;

            // Remove Elements
            let divRemove = document.getElementById(key);
            if (divRemove)
                divRemove.remove()

            // Create Legend
            if (marker_property[key].data.length > 0) {
                let div = document.createElement('div');
                div.innerHTML =  '<button id="' + key + '"' +
                    ' style="background-color: white;"' + 
                    ' onclick="toggleMarkers(\'' + key + '\');">' +
                    marker_property[key].title + 
                    ': ' + marker_property[key].data.length + '</button>';
                legend.appendChild(div);

                if (! marker_property[key].is_show) {
                    let keyElement = document.getElementById(key);
                    let keyElementText = keyElement.textContent;
                    keyElement.innerHTML = keyElementText.strike();
                }
            }
        }

        let divTotalRemove = document.getElementById('total_sites');
        if (divTotalRemove)
            divTotalRemove.remove()

        let div = document.createElement('div');
        div.innerHTML =  '<button id="total_sites"' +
            ' style="background-color: white; margin-top: 5px;"' +
            ' onclick="showAllSites()">TOTAL: ' + 
            total_sites + '</button>';
        legend.appendChild(div);
        */
    }
}

/******************
 * ShowAll Button
 ******************/
function createCenterControl(map) {
  const controlButton = document.createElement("button");

  // Set CSS for the control.
  controlButton.style.backgroundColor = "#fff";
  controlButton.style.border = "2px solid #fff";
  controlButton.style.borderRadius = "3px";
  controlButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
  controlButton.style.color = "rgb(25,25,25)";
  controlButton.style.cursor = "pointer";
  controlButton.style.fontFamily = "Roboto,Arial,sans-serif";
  controlButton.style.fontSize = "16px";
  controlButton.style.lineHeight = "38px";
  controlButton.style.margin = "8px 0 22px";
  controlButton.style.padding = "0 5px";
  controlButton.style.textAlign = "center";
  controlButton.textContent = "Center Map";
  controlButton.title = "Click to recenter the map";
  controlButton.type = "button";
  // Setup the click event listeners: simply set the map to Chicago.
  controlButton.addEventListener("click", () => {
    setCenterZoom();
  });
  return controlButton;
}

function showAllSites() {
    for (key in marker_property) {
        marker_property[key].is_show = true;
        if (marker_property[key].data.length>0) {
            let keyElement = document.getElementById(key);
            if (keyElement) {
                let keyElementText = keyElement.textContent;
                keyElement.innerHTML = keyElementText;
                showMarkers(key);
            }
        }
    }

    /*
    let keyElement = document.getElementById(key);
    let keyElementText = document.getElementById(key).textContent;
    keyElement.innerHTML = keyElementText;
    */
}


function searchSites(keyword_string) {
    var data;
    var data_search;

    if (keyword_string!='') {
        if (data_backup.length)
            data_prev = data_backup;
        else
            data_backup = data_prev;
        data_search = [];
        for (let counter=0; counter < data_prev.length; counter++) {
            data_string = JSON.stringify(data_prev[counter]).toLowerCase();
            if (data_string.includes(keyword_string.toLowerCase())) {
                data_search.push(data_prev[counter]);
            }
        } 

        data = data_search;
    }
    else {
        data_prev = data_backup;
        data = data_prev;
    }
    calculateMapCenter(data);
    setCenterZoom();
        
    resetMarkersData(data);
    refreshMarkersAfterReset();
}

/*************************
 * Search Input
 *************************/
function searchSitesControl(map) {
  const controlButton = document.createElement("input");

  // Set CSS for the control.
  controlButton.style.margin = "8px 3px 22px";
  //controlButton.style.padding = "0 0px";
  controlButton.style.borderRadius = "3px";
  controlButton.style.border = "0px solid #fff";
  controlButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
  controlButton.style.fontFamily = "Roboto,Arial,sans-serif";
  controlButton.style.fontSize = "16px";
  controlButton.style.lineHeight = "2em";
  controlButton.style.textAlign = "center";
  controlButton.placeholder = "search";
  /*
  controlButton.style.backgroundColor = "#fff";
  controlButton.style.border = "2px solid #fff";
  controlButton.style.borderRadius = "3px";
  controlButton.style.boxShadow = "0 2px 6px rgba(0,0,0,.3)";
  controlButton.style.color = "rgb(25,25,25)";
  controlButton.style.cursor = "pointer";
  controlButton.style.fontFamily = "Roboto,Arial,sans-serif";
  controlButton.style.fontSize = "16px";
  controlButton.style.lineHeight = "38px";
  controlButton.style.margin = "8px 3px 22px";
  controlButton.style.padding = "0 5px";
  controlButton.style.textAlign = "center";
  controlButton.textContent = "Toggle Cluster";
  controlButton.title = "Click to toggle clustering";
  */
  controlButton.type = "input";
  // Execute a function when the user presses a key on the keyboard
  controlButton.addEventListener("keypress", function(event) {
    // If the user presses the "Enter" key on the keyboard
    if (event.key === "Enter") {
        // Cancel the default action, if needed
        event.preventDefault();
        searchSites(controlButton.value);
    }
  });
  return controlButton;
}

async function initMap() {
    // Request needed libraries.
    const { Map, InfoWindow } = await google.maps.importLibrary("maps");
    //const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    map = new Map(document.getElementById("map"), {
      mapId: "MAP_VIEW",
      center: {lat: -1.233982000061532, lng: 116.83728437200422},
      zoom: 5,
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
        mapTypeIds: ["roadmap", "terrain"],
    },
    });

    // Create the DIV to hold the control.
    const centerControlDiv = document.createElement("div");
    // Create the control.
    const centerControl = createCenterControl(map);

    const searchSitesDiv = document.createElement("div");
    const searchSites = searchSitesControl(map);

    // Append the control to the DIV.
    centerControlDiv.appendChild(centerControl);
    map.controls[google.maps.ControlPosition.TOP_CENTER].push(centerControlDiv);

    searchSitesDiv.appendChild(searchSites);
    map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(searchSitesDiv);

    legend = document.getElementById("legend");
    map.controls[google.maps.ControlPosition.RIGHT_TOP].push(legend);

}
