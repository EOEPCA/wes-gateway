"""Offline manifest checks. Requires helm and Python's PyYAML package."""
from pathlib import Path
import ast
import subprocess
import yaml

CHART = Path(__file__).resolve().parents[1]


def render(*args, error=None, namespace='workflows'):
    result = subprocess.run(
        ['helm', 'template', 'wes', str(CHART), '--namespace', namespace, *args],
        text=True, capture_output=True,
    )
    if error:
        assert result.returncode != 0, 'Expected rendering to fail'
        assert error in result.stderr, result.stderr
        return
    assert result.returncode == 0, result.stderr
    docs = [d for d in yaml.safe_load_all(result.stdout) if d]
    identities = [(d['kind'], d['metadata']['name']) for d in docs]
    assert len(identities) == len(set(identities))
    for doc in docs:
        if doc['kind'] not in ('Deployment', 'DaemonSet'):
            continue
        spec = doc['spec']['template']['spec']
        labels = doc['spec']['template']['metadata']['labels']
        assert all(labels.get(k) == v for k, v in doc['spec']['selector']['matchLabels'].items())
        for container in spec.get('initContainers', []) + spec['containers']:
            env = container.get('env', [])
            assert len(env) == len({e['name'] for e in env}), 'Duplicate environment variable'
            script = (container.get('args') or container.get('command'))[-1]
            subprocess.run(['sh', '-n'], input=script, text=True, check=True)
            if "python - <<'PY'" in script:
                patch = script.split("python - <<'PY'\n", 1)[1].split('\nPY', 1)[0]
                ast.parse(patch)
    return docs


def one(docs, kind, suffix=''):
    return next(d for d in docs if d['kind'] == kind and d['metadata']['name'].endswith(suffix))


def container(doc):
    return doc['spec']['template']['spec']['containers'][0]


def env(doc):
    return {e['name']: e for e in container(doc)['env']}


def example(name):
    return ['-f', str(CHART / 'examples' / f'{name}.yaml')]


def main():
    default = render()
    assert {d['kind'] for d in default} == {'Deployment', 'Service', 'ServiceAccount', 'Role', 'RoleBinding'}
    server = one(default, 'Deployment')
    script = container(server)['args'][0]
    assert '--bypass_celery' in script
    assert 'AWS_ENDPOINT_URL' not in env(server)
    assert 'AWS_ACCESS_KEY_ID' not in script
    assert 'processing-manager' not in script
    account = one(default, 'ServiceAccount')['metadata']['name']
    assert server['spec']['template']['spec']['serviceAccountName'] == account
    assert one(default, 'RoleBinding')['subjects'][0]['name'] == account
    assert all(server['spec']['template']['metadata']['labels'][k] == v for k, v in one(default, 'Service')['spec']['selector'].items())

    custom = render('--set', 'service.port=80,serviceAccount.create=false,serviceAccount.name=external,fullnameOverride=my-wes')
    assert not any(d['kind'] == 'ServiceAccount' for d in custom)
    assert one(custom, 'RoleBinding')['subjects'][0]['name'] == 'external'
    assert one(custom, 'Service')['spec']['ports'][0]['port'] == 80
    assert container(one(custom, 'Deployment'))['ports'][0]['containerPort'] == 8080

    celery = render(*example('celery'), *example('minio'))
    deployments = [d for d in celery if d['kind'] == 'Deployment']
    assert len(deployments) == 2
    for dep in deployments:
        assert env(dep)['TOIL_WES_BROKER_URL']['valueFrom']['secretKeyRef']['name'] == 'toil-broker'
        assert env(dep)['AWS_ENDPOINT_URL']['value'] == 'http://s3-service.zoo.svc.cluster.local:9000'
        assert dep['spec']['template']['spec']['volumes'][0]['persistentVolumeClaim']['claimName'] == 'toil-workflows'
        assert '--bypass_celery' not in container(dep)['args'][0]
    assert not any(d['kind'] == 'PersistentVolumeClaim' for d in celery)

    url = render('--set', 'celery.enabled=true,celery.brokerUrl=amqp://broker:5672,sharedStorage.enabled=true')
    assert env(one(url, 'Deployment', 'celery'))['TOIL_WES_BROKER_URL']['value'] == 'amqp://broker:5672'
    assert one(url, 'PersistentVolumeClaim')['metadata']['name'] == 'wes-toil-wes-shared'

    pull_args = ['--set', 'imagePullSecrets[0].name=registry-one,imagePullSecrets[1].name=registry-two']
    private = render(*example('celery'), *pull_args)
    expected_secrets = [{'name': 'registry-one'}, {'name': 'registry-two'}]
    assert one(private, 'ServiceAccount')['imagePullSecrets'] == expected_secrets
    for dep in (d for d in private if d['kind'] == 'Deployment'):
        spec = dep['spec']['template']['spec']
        assert spec['imagePullSecrets'] == expected_secrets
        assert spec['serviceAccountName'] == one(private, 'ServiceAccount')['metadata']['name']
    assert 'imagePullSecrets' not in one(default, 'ServiceAccount')
    external = render(*pull_args, '--set', 'serviceAccount.create=false,serviceAccount.name=external')
    assert not any(d['kind'] == 'ServiceAccount' for d in external)
    assert one(external, 'Deployment')['spec']['template']['spec']['imagePullSecrets'] == expected_secrets

    nfs = render(*example('nfs'))
    pv = one(nfs, 'PersistentVolume')
    pvc = one(nfs, 'PersistentVolumeClaim')
    assert pv['spec']['persistentVolumeReclaimPolicy'] == 'Retain'
    assert pvc['spec']['storageClassName'] == ''
    assert all(pv['metadata']['labels'][k] == v for k, v in pvc['spec']['selector']['matchLabels'].items())
    other = render(*example('nfs'), namespace='other')
    assert pv['metadata']['name'] != one(other, 'PersistentVolume')['metadata']['name']
    assert pv['metadata']['labels']['toil-wes/pv-binding'] != one(other, 'PersistentVolume')['metadata']['labels']['toil-wes/pv-binding']
    assert 'TOIL_KUBERNETES_HOST_PATH=/mnt/toil-shared' in container(one(nfs, 'Deployment'))['args'][0]
    explicit = render(*example('nfs'), '--set', 'hostPath=/mnt/explicit,sharedStorage.storageClass=efs')
    assert not any(d['kind'] == 'PersistentVolume' for d in explicit)
    assert 'TOIL_KUBERNETES_HOST_PATH=/mnt/explicit' in container(one(explicit, 'Deployment'))['args'][0]

    assert render('--set', 'enabled=false') == []
    render('--set', 'celery.enabled=true,celery.brokerUrl=amqp://broker:5672', error='requires sharedStorage.enabled')
    render('--set', 'celery.enabled=true,sharedStorage.enabled=true', error='external broker')
    render('--set', 'sharedStorage.enabled=true,sharedStorage.create=false', error='existingClaim is required')
    render('--set', 'sharedStorage.enabled=true,stateStore=/elsewhere', error='must be within')
    render('--set', 'nfsMount.enabled=true', error='nfsMount.server is required')
    render('--set', 's3.realaws=false', error='s3.host is required')
    render('--set', 'serviceAccount.create=false', error='serviceAccount.name is required')
    render('--set', 'replicaCount=2', error='requires celery.enabled')
    render('--set', 'service.port=0', error='port')
    render('--set', 'toilWes.enabled=true', error='toilWes')
    render('--set', 'fullnameOverride=' + 'a' * 63, *example('celery'))
    render('--set-string', 'env.TOIL_APPLIANCE_SELF=example/toil:custom')
    print('PASS: default, Celery, S3, NFS, naming, wiring, embedded scripts and invalid configuration checks')


if __name__ == '__main__':
    main()
