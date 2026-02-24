/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pAudio', a PC based personal audio system.
*/

export async function send_cmd(cmd) {
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

        if (!response.ok) throw new Error('backend error');

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
            console.log('server timeout:', err.message)
            return 'server timeout';
        }
        console.log('network error:', err.message)
        return 'network error: ' + err.message;
    }
}


export async function get_state() {

    const ans = await send_cmd('preamp state');

    if ( typeof ans != 'object' ){
        console.log("'preamp state' not a dict", typeof ans, ans)
        return {}
    }

    if ( Object.keys(ans).length <= 5 ){
        console.log("'preamp state' not valid:", typeof ans, ans)
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
