import sys
from java.lang import Thread

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
    print('ERROR: Ambiente invalido')
    sys.exit(1)

cfg = ENVS[ENV]

APP_NAME = "%s-%s" % (APP_BASE, ENV)
APP_VERSION = "v%s" % VERSION
CONTEXT_ROOT = '/%s' % APP_BASE

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
            if app.startswith(appName + "#"):
                versions.append(app)
    except:
        pass
    return versions

def wait_for_app_state(appName, expectedState, maxWait=30):
    """
    Espera hasta que la app alcance el estado esperado
    expectedState: 'STATE_ACTIVE', 'STATE_ADMIN', 'STATE_NEW', etc.
    """
    print("  Waiting for %s to reach %s..." % (appName, expectedState))
    waited = 0
    while waited < maxWait:
        try:
            currentState = state(appName, 'AdminServer')
            print("    Current state: %s" % currentState)
            
            if expectedState in currentState:
                print("  OK - State reached: %s" % currentState)
                return True
        except:
            # La app puede no existir si fue undeployed
            if expectedState == 'REMOVED':
                print("  OK - App removed")
                return True
        
        Thread.sleep(2000)  # Esperar 2 segundos
        waited += 2
    
    print("  WARNING - Timeout waiting for state %s" % expectedState)
    return False

try:
    # Obtener versiones actuales
    current_versions = get_app_versions(APP_NAME)
    current_versions.sort()
    
    print("Current versions:", current_versions)
    
    # PASO 1: LIMPIAR VERSIONES ANTIGUAS
    # ===================================
    
    if len(current_versions) >= 2:
        versions_to_remove = current_versions[:-1]
        
        print("Cleaning old versions to make space...")
        for old_version in versions_to_remove:
            print("  Removing:", old_version)
            try:
                # Stop y esperar
                stopApplication(old_version)
                wait_for_app_state(old_version, 'STATE_ADMIN', 15)
                
                # Undeploy y esperar
                undeploy(old_version, targets=cfg['target'])
                Thread.sleep(3000)  # Espera fija después de undeploy
                
                print("  OK - Removed:", old_version)
            except Exception, ex:
                print("  WARNING:", str(ex))
                Thread.sleep(2000)
    
    # Espera adicional
    Thread.sleep(3000)
    
    # Refrescar lista
    current_versions = get_app_versions(APP_NAME)
    print("Versions after cleanup:", current_versions)
    
    # PASO 2: DESPLEGAR NUEVA VERSIÓN
    # ================================
    
    versioned_app_name = "%s#%s" % (APP_NAME, APP_VERSION)
    
    print("Deploying new version:", versioned_app_name)
    
    deploy(
        appName=versioned_app_name,
        path=WAR_PATH,
        targets=cfg['target'],
        upload='false',
        stageMode='nostage'
    )
    
    print("Deployment OK")
    Thread.sleep(3000)
    
    print("Starting new version...")
    startApplication(versioned_app_name)
    
    # Esperar a que esté activa
    if wait_for_app_state(versioned_app_name, 'STATE_ACTIVE', 30):
        print("SUCCESS - New version is LIVE")
        print("  Name:", versioned_app_name)
        print("  Access at: %s" % CONTEXT_ROOT)
    else:
        raise Exception("App did not reach ACTIVE state in time")
    
    # PASO 3: LIMPIEZA FINAL
    # =======================
    
    all_versions = get_app_versions(APP_NAME)
    all_versions.sort()
    
    if len(all_versions) > 2:
        excess_versions = all_versions[:-2]
        print("Final cleanup...")
        
        for old_ver in excess_versions:
            print("  Removing:", old_ver)
            try:
                stopApplication(old_ver)
                Thread.sleep(2000)
                undeploy(old_ver, targets=cfg['target'])
                Thread.sleep(2000)
            except:
                pass
    
    print("DEPLOYMENT COMPLETED SUCCESSFULLY")

except Exception, e:
    print("ERROR during deploy")
    print("Error:", str(e))
    dumpStack()
    
    # Esperar antes de rollback
    print("Waiting before rollback...")
    Thread.sleep(5000)
    
    # ROLLBACK
    current_versions = get_app_versions(APP_NAME)
    if current_versions:
        versioned_app_name = "%s#%s" % (APP_NAME, APP_VERSION)
        stable_versions = [v for v in current_versions if v != versioned_app_name]
        
        if stable_versions:
            latest_stable = stable_versions[-1]
            print("ROLLBACK: Reactivating", latest_stable)
            try:
                startApplication(latest_stable)
                wait_for_app_state(latest_stable, 'STATE_ACTIVE', 20)
                print("Rollback successful")
            except Exception, rollback_ex:
                print("Rollback failed:", str(rollback_ex))
    
    sys.exit(1)

disconnect()
sys.exit(0)