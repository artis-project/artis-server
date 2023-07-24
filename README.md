# artis-server

The artis-project/artis-server repository is a python flask api that provides a REST api to a deployed smart contract. This application is designed to be hosted on google cloud as a cloud run service.

## Prerequisites

- google cloud account
- [gcloud cli installed](https://cloud.google.com/sdk/docs/install) & authenticated
- [github cli installed](https://cli.github.com/) & authenticated

## External services setup

### Ethereum managed fullnode

[alchemy](https://www.alchemy.com/) is a web3 development platform that offers managed services such as an ethereum fullnode. For this project we are using this service and have followed the following steps:

- Sign up and create a new app
- copy the provider-url for later (https://eth-sepolia.g.alchemy.com/v2/<api-key>)

### Metamask accounts & wallets

[metamask](https://metamask.io/) is a web3 wallet provider that simplifies blockchain wallet and account creation. For this project we need multiple accounts that are easily created with metamask.

- Sign up for metamask
- create accounts for
    - the smartcontract admin
    - the logger
- note the private key for later

### Etherscan

[etherscan](https://etherscan.io/apis) is an ethereum block explorer that provides an api that this project is using to dynamically access the abi of the deployed artis-smartcontract.

- create an etherscan account
- note the api-key for later

### Github Variables

Because the services in this project are intertwined we use github variables at an organization level to share two pieces of information. Firstly the address of the deployed smartcontract that is consumed by the *artis-server* to interact with the newest deployed contract and secondly the API url of the deployed *artis-server* instance that is consumed by the *artis-rockpi-logger* in order to query the newest version of the deployed REST API.

To create or update these variables manually:

```bash
gh variable set ARTIS_API_URL --org artis-project
gh variable set ARTIS_SC_ADDRESS --org artis-project
```

In our CI/CD setup these variables are updated (automatically) and queried by each service independently. In order to authenticate we are using personal access tokens:

- create a fine-grained personal access token to allow reading and writing to variables (if you want you can seperate read and write into two tokens)
    - to allow personal access tokens: artis-project > settings > Third-party Access > Personal access tokens > Allow access via fine-grained access tokens > do not require administrator approval > Allow access via personal access tokens (classic) > enroll
        - or ask an administrator to do this for you
    - to create: <your github account> > settings > Developer settings > Personal access tokens > Fine-grained tokens > generate new token
        - name: ACCESS_ARTIS_ORG_VARIABLES
        - Resource owner: artis-project
        - Permissions > Organizations permissions > Variables > Read and write
        - generate token and note for later

## Dependencies

All dependencies are defined in the requirements.txt file. To install them run

```bash
python -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
```

## Local Development

The flask service can be run locally with the command:

```bash
source ./.venv/bin/activate
python app.py
```

If you run the service locally you need to set some environment variables in a .env file:

`.env`
---
SMARTCONTRACT_ADMIN_PRIVATE_KEY = \<smartcontract-admin-private-key\>

HTTP_PROVIDER_URL = \<fullnode-rpc-endpoint\>

ETHERSCAN_API_KEY = \<etherscan-api-key\>

GITHUB_VARIABLES_ACCESS_TOKEN = \<personal access token to read org variables\>

CHAIN_ID = “11155111”

GITHUB_ORG_NAME = “artis-project”

GITHUB_SC_ADDRESS_VARIABLE_NAME = “ARTIS_SC_ADDRESS”

---
## Deployment

- for this we should create a new project in google cloud after (creation you need to [enable billing](https://cloud.google.com/billing/docs/how-to/modify-project?hl=de))

```bash
gcloud projects create my-artis-project --name="artis project" --set-as-default
```

- next we need to allow the necessary apis

```bash
gcloud services enable \
	run.googleapis.com \
	artifactregistry.googleapis.com \
	secretmanager.googleapis.com \
	cloudbuild.googleapis.com
```

- add secretsmanager permissions to the default service account
    
    ```bash
     copy email of default service account
    gcloud iam service-accounts list
    gcloud projects add-iam-policy-binding my-artis-project --member serviceAccount:\<email\> --role=roles/secretmanager.secretAccessor
    ```
    
- create secrets that are being consumed by the service. for each \<name\> replace \<value\> with the secret and execute the command below.
    - \<name\> ⇒ alchemy-provider-url
    - \<name\> ⇒  smartcontract-admin-private-key (must be prefixed with 0x)
    - \<name\> ⇒ github-variables-access-token
    - \<name\> ⇒ etherscan-api-key

```bash
 create secrets for Private Key and Github token
printf "<value>" | gcloud secrets create <name> --data-file=-
```

- at this point we are ready to deploy the service. To customize the deploy command reference the [gcloud docs](https://cloud.google.com/sdk/gcloud/reference/run/deploy)

```bash
gcloud run deploy artis-api \
	--source . \
	--set-env-vars=CHAIN_ID=11155111,GITHUB_ORG_NAME=my-artis-project,GITHUB_SC_ADDRESS_VARIABLE_NAME=ARTIS_SC_ADDRESS \
	--set-secrets=SMARTCONTRACT_ADMIN_PRIVATE_KEY=smartcontract-admin-private-key:latest,HTTP_PROVIDER_URL=alchemy-provider-url:latest,ETHERSCAN_API_KEY=etherscan-api-key:latest,GITHUB_VARIABLES_ACCESS_TOKEN=github-variables-access-token:latest \
	--max-instances=3
```

- when the command has successfully completed, copy the http url of the cloud service and set the github variable to this url (is used by the logger)

```bash
gh variable set ARTIS_API_URL --org my-artis-project
```

- If you want you can add continuous deployment to this service on the google cloud console you can check out this resource [gcloud docs](https://cloud.google.com/run/docs/quickstarts/deploy-continuously?hl=de)


## Learn More
If you want to know more about the project check out the full project report in the [artis-thesis](https://github.com/artis-project/artis-thesis) repository
