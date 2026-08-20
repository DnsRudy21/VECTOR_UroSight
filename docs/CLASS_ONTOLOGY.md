# Ontología de clases

Esta ontología registra únicamente clases observadas en la documentación y anotaciones disponibles. Los nombres mostrados son descriptivos para revisión; no implican diagnóstico ni validación clínica.

| Fuente | Clase original | Clase canónica | Nombre mostrado | Instancias verificadas | Notas |
|--------|----------------|----------------|-----------------|-------------------------|-------|
| USE | `eryth` | `eritrocitos` | Eritrocitos | 21,815 | Clase mayoritaria de USE. |
| USE | `leuko` | `leucocitos` | Leucocitos | 6,169 | Compatible conceptualmente con `pus` de UMID; conservar origen al consolidar. |
| USE | `epith` | `celulas_epiteliales` | Células epiteliales | 6,175 | Célula completa. |
| USE | `epithn` | `celulas_epiteliales_nucleadas` | Núcleos epiteliales | 687 | El identificador canónico se conserva por compatibilidad interna; el README de USE define explícitamente “epithelial nuclei”. No fusionar con `epith`. |
| USE | `cast` | `cilindros` | Cilindros | 3,662 | No observada en UMID. |
| USE | `cryst` | `cristales` | Cristales | 1,644 | No observada en UMID. |
| USE | `mycete` | `levaduras_hongos` | Hongos/levaduras | 2,083 | El nombre crudo no permite una especie más específica. |
| UMID | `rbc` | `eritrocitos` | Eritrocitos | 1,556 | UMID declara RBC; corresponde al identificador YOLO 1. |
| UMID | `pus` | `leucocitos` | Leucocitos | 986 | El README equipara “pus cells” con WBC; corresponde al identificador YOLO 0. |
| UMID | `ep` | `celulas_epiteliales` | Células epiteliales | 437 | Clase epitelial completa; corresponde al identificador YOLO 2. |

## Reglas de consolidación

- Conservar `raw_class`, fuente y clase canónica en cada objeto.
- No añadir bacterias ni otras categorías ausentes de las anotaciones verificadas.
- No tratar `epithn` como sinónimo de `epith`: objeto y núcleo son objetivos distintos en USE.
- La compatibilidad semántica entre USE y UMID permite comparar las tres clases compartidas, pero no demuestra por sí sola compatibilidad de dominio, protocolo o estilo de anotación.
- Los conteos de UMID se obtuvieron directamente de las 2,979 líneas de objeto YOLO: `pus` 986, `rbc` 1,556 y `ep` 437.

## Procedencia de los conteos

Los conteos USE proceden de la auditoría local de XML Pascal VOC. El total UMID procede del recuento directo de líneas válidas de las etiquetas YOLO por split. Los datasets y derivados no se redistribuyen en el repositorio público.
