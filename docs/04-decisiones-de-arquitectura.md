# Decisiones de Arquitectura

Este documento describe las decisiones de diseño clave tomadas para el desarrollo del Scrum Master Bot.

## 1. Arquitectura Hexagonal (Clean Architecture)

El proyecto está estructurado utilizando una Arquitectura Hexagonal, separando claramente las responsabilidades en cuatro capas:

- **Dominio (`src/domain`):** Contiene la lógica de negocio core. Entidades, enums y excepciones. Esta capa no depende de ningún framework (ni SQLAlchemy, ni FastAPI, ni Slack).
- **Aplicación (`src/application`):** Contiene los casos de uso (servicios). Orquesta la interacción entre las entidades de dominio y los repositorios. Tampoco depende de frameworks externos, excepto inyección de repositorios abstractos.
- **Infraestructura (`src/infrastructure`):** Implementaciones concretas. Aquí reside la base de datos (SQLAlchemy ORM), los clientes HTTP (GitHub, Slack, AI), la sincronización con Excel y el Scheduler (APScheduler).
- **Interfaces (`src/interfaces`):** Puntos de entrada de la aplicación. Contiene la API REST (FastAPI) y los handlers de Slack (Slack Bolt).

## 2. Dataclasses sobre Modelos ORM

Decidimos utilizar `dataclasses` estándar de Python para los modelos de dominio, separándolos completamente de los modelos ORM de SQLAlchemy.
- **Ventaja:** El dominio se mantiene puro, facilitando las pruebas unitarias y evitando problemas con el _event loop_ asíncrono al realizar operaciones en la base de datos (lazy loading).
- **Costo:** Requiere mapear explícitamente entre objetos del dominio y registros ORM mediante métodos `to_domain()` y `from_domain()` en los repositorios.

## 3. Separación de Slack, FastAPI y Dominio

Las rutas web y los comandos de Slack actúan como capas de presentación que simplemente serializan datos a JSON o Block Kit y hacen llamadas a los servicios de la capa de aplicación. El núcleo nunca conoce de dónde provino la orden (HTTP, Slack, etc.).

## 4. Inyección de Dependencias

Evitamos librerías pesadas de inyección de dependencias (DI). En su lugar:
- En FastAPI, usamos `Depends()` para resolver la sesión y proveer repositorios.
- En Slack, proveemos un diccionario de servicios base o una _factory function_ `session_maker()` a través del constructor y resolvemos dinámicamente según sea necesario por la sesión.
- En los servicios, las dependencias se pasan mediante el constructor (Constructor Injection), lo que permite inyectar versiones "Mock" (Fakes) muy fácilmente en los tests.
