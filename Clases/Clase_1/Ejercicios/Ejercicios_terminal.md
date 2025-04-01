## Ejercicios de Terminal

```sh
1. ls > lista.txt

2. wc -l < lista.txt

3. ls /computacion2 2> errores.log

4. ls | grep "log"

5. ls | grep ".txt" | wc -l

6. ls /home/computacion2 &> resultado_completo.log

7. ls /computacion2 &> /dev/null

8. exec 3> salida_custom.log
   echo "lorem impsum" >&3
   exec 3>&-

9. exec > sesion.log 2>&1
   echo "La salida del shell se guarda en sesion.log"
   ls /home
   ls /no_existe
   exec >&-

10. ls /var/log | grep "syslog" | wc -l &> conteo_syslog.log
```