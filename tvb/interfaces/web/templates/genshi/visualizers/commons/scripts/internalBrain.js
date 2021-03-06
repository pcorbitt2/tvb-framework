/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

function _VSI_bufferAtPoint(p, idx) {
    var result = HLPR_sphereBufferAtPoint(gl, p, 3, 12, 12);
    var bufferVertices= result[0];
    var bufferNormals = result[1];
    var bufferTriangles = result[2];
    var vertexRegionBuffer = VSI_createColorBufferForSphere(idx, bufferVertices.numItems * 3);
    return [bufferVertices, bufferNormals, bufferTriangles, vertexRegionBuffer];
}

/**
 * Method used for creating a color buffer for a cube (measure point).
 */
function VSI_createColorBufferForSphere(nodeIdx, nrOfVertices) {
    var regionMap = [];

    for (var i = 0; i < nrOfVertices; i++) {
        regionMap.push(nodeIdx);
    }

    var vertexRegionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexRegionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(regionMap), gl.STATIC_DRAW);
    return vertexRegionBuffer;
}


function _VSI_init_sphericalMeasurePoints(){
    for (var i = 0; i < NO_OF_MEASURE_POINTS; i++) {
        measurePointsBuffers[i] = _VSI_bufferAtPoint(measurePoints[i], i);
    }
}

function VSI_StartInternalSensorViewer(urlMeasurePoints,  noOfMeasurePoints, urlMeasurePointsLabels,
                                       shelfObject, minMeasure, maxMeasure, measure){
    _VS_static_entrypoint('', '[]', '', '', urlMeasurePoints, noOfMeasurePoints, '',
                         urlMeasurePointsLabels, '', shelfObject, null, false, false, true,
                         minMeasure, maxMeasure, measure);
    isInternalSensorView = true;
    displayMeasureNodes = true;

    _VSI_init_sphericalMeasurePoints();

}

function VSI_StartInternalActivityViewer(baseDatatypeURL, onePageSize, urlTimeList, urlVerticesList, urlLinesList,
                    urlTrianglesList, urlNormalsList, urlMeasurePoints, noOfMeasurePoints,
                    urlRegionMapList, minActivity, maxActivity,
                    oneToOneMapping, doubleView, shelfObject, urlMeasurePointsLabels, boundaryURL) {

    _VS_movie_entrypoint(baseDatatypeURL, onePageSize, urlTimeList, urlVerticesList, urlLinesList,
                    urlTrianglesList, urlNormalsList, urlMeasurePoints, noOfMeasurePoints,
                    urlRegionMapList, minActivity, maxActivity,
                    oneToOneMapping, doubleView, shelfObject, null, urlMeasurePointsLabels, boundaryURL);
    isInternalSensorView = true;
    displayMeasureNodes = true;
    isFaceToDisplay = true;

    _VSI_init_sphericalMeasurePoints();
}
