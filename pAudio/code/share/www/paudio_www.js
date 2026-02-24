#!/usr/bin/env node

/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pAudio', a PC based personal audio system.
*/

const express = require('express');
const net = require('net');
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const os = require('os');

const app = express();
var   WEB_PORT = 8088;
const BACKEND_TIMEOUT = 500

const CONFIG_PATH = path.join(os.homedir(), 'pAudio/config.yml');
var   CONFIG = {}

// Load config yaml
try {
    const fileContents = fs.readFileSync(CONFIG_PATH, 'utf8');
    CONFIG = yaml.load(fileContents);
    //console.log(CONFIG);

    if ( 'web_port' in CONFIG ){
        if (
            typeof CONFIG.web_port === 'number' &&
            Number.isInteger(CONFIG.web_port) &&
            CONFIG.web_port !== 80 &&
            CONFIG.web_port > 1000
        ){
            WEB_PORT = CONFIG.web_port;

        }else{
            console.log("CONFIG.web_port must be > 1000");
        }
    }

} catch (e) {
    console.error("error reading YAML:", e);
    return null;
}


// Command line option '-v' VERBOSE
let verbose     = false;
process.argv.slice(2).forEach(opt => {
    if (opt === '-v') {
        verbose = true;
        console.log('(verbose mode)')
    }
});


// tcp bridge (promised to use async/await)
function backendSocket(cmd, backend_port) {

    return new Promise((resolve, reject) => {

        const client = new net.Socket();
        let response = '';

        client.setTimeout(BACKEND_TIMEOUT);

        client.connect(backend_port, CONFIG.paudio_addr, () => {
            client.write(cmd);
        });

        client.on('data', (data) => {
            response += data.toString();
        });

        client.on('end', () => resolve(response));

        client.on('error', (err) => reject(err.message));

        client.on('timeout', () => {
            client.destroy();
            // we return whatever we have up to the timeout
            resolve(response);
        });
    });
}

// Static files are found in the 'public/' folder
app.use( express.static( path.join(__dirname, 'public') ) );

// we need json to listen commands in API RESTful style
app.use(express.json());


// API RESTful style
app.post('/api/command', async (req, res) => {

    const { command } = req.body;

    if (!command) {
        return res.status(400).json({ error: "no command found" });
    }

    let backend_port = CONFIG.paudio_port;

    // Divert "ctrl ...." to paudio_ctrl
    const prefix = command.trim().split(' ')[0]
    if ( prefix == 'ctrl' ){
        backend_port += 1;
    }

    try {
        const result = await backendSocket(command, backend_port);
        if (verbose) {
            console.log('Rx:',  command);
            console.log('Tx:',  result);
        }

        // if backend is JSON, try to return JSON to frontend
        try {
            res.json(JSON.parse(result));
        // else plain text
        } catch {
            res.send(result);
        }
    } catch (error) {
        console.log(command, error);
        res.status(500).json({ error: "backend error" });
    }
});


app.listen(WEB_PORT, () => {
    console.log(`Node.js server active at port ${WEB_PORT}`);
    console.log(`Reading config at: ${CONFIG_PATH}`);
});
