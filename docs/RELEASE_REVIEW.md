# Revisión de publicación — 8 de septiembre de 2026

## Resultado

Código fuente preparado para publicación. El modelo operativo conserva SHA-256 `c5fba1aeccb60ca8eac49c1750123a5dc85f22456f02f805f62fff6386669530`. Esta revisión no modifica inferencia, entrenamiento ni pesos, y no reconstruye el portable.

## Contenido

- README principal en español y versión inglesa independiente, con captura real del modo demostración sin datos de pacientes.
- Documentación vigente de arquitectura, ontología, modelo, experimentos y reentrenamiento.
- Planes cumplidos e informe de un modelo anterior retirados del árbol publicable; copia privada en `local_archive/2026-09-08/`.
- Datos originales y derivados, 99 campos de revisión, manifiestos, resultados y mejor checkpoint del piloto conservados localmente.
- Checkpoint final redundante y exportaciones de prueba trasladados al mismo archivo local. No se ha liberado su espacio en disco.
- Historial Git y atribuciones conservados; redacción pública sin notas sobre herramientas de escritura ni rutas personales.

## Comprobaciones

| Control | Resultado |
|:---|:---|
| Pruebas automatizadas | 60 aprobadas, 0 fallidas |
| `publish.ps1 -CheckOnly` | Completado sin commit ni push |
| `git push --dry-run origin main` | Acceso aceptado; sin transferencia de cambios |
| Credenciales por patrones | Sin coincidencias en el árbol publicable y 211 blobs históricos alcanzables, incluidos mensajes de commits/tags |
| Dependencias declaradas y transitivas | 57 paquetes resueltos; `pip-audit` no encontró vulnerabilidades conocidas |
| Enlaces locales Markdown | Sin destinos inexistentes |
| Identidad del modelo operativo | Hash sin cambios |
| Archivo público | Fuentes y recursos visuales; datos, secretos, modelos y resultados privados excluidos |

La auditoría de dependencias corresponde a las versiones que resolvieron los archivos de requisitos en esta fecha, no a todos los paquetes instalados en el equipo ni a los binarios del portable. El informe completo se conserva en `artifacts/dependency_audit.json`.

El análisis de credenciales utiliza patrones conocidos y no certifica ausencia absoluta de secretos. Se conserva la licencia AGPL-3.0-only y los avisos de terceros; no se acredita titularidad jurídica ni autorización de terceros mediante pruebas automáticas. Véanse [publicación](PUBLISHING.md) y [avisos de terceros](../THIRD_PARTY_NOTICES.md).

## Publicación

`publish.cmd` realiza comprobaciones, crea un commit y envía los cambios a `DnsRudy21/VECTOR_UroSight`. La autenticación es externa al repositorio. Se detiene ante fallos o divergencia remota y no usa push forzado.

Esta revisión preparó el acceso de publicación; no ejecutó un push con los cambios.
