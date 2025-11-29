# Problema JACK no se inicia con real-time scheduling

    $ jackd -d dummy 
    jackdmp 1.9.21 
    Copyright 2001-2005 Paul Davis and others. 
    Copyright 2004-2016 Grame. 
    Copyright 2016-2022 Filipe Coelho. 
    jackdmp comes with ABSOLUTELY NO WARRANTY 
    This is free software, and you are welcome to redistribute it 
    under certain conditions; see the file COPYING for details 
    JACK server starting in realtime mode with priority 10 
    self-connect-mode is "Don't restrict self connect requests" 
    Cannot use real-time scheduling (RR/10) (1: Operation not permitted) 
    AcquireSelfRealTime error



En los Kernels modernos (como el 6.12 que usas) con Systemd, tu terminal se ejecuta dentro de un "Cgroup" (slice) que por defecto tiene 0 microsegundos de tiempo asignado para procesos Real-Time para evitar que bloquees el sistema.

Aquí tienes la solución jerárquica para arreglar esto en Armbian:
Solución 1: Desactivar el "Throttling" de RT globalmente (La más efectiva)

Vamos a decirle al Kernel que deje de restringir el tiempo de CPU para los grupos de tiempo real.


    sudo nano /etc/sysctl.d/99-realtime.conf
    
        kernel.sched_rt_runtime_us = -1

