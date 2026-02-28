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


export function buttonsToneBalanceHighlight(){
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


export function buttonMuteHighlight(){
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


export function buttonMonoHighlight(){
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


export function buttonSoloHighlight(){

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


export function buttonPolarityHighlight(){

    if ( STATE.polarity != '++' ) {
        document.getElementById("buttonPolarity").style.background = "rgb(100, 0, 0)";

    } else {
        document.getElementById("buttonPolarity").style = "button";
    }

    document.getElementById("buttonPolarity").innerText = STATE.polarity;
}


export function buttonLoudHighlight(){
    if ( STATE.equal_loudness == true ) {
        document.getElementById("buttonLoud").style.background = "rgb(0, 90, 0)";
        document.getElementById("buttonLoud").style.color = "white";
    } else {
        document.getElementById("buttonLoud").style.background = "rgb(100, 100, 100)";
        document.getElementById("buttonLoud").style.color = "rgb(150, 150, 150)";
    }
}


export function buttonAODHighlight(){
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


export function buttonSubsonicHighlight(){
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


export function levelInfoHighlight() {
    // currently only indicates subsonic filter activated
    if (STATE.subsonic != 'off' ){
        document.getElementById("levelInfo").style.borderWidth = "thick";
        document.getElementById("levelInfo").style.borderColor = "DarkRed";
    }else{
        document.getElementById("levelInfo").style.borderWidth = "thin";
        document.getElementById("levelInfo").style.borderColor = "white";
   }
}


export function buttonCompressorHighlight(){
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

