## Ejecución del código en Docker

```bash
docker run -d -v /path/to/your/folder/to/use:/srv -p 80:80 gtstef/filebrowser:latest
```
`/path/to/your/folder/to/use` es la ruta de la carpeta que deseamos utilizar para almacenar los archivos del file browser