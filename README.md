# Tilapia

![](https://github.com/huazhouwang/tilapia/actions/workflows/test-runner.yml/badge.svg)

A multi-chain wallet (or library), written in python,
supports btc, bch, ltc, eth, bsc, etc.

## Get Start
### Local
1. Prepare python env, recommend >= 3.8
2. Install requirements
    * `pip install -r requirements.txt` (optional, use only as library)
    * `pip install -r requirements-optional.txt` (optional, api server needs)
    * `pip install -r requiremetns-dev.txt` (optional, develop needs)
3. Play with restful api
   * `./scripts/run.sh`
   * `curl --request GET --url http://127.0.0.1:8000/ping`
   * Now you can test all apis under 'wallet/api'

### Docker
1. `cd $my_repo_dir`
2. `docker build -t tilapia -f ./docker/Dockerfile .`
3. `docker run -d -it -v $(pwd):/repo --name tilapia -p 127.0.0.1:8000:8000 tilapia`

> Forked from [OneKeyHQ/electrum](https://github.com/OneKeyHQ/electrum) and cleaned up deeply.
