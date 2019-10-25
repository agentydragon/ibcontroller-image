# ibcontroller-image

Docker container running IB Controller.

## Building

```
# To prevent redownloading huge images on small Dockerfile changes,
# download them first. See https://github.com/moby/moby/issues/15717
# which prevents the ADD Docker command from caching downloads.

./download.sh
docker build .
```

## Tagging

```
docker login --username=agentydragon
docker tag <...> agentydragon/ibcontroller
docker push agentydragon/ibcontroller
```

## Running

```
docker run -e "IB_LOGIN_ID=<...>" -e "IB_PASSWORD=<...>" --name derg -it agentydragon/ibcontroller
```

### Debug and connect to UI

To run with attaching port for VNC:

```
docker run -e "IB_LOGIN_ID=<...>" -e "IB_PASSWORD=<...>" --name derg -P -it agentydragon/ibcontroller
```

Use `docker ps` to find the port mapped to 5900. Connect to it over VNC.

### Exec

```
docker exec -it derg python3 /root/read_snapshot.py --port=7496
```

### Cleanup

```
docker rm derg
```

## TODOs

* Is gtk-2 really needed? I only added it when I forgot a DISPLAY=:1 line.
