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

/*
 * ---------------------------------------===========================================--------------------------------------
 * WARNING: This script is just adding some functionality specific to the stimulus visualization on top of what is defined 
 * in /static/js/vertice_pick/base_vertice_pick.js. As such in all the cases when this script is used, you must first 
 * include base_vertice_pick.js. In case you need to ADD FUNCTIONS here, either make sure you don't "overwrite" something
 * necessary from base_vertice_pick.js, or just prefix your functions. (e.g. STIM_PICK_${function_name}).
 * ---------------------------------------===========================================--------------------------------------
 */

/* globals gl, displayMessage */
var BUFFER_TIME_STEPS = 8;
var DATA_CHUNK_SIZE = null;
var TICK_STEP = 33; // 30Hz
var maxValue = 0;
var minValue = 0;
var drawTickInterval = null;
var AG_isStopped = false;
var sliderSel = false;
var minTime = 0;
var maxTime = 0;
var displayedStep = 0;
var totalTimeStep = 0;
var currentStimulusData = null;
var nextStimulusData = null;
var asyncLoadStarted = false;
var endReached = false;


/**
 * Start the movie mode visualization of the received data.
 */
function STIM_PICK_setVisualizedData(data) {

    BASE_PICK_isMovieMode = true;
    currentStimulusData = data['data'];
    minTime = data['time_min'];
    maxTime = data['time_max'];
    DATA_CHUNK_SIZE = data['chunk_size'];
    var colorValuesChanged = (maxValue != data['max']);
    maxValue = data['max'];
    minValue = data['min'];

    // If for some reason the draw timeout was not cleared, clear it now.
    if (drawTickInterval != null) {
        clearInterval(drawTickInterval);
    }
    endReached = false;
    // Reset the flags and set a new draw timeout.
    drawTickInterval = setInterval(tick, TICK_STEP);
    displayedStep = 0;
    totalTimeStep = minTime;

    BASE_PICK_initLegendInfo(maxValue, minValue);
    if (colorValuesChanged) {
        ColSch_initColorSchemeGUI(minValue, maxValue);
    }

    if (AG_isStopped){ // unpause movie
        pauseMovie();  // this should be called toggle ...
    }

    $(".slider-div").show();
    $(".action-run").hide();

    // todo: The initialisation of the time line is very similar to the one in virtualbrain.js. The globals are different and some update conditions.

    // The slider is disabled because seeking is buggy.
    // Seeking outside the current chunk should immediately load a new chunk and pause until the load has finished.
    // todo: create a movie module that supports seeking by extracting movie stuff from virtualbrain.js

    // Initialize slider for timeLine
    $("#slider").slider({
        min:minTime, max: maxTime, disabled: true,
        slide: function() {
            sliderSel = true;
            totalTimeStep = $("#slider").slider("option", "value");
            displayedStep = parseInt((totalTimeStep - minTime) % DATA_CHUNK_SIZE);
            $('#TimeNow').val(totalTimeStep);
        },
        stop: function(event, target) {
            sliderSel = false;
            totalTimeStep = target.value;
            displayedStep = parseInt((totalTimeStep - minTime) % DATA_CHUNK_SIZE);
            $('#TimeNow').val(totalTimeStep);
            //loadFromTimeStep(target.value);
        }
    });

    // init the go to time input.
    $('#TimeNow').click(function(){
        if (!AG_isStopped){
            pauseMovie();
        }
        $(this).select();
    }).change(function(ev){
        var val = parseFloat(ev.target.value);
        if (val == null || val < minTime || val > maxTime){
            val = 0;
            ev.target.value = 0;
        }
        $('#slider').slider('value', val);
        //loadFromTimeStep(val);
    });
}

/**
 * Stop the movie-mode visualization. Reset flags and steps, also remove the
 * tick - timeout and reset the color buffers.
 */
function STIM_PICK_stopDataVisualization() {

    if (noOfUnloadedBrainDisplayBuffers != 0) {
        displayMessage("The load operation for the surface data is not completed yet!", "infoMessage");
        return;
    }
    BASE_PICK_isMovieMode = false;
    document.getElementById('brainLegendDiv').innerHTML = '';
    displayedStep = 0;
    if (drawTickInterval != null) {
        clearInterval(drawTickInterval);
    }
    $(".slider-div").hide();
    $(".action-run").show();
    asyncLoadStarted = false;
    BASE_PICK_buffer_default_color();
    drawScene();
}

/**
 * Since the min-max interval can be quite large, just load it in chunks.
 */
function STIM_PICK_loadNextStimulusChunk() {

    var currentChunkIdx = parseInt((totalTimeStep - minTime) / DATA_CHUNK_SIZE);
    if ((currentChunkIdx + 1) * DATA_CHUNK_SIZE < (maxTime - minTime)) {
        // We haven't reached the final chunk so just load it normally.
        asyncLoadStarted = true;
        doAjaxCall({
            type:'GET',
            url:'/spatial/stimulus/surface/get_stimulus_chunk/' + (currentChunkIdx + 1),
            success:function (data) {
                nextStimulusData = $.parseJSON(data);
                asyncLoadStarted = false;
            },
            error: function() {
                displayMessage("Something went wrong in getting the next stimulus chunk!", "warningMessage")
            }
        });
    } else {
        // No more chunks to load. Set end of data flat and block the async load by setting
        // asyncLoadStarted to true so no more calls to loadNextStimulusChunk are done for this data.
        asyncLoadStarted = true;
        endReached = true;
    }
}

/** Update color buffers for the current movie
 todo: this is almost the same as virtualbrain.js:updateColors */
function updateColors(currentTimeInFrame){
    var currentActivity = currentStimulusData[currentTimeInFrame];
    // Compute the colors for this current step:
    for (var i=0; i < BASE_PICK_brainDisplayBuffers.length;i++) {
        var upperBorder = BASE_PICK_brainDisplayBuffers[i][0].numItems / 3;
        var offset_start = i * 40000;
        var currentActivitySlice = currentActivity.slice(offset_start, offset_start + upperBorder);
        var activity = new Float32Array(currentActivitySlice);

        gl.bindBuffer(gl.ARRAY_BUFFER, BASE_PICK_brainDisplayBuffers[i][3]);
        gl.bufferData(gl.ARRAY_BUFFER, activity, gl.STATIC_DRAW);
    }
}

/**
 * Function called every TICK_STEP milliseconds. This is only done in movie mode.
 */
function tick() {

    if (noOfUnloadedBrainDisplayBuffers != 0) {
        displayMessage("The load operation for the surface data is not completed yet!", "infoMessage");
        return;
    }
    if (sliderSel){
        return;
    }

    //If we reached maxTime, the movie ended
    var buttonRun = $('.action-run')[0];
    var buttonStop = $('.action-stop')[0];

    if (BASE_PICK_isMovieMode && totalTimeStep < maxTime) {
        // We are still in movie mode and didn't pass the end of the data.
        if (displayedStep >= currentStimulusData.length) {
            if (currentStimulusData.length > maxTime - minTime || endReached ) {
                //We had reached the end of the movie mode.
                STIM_PICK_stopDataVisualization();
                buttonRun.className = buttonRun.className.replace('action-idle', '');
                buttonStop.className = buttonStop.className + " action-idle";
            } else {
                //If the async load of the next data chunk is done, do the switch otherwise just wait
                if (nextStimulusData != null) {
                    currentStimulusData = nextStimulusData;
                    displayedStep = 0;
                    nextStimulusData = null;
                } else {
                    return;
                }
            }
        }

        updateColors(displayedStep);

        if (! AG_isStopped ) {
            // We are in movie mode so drawScene was called automatically. We don't
            // want to update the slices here to improve performance. Increse the timestep.
            displayedStep += 1;
            totalTimeStep += 1;
            if (currentStimulusData.length < (maxTime - minTime) &&    // todo : this condition has to change to support seeking
                displayedStep + BUFFER_TIME_STEPS >= currentStimulusData.length &&
                nextStimulusData == null && !asyncLoadStarted) {
                STIM_PICK_loadNextStimulusChunk();
            }
        }

        drawScene();

        // update Movie timeline
        if (!sliderSel && ! AG_isStopped) {
            document.getElementById("TimeNow").value = toSignificantDigits(totalTimeStep, 2);
            $("#slider").slider("option", "value", totalTimeStep);
        }
   } else {
       //We had reached the end of the movie mode.
       STIM_PICK_stopDataVisualization();
       buttonRun.className = buttonRun.className.replace('action-idle', '');
       buttonStop.className = buttonStop.className + " action-idle";
   }
}


function drawScene() {
    // Use function offered by base_vertice_pick.js to draw the brain:
    BASE_PICK_drawBrain();

    // Draw the legend for the stimulus now.
    if (BASE_PICK_isMovieMode) {
        mvPushMatrix();
        loadIdentity();
        drawBuffers(gl.TRIANGLES, [LEG_legendBuffers]);
        mvPopMatrix();
    }
}