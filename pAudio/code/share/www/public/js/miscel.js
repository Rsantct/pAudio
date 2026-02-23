export async function send_cmd(cmd) {
    // Si la petición tarda más de 4 segundos, la cancelamos
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
                return 'server error'
            }else{
                return respuTxt;
            }
        }

    } catch (err) {
        // Differ on timeout or network error
        if (err.name === 'AbortError') {
            return 'server timeout';
        }
        return JSON.stringify({ error: true, reason: err.message });
    }
}

