#!/usr/bin/env node

/*
    Copyright (c) Rafael Sánchez
    This file is part of 'pAudio', a PC based personal audio system.
*/

// The DEFAULT listening HTTP PORT unless passed via command line
let NODEJS_PORT = 8088;
const myArgs = process.argv.slice(2);
if (myArgs[0]){
    NODEJS_PORT = myArgs[0];
}


// Importing modules (require)
const http  = require('http');
const url   = require('url');
const fs    = require('fs');
const net   = require('net');
const yaml  = require('js-yaml');
const os    = require('os');


// Command line option '-v' VERBOSE -vv VERY VERBOSE
var verbose = false;
var vv      = false;
const opcs = process.argv.slice(2);
if ( opcs.indexOf('-v') != -1 ){
    verbose = true;
}
if ( opcs.indexOf('-vv') != -1 ){
    verbose = true;
    vv      = true;
}
var PA_ADDR = '0.0.0.0'
var PA_PORT = 9980


// Getting address & port to communicate to pAudio
try {
    const UHOME = os.homedir();
    let fileContents = fs.readFileSync(UHOME + '/pAudio/config.yml', 'utf8');
    let CFG = yaml.load(fileContents);
    const tmp_ADDR =   CFG.paudio_addr;
    const tmp_PORT =   CFG.paudio_port;
    if (tmp_ADDR){
        PA_ADDR = tmp_ADDR;
        if (PA_ADDR == 'localhost'){
            // force ipv4:
            PA_ADDR = '127.0.0.1';
        }
    }
    if (tmp_PORT){
        PA_PORT = tmp_PORT;
    }
    console.log('Using pAudio address at ' + PA_ADDR + ':' + PA_PORT)

} catch (e) {
    console.log(e);
    console.log('Using DEFAULT pAudio address at ' + PA_ADDR + ':' + PA_PORT)
}
const PA_CTRL_PORT = PA_PORT + 1


// Helpers to printout http TX and RX chunks w/o repeating them
var last_cmd_phrase = '';
var last_http_sent  = '';


// Color escape sequences for console.log usage
// https://stackoverflow.com/questions/9781218/how-to-change-node-jss-console-font-color

const Reset = "\x1b[0m";
const Bright = "\x1b[1m";
const Dim = "\x1b[2m";
const Underscore = "\x1b[4m";
const Blink = "\x1b[5m";
const Reverse = "\x1b[7m";
const Hidden = "\x1b[8m";

const FgBlack = "\x1b[30m";
const FgRed = "\x1b[31m";
const FgGreen = "\x1b[32m";
const FgYellow = "\x1b[33m";
const FgBlue = "\x1b[34m";
const FgMagenta = "\x1b[35m";
const FgCyan = "\x1b[36m";
const FgWhite = "\x1b[37m";

const BgBlack = "\x1b[40m";
const BgRed = "\x1b[41m";
const BgGreen = "\x1b[42m";
const BgYellow = "\x1b[43m";
const BgBlue = "\x1b[44m";
const BgMagenta = "\x1b[45m";
const BgCyan = "\x1b[46m";
const BgWhite = "\x1b[47m";


// This is the MAIN function, it is called from the httpServer
// when some httpRequest is received.
function onHttpReq( httpReq, httpRes ){

    // Sends back a requested file to the browser
    function http_serve_file(fpath){

        let fileEncoding = 'utf8';
        if (ctype.match(/image/g)){
            fileEncoding = null;
            httpRes.writeHead(200, {'Content-Type': ctype,
                                    'Cache-Control': 'max-age=60'});

        }else{
            httpRes.writeHead(200, {'Content-Type': ctype});
        }

        fs.readFile(fpath, fileEncoding, (err,data) => {
            if (! err) {
                httpRes.write(data);
                httpRes.end();
                if (vv) console.log( FgBlue, '(node) httpServer TX: ', ctype, '('+fpath+')', Reset );
            }else{
                httpRes.end();
                if (vv) console.log( FgRed, '(node) httpServer ERROR READING: ', '('+fpath+')', Reset );
            }
        });

    };


    const   docRoot = __dirname + '/../'
    var     fpath = '';
    var     ctype = ''


    // very verbose mode
    if (vv) console.log( FgCyan, '(node) httpServer RX:', httpReq.url, Reset );


    // Prepare http header
    httpRes.setHeader('server', 'pAudio / Node.js ' + process.version);


    // Parse the requested URL:

    // Index.html
    // (i) index_big.html is used for better layout in a landscape tablet screen.
    if (httpReq.url === '/' || httpReq.url === '/index.html'
                            || httpReq.url === '/index_big.html') {
        ctype = 'text/html';
        fpath = docRoot + 'index.html';
        if (httpReq.url === '/index_big.html'){
            fpath = fpath.replace('index', 'index_big');
        }
        http_serve_file(fpath);
    }

    // Manifest file
    else if (httpReq.url.match(/site\.webmanifest/g)) {
        ctype = 'text/plain';
        fpath = docRoot + httpReq.url;
        http_serve_file(fpath);
    }

    // Css
    else if (httpReq.url.match("\.css$")) {
        ctype = 'text/css';
        fpath = docRoot + httpReq.url;
        http_serve_file(fpath);
    }

    // Javascript
    else if (httpReq.url === '/js/main.js') {
        ctype = 'application/javascript';
        fpath = docRoot + httpReq.url;
        http_serve_file(fpath);
    }

    // Favicons for Mozilla and Chrome like browsers
    else if (httpReq.url.match(/^\/favicon/g)){
        ctype = 'image/vnd.microsoft.icon';
        fpath = docRoot + httpReq.url;
        http_serve_file(fpath);
    }

    // Images
    //      Pending to use ETag to allow browsers to cache images at client end.
    //      By now, we will use Cache-Control 60 seconds for Safary to chache the
    //      sent image. Firefox uses cached image even if omitted this header.
    else if ( httpReq.url.match(/\/images/g) ) {
        ctype = 'image';
        if       ( httpReq.url.slice(-4, ) === '.png' ) {
            ctype = 'image/png';
        }else if ( httpReq.url.slice(-4, ) === '.jpg' ) {
            ctype = 'image/jpg';
        }

        // The browser's clientside javascript will request some stamp
        // after the filename, e.g. images/brutefir_eq.png?554766166
        fpath = docRoot + httpReq.url;
        fpath = fpath.split('?').slice(0, 1)[0]

        http_serve_file(fpath);
    }

    // A query for the server side (url = ....?command=....)
    else if (httpReq.url.match(/\?command=/g)){

        let q = url.parse(httpReq.url, true).query;
        let cmd_phrase = q.command;

        if ( cmd_phrase ){

            // debugging received commands but not repeating :-)
            if (last_cmd_phrase !== cmd_phrase){
                if (verbose){
                    console.log(FgGreen, '(node) httpServer RX: ' + httpReq.url);
                }
                last_cmd_phrase = cmd_phrase;
            }

            let port = PA_PORT;

            // Diverting special commands to paudio_ctrl server
            if (cmd_phrase.match(/restart_/g) || cmd_phrase.match(/amp_/g)){
                port += 1;
            }

            // Create a socket client to the pAudio TCP server side
            const client = net.createConnection( { port:port,
                                                   host:PA_ADDR },
                                                   () => {
            });

            // If the TCP server is unavailable, then do nothing but ending the http stuff
            client.on('error', function(err){
                httpRes.end();
                client.destroy();
                console.log(err);
                console.log( FgRed, '(node) cannot connect to pAudio at '
                             + PA_ADDR + ':' + port, Reset );
            });

            // Will use timeout when connecting as a client to the pAudio server
            // (i) It is a must to ending the socket if timeout happens
            //     https://nodejs.org/api/net.html#net_socket_settimeout_timeout_callback
            //     Some heavy commands (i.e. player get_all_info) takes a while > 200 ms
            if (cmd_phrase.match(/^player/g)){
                client.setTimeout(500);
            }else{
                client.setTimeout(250);
            }
            client.on('timeout', () => {
              console.log( FgRed, '(node) sending to pAudio:', cmd_phrase, Reset);
              console.log( FgRed, '(node) client socket timeout to pAudio at '
                           + PA_ADDR + ':' + port, Reset );
              client.end();
            });

            // The socket client is ready to send data through by:
            client.write( cmd_phrase + '\r\n' );
            if (verbose){
                console.log( FgGreen, '(node) ' + PA_ADDR + ':' +
                             port + ' TX: ' + cmd_phrase, Reset );
            }

            // The key (**) ==> the handler for socket received data
            client.on('data', (data) => {

                const ans = data.toString();
                if (verbose){
                    if ( ans.length > 40 ){
                        console.log( FgGreen, '(node) ' + PA_ADDR + ':' +
                                     port + ' RX:', ans.slice(0,40) +
                                     ' ... ...', Reset );
                    }
                    else {
                        console.log( FgGreen, '(node) ' + PA_ADDR + ':' +
                                     port + ' RX:', ans, Reset);
                    }
                }

                client.end();

                // (**) Important to write and end the httpResponse
                //      here INSIDE the client.on('data') HANDLER
                //      because of the handler (and all JS) is asynchronous
                httpRes.writeHead(200, {'Content-Type':'text/plain'});
                if (ans){
                    httpRes.write(ans);
                    // debugging sent chunks but no repeating :-)
                    if (last_http_sent !== ans){
                        if (verbose){
                            if ( ans.length > 40 ){
                                console.log( FgGreen, '(node) httpServer TX: ' + ans.slice(0,40), Reset );
                            }
                            else {
                                console.log( FgGreen, '(node) httpServer TX: ' + ans, Reset );
                            }
                        }
                        last_http_sent = ans;
                    }
                }
                httpRes.end();
            });
        }
    }


    // An unaccepted httpRequest
    else {
        const ans = 'NACK'
        ctype = 'text/plain'
        httpRes.writeHead(200, {'Content-Type': ctype});
        httpRes.write(ans + '\n');
        httpRes.end();
        console.log( FgBlue, '(node) httpServer TX: ', ctype, ans, Reset);
    }
}

// Starts an HTTP SERVER, which automagically will trigger
// a function when a 'request' event occurs.
http.createServer( onHttpReq ).listen( NODEJS_PORT );

console.log('Node.js', process.version);
console.log('Server running at http://localhost:' + NODEJS_PORT + '/');
