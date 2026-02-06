import sys

ENV = sys.argv[1]
WLS_USER = sys.argv[2]
WLS_PASS = sys.argv[3]
APP_BASE = sys.argv[4]
VERSION = sys.argv[5]
WAR_PATH = sys.argv[6]

ENVS = {
    'dev':  {'url': 't3://my-weblogic-dev:7001', 'target': 'AdminServer'},
    'qa':   {'url': 't3://my-weblogic-qa:7001', 'target': 'AdminServer'},
    'prod': {'url': 't3://my-weblogic-prod:7001', 'target': 'AdminServer'}
}

if ENV not in ENVS:
    print('❌ Ambiente inválido')
    sys.exit(1)

cfg = ENVS[ENV]

# Usar NOMBRE FIJO (no incluir versión en el nombre de la app)
APP_NAME = "%s-%s" % (APP_BASE, ENV)  # 👈 hola-prod (sin número de versión)
#CONTEXT_ROOT = '/%s' % APP_BASE  # /hola

print("====================================")
print(" ENV         :", ENV)
print(" APP NAME    :", APP_NAME)
print(" VERSION     :", VERSION)
#print(" CONTEXT ROOT:", CONTEXT_ROOT)
print(" WAR         :", WAR_PATH)
print("====================================")

connect(WLS_USER, WLS_PASS, cfg['url'])

try:
    # Verificar si la app ya existe
    appExists = False
    try:
        appDeployment = getMBean('/AppDeployments/' + APP_NAME)
        if appDeployment:
            appExists = True
            print("🟢 App exists - doing PRODUCTION REDEPLOYMENT")
    except:
        print("🆕 App doesn't exist - doing INITIAL DEPLOYMENT")
    
    if appExists:
        # PRODUCTION REDEPLOYMENT (zero downtime)
        print("🚀 Starting production redeployment...")
        redeploy(
            appName=APP_NAME,
            planPath=WAR_PATH,
            upload='false'
        )
        print("✅ Production redeployment completed (zero downtime)")
    else:
        # INITIAL DEPLOYMENT
        print("🚀 Deploying for first time...")
        deploy(
            appName=APP_NAME,
            path=WAR_PATH,
            targets=cfg['target'],
            upload='false',
            stageMode='nostage',
            #contextRoot=CONTEXT_ROOT
        )
        startApplication(APP_NAME)
        print("✅ Initial deployment completed")

    #print("🎉 Application is live at:", CONTEXT_ROOT)

except Exception, e:
    print("❌ ERROR during deploy")
    print(e)
    dumpStack()
    sys.exit(1)

disconnect()
sys.exit(0)