import sys

ENV = sys.argv[1]
APP_NAME = sys.argv[2]
WAR_PATH = sys.argv[3]
WLS_USER = sys.argv[4]
WLS_PASS = sys.argv[5]

ENVS = {
    'dev':  {'url': 't3://localhost:7001', 'target': 'AdminServer'},
    'qa':   {'url': 't3://localhost:7001', 'target': 'AdminServer'},
    'prod': {'url': 't3://localhost:7001', 'target': 'AdminServer'}
}

cfg = ENVS[ENV]

connect(WLS_USER, WLS_PASS, cfg['url'])

print('🔍 Searching previous deployments...')
existing_apps = []
for app in cmo.getAppDeployments():
    if app.getName().startswith(APP_NAME.split('-')[0] + '-' + ENV):
        existing_apps.append(app.getName())

previous_app = sorted(existing_apps)[-1] if existing_apps else None
print('📦 Previous app:', previous_app)

try:
    print('🚀 Deploying new version:', APP_NAME)
    deploy(APP_NAME, WAR_PATH, targets=cfg['target'], upload='false')

    if previous_app:
        print('🧹 Removing previous version:', previous_app)
        undeploy(previous_app, targets=cfg['target'])

    print('✅ Deployment successful')

except:
    print('❌ Deployment failed — rollback')

    if previous_app:
        print('↩️ Rolling back to:', previous_app)
        startApplication(previous_app)

    dumpStack()
    exit(1)

disconnect()
exit(0)
