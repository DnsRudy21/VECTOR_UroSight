# Publicación en GitHub

Destino configurado: [DnsRudy21/VECTOR_UroSight](https://github.com/DnsRudy21/VECTOR_UroSight). Se publica el código fuente, documentación, pruebas, herramientas y recursos visuales propios.

## Una vez por equipo

1. Instalar Git y Python 3.11.
2. Instalar dependencias: `python -m pip install -r requirements-dev.txt`. Si usa `.venv`, instalar allí; el publicador la detecta automáticamente.
3. Configurar nombre y correo de Git. Puede usar el correo privado `noreply` que muestra GitHub en sus ajustes de cuenta.
4. Iniciar sesión mediante Git Credential Manager o una clave SSH. No escriba tokens en el script, en `.env.example` ni en la URL del remoto.

## Publicar con doble clic

Abra `publish.cmd` desde la raíz. El script:

1. Verifica que la rama sea `main` y el destino coincida con este repositorio.
2. Revisa archivos publicables e historial local alcanzable, sin imprimir posibles valores secretos.
3. Ejecuta las pruebas y comprueba errores de espacios en los cambios.
4. Consulta el remoto y se detiene si su estado no es antecesor de la rama local.
5. Añade los cambios, crea un commit si hace falta y ejecuta un push normal.

No instala programas, no cambia la visibilidad del repositorio y no sobrescribe el historial remoto. La autenticación puede requerir iniciar sesión en el primer uso. Los cambios posteriores también se incluyen: revise su contenido antes de abrir el publicador.

Para revisar sin crear commits ni enviar archivos:

```powershell
powershell -NoProfile -File scripts/publish.ps1 -CheckOnly
```

Si falla una prueba, la revisión detecta contenido inesperado o el remoto diverge, resuelva el problema antes de reintentar. Un push fallido puede dejar un commit local listo para un nuevo intento. No use `--force` para eludir estas comprobaciones.

## Seguridad de la distribución

`tools/publication_check.py` usa una lista de ubicaciones y formatos permitidos, límite de 5 MiB por archivo y patrones de credenciales conocidos. Incluye objetos y mensajes del historial alcanzable por las referencias Git locales. No analiza ramas remotas no descargadas, archivos externos ni credenciales de formatos desconocidos; tampoco sustituye revisión humana de imágenes o datos identificables.

`.gitignore` excluye datasets, pesos, secretos, salidas, cachés y material privado. Un archivo ya rastreado no se protege solo con `.gitignore`; el control de publicación también examina esos archivos.

Si aparece una credencial real, revóquela o rótela antes de sanear el historial. Véase la [guía oficial de GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

La auditoría de dependencias se puede repetir con `pip-audit` en un entorno de mantenimiento:

```powershell
python -m pip_audit -r requirements.txt -r requirements-local.txt -r requirements-dev.txt -r requirements-build.txt
```

## Licencias y alcance

Se conserva GNU AGPL-3.0-only y el archivo de atribuciones. Ultralytics ofrece [AGPL y licencia Enterprise](https://www.ultralytics.com/license); la alternativa comercial no significa que todo uso comercial bajo AGPL esté prohibido. Qt/PySide6 conserva sus [condiciones y avisos propios](https://doc.qt.io/qtforpython-6/licenses.html).

Esta entrega no redistribuye datasets, pesos ni ejecutables. Para publicarlos por separado hay que comprobar los derechos de cada componente y cumplir sus obligaciones. El nombre de una universidad en agradecimientos no implica respaldo institucional ni autorización para usar sus marcas.

La revisión técnica reduce riesgos de publicación; no acredita titularidad de aportaciones de terceros ni constituye certificación jurídica o clínica. El responsable debe contar con los derechos de publicación del material propio y de sus colaboradores.
