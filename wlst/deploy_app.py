connect('weblogic','Welcome1','t3://localhost:7001')
deploy(appName='hola', path='/u01/oracle/apps/hola-weblogic-app.war', targets='AdminServer', upload='false', stageMode='nostage')
disconnect()
exit()
