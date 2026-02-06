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

APP_NAME = "%s-%s" % (APP_BASE, ENV)  # hola-dev
APP_VERSION = "v%s" % VERSION  # v60, v61, v62...
CONTEXT_ROOT = '/%s' % APP_BASE  # /hola

print("====================================")
print(" ENV         :", ENV)
print(" APP NAME    :", APP_NAME)
print(" APP VERSION :", APP_VERSION)
print(" CONTEXT ROOT:", CONTEXT_ROOT)
print(" WAR         :", WAR_PATH)
print("====================================")

connect(WLS_USER, WLS_PASS, cfg['url'])

def get_app_versions(appName):
    """Obtiene todas las versiones desplegadas de una app"""
    versions = []
    try:
        cd('/AppDeployments')
        apps = ls(returnMap='true')
        for app in apps:
            if app.startswith(appName):
                versions.append(app)
    except:
        pass
    return versions

try:
    # Obtener versiones actuales
    current_versions = get_app_versions(APP_NAME)
    print("🟢 Current versions:", current_versions)
    
    # Nombre completo con versión: hola-dev#v60
    versioned_app_name = "%s#%s" % (APP_NAME, APP_VERSION)
    
    print("🚀 Deploying new version:", versioned_app_name)
    
    # Deploy la nueva versión (coexiste con las anteriores)
    deploy(
        appName=versioned_app_name,
        path=WAR_PATH,
        targets=cfg['target'],
        upload='false',
        stageMode='nostage',
        contextRoot=CONTEXT_ROOT
    )
    
    print("🔄 Starting new version...")
    startApplication(versioned_app_name)
    
    print("✅ New version deployed and started")
    
    # Limpiar versiones antiguas (mantener solo las últimas 2)
    all_versions = get_app_versions(APP_NAME)
    all_versions.sort()  # Ordenar por nombre
    
    if len(all_versions) > 2:
        versions_to_remove = all_versions[:-2]  # Todas excepto las últimas 2
        print("🧹 Cleaning old versions:", versions_to_remove)
        
        for old_version in versions_to_remove:
            try:
                print("🗑️ Removing:", old_version)
                stopApplication(old_version)
                undeploy(old_version, targets=cfg['target'])
            except Exception, ex:
                print("⚠️ Failed to remove %s: %s" % (old_version, str(ex)))
    
    print("🎉 Deployment completed successfully")
    print("   Live at: %s (version %s)" % (CONTEXT_ROOT, APP_VERSION))

except Exception, e:
    print("❌ ERROR during deploy")
    print("Error:", str(e))
    dumpStack()
    
    # Rollback: activar la versión anterior si existe
    if current_versions:
        latest_version = current_versions[-1]
        print("↩️ Rolling back to:", latest_version)
        try:
            startApplication(latest_version)
            print("✅ Rollback successful")
        except:
            print("❌ Rollback failed")
    
    sys.exit(1)

disconnect()
sys.exit(0)