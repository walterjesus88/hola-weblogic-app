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

try:
    # Obtener versiones actuales
    current_versions = get_app_versions(APP_NAME)
    current_versions.sort()  # Ordenar para tener las más antiguas primero
    
    print("Current versions:", current_versions)
    
    # PASO 1: LIMPIAR VERSIONES ANTIGUAS SI HAY 2 O MÁS
    # ==================================================
    # WebLogic permite máximo 2 versiones por defecto
    # Si ya hay 2, eliminamos la más antigua para hacer espacio
    
    if len(current_versions) >= 2:
        # Eliminar las versiones más antiguas, dejando solo la última
        versions_to_remove = current_versions[:-1]  # Todas excepto la última
        
        print("Cleaning old versions to make space...")
        for old_version in versions_to_remove:
            print("  Removing:", old_version)
            try:
                stopApplication(old_version)
                undeploy(old_version, targets=cfg['target'])
                print("  OK - Removed:", old_version)
            except Exception, ex:
                print("  WARNING - Could not remove %s: %s" % (old_version, str(ex)))
    
    # Refrescar la lista después de limpiar
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
    
    print("Starting new version...")
    startApplication(versioned_app_name)
    
    print("SUCCESS - New version is LIVE")
    print("  Name:", versioned_app_name)
    print("  Access at: %s" % CONTEXT_ROOT)
    
    # PASO 3: LIMPIAR VERSIONES ADICIONALES (opcional)
    # =================================================
    # Mantener solo las últimas 2 versiones como política de retención
    
    all_versions = get_app_versions(APP_NAME)
    all_versions.sort()
    
    if len(all_versions) > 2:
        excess_versions = all_versions[:-2]  # Todas excepto las últimas 2
        print("Final cleanup - removing excess versions...")
        
        for old_ver in excess_versions:
            print("  Removing:", old_ver)
            try:
                stopApplication(old_ver)
                undeploy(old_ver, targets=cfg['target'])
            except:
                pass
    
    print("DEPLOYMENT COMPLETED SUCCESSFULLY")

except Exception, e:
    print("ERROR during deploy")
    print("Error:", str(e))
    dumpStack()
    
    # ROLLBACK: Reactivar la última versión estable
    current_versions = get_app_versions(APP_NAME)
    if current_versions:
        latest_stable = current_versions[-1]
        print("ROLLBACK: Reactivating", latest_stable)
        try:
            startApplication(latest_stable)
            print("Rollback successful")
        except:
            print("Rollback failed")
    
    sys.exit(1)

disconnect()
sys.exit(0)