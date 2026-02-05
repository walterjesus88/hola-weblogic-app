# deploy_app.py
import sys

# argumentos desde Jenkins
ENV = sys.argv[1]          # dev | qa | prod
WLS_USER = sys.argv[2]
WLS_PASS = sys.argv[3]
WAR_PATH = sys.argv[4]
APP_NAME = sys.argv[5]

# configuración por ambiente
ENVS = {
    'dev': {
        'url': 't3://localhost:7001',
        'target': 'AdminServer'
    },
    'qa': {
        'url': 't3://localhost:7001',
        'target': 'AdminServer'
    },
    'prod': {
        'url': 't3://localhost:7001',
        'target': 'AdminServer'
    }
}

if ENV not in ENVS:
    print('❌ Ambiente inválido:', ENV)
    sys.exit(1)

cfg = ENVS[ENV]

print('====================================')
print(' Deploying to environment:', ENV)
print(' URL:', cfg['url'])
print(' Target:', cfg['target'])
print(' WAR:', WAR_PATH)
print(' USER:',WLS_USER)
print(' PASS:',WLS_PASS)
print('====================================')

# conexión
connect(WLS_USER, WLS_PASS, cfg['url'])

try:
    if appExists(APP_NAME):
        print('🔁 Redeploying application:', APP_NAME)
        undeploy(APP_NAME, targets=cfg['target'])
    
    print('🚀 Deploying application:', APP_NAME)
    deploy(
        appName=APP_NAME,
        path=WAR_PATH,
        targets=cfg['target'],
        upload='false',
        stageMode='nostage'
    )

    print('✅ Deployment successful')

except Exception, e:
    print('❌ Deployment failed')
    print(e)
    dumpStack()
    sys.exit(1)

disconnect()
sys.exit(0)
