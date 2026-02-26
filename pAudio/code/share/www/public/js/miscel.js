/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pAudio', a PC based personal audio system.
*/

export async function send_cmd(cmd, verbose=false) {
    // Cancel if it takes more than 4 seconds
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    try {
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) throw new Error('(send_cmd) backend error');

        const responseTxt = await response.text();

        try {
            // response as JSON Object
            return JSON.parse(responseTxt.replaceAll(': null', ': ""'));

        } catch {
            // response as plain text
            return responseTxt;
        }

    } catch (err) {

        // distinguishes between timeout and network error
        if (err.name === 'AbortError') {
            if (verbose) { console.log('(send_cmd) server timeout:', err.message) }
            return '(send_cmd) server timeout';
        }

        if (verbose) { console.log('(send_cmd) network error:', err.message) }

        return '(send_cmd) network error: ' + err.message;
    }
}


// Aux function to stop the execution
export const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));


export async function get_state( verbose=false ) {

    const ans = await send_cmd('preamp state', verbose);

    if ( typeof ans != 'object' ){
        if (verbose) { console.log("(get_state) not a dict:", ans) }
        return {}
    }

    if ( Object.keys(ans).length <= 5 ){
        if (verbose) { console.log("(get_state) not valid:", ans) }
        return {}
    }

    return ans
}


export function allAreTrue(arr) {
  return arr.every(element => element === true);
}


export function flash_element(e, timeout=950){
    e.classList.add('btn-flash');
    setTimeout(() => {
        e.classList.remove('btn-flash');
    }, timeout);
}


export async function do_until_function_istrue( my_function, period_ms, verbose=true ) {

    if (!period_ms){
        period_ms = 5000;
    }

    let istrue = false;

    while ( !istrue ) {

        const now = new Date().toLocaleTimeString();

        if (verbose) {
            const segundos = Math.round(period_ms / 1000);
            console.log(`${now} Waiting ${segundos} s for <${my_function.name}> response`);
        }

        istrue = await my_function();

        if (istrue) {
            if (verbose) {
                console.log(`<${my_function.name}> OK`);
            }
            break;
        }

        await sleep(period_ms);
    }

    return istrue;
}


export function player_controls_clear() {
    document.getElementById("buttonStop").style.background  = "rgb(100, 100, 100)";
    document.getElementById("buttonStop").style.color       = "lightgray";
    document.getElementById("buttonPause").style.background = "rgb(100, 100, 100)";
    document.getElementById("buttonPause").style.color      = "lightgray";
    document.getElementById("buttonPlay").style.background  = "rgb(100, 100, 100)";
    document.getElementById("buttonPlay").style.color       = "lightgray";
}


export function player_info_clear() {
    document.getElementById("bitrate").innerText = "-\nkbps"
    document.getElementById("artist").innerText = "-"
    document.getElementById("track_info").innerText = "-"
    document.getElementById("track_info").innerText += "\n-"
    document.getElementById("time").innerText = "-"
    document.getElementById("album").innerText = "-"
    document.getElementById("title").innerText = "-"
}
