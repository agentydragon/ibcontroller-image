# ibcontroller-image

Docker container running IB Controller.

## Building

```
docker login --username=agentydragon
docker build .
docker tag <...> agentydragon/ibcontroller
docker push agentydragon/ibcontroller
```
