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

        const respuTxt = await response.text();

        try {
            return JSON.parse(respuTxt.replaceAll(': null', ': ""'));

        } catch {
            if (respuTxt.toLowerCase().includes('refused')){
                return 'refused from server'
            }else{
                return respuTxt;
            }
        }

    } catch (err) {
        // Differ on timeout or network error
        if (err.name === 'AbortError') {
            return 'server timeout';
        }
        return 'error: ' + err.message;
    }
}

