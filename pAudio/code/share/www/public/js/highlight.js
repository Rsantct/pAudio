/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pAudio', a PC based personal audio system.
*/

// main.STATE will be updated also here for functions below to work
var STATE = {}

// a setter for this STATE
export function set_STATE(value){
    STATE = value
}


export function clear_highlighteds(){
    document.getElementById('mainSelector').style.color     = "rgb(200,200,200)";
    document.getElementById('drcSelector').style.color      = "rgb(200,200,200)";
    document.getElementById('xoSelector').style.color       = "rgb(200,200,200)";
    document.getElementById('targetSelector').style.color   = "rgb(200,200,200)";
}


export function toneDefeatHighlight(){

    const btd = document.getElementById("tone_defeat");

    if (STATE.tone_defeat){
        btd.className = "btn-maroon";
        document.getElementById("bassInfo").style.color = "grey";
        document.getElementById("trebleInfo").style.color = "grey";
    }else{
        btd.className = "btn-dimm-gray";
        document.getElementById("bassInfo").style.color = "white";
        document.getElementById("trebleInfo").style.color = "white";
    }
}


export function buttonsToneBalanceHighlight(){

    const thin  = "2px solid rgb(100, 100, 100)";
    const thick = "3px solid rgb(160, 160, 160)";

    if ( STATE.bass < 0 ){
        document.getElementById("bass-").style.border = thick;
        document.getElementById("bass+").style.border = thin;
    }else if ( STATE.bass > 0 ){
        document.getElementById("bass-").style.border = thin;
        document.getElementById("bass+").style.border = thick;
    }else{
        document.getElementById("bass-").style.border = thin;
        document.getElementById("bass+").style.border = thin;
    }

    if ( STATE.treble < 0 ){
        document.getElementById("treb-").style.border = thick;
        document.getElementById("treb+").style.border = thin;
    }else if ( STATE.treble > 0 ){
        document.getElementById("treb-").style.border = thin;
        document.getElementById("treb+").style.border = thick;
    }else{
        document.getElementById("treb-").style.border = thin;
        document.getElementById("treb+").style.border = thin;
    }

    if ( STATE.balance < 0 ){
        document.getElementById("bal-").style.border = thick;
        document.getElementById("bal+").style.border = thin;
    }else if ( STATE.balance > 0 ){
        document.getElementById("bal-").style.border = thin;
        document.getElementById("bal+").style.border = thick;
    }else{
        document.getElementById("bal-").style.border = thin;
        document.getElementById("bal+").style.border = thin;
    }
}


export function buttonMuteHighlight(){

    const e_mute  = document.getElementById("buttonMute");
    const e_level = document.getElementById("levelInfo");

    if ( STATE.muted == true ) {
        e_mute .style.background = "rgb(185, 185, 185)";
        e_mute .style.color = "white";
        e_level.style.color = "rgb(150, 90, 90)";

    } else {
        e_mute .style.background = "rgb(100, 100, 100)";
        e_mute .style.color = "lightgray";
        e_level.style.color = "white";
    }
}


export function buttonMonoHighlight(){

    const e = document.getElementById("buttonMono");

    if ( STATE.midside == 'mid' ) {
        e.className = "btn-maroon";
        e.innerText = 'MO';

    } else if ( STATE.midside == 'side' ) {
        e.className = "btn-maroon";
        e.innerText = 'L-R';

    } else if ( STATE.solo == 'l' ) {
        e.className = "btn-maroon";
        e.innerText = 'L_';

    } else if ( STATE.solo == 'r' ) {
        e.className = "btn-maroon";
        e.innerText = '_R';

    } else if ( STATE.solo == 'off' ) {
        e.className = "btn-green";
        e.innerText = 'ST';
    }

    // 'polarity' setting will modify the button border
    if ( STATE.polarity != '++' ) {
        e.style.border = "3px solid rgb(200, 10, 10)";

    } else {
        e.style.border = "2px solid rgb(120, 120, 120)";
    }
}


export function buttonSoloHighlight(){

    const e = document.getElementById("buttonSolo");

    if ( STATE.solo == 'off' ) {
        e.style = "button";
        e.innerText = 'L|R';

    } else if ( STATE.solo == 'l' ) {
        e.style.background = "rgb(100, 0, 0)";
        e.innerText = 'L_';

    } else if ( STATE.solo == 'r' ) {
        e.style.background = "rgb(100, 0, 0)";
        e.innerText = '_R';
    }

}


export function buttonPolarityHighlight(){

    const e = document.getElementById("buttonPolarity");

    if ( STATE.polarity != '++' ) {
        e.style.background = "rgb(100, 0, 0)";

    } else {
        e.style = "button";
    }

    e.innerText = STATE.polarity;
}


export function buttonLoudHighlight(){

    const e = document.getElementById("buttonLoud");

    if ( STATE.equal_loudness == true ) {
        e.style.background = "rgb(0, 90, 0)";
        e.style.color = "white";
    } else {
        e.style.background = "rgb(100, 100, 100)";
        e.style.color = "rgb(150, 150, 150)";
    }
}


export function buttonAODHighlight(){

    const e = document.getElementById("buttAOD");

    if ( STATE.extra_delay === 0 ) {
        e.className = "btn-dimm-gray";

    } else {
        e.className = "btn-maroon";
        e.style.display = 'inline-table';
    }
}


export function buttonSubsonicHighlight(){

    const e = document.getElementById("subsonic");

    if ( STATE.subsonic == 'off' ) {
        e.className = "btn-dimm-gray";
        e.innerText = 'SUBS\n-';

    } else if ( STATE.subsonic == 'mp' ) {
        e.className = "btn-maroon";
        e.innerText = 'SUBS\nmp';

    } else if ( STATE.subsonic == 'lp' ) {
        e.className = "btn-red";
        e.innerText = 'SUBS\nlp';
    }
}


export function levelInfoHighlight() {

    const e = document.getElementById("levelInfo");

    // curently only indicates if the subsonic filter is activated
    if (STATE.subsonic != 'off' ){
        e.style.borderWidth = "thick";
        e.style.borderColor = "DarkRed";
    }else{
        e.style.borderWidth = "thin";
        e.style.borderColor = "white";
   }
}


export function buttonCompressorHighlight(){

    const e = document.getElementById("bt_compressor");

    if ( STATE.compressor === 'off' ) {
        e.innerHTML = 'comp.<br>OFF';
        e.className = "btn-dimm-gray";

    } else {
        e.innerHTML = 'COMP.<br>' + STATE.compressor;
        e.className = "btn-maroon";
        e.style.display = 'inline-block';
    }
}


export function buttonSwapLRHighlight(){

    const e = document.getElementById("bt_swap_lr");

    if ( STATE.lr_swapped == true ) {
        e.innerHTML = "R L";
        e.className = "btn-dimm-gray";
        e.style.display = 'inline-block';

    } else {
        e.innerHTML = "L R";
        e.className = "btn-red";
    }
}


export function clear_macro_buttons_highlight(){

    const macro_buttons = document.querySelectorAll('.macro_button_highlighted');

    macro_buttons.forEach(b => {
        b.className = 'macro_button';
    });
}


export function highlight_macro_button(id){
    try{
        document.getElementById(id).className = 'macro_button_highlighted';
    }catch(e){
        console.log('error highlighting id:' + id, e.message)
    }
}

