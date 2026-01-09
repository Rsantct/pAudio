#!/usr/bin/env python3

# Copyright (c) Rafael Sánchez
# This file is part of 'pAudio', a PC based personal audio system.

""" A JACK wrapper
"""

from    common import *
import  jack
import  multiprocessing as mp

JCLI = None

VERBOSE = CONFIG["verbose"]

def _jcli_activate(cli_name = 'jack_mod'):

    global JCLI

    try:
        JCLI = jack.Client(cli_name, no_start_server=True)
        JCLI.activate()

    except Exception as e:
        print(f'{Fmt.BOLD}(jack_mod) cannot activate jack.Client `{cli_name}`: {str(e)}{Fmt.BOLD}')
        return str(e)

    return 'done'


def run_jackd(  alsa_dev='', io_mode='recplay', fs=44100, period=1024, nperiods=2,
                jloops_list=[], dither=False, softmode=False ):
    """ Run JACK in a separate process, including jack_loops
    """

    if VERBOSE:
        print(f'{Fmt.BLUE}(jack_mod) Trying to run JACK ...{Fmt.END}')

    if dither:
        dither = 'shaped'
    else:
        dither = 'none'

    if softmode:
        sm = '--softmode'
    else:
        sm = ''

    if 'rec' in io_mode and 'play' in io_mode:
        mode = 'd'

    elif 'rec' in io_mode and not 'play' in io_mode:
        mode = 'C'

    elif not 'rec' in io_mode and 'play' in io_mode:
        mode = 'P'
    else:
        print(f'{Fmt.RED}(jack_mod) BAD io_mode{Fmt.END}')
        return False

    with open(f'{LOGFOLDER}/jackd.log', 'w') as f:
        f.write('JACKD COMMAND LINE:\n')
        f.write(jack_cmd)
        f.write('\n\n')

    jack_cmd = f'jackd -d alsa -{mode} {alsa_dev} -r {fs} -p {period} -n {nperiods} -z {dither}' + \
               f' {sm} 1>{LOGFOLDER}/jackd.log 2>&1'

    sp.Popen( jack_cmd, shell=True )

    if wait4jackports('system', timeout=10):

        run_jloops(jloops_list)

        dit = 'dither:shaped' if dither else ''
        if VERBOSE:
            print(f'{Fmt.BLUE}(jack_mod) JACK fs:{fs} period:{period} n:{nperiods} {dit}{Fmt.END}')
        return True

    else:
        return False


def _jack_loop(clientname, nports=2):
    """ Creates a jack loop with given 'loopname'

        NOTICE: this process will keep running until broken,
                so if necessary you'll need to thread this when calling here.

        CREDITS:  https://jackclient-python.readthedocs.io/en/0.4.5/examples.html
    """

    if VERBOSE:
        print( f'{Fmt.CYAN}(jack_loop) trying to run: {clientname} with {nports} ports ...{Fmt.END}' )


    # The jack module instance for our looping ports
    client = jack.Client(name=clientname, no_start_server=True)

    if client.status.name_not_unique:
        client.close()
        print( f'{Fmt.CYAN}{Fmt.RED}(jack_loop) \'{clientname}\' already exists in JACK, nothing done.{Fmt.END}' )
        return

    # Will use the multiprocessing.Event mechanism to keep this alive
    event = mp.Event()

    # This sets the actual loop that copies frames from our capture to our playback ports
    @client.set_process_callback
    def process(frames):
        assert len(client.inports) == len(client.outports)
        assert frames == client.blocksize
        for i, o in zip(client.inports, client.outports):
            o.get_buffer()[:] = i.get_buffer()

    # If jack shutdowns, will trigger on 'event' so that the below 'whith client' will break.
    @client.set_shutdown_callback
    def shutdown(status, reason):
        if VERBOSE:
            print(f'{Fmt.GRAY}(jack_loop) JACK shutdown!{Fmt.END}')
            print(f'{Fmt.GRAY}(jack_loop) JACK status:{Fmt.END}', status)
            print(f'{Fmt.GRAY}(jack_loop) JACK reason:{Fmt.END}', reason)
        # This triggers an event so that the below 'with client' will terminate
        event.set()


    # Create the ports
    for n in range( nports ):
        client.inports.register(f'input_{n+1}')
        client.outports.register(f'output_{n+1}')
    # client.activate() not needed, see below

    # This is the keeping trick
    with client:
        # When entering this with-statement, client.activate() is called.
        # This tells the JACK server that we are ready to roll.
        # Our above process() callback will start running now.

        if VERBOSE:
            print( f'{Fmt.CYAN}(jack_loop) running {clientname}{Fmt.END}' )
        try:
            event.wait()
        except KeyboardInterrupt:
            print(f'\n{Fmt.CYAN}(jack_loop) Interrupted by user{Fmt.END}')
        except:
            print(f'\n{Fmt.CYAN}(jack_loop) Terminated{Fmt.END}')


def run_jloops(loop_names=[]):
    """ Preparing the loops
    """
    if VERBOSE:
        print(f'{Fmt.CYAN}(jack_mod) Please wait for JACK LOOPS: {loop_names}{Fmt.END}')

    for loop_name in loop_names:
        jloop = mp.Process( target=_jack_loop, args=(loop_name, 2) )
        jloop.start()


def get_samplerate():
    """ wrap function """
    return JCLI.samplerate


def get_bufsize():
    """ wrap function """
    return JCLI.blocksize


def get_device():
    """ This is not in Jack-CLIENT API
    """
    device = ''
    try:
        tmp = sp.check_output('pgrep -fla jackd'.split()).decode()
    except:
        return device

    if not 'hw:' in tmp:
        return device

    tmp = tmp.split('hw:')[-1]

    if ',' in tmp:
        device = tmp.split(',')[0].strip()
    else:
        device = tmp.split(' ')[0].strip()

    return device


def get_all_connections(pname):
    """ wrap function """
    ports = JCLI.get_all_connections(pname)
    return ports


def get_ports(pattern='',  is_audio=True, is_midi=False,
                           is_input=False, is_output=False,
                           is_physical=False, can_monitor=False,
                           is_terminal=False ):
    """ wrap function """
    ports = JCLI.get_ports(pattern, is_audio, is_midi,
                                    is_input, is_output,
                                    is_physical, can_monitor,
                                    is_terminal )
    return ports


def connect(p1, p2, mode='connect', verbose=True):
    """ Low level tool to connect / disconnect a pair of ports.
    """

    # will retry 10 times every .1 sec
    times = 10
    while times:

        try:
            if 'dis' in mode or 'off' in mode:
                JCLI.disconnect(p1, p2)
            else:
                JCLI.connect(p1, p2)
            result = 'done'
            break

        except jack.JackError as e:
            result = f'{e}'
            if verbose:
                print( f'(jack_mod) Exception: {result}' )

        sleep(.1)
        times -= 1

    return result


def connect_bypattern( cap_pattern, pbk_pattern, mode='connect' ):
    """ High level tool to connect/disconnect a given port name patterns.
        Also works for port alias patterns.
    """

    # Try to get ports by a port name pattern
    cap_ports = JCLI.get_ports( cap_pattern, is_output=True )
    pbk_ports = JCLI.get_ports( pbk_pattern, is_input=True )

    # If not found, it can be an ALIAS pattern
    if not cap_ports:
        for p in JCLI.get_ports( is_output=True ):
            # A port can have 2 alias
            for palias in p.aliases:
                if cap_pattern in palias:
                    cap_ports.append(p)
    if not pbk_ports:
        for p in JCLI.get_ports( is_input=True ):
            # A port can have 2 alias
            for palias in p.aliases:
                if pbk_pattern in palias:
                    pbk_ports.append(p)

    #print('CAPTURE  ====> ', cap_ports)  # DEBUG
    #print('PLAYBACK ====> ', pbk_ports)

    errors = ''
    if not cap_ports:
        tmp = f'cannot find capture jack port "{cap_pattern}" '
        print(f'(jack_mod) {tmp}')
        errors += tmp
    if not pbk_ports:
        tmp = f'cannot find playback jack port "{pbk_pattern}" '
        print(f'(jack_mod) {tmp}')
        errors += tmp

    mode = 'disconnect' if ('dis' in mode or 'off' in mode) else 'connect'
    for cap_port, pbk_port in zip(cap_ports, pbk_ports):
        connect(cap_port, pbk_port, mode)


    if not errors:
        return 'ordered'
    else:
        return errors


def clear_preamp():
    """ Force clearing ANY clients, no matter what source was selected
    """
    preamp_ports = JCLI.get_ports('pre_in_loop', is_input=True)
    for preamp_port in preamp_ports:
        for client in JCLI.get_all_connections(preamp_port):
            connect( client, preamp_port, mode='off' )

