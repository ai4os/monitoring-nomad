# Nomad monitoring

Scripts to gather Nomad metrics (coming both from Nomad and from PAPI) and expose them to Grafana.

You can define environment variables in a `.env` file.

```bash
export NOMAD_ADDR=https://193.146.75.205:4646
export NOMAD_CACERT=/path/to/nomad-ca.pem
export NOMAD_CLIENT_CERT=/path/to/cli.pem
export NOMAD_TLS_SERVER_NAME=node-ifca-0
```