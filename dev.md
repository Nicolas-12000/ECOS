# Flujo de ramas (Git Flow ligero)

Este repositorio usa un flujo simple basado en Git Flow para mantener orden y trazabilidad sin sobrecarga.

## Ramas principales

- main: versiones estables y entregas oficiales
- develop: integracion continua de trabajo

## Ramas de trabajo

- feature/*: nuevas funcionalidades
- fix/*: correcciones no urgentes
- release/*: preparacion de entregas
- hotfix/*: arreglos urgentes sobre main

## Ciclo recomendado

1. Crear una rama desde develop:
   - feature/nombre-corto
2. Trabajar y hacer commits pequenos y claros.
3. Abrir PR a develop con descripcion breve y checklist.
4. Para entrega: crear release/x.y desde develop.
5. Merge de release a main y develop, luego tag.

## Convenciones

- Prefiere ramas cortas y especificas.
- Nombres en kebab-case.
- Nunca trabajar directo en main.
