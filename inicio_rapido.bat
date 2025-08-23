@echo off
echo ================================================
echo     INICIO RAPIDO - LINK STATE CON SOCKETS
echo ================================================
echo.
echo Este script inicia 4 nodos Link State para demostrar
echo el protocolo distribuido en accion.
echo.
echo Nodos que se iniciaran:
echo - Nodo A (puerto 65001)
echo - Nodo B (puerto 65002) 
echo - Nodo F (puerto 65006)
echo - Nodo D (puerto 65004)
echo.
echo Presiona Ctrl+C para detener todos los nodos
echo.
pause

echo.
echo Iniciando nodos...
echo.

start "Nodo A" cmd /k "python link_state_socket.py A 65001"
timeout /t 2 /nobreak >nul

start "Nodo B" cmd /k "python link_state_socket.py B 65002"  
timeout /t 2 /nobreak >nul

start "Nodo F" cmd /k "python link_state_socket.py F 65006"
timeout /t 2 /nobreak >nul

start "Nodo D" cmd /k "python link_state_socket.py D 65004"
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo Nodos iniciados!
echo ============================================
echo.
echo Comandos utiles:
echo.
echo 1. Para ver el cliente interactivo:
echo    python cliente_link_state.py
echo.
echo 2. Para ver el coordinador:
echo    python coordinador_link_state.py  
echo.
echo 3. Para iniciar nodos individuales:
echo    python link_state_socket.py [NODO] [PUERTO]
echo.
echo Los nodos tardaran unos segundos en converger...
echo.
pause
