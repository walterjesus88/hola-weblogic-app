import sys

ENV = sys.argv[1]
WLS_USER = sys.argv[2]
WLS_PASS = sys.argv[3]
APP_BASE = sys.argv[4]
VERSION =  sys.argv[5] #"fail"
WAR_PATH = sys.argv[6]

# if VERSION == "fail":
#     raise Exception("Forced failure for rollback test")


# ENVS = {
#     'dev':  {'url': 't3://localhost:7001', 'target': 'AdminServer'},
#     'qa':   {'url': 't3://localhost:7001', 'target': 'AdminServer'},
#     'prod': {'url': 't3://localhost:7001', 'target': 'AdminServer'}
# }

ENVS = {
    'dev':  {'url': 't3://my-weblogic-dev:7001', 'container': 'my-weblogic-dev','target': 'AdminServer'},
    'qa':   {'url': 't3://my-weblogic-qa:7001', 'container': 'my-weblogic-qa','target': 'AdminServer'},
    'prod': {'url': 't3://my-weblogic-prod:7001', 'container': 'my-weblogic-prod','target': 'AdminServer'}
}

if ENV not in ENVS:
    print('❌ Ambiente inválido')
    sys.exit(1)

cfg = ENVS[ENV]

NEW_APP = "%s-%s-%s" % (APP_BASE, ENV, VERSION)

print("====================================")
print(" ENV        :", ENV)
print(" NEW APP    :", NEW_APP)
print(" WAR        :", WAR_PATH)
print(" TARGET     :", cfg['target'])
print("====================================")

connect(WLS_USER, WLS_PASS, cfg['url'])

def get_active_versions(base):
    apps = []
    for app in cmo.getAppDeployments():
        name = app.getName()
       
        if name.startswith(base + "-" + ENV):
            apps.append(name)
    return apps

try:
    active_apps = get_active_versions(APP_BASE)

    print("🟢 Active apps:", active_apps)

    # Context root único por ambiente
    context_root = '/%s-%s' % (APP_BASE, ENV)  # 👈 /hola-dev, /hola-qa, /hola-prod

    print("🚀 Deploying new version...")
    deploy(
        appName=NEW_APP,
        path=WAR_PATH,
        targets=cfg['target'],
        upload='false',
        stageMode='nostage',
        contextRoot=context_root  # 👈 CLAVE
    )

    print("✅ Deployment OK")

    print("🔄 Activating new version")
    startApplication(NEW_APP)

    print("🧹 Removing old versions")
    for app in active_apps:
        print("🗑️ Undeploy:", app)
        undeploy(app, targets=cfg['target'])

    print("🎉 Release completed")

except Exception, e:
    print("❌ ERROR during deploy, rolling back")
    print(e)
    dumpStack()

    print("↩️ Rolling back to previous version")
    for app in active_apps:
        try:
            startApplication(app)
        except:
            pass

    sys.exit(1)

disconnect()
sys.exit(0)
