microservicio_anuncio

Para ejecutar y probar toda las funcionalidades de microservicio anuncio, se simulo sus conexiones con microservicio usuario y microservicio middleware 
para ejecutar se debe hacer lo siguiente:

- Se debe crear network demo_01 con "dokcer create docker network create demo_01", si es que no esta creada
- Se debe hacer "docker-compose build" en carpeta de microservicio anuncio y luego "docker-compose up"
- Se debe hacer "docker-compose build" en carpeta de microservicio usuario y luego "docker-compose up"
- se debe hacer "docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 --network=demo_01 rabbitmq:3.12-management"
- se debe hacer "docker-compose build" en carpeta de microservicio middleware y luego "docker-compose up"

Consideraciones:

- El programa empezara a funcionar al acceder a "http://172.18.0.3/", la ip puede variar. Ademas se conecta a traves de ip a la cola rabbitMQ y al   microservicio usuario y middleware tambien se conecta a traves de ip a cola rabbitMQ, por lo que se puede ver afectado.

- Se dejo "http://172.18.0.3/" para inciar el funcionamiento para asi decidir cuando comienza y poder revisar el resto de funcionalidad, dado que no es una solicitud get, lo mas correcto seria usar @app.on_event("startup") para que inicie cuando el contenedor se active.

Repositorio: https://github.com/seed4407/microservicio.git
