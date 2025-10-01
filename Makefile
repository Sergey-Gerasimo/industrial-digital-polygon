DC = docker compose
EXEC = docker exec -it
LOGS = docker logs
ENV = --env-file .env
APP_FILE = docker/app.yaml
STORAGES_FILE = docker/storages.yaml
FRONTEND_FILE = docker/frontend.yaml
PROXY_FILE = docker/proxy.yaml
APP_CONTAINER = backend

.PHONY: network
network:
	docker network create backend-dev || true


.PHONY: clean
clean:
	${DC} -f ${STORAGES_FILE} -f ${APP_FILE} -f ${FRONTEND_FILE} -f ${PROXY_FILE} down
	docker network rm backend-dev || true

.PHONY: app
app: network
	${DC} -f ${APP_FILE} ${ENV} up --build -d

.PHONY: storages
storages: network
	${DC} -f ${STORAGES_FILE} ${ENV} up --build -d

.PHONY: frontend
frontend:
	${DC} -f ${FRONTEND_FILE} ${ENV}up --build -d

.PHONY: proxy
proxy: network
	${DC} -f ${PROXY_FILE} ${ENV} up --build -d

.PHONY: all
all: network
	${DC} -f ${STORAGES_FILE} -f ${APP_FILE} -f ${FRONTEND_FILE} -f ${PROXY_FILE} ${ENV} up --build -d

.PHONY: app-down
app-down:
	${DC} -f ${APP_FILE} down

.PHONY: frontend-down
frontend-down:
	${DC} -f ${FRONTEND_FILE} down

.PHONY: proxy-down
proxy-down:
	${DC} -f ${PROXY_FILE} down

.PHONY: storages-down
storages-down:
	${DC} -f ${STORAGES_FILE} down

.PHONY: app-shell
app-shell:
	${EXEC} ${APP_CONTAINER} bash

.PHONY: app-logs
app-logs:
	${LOGS} ${APP_CONTAINER} -f

.PHONY: test
test:
	${EXEC} ${APP_CONTAINER} pytest