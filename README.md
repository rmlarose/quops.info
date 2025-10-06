# QuOps.Info

A community-driven web app to track state-of-the-art quantum computations.

## Developer information

### Getting started

#### Database

In the root directory of the repository, create a `.streamlit/secrets.toml` file with the following contents:

```text
[mongo]
host = <host information from admin>
database = <database information from admin>
collection = <collection information from admin>
```

To connect to the database, network access must be granted to your IP(v4) address. Contact an admin for setup.