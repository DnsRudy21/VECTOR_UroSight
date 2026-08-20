# Contribuir a VECTOR UroSight

Gracias por considerar una contribución. Este es un proyecto académico de visión por computadora y toda modificación debe preservar la trazabilidad, la revisión humana y las limitaciones clínicas documentadas.

## Flujo recomendado

1. Cree una rama desde `main`.
2. Mantenga separados dominio, inferencia, procesamiento, reglas, interfaz y reportes.
3. Añada o actualice pruebas para cada cambio relevante.
4. Ejecute `python -m pytest -q` antes de enviar un pull request.
5. Documente cambios de arquitectura o metodología en `docs/DECISIONS.md`.

## Reglas de datos y seguridad

- No incluya datos clínicos identificables, imágenes privadas, datasets, pesos ni credenciales.
- No afirme validación clínica o capacidad diagnóstica.
- Use datos sintéticos o expresamente autorizados en pruebas y capturas.
- No adapte el modelo o umbral usando el conjunto de test publicado.

## Licencia de contribuciones

Al enviar una contribución, acepta que se distribuya bajo GNU AGPL-3.0. Identifique claramente cualquier material de terceros y su licencia.
