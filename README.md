# Práctica calificada 1: despliegue en Windows 11

Repositorio: https://github.com/jort-tec-snt/lab04-pract-calificada

Guía para ejecutar los casos 1 y 2 solicitados en `GLAB-S04-Contenedores-Microservicios.md`.

> **Estado actual:** el Caso 1 está implementado en `caso1/`, con sus tres Dockerfiles. Sus construcciones y descargas reales todavía están pendientes de prueba. El Caso 2 sigue pendiente de implementación; sus comandos son la organización prevista para la entrega. El Dockerfile de la raíz corresponde únicamente al saludo del procedimiento previo.

## 1. Preparar Windows 11

Se utilizarán PowerShell y Docker Desktop con WSL 2 y contenedores Linux. Comprobar los requisitos vigentes de Windows, memoria y virtualización en la [documentación oficial de Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/).

Si WSL no está instalado, abrir **PowerShell como administrador** y ejecutar:

```powershell
wsl --install
```

Reiniciar Windows y completar la configuración que solicite WSL. Si ya está instalado, actualizarlo:

```powershell
wsl --update
```

Comprobar la instalación:

```powershell
wsl --version
```

Referencia: [instalación de WSL de Microsoft](https://learn.microsoft.com/en-us/windows/wsl/install).

Descargar e instalar **Docker Desktop** desde la página oficial enlazada arriba, seleccionar el backend **WSL 2** y abrir Docker Desktop al terminar. Mantenerlo abierto durante las pruebas y usar el modo de **contenedores Linux**.

Abrir PowerShell y ejecutar cada comando por separado:

```powershell
docker --version
docker compose version
docker info --format '{{.OSType}}'
docker ps
```

`docker info` debe mostrar `linux`. Resolver cualquier error antes de continuar.

## 2. Obtener el proyecto

Abrir el [repositorio en GitHub](https://github.com/jort-tec-snt/lab04-pract-calificada), seleccionar **Code → Download ZIP**, extraer el ZIP y abrir PowerShell en la carpeta extraída.

Si se tiene Git instalado, como alternativa:

```powershell
git clone https://github.com/jort-tec-snt/lab04-pract-calificada.git
cd lab04-pract-calificada
```

La estructura de los casos es la siguiente; `caso2/` todavía está pendiente de creación:

```text
lab04-pract-calificada/
├── README.md
├── caso1/
│   ├── app.py
│   ├── downloader.py
│   ├── templates/
│   ├── static/
│   ├── requirements.txt
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── Dockerfile.optimizado
│   └── Dockerfile.multistage
└── caso2/
    ├── app.py
    ├── requirements.txt
    ├── .dockerignore
    ├── Dockerfile
    ├── Dockerfile.optimizado
    └── Dockerfile.multistage
```

**Ejecutar únicamente los comandos de un caso que ya esté incluido en la entrega.** El Caso 1 escucha en `0.0.0.0:5000` dentro del contenedor. Se prevé la misma configuración para el Caso 2, con puertos distintos en Windows para permitir su ejecución simultánea:

| Caso | Aplicación solicitada | Puerto de Windows | Puerto del contenedor |
| --- | --- | ---: | ---: |
| 1 | Descarga de videos de YouTube, Instagram, TikTok, Facebook y LinkedIn | 5001 | 5000 |
| 2 | Registro de la consulta electoral y exportación a Excel según el enunciado | 5002 | 5000 |

## 3. Desplegar el Caso 1

Las imágenes incluyen Python, FFmpeg y Node.js 22 para ejecutar [yt-dlp y sus dependencias](https://github.com/yt-dlp/yt-dlp#dependencies). Node se habilita como motor JavaScript según la [configuración EJS de yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/EJS). La imagen base incorpora Node para disponer del motor también en Alpine; la aplicación web está escrita en Python.

Desde la raíz del repositorio, construir las tres variantes solicitadas. Ejecutar los comandos uno por uno y detenerse ante un error:

```powershell
docker build -f .\caso1\Dockerfile -t caso1:v1.0 .\caso1
docker build -f .\caso1\Dockerfile.optimizado -t caso1:v1.1-alpine .\caso1
docker build -f .\caso1\Dockerfile.multistage -t caso1:v1.2-alpine .\caso1
```

Ejecutar la variante multistage:

```powershell
docker run -d --name caso1 -p 127.0.0.1:5001:5000 caso1:v1.2-alpine
```

Comprobar el contenedor y revisar sus mensajes de inicio:

```powershell
docker ps --filter name=caso1
docker logs caso1
```

Abrir <http://localhost:5001>, pegar un enlace de video y pulsar **Descargar video**. La aplicación entrega el archivo al navegador e informa su tamaño real una vez recibido. Si falla, muestra el error de la plataforma.

Se admite un video por solicitud, con límite final de 200 MiB y hasta 3 minutos para prepararlo. Las imágenes usan `appuser` y contienen un chequeo `/health`. La descarga real en cada plataforma, el usuario y el estado de salud del contenedor están pendientes de verificación; no se garantiza acceso a enlaces privados o restringidos.

Los archivos temporales se eliminan al terminar la respuesta o ante un error. El archivo descargado queda en la ubicación seleccionada por el navegador de Windows.

`yt-dlp` se instala con su versión estable disponible al construir. Si una plataforma cambia y la descarga deja de funcionar, revisar primero el error; para incorporar actualizaciones, reconstruir la variante elegida con `--no-cache`. Antes de reemplazar el contenedor, detener las descargas en curso. Cambiar una imagen no actualiza por sí solo un contenedor ya creado.

## 4. Desplegar el Caso 2

Desde la raíz del repositorio, construir las tres variantes:

```powershell
docker build -f .\caso2\Dockerfile -t caso2:v1.0 .\caso2
docker build -f .\caso2\Dockerfile.optimizado -t caso2:v1.1-alpine .\caso2
docker build -f .\caso2\Dockerfile.multistage -t caso2:v1.2-alpine .\caso2
```

Ejecutar la variante multistage:

```powershell
docker run -d --name caso2 -p 127.0.0.1:5002:5000 caso2:v1.2-alpine
```

Comprobar el contenedor y revisar sus mensajes de inicio:

```powershell
docker ps --filter name=caso2
docker logs caso2
```

Abrir <http://localhost:5002>. El enunciado pide consultar la condición de miembro de mesa en el portal electoral y, si corresponde, registrar en Excel una lista con:

- DNI.
- Miembro de mesa.
- Nombres.
- Ubicación: región, provincia y distrito.
- Dirección del local de votación.

El portal indicado en el Markdown es <https://consultaelectoral.onpe.gob.pe/inicio>. La validación pendiente incluye comprobar el flujo implementado, descargar el Excel y abrirlo en Windows para revisar sus columnas y datos. Cualquier integración o configuración necesaria se documentará al implementar el caso; todavía no hay una consulta electoral automatizada disponible.

## 5. Detener y volver a iniciar

Después de crear los contenedores, detener cada aplicación con:

```powershell
docker stop caso1
docker stop caso2
```

Para volver a abrirlas, iniciar Docker Desktop y ejecutar:

```powershell
docker start caso1
docker start caso2
```

Volver a <http://localhost:5001> y <http://localhost:5002>. `docker run` crea un contenedor; no repetirlo con un nombre que ya exista.

## 6. Problemas de despliegue

| Problema | Comprobación o acción |
| --- | --- |
| No se encuentra la carpeta del caso | Confirmar que la entrega incluye ambos casos y que PowerShell está en la raíz del repositorio |
| `docker` no se reconoce | Completar la instalación de Docker Desktop y abrir una terminal nueva |
| No se puede conectar al motor Docker | Abrir Docker Desktop, esperar su inicio y repetir `docker ps` |
| Conflicto de nombre | Revisar `docker ps -a`; si el contenedor existe y está detenido, usar `docker start caso1` o `docker start caso2` |
| Puerto ocupado | Liberar el puerto o escoger otro puerto de Windows al crear el contenedor; actualizar también la URL del navegador |
| Contenedor detenido o página inaccesible | Revisar `docker ps -a` y `docker logs caso1` o `docker logs caso2` |

Los tamaños de imágenes, estados de salud y resultados funcionales de los casos se comprobarán sobre las implementaciones finales. Esta guía todavía no acredita una prueba en Windows 11.
