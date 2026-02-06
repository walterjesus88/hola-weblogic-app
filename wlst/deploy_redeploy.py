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
    print('❌ Ambiente invalido')
    sys.exit(1)

cfg = ENVS[ENV]

# Nombre fijo de la app (sin versión)
APP_NAME = "%s-%s" % (APP_BASE, ENV)  # hola-dev
CONTEXT_ROOT = '/%s' % APP_BASE  # /hola

print("====================================")
print(" ENV         :", ENV)
print(" APP NAME    :", APP_NAME)
print(" VERSION     :", VERSION)
print(" CONTEXT ROOT:", CONTEXT_ROOT)
print(" WAR         :", WAR_PATH)
print(" TARGET      :", cfg['target'])
print("====================================")

connect(WLS_USER, WLS_PASS, cfg['url'])

# Variable para guardar estado de rollback
previous_war_path = None

try:
    # Verificar si existe la app
    appExists = False
    try:
        appDeployment = getMBean('/AppDeployments/' + APP_NAME)
        if appDeployment:
            appExists = True
            # Guardar el path del WAR anterior para rollback
            previous_war_path = appDeployment.getSourcePath()
            print("🟢 App exists. Previous WAR:", previous_war_path)
    except:
        print("🆕 App doesn't exist")
    
    if appExists:
        # ACTUALIZACIÓN: Undeploy + Deploy
        print("🔄 Updating application...")
        
        print("🛑 Stopping current version...")
        stopApplication(APP_NAME)
        
        print("🗑️ Undeploying current version...")
        undeploy(APP_NAME, targets=cfg['target'])
    
    # Deploy la nueva versión (funciona tanto para inicial como para update)
    print("🚀 Deploying version %s..." % VERSION)
    deploy(
        appName=APP_NAME,
        path=WAR_PATH,
        targets=cfg['target'],
        upload='false',
        stageMode='nostage',
        contextRoot=CONTEXT_ROOT
    )
    
    print("✅ Deployment successful")
    
    print("🔄 Starting application...")
    startApplication(APP_NAME)
    
    print("🎉 Application is LIVE")
    print("   Name: %s" % APP_NAME)
    print("   Version: %s" % VERSION)
    print("   Context: %s" % CONTEXT_ROOT)

except Exception, e:
    print("❌ ERROR during deploy")
    print("Error:", str(e))
    dumpStack()
    
    # ROLLBACK si había una versión anterior
    if previous_war_path:
        print("↩️ ROLLBACK: Redeploying previous version...")
        try:
            deploy(
                appName=APP_NAME,
                path=previous_war_path,
                targets=cfg['target'],
                upload='false',
                stageMode='nostage',
                contextRoot=CONTEXT_ROOT
            )
            startApplication(APP_NAME)
            print("✅ Rollback successful - previous version restored")
        except Exception, rollback_error:
            print("❌ Rollback FAILED:", str(rollback_error))
            print("⚠️ MANUAL INTERVENTION REQUIRED")
    
    sys.exit(1)

disconnect()
sys.exit(0)