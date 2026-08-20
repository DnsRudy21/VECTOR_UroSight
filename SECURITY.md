# Security policy

## Supported version

Security updates target the latest revision of the `main` branch. Experimental builds and third-party models are not covered by a support guarantee.

## Reporting a vulnerability

Please report security concerns privately to the project owner before opening a public issue. Do not include credentials, patient information, private microscopy images, or exploitable details in public reports.

## Credentials and clinical data

- Store service credentials only in a local `.env` file.
- Never commit `.env`, API keys, patient records, model-service responses containing private data, or identifiable images.
- Use only de-identified demonstration data unless an approved institutional process provides the required authorization and safeguards.

VECTOR UroSight is an academic prototype and is not a clinical information system or diagnostic device.
