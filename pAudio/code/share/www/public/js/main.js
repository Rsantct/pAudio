import * as mc from "./miscel.js";

const AUTO_UPDATE_INTERVAL = 1000;      // Auto-update interval millisec

const HELP_EN = `
The volume MUST be controlled here.

[LC] Loudness Contour compensation allows a tonal balanced low volume listenting experience.

[0.0] dB means the normal "loud SPL" for your listening position, say around 75~80 dBSPL.

CHECK that your DAC and AMPLIFIER are running at "full volume" to reach your target "loud SPL".

If your music program is loud (most CDs are), use the LU_offset slider to compensate.

LU_monitor indicates approximately how much excess volume your music program has.

Some LU_offset settings:

- 0 dB: very rare recordings. The BIS Records label is a good reference.
- 6 dB: a good mastered CD
- 9 dB: most CD even in classical
- 12 dB: most pop music CD
- 15 dB: ultra compressed music, usually in pop
`

const HELP_CAT = `
El volum HA DE ser controlat aquí.

[LC] 'Loudness Contour'. La compensació de contorn de sonoritat permet una experiència d'escolta de baix volum amb un equilibri tonal.

[0.0] dB significa el "SPL fort" normal per a la vostra posició d'escolta, per exemple, al voltant de 75~80 dBSPL.

COMPROVEU que el vostre DAC i AMPLIFICADOR funcionin a "volum complet" per assolir el vostre "SPL fort" objectiu.

Si el vostre programa de música és alt (la majoria de CD ho són), utilitzeu el control lliscant LU_offset per compensar.

LU_monitor indica aproximadament quant volum d'excés té el vostre programa de música.

Alguns paràmetres de LU_offset:

- 0 dB: enregistraments molt poc freqüents. El segell BIS Records és una bona referència.
- 6 dB: un bon CD masteritzat
- 9 dB: la majoria de CD, fins i tot en música clàssica
- 12 dB: la majoria de CD de música pop
- 15 dB: música ultracomprimida, normalment en música pop
`

const HELP_SP = `
El volumen DEBE controlarse aquí.

La compensación del contorno de sonoridad

[LC] 'Loudness Contour' permite una experiencia auditiva a bajo volumen con equilibrio tonal.

[0.0] dB significa el "SPL alto" normal para su posición de escucha, aproximadamente entre 75 y 80 dB SPL.

COMPRUEBE que su DAC y amplificador funcionen a "máximo volumen" para alcanzar el "SPL alto" objetivo.

Si su programa de música tiene un volumen alto (la mayoría de los CD lo tienen), utilice el control deslizante LU_offset para compensar.

LU_monitor indica aproximadamente el exceso de volumen de su programa de música.

Algunos ajustes de LU_offset:

- 0 dB: grabaciones muy poco frecuentes. El sello BIS Records es una buena referencia.
- 6 dB: un CD masterizado de calidad
- 9 dB: la mayoría de los CD, incluso de música clásica
- 12 dB: la mayoría de los CD de música pop
- 15 dB: música ultracomprimida, generalmente de música pop
`



//////// GLOBAL VARIABLES ////////
var STATE               = {};       // The preamp-convolver state

var player_info         = {};

var aux_info            = { 'onoff': '',
                            'loudness_monitor': {'LU_I': 0, 'LU_M': 0, 'scope': 'track' },
                            'last_macro': '',
                            'warning': ''
};

var web_config          = { 'main_selector':      'sources',
                            'hide_LU':            false,
                            'show_graphs':        false,
                            'user_macros':        []
};

var drc_sets            = [];

var mFnames             = [];

var macro_button_list   = [];

var metablank           = {         // A player's metadata blank dict
                            'player':       '',
                            'time_pos':     '',
                            'time_tot':     '',
                            'bitrate':      '',
                            'format':       '',
                            'file':         '',
                            'artist':       '',
                            'album':        '',
                            'title':        '',
                            'track_num':    '',
                            'tracks_tot':   ''
};


var server_available    = false;
var show_advanced       = false;    // defaults for display advanced controls
var hide_graphs         = true;     // defaults for displaying graphs

var last_eq_params      = {};       // To evaluate if eq curve changed
var last_drc            = '';       // To evaluate if drc changed
var last_disc           = '';       // Helps on refreshing cd tracks list
var last_source         = '';       // Helps on refreshing sources playlits
var last_loudspeaker    = '';       // Will detect if audio processes has beeen
                                    // restarted with new loudspeaker configuration.
var last_delay          = 0;        // A helper for the delay toggle button


var hold_selected_track = 0;        // A counter to keep the selected cd track during updates
var main_cside_msg      = '';       // The message displayed on page header
var hold_cside_msg      = 0;        // A counter to keep main_cside_msg during updates


//////// PAGE MANAGEMENT ////////

function fill_in_page_statics(){

    function fill_in_main_selector(){

        async function fill_in_main_as_sources() {
            // MAIN SELECTOR manages sources:

            // getting sources names
            try{
                var sources = await mc.send_cmd( 'get_sources' );
            }catch(e){
                console.log( e.name, e.message );
                return;
            }

            // clearing selector options
            select_clear_options("mainSelector");
            // Filling in options in a selector
            // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
            var mySel = document.getElementById("mainSelector");
            for ( const i in sources) {
                var option = document.createElement("option");
                option.text = sources[i];
                mySel.add(option);
            }
            // And adds the source 'none' as expected in core.Preamp
            // so that all sources will be disconnected.
            var option = document.createElement("option");
            option.text = 'none';
            mySel.add(option);
        }


        function fill_in_main_as_macros() {
            // MAIN SELECTOR manages macros:

            // clearing selector options
            select_clear_options("mainSelector");

            // Filling in options in a selector
            // https://www.w3schools.com/jsref/dom_obj_select.asp
            var mySel = document.getElementById("mainSelector");
            for ( const i in mFnames) {
                var mFname = mFnames[i];
                var mName  = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
                var option = document.createElement("option");
                option.text = mName;
                mySel.add(option);
            }
        }


        // standard: main selector as SOURCE manager
        if ( web_config.main_selector == 'sources' ){
            document.getElementById("mainSelector").title = 'Source Selector';
            document.getElementById("macro_buttons").style.display = 'inline-table';
            fill_in_main_as_sources();

        // alternative: main selector as MACROS manager
        }else{
            document.getElementById("mainSelector").title = 'Macros Launcher';
            document.getElementById("macro_buttons").style.display = 'none';
            fill_in_main_as_macros();
        }
    }

    async function fill_in_xo_selector() {
        try{
            var xo_sets = await mc.send_cmd( 'get_xo_sets' ) ;
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        select_clear_options("xoSelector");
        const mySel = document.getElementById("xoSelector");
        for ( const i in xo_sets ) {
            var option = document.createElement("option");
            option.text = xo_sets[i];
            mySel.add(option);
        }
    }

    function fill_in_drc_selector() {
        select_clear_options("drcSelector");
        const mySel = document.getElementById("drcSelector");
        for ( const i in drc_sets ) {
            var option = document.createElement("option");
            option.text = drc_sets[i];
            mySel.add(option);
        }
    }

    async function fill_in_target_selector() {
        try{
            var target_files = await mc.send_cmd( 'get_target_sets' );
        }catch(e){
            console.log( e.name, e.message );
            return;
        }
        select_clear_options("targetSelector");
        const mySel = document.getElementById("targetSelector");
        for ( const i in target_files ) {
            var option = document.createElement("option");
            option.text = target_files[i];
            mySel.add(option);
        }
    }

    function fill_in_LUscope_selector() {
        select_clear_options("LUscopeSelector");
        const mySel = document.getElementById("LUscopeSelector");
        const scopes = ['source', 'album', 'track'];
        for ( const i in scopes ) {
            var option = document.createElement("option");
            option.text = scopes[i];
            mySel.add(option);
        }
    }


    manage_main_cside( ':: pAudio :: ' + STATE.loudspeaker );


    // updates level cell info with ref_SPL
    document.getElementById("levelInfo").title = 'Target volume ref@' +
                                                 STATE.loudspeaker_ref_SPL + 'dBSPL';

    fill_in_main_selector();
    ////
    fill_in_target_selector();
    ////
    fill_in_xo_selector();
    ////
    fill_in_drc_selector();
    ////
    fill_in_LUscope_selector();

}


function manage_main_cside( msg = '' ){

    function CamillaDSP_is_ready() {

        const c = aux_info.CamillaDSP_state;

        if ( ! c ) {
            return false
        }

        if ( c.includes('NOT') || c.includes('INACTIVE') ) {
            return false

        }else{
            return true
        }
    }


    if ( ! msg ){
        msg = main_cside_msg;
    }

    // Server warnings overrides any message
    if ( aux_info.warning !== '') {
        msg = aux_info.warning;

    } else if (STATE.convolver_runs==false) {
        msg = '( sleeping )';

    } else if( ! CamillaDSP_is_ready() ) {
        msg = 'DSP unloaded, needs restart';
        document.getElementById("but_restart").style.display = "inline-block";
        document.getElementById("but_help").style.display = "none";

    } else {

        if (hold_cside_msg > 0){
            hold_cside_msg -= 1;

        } else {

            document.getElementById("but_restart").style.display = "none";
            document.getElementById("but_help").style.display = "inline-block";

            if (STATE.loudspeaker){
                if (STATE.drc_set == 'none'){
                    msg = STATE.loudspeaker;

                } else {
                    msg = STATE.loudspeaker + ' (' + STATE.drc_set + ')';
                }
            }
        }
    }

    document.getElementById("main_cside").innerText = msg;
}


async function init(){

    function download_drc_graphs(){
        if (web_config.show_graphs==false){
            return;
        }
        // geat all drc_xxxx.png at once at start, so them will remain in cache.
        for (const i in drc_sets){
            document.getElementById("drc_img").src =  'images/'
                                                    + STATE.loudspeaker
                                                    + '/drc_' + drc_sets[i]
                                                    + '.png';


        }
        document.getElementById("drc_img").src =  'images/'
                                                + STATE.loudspeaker
                                                + '/drc_none.png';
    }


    async function get_web_config(){
        try{
            web_config = await mc.send_cmd('ctrl get_web_config');
            mFnames = web_config.user_macros;
        }catch(e){
            console.log('response error to \'ctrl get_web_config\'', e.message);
        }

        if (web_config.show_graphs==false){
            document.getElementById("button_toggleEQgraphs").style.display = "none";
        }

        if ( web_config["onoff"].includes('amp') ){
            document.getElementById("OnOffButton").title = "Amplifier ON/OFF";
        }else if ( web_config["onoff"].includes('udio') ){
            document.getElementById("OnOffButton").title = "pAudio ON/OFF";
        }

    }


    function show_hide_LU_frame(){
        if ( web_config.hide_LU == true ){
            document.getElementById("LU_offset").style.display = 'none';
            document.getElementById("LU_monitor").style.display = 'none';
        }else{
            document.getElementById("LU_offset").style.display = 'block';
            document.getElementById("LU_monitor").style.display = 'block';
        }
    }


    function fill_in_macro_buttons() {

        // If empty macros list, do nothing
        if ( mFnames.length == 0 ){
            console.log( '(i) empty macros array')
            document.getElementById( "macro_buttons").style.display = 'none';
            return
        }

        // If any macro found, lets show the corresponding button
        document.getElementById( "macros_toggle_button").style.display = 'inline';


        // Expands number of buttons to a multiple of 3 (arrange of Nx3 buttons)
        // (i) mFnames is supposed to be properly sorted.
        var bTotal = parseInt(mFnames[mFnames.length - 1].split('_')[0])
        bTotal = 3 * ( Math.floor( (bTotal - 1) / 3) + 1 )

        var mtable = document.getElementById("macro_buttons");
        var row  = mtable.insertRow(-1); // at index -1

        // Iterate over button available cells
        for (let bPos = 1; bPos <= bTotal; bPos++) {

            // Iterate over macro filenames
            let found = false;
            for ( const i in mFnames ){
                // Macro file names: 'N_macro_name' where N is the button position
                var mFname = mFnames[i];
                var mPos  = mFname.split('_')[0];
                var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
                if ( mPos == bPos ){
                    found = true;
                    break;
                }
            }

            // Insert a cell
            var cell = row.insertCell(-1); // at index -1
            cell.className = 'macro_cell';

            // Create a button Element
            var btn = document.createElement('button');
            btn.type = "button";
            btn.className = "macro_button";
            macro_button_list.push(mName);
            if ( found == true ){
                btn.id = mName;
                btn.innerHTML = mName;
                // This doesn't work: always pass mFname incorrectly to run_macro()
                //btn.onclick=function(){run_macro(mFname)}
                // As a workaround lets set the onclick attribute:
                btn.setAttribute( "onclick",
                                  "oc_run_macro(\'" + mFname + "\')" );
            }else{
                btn.innerHTML = '-';
            }

            // Put the button inside the cell
            cell.appendChild(btn);

            // Arrange 3 buttons per row
            if ( bPos % 3 == 0 ) {
                row  = mtable.insertRow(-1); // at index -1
            }
        }
    }


    console.log('Preparing page');

    await get_web_config();

    get_drc_sets();

    await update_STATE();

    download_drc_graphs();

    manage_main_cside();

    fill_in_macro_buttons();

    //fill_in_playlists_selector();

    show_hide_LU_frame();

    // SCHEDULES THE PAGE_UPDATE (only runtime variable items)
    console.log('Looping to page_update ...');
    setInterval( page_update, AUTO_UPDATE_INTERVAL );
}


function page_update() {

    async function player_get(){
        try{
            const tmp = await mc.send_cmd('player get_all_info');
            if (tmp != "null"){
                player_info = tmp;
            }else{
                main_cside_msg = ':: pAudio :: players OFFLINE';
                return;
            }
        }catch(e){
            console.log( 'response error to player get_all_info', e.message );
            return;
        }
    }


    function player_refresh(){

        function player_random_mode_update(mode){
            if        ( mode=='on' ) {
                document.getElementById("random_toggle_button").style.background  = "rgb(185, 185, 185)";
                document.getElementById("random_toggle_button").style.color       = "white";

            } else {
                document.getElementById("random_toggle_button").style.background  = "rgb(100, 100, 100)";
                document.getElementById("random_toggle_button").style.color       = "lightgray";
            }
        }


        function player_controls_update(playerState) {

            if ( ! playerState ){
                return
            }

            if        ( playerState.includes('stop') ) {
                document.getElementById("buttonStop").style.background  = "rgb(185, 185, 185)";
                document.getElementById("buttonStop").style.color       = "white";
                document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
                document.getElementById("buttonPause").style.color      = "lightgray";
                document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
                document.getElementById("buttonPlay").style.color       = "lightgray";

            } else if ( playerState.includes('pause') ){
                document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
                document.getElementById("buttonStop").style.color       = "lightgray";
                document.getElementById("buttonPause").style.background = "rgb(185, 185, 185)";
                document.getElementById("buttonPause").style.color      = "white";
                document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
                document.getElementById("buttonPlay").style.color       = "lightgray";

            } else if ( playerState.includes('play') ) {
                document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
                document.getElementById("buttonStop").style.color       = "lightgray";
                document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
                document.getElementById("buttonPause").style.color      = "lightgray";
                document.getElementById("buttonPlay").style.background  = "rgb(185, 185, 185)";
                document.getElementById("buttonPlay").style.color       = "white";
            }
        }


        function player_metadata_update(d) {

            if ( !d ){
                return
            }

            if ( d['artist'] == ''  && d['album'] == '' && d['title'] == '' ){
                d = metablank;
            }

            if (d['format']) {
                document.getElementById("format").innerText = d['format'];
            } else {
                document.getElementById("format").innerText = "-:-:2"
            }

            if (d['file']) {
                document.getElementById("file").innerText = d['file'];
            } else {
                document.getElementById("file").innerText = "-"
            }

            if (d['track_uri']) {
                document.getElementById("file").innerText = d['track_uri'];
            } else {
                document.getElementById("file").innerText = "-"
            }

            if (d['bitrate']) {
                document.getElementById("bitrate").innerText = d['bitrate'] + "\nkbps";
            } else {
                document.getElementById("bitrate").innerText = "-\nkbps"
            }

            if (d['artist']) {
                document.getElementById("artist").innerText  = d['artist'];
            } else {
                document.getElementById("artist").innerText = "-"
            }

            if (d['track_num']) {
                document.getElementById("track_info").innerText   = d['track_num'];
            } else {
                document.getElementById("track_info").innerText = "-"
            }

            if (d['tracks_tot']) {
                document.getElementById("track_info").innerText += ('\n' + d['tracks_tot']);
            } else {
                document.getElementById("track_info").innerText += "\n-"
            }

            let tpos = d['time_pos'];
            let ttot = d['time_tot'];
            if ( ! tpos ){
                tpos = '-'
            }
            if ( ! ttot ){
                ttot = '-'
            }
            document.getElementById("time").innerText    = tpos + "\n" + ttot;

            if (d['album']) {
                document.getElementById("album").innerText   = d['album'];
            } else {
                document.getElementById("album").innerText = "-"
            }

            if (d['title']) {
                document.getElementById("title").innerText   = d['title'];
            } else {
                document.getElementById("title").innerText = "-"
            }

        }


        async function fill_in_track_selector() {
            // getting tracks
            try{
                var tracks = await mc.send_cmd( 'player list_playlist' );
            }catch(e){
                console.log( e.name, e.message );
                return;
            }
            // clearing selector options
            select_clear_options("track_selector");
            // Filling in options in a selector
            // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
            var mySel = document.getElementById("track_selector");
            var option = document.createElement("option");
            option.text = '--';
            mySel.add(option);
            for ( const i in tracks) {
                var option = document.createElement("option");
                option.text = tracks[i];
                mySel.add(option);
            }
            mySel.add(option);
        }


        player_controls_update(     player_info.state       );
        player_metadata_update(     player_info.metadata    );
        player_random_mode_update(  player_info.random_mode );

        // Updates tracks list if disc has changed
        if (last_disc != player_info.discid) {
            fill_in_track_selector();
            last_disc = player_info.discid;
        }

        // Updates the playlist loader when source changed, keep hidden if empty.
        //if (last_source != STATE.source){
        //    const plists = fill_in_playlists_selector();
        //    if ( plists.length > 0 ) {
        //        document.getElementById( "playlist_selector").style.display = "inline";
        //    }else{
        //        document.getElementById( "playlist_selector").style.display = "none";
        //    }
        //    last_source = STATE.source;
        //}

        // Displays the track selector if source == 'cd'
        if ( STATE.source == "cd") {
            document.getElementById( "track_selector").style.display = "inline";
        }
        else {
            document.getElementById( "track_selector").style.display = "none";
        }

        // Clears the CD track selector when expired
        hold_selected_track -= 1;
        if (hold_selected_track == 0) {
            document.getElementById('track_selector').value = '--';
        }

        // Displays the [url] button if source == 'iradio' or 'istreams'
        if (STATE.source == "iradio" ||
            STATE.source == "istreams") {
            document.getElementById( "url_button").style.display = "inline";
        }
        else {
            document.getElementById( "url_button").style.display = "none";
        }
    }


    async function aux_info_refresh(){

        try{
            aux_info = await mc.send_cmd('ctrl aux_info');
        }catch(e){
            console.log('response error to \'ctrl aux_info\'', e.message);
            aux_info.onoff = '--';
            server_available = false;
        }

        if ( aux_info.loudspeaker ) {
            document.title = 'pAudio ' + aux_info.loudspeaker;
        }

        if ( aux_info.onoff == 'off' || aux_info.onoff == 'on' ) {
            document.getElementById("OnOffButton").innerText = aux_info.onoff.toUpperCase();
            document.getElementById("OnOffButton").style.display = 'block';

        }else{
            document.getElementById("OnOffButton").style.display = 'none';
        }

        if ( ! aux_info.last_macro ){
            clear_macro_buttons_highlight();

        }else{
            const x = aux_info.last_macro;
            const mName = x.slice(x.indexOf('_') + 1, x.length);
            clear_macro_buttons_highlight();
            highlight_macro_button(mName)
        }
    }


    function LU_refresh(){
        // Updates the LU offset slider
        document.getElementById("LU_slider").value           = (15 - STATE.lu_offset);
        document.getElementById("LU_offset_value").innerText =
                                            'LU offset: ' + -1 * STATE.lu_offset;
        // Updates the Integrated LU monitor
        const LU_I  = aux_info.loudness_monitor.LU_I
        let scope   = aux_info.loudness_monitor.scope
        // Preferred displaying 'track' instead of 'title'
        if ( scope == 'title' ) {
            scope = 'track';
        }
        document.getElementById("LU_meter").value           = -LU_I;
        document.getElementById("LUscopeSelector").value    = scope;
        if (LU_I <= 0){
          document.getElementById("LU_meter_value").innerHTML ='LU monit: ' + LU_I;
        }else{
          document.getElementById("LU_meter_value").innerHTML ='LU monit: +' + LU_I;
        }
    }


    function graphs_update(){

        function eq_changed(){
            // evaluates if the set of params that determines an eq curve contour has changed
            let result = false;
            const eq_params = { 'level':    STATE.level,    'eq_loud':  STATE.equal_loudness,
                                'bass':     STATE.bass,     'treb':     STATE.treble,
                                'target':   STATE.target,   'tone_defeat': STATE.tone_defeat
                            };
            if ( JSON.stringify(eq_params) !== JSON.stringify(last_eq_params) ) {
                //console.log('eq changed');
                last_eq_params = eq_params;
                result = true;
            }else{
                result = false;
            }
            return result
        }


        function drc_changed(){
            let result = false;
            if ( STATE.drc_set !== last_drc ) {
                //console.log('drc changed');
                last_drc = STATE.drc_set;
                result = true;
            }else{
                result = false;
            }
            return result
        }


        if ( ! hide_graphs ) {
        // The temporary 'new_eq_graph' flag helps on slow machines because the new PNG graph
        // can take a while after the 'done' is received when issuing some audio command.
            if (eq_changed() == true || aux_info.new_eq_graph == true) {
                // A trick to avoid using the cached image by adding an offset timestamp
                // inside the  http.GET image source request
                document.getElementById("eq_img").src = 'images/eq.png?'
                                                          + Math.floor(Date.now());
            }
            if (drc_changed() == true) {
                // Here we can use cached images because drc graphs does not change
                document.getElementById("drc_img").src =  'images/'
                                                        + STATE.loudspeaker
                                                        + '/drc_' + STATE.drc_set
                                                        + '.png';
            }
        }
    }


    function state_refresh(){

        if ( Object.keys(STATE).length <= 5 ){
            return
        }

        // Updates level, balance, tone and delay info
        document.getElementById("levelInfo").innerHTML  = STATE.level.toFixed(1);
        document.getElementById("balInfo").innerHTML    = 'BAL: '  + STATE.balance;
        document.getElementById("bassInfo").innerText   = 'BASS: ' + STATE.bass;
        document.getElementById("trebleInfo").innerText = 'TREB: ' + STATE.treble;
        document.getElementById("buttAOD").innerText = STATE.extra_delay + ' ms';

        // Delete level info if convolver off
        if (STATE.convolver_runs == false){
            document.getElementById("levelInfo").innerHTML  = '--';
        }

        // Updates current SOURCES, XO, DRC, and TARGET (PEQ is meant to be static)
        if ( web_config.main_selector == 'macros' ){
            const mName = aux_info.last_macro;
            document.getElementById("mainSelector").value =
                                mName.slice(mName.indexOf('_') + 1, mName.length);
        }else{
            document.getElementById("mainSelector").value = STATE.source;
        }
        document.getElementById("xoSelector").value     = STATE.xo_set;
        document.getElementById("drcSelector").value    = STATE.drc_set;
        document.getElementById("targetSelector").value = STATE.target;

        // Highlights activated buttons and related indicators accordingly
        buttonMuteHighlight()
        buttonMonoHighlight()
        buttonSoloHighlight()
        buttonPolarityHighlight()
        buttonLoudHighlight()
        buttonsToneBalanceHighlight()
        toneDefeatHighlight()
        buttonSubsonicHighlight()
        buttonAODHighlight()
        levelInfoHighlight()
        buttonCompressorHighlight()

        // Used by the delay toggle button
        if (STATE.extra_delay !== 0) {
            last_delay = STATE.extra_delay;
        }
    }


    function player_controls_clear() {
        document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonStop").style.color       = "lightgray";
        document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonPause").style.color      = "lightgray";
        document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
        document.getElementById("buttonPlay").style.color       = "lightgray";
    }


    function player_info_clear() {
        document.getElementById("bitrate").innerText = "-\nkbps"
        document.getElementById("artist").innerText = "-"
        document.getElementById("track_info").innerText = "-"
        document.getElementById("track_info").innerText += "\n-"
        document.getElementById("time").innerText = "-"
        document.getElementById("album").innerText = "-"
        document.getElementById("title").innerText = "-"
    }


    //// AUX STUFF
    aux_info_refresh();
    manage_main_cside();

    // PREAMP STUFF
    update_STATE();

    //  Cancel updating if not answer
    if ( Object.keys(STATE).length == 0 ){
        document.getElementById("levelInfo").innerHTML  = '--';
        main_cside_msg = ':: pAudio :: not connected';
        player_info_clear();
        player_controls_clear();
        return;
    }

    // Try retrieving the drc_sets
    if ( drc_sets.length == 0 ){
        console.log('Retrying get_drc_sets')
        get_drc_sets()
    }

    //  Refresh static stuff if loudspeaker's audio processes has changed
    if ( last_loudspeaker != STATE.loudspeaker ){
        fill_in_page_statics();
        last_loudspeaker = STATE.loudspeaker;
    }

    state_refresh();

    //// PLAYER STUFF
    player_get();
    player_refresh();
    //
    LU_refresh();
    //
    graphs_update();
}


//////// HANDLERS: AUDIO 'onchange' 'onmousedown' ////////

function oc_main_select(itemName){
    // (i) The main selector can have two flavors:
    //      - regular source selector management
    //      - alternative macros management

    // helper for macros manager behavior
    function find_macroName(x){
        var result = '';
        for ( const i in mFnames ){
            var mFname = mFnames[i];
            var mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);
            if ( x == mName ){
                result = mFname;
                break
            }
        }
        return result;
    }

    hold_cside_msg = 3;
    main_cside_msg = 'Please wait for "' + itemName + '"';

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout( () => { await mc.send_cmd('source ' + itemName); }, 200 );
    async function tmp(itemName){
        // regular behavior managing preamp sourcess
        if ( web_config.main_selector == 'sources' ){
            await mc.send_cmd('source ' + itemName);
        // alternative behavior managing macros
        }else{
            mName = find_macroName(itemName);
            await mc.send_cmd( 'ctrl run_macro ' + mName );
        }
    }
    setTimeout( tmp, 200, itemName );  // 'itemName' is given as argument for 'tmp'

    clear_macro_buttons_highlight();
    document.getElementById('mainSelector').style.color = "white";

}


async function oc_drc_select(drcName){
    await mc.send_cmd('set_drc ' + drcName);
    clear_highlighteds();
    document.getElementById('drcSelector').style.color = "white";
}


async function oc_xo_select(xoName){
    await mc.send_cmd('set_xo ' + xoName);
    clear_highlighteds();
    document.getElementById('xoSelector').style.color = "white";
}


async function oc_target_select(xoName){
    await mc.send_cmd('set_target ' + xoName);
    clear_highlighteds();
    document.getElementById('targetSelector').style.color = "white";
}


async function oc_LU_scope_select(scope){
    await mc.send_cmd('ctrl set_loudness_monitor_scope ' + scope);
    clear_highlighteds();
    document.getElementById('LUscopeSelector').style.color = "white";
}


async function omd_audio_change(param, value) {
    STATE[param] += value;
    if ( param == 'level') {
        document.getElementById( 'levelInfo'  ).innerHTML =
                                    STATE[param].toFixed(1);
    }
    else if( param == 'bass'){
        document.getElementById( 'bassInfo'   ).innerHTML =
                         'BASS: ' + STATE[param].toFixed(0);
    }
    else if( param == 'treble'){
        document.getElementById( 'trebleInfo' ).innerHTML =
                         'TREB: ' + STATE[param].toFixed(0);
    }
    else if( param == 'balance'){
        document.getElementById( 'balInfo'    ).innerHTML =
                         'BAL: '  + STATE[param].toFixed(0);
    }
    else{
        return;
    }
    await mc.send_cmd( param + ' ' + value + ' ' + 'add' );
}


async function omd_mute_toggle() {
    await mc.send_cmd( 'mute toggle' );
    STATE.muted = ! STATE.muted;
    buttonMuteHighlight();
}


async function omd_equal_loudness_toggle() {
    await mc.send_cmd( 'equal_loudness toggle' );
    STATE.equal_loudness = ! STATE.equal_loudness;
    buttonLoudHighlight();
}


async function omd_mono_toggle() {

    // normal: only stereo/mono (off/mid)
    if (!show_advanced){

        if (STATE.midside == "mid" || STATE.midside == "side"){
            STATE.midside = "off";
            await mc.send_cmd( 'midside off' );
        }else{
            STATE.midside = "mid";
            await mc.send_cmd( 'midside mid' );
        }

    // advanced-controls: rotate stereo/mono/L-R (off/mid/side)
    }else{

        if (STATE.midside == "off"){
            STATE.midside = "mid";
            await mc.send_cmd( 'midside mid' );
        }else if (STATE.midside == "mid"){
            STATE.midside = "side";
            await mc.send_cmd( 'midside side' );
        }else if (STATE.midside == "side"){
            STATE.midside = "off";
            await mc.send_cmd( 'midside off' );
        }
    }

    buttonMonoHighlight();
}


async function omd_solo_rotate() {

    if (STATE.solo == "off"){
        await mc.send_cmd( 'solo L' );
    }else if(STATE.solo == "l"){
        await mc.send_cmd( 'solo R' );
    }else if(STATE.solo == "r"){
        await mc.send_cmd( 'solo off' );
    }

    // Solo highlight falls on the Mono/Stereo Button
}


async function omd_polarity_rotate() {

    if (STATE.polarity == "++"){
        await mc.send_cmd( 'polarity +-' );

    }else if(STATE.polarity == "+-"){
        await mc.send_cmd( 'polarity -+' );

    }else if(STATE.polarity == "-+"){
        await mc.send_cmd( 'polarity --' );

    }else if(STATE.polarity == "--"){
        await mc.send_cmd( 'polarity ++' );

    }

    buttonPolarityHighlight();
}


async function omd_delay_toggle() {
    if (STATE.extra_delay !== 0) {
        await mc.send_cmd('preamp add_delay 0');
    }else{
        await mc.send_cmd('preamp add_delay ' + last_delay.toString());
    }
}


//////// HANDLERS: PLAYER 'onchange' 'onmousedown' 'onclick' ////////

async function omd_playerCtrl(action) {
    if (action == 'random_toggle') {
        await mc.send_cmd( 'player random_mode toggle' );
    } else {
        await mc.send_cmd( 'player ' + action );
    }
}


async function oc_load_playlist(plistname) {
    if (plistname == '-CLEAR-') {
        await mc.send_cmd( 'player clear_playlist ' );
    } else if (plistname != '--') {
        await mc.send_cmd( 'player clear_playlist ' );
        await mc.send_cmd( 'player load_playlist ' + plistname );
    }
}


async function omd_select_track_number_dialog() {
    var tracknum = prompt('Enter track number to play:');
    if ( true ) {
        await mc.send_cmd( 'player play_track ' + tracknum );
    }
}


async function oc_play_track_number(N) {
    await mc.send_cmd( 'player play_track ' + N );
    hold_selected_track = 10;
}


async function ck_play_url() {
    var url = prompt('Enter url to play:');
    if ( url.slice(0,5) == 'http:' || url.slice(0,6) == 'https:' ) {
        await mc.send_cmd( 'ctrl play_url ' + url );
    }
}


//////// HANDLERS: AUX 'onmousedown' 'onclick' 'oninput' ////////

function ck_help() {

    let lang = web_config["help_lang"]
    if (!lang){ lang = 'en' }

    let msg = HELP_EN;

    if ( lang.toLowerCase().includes('sp') ){
        msg = HELP_SP
    }
    if ( lang.toLowerCase().includes('cat') ){
        msg = HELP_CAT
    }

    window.alert(msg);
}


async function ck_paudio_restart() {

    // RESTART mode
    if (web_config["monkey_button"].includes('start')){

        if ( confirm('Are you sure to RESTART pAudio?') ){

            ans = await mc.send_cmd('ctrl restart_paudio restart');
            alert(ans);
            ck_display_advanced('off');
        }

        return;
    }

    // START / STOP mode (toggle)
    let msg = 'Are you sure to START pAudio?';
    let mode = 'start'

    const curr = await mc.send_cmd('ctrl restart_paudio state');

    if (curr == 'true') {
        msg = 'Are you sure to STOP pAudio?';
        mode = 'stop'
    }

    if ( ! confirm(msg) ){
        return
    }

    ans = await mc.send_cmd('ctrl restart_paudio ' + mode);

    alert(ans);

    ck_display_advanced('off');
}


async function omd_onoff(mode) {

    let msg = ('Are you sure to ' + mode.toUpperCase() + ' pAudio?');
    let cmd = 'ctrl restart_paudio'

    if ( web_config["onoff"].includes('amp') ){
                msg = 'Are you sure to ' + mode.toUpperCase() + ' the AMPLIFIER?'
        cmd = 'ctrl amp_switch'
    }

    const ays = window.confirm( msg );
    if (ays){
        const ans = await mc.send_cmd( cmd + ' ' + mode );
        if (ans){
            window.alert( ans );
        }
    }
}


async function oi_LU_slider_action(slider_value){
    await mc.send_cmd( 'lu_offset ' + (15 - parseInt(slider_value) ).toString() )
}


function highlight_macro_button(id){
    try{
        document.getElementById(id).className = 'macro_button_highlighted';
    }catch(e){
        console.log(e.message)
    }
}


async function oc_run_macro(mFname){

    await mc.send_cmd( 'ctrl run_macro ' + mFname );

    const mName = mFname.slice(mFname.indexOf('_') + 1, mFname.length);

    clear_macro_buttons_highlight();

    // (i) The arrow syntax '=>' fails on Safari iPad 1 (old version)
    // setTimeout(() => { highlight_macro_button(mName);}, 200);
    function tmp(mName){
        highlight_macro_button(mName);
    }
    setTimeout( tmp, 200, mName );  // 'mName' is given as argument for 'tmp'

    hold_cside_msg = 3;
    main_cside_msg = 'Please wait for "' + mName + '"' ;
}


function omd_macro_buttons_display_toggle() {
    var curMode = document.getElementById( "macro_buttons").style.display;
    if (curMode == 'none') {
        document.getElementById( "macro_buttons").style.display = 'inline-table'
        web_config.main_selector = 'sources';
    }
    else {
        document.getElementById( "macro_buttons").style.display = 'none'
        web_config.main_selector = 'macros';
    }
    fill_in_page_statics();
}


function ck_display_advanced(mode) {
    // (i) This also allows access to the RESTART button

    if ( mode == 'toggle' ){
        if ( show_advanced !== true ) {
            show_advanced = true;
        }
        else {
            show_advanced = false;
        }
    }
    else if ( mode == 'off' ){
        show_advanced = false;
    }
    else if ( mode == 'on' ){
        show_advanced = true;
    }

    if ( show_advanced == true ) {
        document.getElementById("format_file").style.display = "table-row";
        document.getElementById("div_advanced_controls").style.display = "block";
        document.getElementById("level_buttons13").style.display = "table-cell";
        document.getElementById("but_restart").style.display = "inline-block";
        document.getElementById("but_help").style.display = "none";
        document.getElementById("SoloInfo").style.display = "table-cell";
        document.getElementById("PolarityInfo").style.display = "table-cell";
        document.getElementById("buttAOD").style.display = "inline-block";
        document.getElementById("subsonic").style.display = "inline-block";
        document.getElementById("tone_defeat").style.display = "inline-block";
        document.getElementById("bt_compressor").style.display = "inline-block";
    }
    else {
        document.getElementById("format_file").style.display = "none";
        document.getElementById("div_advanced_controls").style.display = "none";
        document.getElementById("level_buttons13").style.display = "none";
        document.getElementById("but_restart").style.display = "none";
        document.getElementById("but_help").style.display = "inline-block";
        document.getElementById("SoloInfo").style.display = "none";
        document.getElementById("PolarityInfo").style.display = "none";
        if ( STATE.extra_delay === 0 ) {
            document.getElementById("buttAOD").style.display = "none";
        }
        document.getElementById("subsonic").style.display = "none";
        document.getElementById("tone_defeat").style.display = "none";
        document.getElementById("bt_compressor").style.display = "none";
    }
}


function omd_graphs_toggle() {
    if ( web_config.show_graphs == false ){
        return;
    }
    if ( hide_graphs == true ) {
        hide_graphs = false;
    }
    else {
        hide_graphs = true;
    }

    if ( hide_graphs == false ){
        if (drc_sets.length > 0){
            document.getElementById("drc_graph").style.display = 'block';
        }
        document.getElementById("eq_graph").style.display = 'block';
    }else{
        document.getElementById("drc_graph").style.display = 'none';
        document.getElementById("eq_graph").style.display = 'none';
    }
}



////////  MISCEL INTERNALS  ////////


async function get_drc_sets() {

    try {
        drc_sets = await mc.send_cmd( 'get_drc_sets' );
    }catch(e){
        console.log('(i) cannot get drc sets')
    }
}


async function update_STATE() {
    try{
        STATE = await mc.send_cmd('preamp state');
        server_available = true;
    }catch(e){
        server_available = false;
        main_cside_msg = ':: pAudio :: not connected';
    }
}


async function fill_in_playlists_selector() {

    // getting playlists
    var plists = [];
    try{
        plists = await mc.send_cmd( 'player get_playlists' );
    }catch(e){
        console.log( 'response error to \'get_playlists\'', e.message );
        return plists;
    }

    // clearing selector options
    select_clear_options("playlist_selector");

    // Filling in options in a selector
    // https://www.w3schools.com/jsref/dom_obx.length-1j_select.asp
    var mySel = document.getElementById("playlist_selector");
    var option = document.createElement("option");
    option.text = '--';
    mySel.add(option);
    for ( const i in plists) {
        var option = document.createElement("option");
        option.text = plists[i];
        mySel.add(option);
    }
    var option = document.createElement("option");
    option.text = '-CLEAR-';
    mySel.add(option);

    return plists
}


function select_clear_options(ElementId){
    // https://www.w3schools.com/jsref/dom_obj_select.asp
    var mySel = document.getElementById(ElementId);
    while (mySel.length > 0){
        mySel.remove( mySel.length-1 );
    }
}


function clear_highlighteds(){
    document.getElementById('mainSelector').style.color     = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}


function clear_macro_buttons_highlight(){
    for (let i = 0; i < macro_button_list.length; i++) {
        document.getElementById(macro_button_list[i]).className = 'macro_button';
    }
}


function allAreTrue(arr) {
  return arr.every(element => element === true);
}


//////// ELEMENTS HIGHLIGHT ////////

function toneDefeatHighlight(){
    if (STATE.tone_defeat){
        document.getElementById("tone_defeat").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("tone_defeat").style.background = "rgb(100, 0, 0)";
        document.getElementById("tone_defeat").style.color = "rgb(255, 200, 200)";
        document.getElementById("bassInfo").style.color = "grey";
        document.getElementById("trebleInfo").style.color = "grey";
    }else{
        document.getElementById("tone_defeat").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("tone_defeat").style.background = "rgb(100, 100, 100)";
        document.getElementById("tone_defeat").style.color = "rgb(180, 180, 180)";
        document.getElementById("bassInfo").style.color = "white";
        document.getElementById("trebleInfo").style.color = "white";
    }
}


function buttonsToneBalanceHighlight(){
    if ( STATE.bass < 0 ){
        document.getElementById("bass-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bass+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( STATE.bass > 0 ){
        document.getElementById("bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bass+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bass-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bass+").style.border = "2px solid rgb(100, 100, 100)";
    }
    if ( STATE.treble < 0 ){
        document.getElementById("treb-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("treb+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( STATE.treble > 0 ){
        document.getElementById("treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("treb+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("treb-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("treb+").style.border = "2px solid rgb(100, 100, 100)";
    }
    if ( STATE.balance < 0 ){
        document.getElementById("bal-").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bal+").style.border = "2px solid rgb(100, 100, 100)";
    }else if ( STATE.balance > 0 ){
        document.getElementById("bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bal+").style.border = "3px solid rgb(160, 160, 160)";
    }else{
        document.getElementById("bal-").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bal+").style.border = "2px solid rgb(100, 100, 100)";
    }
}


function buttonMuteHighlight(){
    if ( STATE.muted == true ) {
        document.getElementById("buttonMute").style.background = "rgb(185, 185, 185)";
        document.getElementById("buttonMute").style.color = "white";
        document.getElementById("buttonMute").style.fontWeight = "bolder";
        document.getElementById("levelInfo").style.color = "rgb(150, 90, 90)";
    } else {
        document.getElementById("buttonMute").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonMute").style.color = "lightgray";
        document.getElementById("buttonMute").style.fontWeight = "normal";
        document.getElementById("levelInfo").style.color = "white";
    }
}


function buttonMonoHighlight(){
    if ( STATE.midside == 'mid' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'MO';
    } else if ( STATE.midside == 'side' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttonMono").innerText = 'L-R';
    } else {
        document.getElementById("buttonMono").style = "button";
        document.getElementById("buttonMono").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonMono").innerText = 'ST';
    }

    // 'solo' setting will override displaying mono stereo
    if ( STATE.solo == 'l' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").innerText = 'L_';
    } else if ( STATE.solo == 'r' ) {
        document.getElementById("buttonMono").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonMono").innerText = '_R';
    }

    // 'polarity' setting will modify the button border
    if ( STATE.polarity != '++' ) {
        document.getElementById("buttonMono").style.border = "3px solid rgb(200, 10, 10)";
    } else {
        document.getElementById("buttonMono").style.border = "2px solid rgb(120, 120, 120)";
    }
}


function buttonSoloHighlight(){

    if ( STATE.solo == 'off' ) {
        document.getElementById("buttonSolo").style = "button";
        document.getElementById("buttonSolo").innerText = 'L|R';

    } else if ( STATE.solo == 'l' ) {
        document.getElementById("buttonSolo").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonSolo").innerText = 'L_';

    } else if ( STATE.solo == 'r' ) {
        document.getElementById("buttonSolo").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttonSolo").innerText = '_R';
    }

}


function buttonPolarityHighlight(){

    if ( STATE.polarity != '++' ) {
        document.getElementById("buttonPolarity").style.background = "rgb(100, 0, 0)";

    } else {
        document.getElementById("buttonPolarity").style = "button";
    }

    document.getElementById("buttonPolarity").innerText = STATE.polarity;
}


function buttonLoudHighlight(){
    if ( STATE.equal_loudness == true ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
    }
}


function buttonAODHighlight(){
    if ( STATE.extra_delay === 0 ) {
        document.getElementById("buttAOD").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("buttAOD").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttAOD").style.color = "rgb(180, 180, 180)";
    } else {
        document.getElementById("buttAOD").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("buttAOD").style.background = "rgb(100, 0, 0)";
        document.getElementById("buttAOD").style.color = "rgb(255, 200, 200)";
        document.getElementById("buttAOD").style.display = 'inline-table';
    }
}


function buttonSubsonicHighlight(){
    if ( STATE.subsonic == 'off' ) {
        document.getElementById("subsonic").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("subsonic").style.background = "rgb(100, 100, 100)";
        document.getElementById("subsonic").style.color = "rgb(180, 180, 180)";
        document.getElementById("subsonic").innerText = 'SUBS\n-';
    } else if ( STATE.subsonic == 'mp' ) {
        document.getElementById("subsonic").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("subsonic").style.background = "rgb(100, 0, 0)";
        document.getElementById("subsonic").style.color = "rgb(255, 200, 200)";
        document.getElementById("subsonic").innerText = 'SUBS\nmp';
    } else if ( STATE.subsonic == 'lp' ) {
        document.getElementById("subsonic").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("subsonic").style.background = "rgb(150, 0, 0)";
        document.getElementById("subsonic").style.color = "rgb(255, 200, 200)";
        document.getElementById("subsonic").innerText = 'SUBS\nlp';
    }
}


function levelInfoHighlight() {
    // currently only indicates subsonic filter activated
    if (STATE.subsonic != 'off' ){
        document.getElementById("levelInfo").style.borderWidth = "thick";
        document.getElementById("levelInfo").style.borderColor = "DarkRed";
    }else{
        document.getElementById("levelInfo").style.borderWidth = "thin";
        document.getElementById("levelInfo").style.borderColor = "white";
   }
}

function buttonCompressorHighlight(){
    if ( STATE.compressor === 'off' ) {
        document.getElementById("bt_compressor").innerHTML = 'comp.<br>OFF';
        document.getElementById("bt_compressor").style.border = "2px solid rgb(100, 100, 100)";
        document.getElementById("bt_compressor").style.background = "rgb(100, 100, 100)";
        document.getElementById("bt_compressor").style.color = "rgb(180, 180, 180)";
    } else {
        document.getElementById("bt_compressor").innerHTML = 'COMP.<br>' + STATE.compressor;
        document.getElementById("bt_compressor").style.border = "3px solid rgb(160, 160, 160)";
        document.getElementById("bt_compressor").style.background = "rgb(100, 0, 0)";
        document.getElementById("bt_compressor").style.color = "rgb(255, 200, 200)";
        document.getElementById("bt_compressor").style.display = 'inline-block';
    }
}


/**
 * Inicialización de eventos para pAudio
 */
document.addEventListener('DOMContentLoaded', () => {

    // --- Utilidad para asignar eventos de forma masiva ---
    const addListener = (id, event, fn) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener(event, fn);
    };

    // --- BOTONES CON CLICK ---
    addListener('but_restart', 'click', () => ck_paudio_restart());
    addListener('but_help', 'click', () => ck_help());
    addListener('advanced_switch', 'click', () => ck_display_advanced('toggle'));
    addListener('url_button', 'click', () => ck_play_url());

    // --- BOTONES CON MOUSEDOWN ---
    addListener('OnOffButton', 'mousedown', () => omd_onoff('toggle'));
    addListener('buttonLoud', 'mousedown', () => omd_equal_loudness_toggle());
    addListener('buttonSolo', 'mousedown', () => omd_solo_rotate());
    addListener('track_number_button', 'mousedown', () => omd_select_track_number_dialog());
    addListener('buttonMono', 'mousedown', () => omd_mono_toggle());
    addListener('buttonPolarity', 'mousedown', () => omd_polarity_rotate());

    // Preamp y filtros
    addListener('subsonic', 'mousedown', () => mc.send_cmd('preamp subsonic rotate'));
    addListener('buttonMute', 'mousedown', () => omd_mute_toggle());
    addListener('tone_defeat', 'mousedown', () => mc.send_cmd('preamp tone_defeat toggle'));
    addListener('buttAOD', 'mousedown', () => omd_delay_toggle());
    addListener('bt_compressor', 'mousedown', () => mc.send_cmd('preamp compressor rotate'));
    addListener('buttonLoudMonReset', 'mousedown', () => mc.send_cmd('ctrl reset_loudness_monitor'));

    // Cambios de Audio (Bass, Bal, Treb, Level)
    addListener('level_m1', 'mousedown', () => omd_audio_change('level', -1));
    addListener('level_p1', 'mousedown', () => omd_audio_change('level', 1));
    addListener('level_m3', 'mousedown', () => omd_audio_change('level', -3));
    addListener('level_p3', 'mousedown', () => omd_audio_change('level', 3));

    addListener('bass-', 'mousedown', () => omd_audio_change('bass', -1));
    addListener('bass+', 'mousedown', () => omd_audio_change('bass', 1));
    addListener('bal-', 'mousedown', () => omd_audio_change('balance', -1));
    addListener('bal+', 'mousedown', () => omd_audio_change('balance', 1));
    addListener('treb-', 'mousedown', () => omd_audio_change('treble', -1));
    addListener('treb+', 'mousedown', () => omd_audio_change('treble', 1));

    // Graficos y Player
    addListener('button_toggleEQgraphs', 'mousedown', () => omd_graphs_toggle());
    addListener('buttonPrevious', 'mousedown', () => omd_playerCtrl('previous'));
    addListener('buttonRew', 'mousedown', () => omd_playerCtrl('rew'));
    addListener('buttonFF', 'mousedown', () => omd_playerCtrl('ff'));
    addListener('buttonNext', 'mousedown', () => omd_playerCtrl('next'));
    addListener('random_toggle_button', 'mousedown', () => omd_playerCtrl('random_toggle'));
    addListener('buttonEject', 'mousedown', () => omd_playerCtrl('eject'));
    addListener('buttonStop', 'mousedown', () => omd_playerCtrl('stop'));
    addListener('buttonPause', 'mousedown', () => omd_playerCtrl('pause'));
    addListener('buttonPlay', 'mousedown', () => omd_playerCtrl('play'));
    addListener('macros_toggle_button', 'mousedown', () => omd_macro_buttons_display_toggle());

    // --- SELECTS (CHANGE) E INPUTS ---
    addListener('playlist_selector', 'change', (e) => oc_load_playlist(e.target.value));
    addListener('track_selector', 'change', (e) => oc_play_track_number(e.target.selectedIndex));
    addListener('mainSelector', 'change', (e) => oc_main_select(e.target.value));
    addListener('samplerateSelector', 'change', (e) => oc_restart_samplerate(e.target.value));
    addListener('LUscopeSelector', 'change', (e) => oc_LU_scope_select(e.target.value));
    addListener('targetSelector', 'change', (e) => oc_target_select(e.target.value));
    addListener('xoSelector', 'change', (e) => oc_xo_select(e.target.value));
    addListener('drcSelector', 'change', (e) => oc_drc_select(e.target.value));

    addListener('LU_slider', 'input', (e) => oi_LU_slider_action(e.target.value));
});


// INIT
if (document.readyState === 'complete') {
    init();
} else {
    window.addEventListener('load', init);
}
