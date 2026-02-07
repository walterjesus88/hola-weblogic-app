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

def get_active_version(appName):
    """
    Obtiene la versión actualmente ACTIVA (no RETIRED)
    Retorna el nombre completo de la app activa o None
    """
    try:
        cd('/AppDeployments')
        apps = ls(returnMap='true')
        for app in apps:
            if app.startswith(appName + "#"):
                try:
                    cd('/AppDeployments/' + app)
                    # Verificar si está en estado activo
                    appBean = cmo
                    deploymentState = appBean.getDeploymentState()
                    cd('/')
                    
                    # STATE_ACTIVE = 2, STATE_RETIRED = 4
                    if deploymentState == 2:
                        return app
                except:
                    pass
    except:
        pass
    return None

try:
    # PASO 1: Identificar versión activa ANTES del deploy
    # ====================================================
    
    active_before = get_active_version(APP_NAME)
    print("Active version before deploy:", active_before)
    
    # Obtener todas las versiones
    current_versions = get_app_versions(APP_NAME)
    current_versions.sort()
    print("All versions:", current_versions)
    
    # PASO 2: LIMPIAR versiones RETIRED (fallidas)
    # =============================================
    
    print("Cleaning RETIRED versions...")
    for ver in current_versions:
        if ver != active_before:  # No tocar la versión activa
            try:
                cd('/AppDeployments/' + ver)
                deploymentState = cmo.getDeploymentState()
                cd('/')
                
                # Si está RETIRED (4), eliminarla
                if deploymentState == 4:
                    print("  Removing RETIRED version:", ver)
                    undeploy(ver, targets=cfg['target'])
                    Thread.sleep(2000)
            except Exception, ex:
                print("  Could not check/remove %s: %s" % (ver, str(ex)))
    
    # Refrescar lista después de limpiar
    Thread.sleep(2000)
    current_versions = get_app_versions(APP_NAME)
    current_versions.sort()
    print("Versions after cleanup:", current_versions)
    
    # PASO 3: Si hay 2 versiones, eliminar la más antigua
    # ====================================================
    
    if len(current_versions) >= 2:
        # Eliminar todas excepto la activa
        versions_to_remove = [v for v in current_versions if v != active_before]
        
        print("Making space for new version...")
        for old_version in versions_to_remove:
            print("  Removing:", old_version)
            try:
                stopApplication(old_version)
                Thread.sleep(3000)
                
                undeploy(old_version, targets=cfg['target'])
                Thread.sleep(2000)
                
                print("  OK - Removed:", old_version)
            except Exception, ex:
                print("  WARNING:", str(ex))
    
    Thread.sleep(3000)
    
    # PASO 4: DESPLEGAR NUEVA VERSIÓN
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
    
    print("Deploy completed")
    Thread.sleep(3000)
    
    print("Starting new version...")
    startApplication(versioned_app_name)
    
    # Espera simple después de start
    Thread.sleep(5000)
    
    # Verificar si se desplegó correctamente
    active_after = get_active_version(APP_NAME)
    print("Active version after deploy:", active_after)
    
    if active_after == versioned_app_name:
        print("SUCCESS - New version is LIVE")
        print("  Name:", versioned_app_name)
        print("  Access at: %s" % CONTEXT_ROOT)
    else:
        raise Exception("New version did not become active. Active: %s" % active_after)
    
    print("DEPLOYMENT COMPLETED SUCCESSFULLY")

except Exception, e:
    print("ERROR during deploy")
    print("Error:", str(e))
    dumpStack()
    
    # ROLLBACK INTELIGENTE
    # ====================
    
    print("Waiting before rollback...")
    Thread.sleep(5000)
    
    # Buscar la última versión ACTIVA (no la que acabamos de intentar)
    versioned_app_name = "%s#%s" % (APP_NAME, APP_VERSION)
    
    print("Identifying version for rollback...")
    all_versions = get_app_versions(APP_NAME)
    
    # Filtrar: solo versiones que NO sean la nueva (fallida)
    # y que NO estén RETIRED
    candidate_versions = []
    for ver in all_versions:
        if ver != versioned_app_name:
            try:
                cd('/AppDeployments/' + ver)
                deploymentState = cmo.getDeploymentState()
                cd('/')
                
                # Solo versiones ACTIVE (2) o PREPARED (1)
                if deploymentState in [1, 2]:
                    candidate_versions.append(ver)
            except:
                pass
    
    if candidate_versions:
        candidate_versions.sort()
        rollback_version = candidate_versions[-1]  # La más reciente
        
        print("ROLLBACK: Activating", rollback_version)
        try:
            # Primero detener la versión fallida
            try:
                print("Stopping failed version:", versioned_app_name)
                stopApplication(versioned_app_name)
                Thread.sleep(3000)
            except:
                pass
            
            # Activar la versión de rollback
            startApplication(rollback_version)
            Thread.sleep(3000)
            
            active_after_rollback = get_active_version(APP_NAME)
            if active_after_rollback == rollback_version:
                print("Rollback successful - Active:", rollback_version)
            else:
                print("Rollback may have failed - Active:", active_after_rollback)
                
        except Exception, rollback_ex:
            print("Rollback failed:", str(rollback_ex))
    else:
        print("No suitable version found for rollback")
        print("Available versions:", all_versions)
    
    sys.exit(1)

disconnect()
sys.exit(0)