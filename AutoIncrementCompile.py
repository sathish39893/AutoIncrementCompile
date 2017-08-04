'''
Auto Incremental Compilation for Siebel Tools

Author: SATHISH PANTHAGANI
email: sathish.panthagani@accenture.com
Inputs: Tools Path, SRF File Path, Object List File

Outputs: Compilation Objects to SRF File

'''

from pywinauto.application import Application
import pywinauto.timings as pywintime
import pywinauto.base_wrapper as basewrapper
import os,sys,time

print("*"*60+"\n\n\tAuto Incremental Compilation for Siebel Tools\n\t\tversion: 1.5\n\n"+"*"*60)

if len(sys.argv) < 2:
	print("Usage: %s configfile \nexample: %s AutoIncrementCompile_params.txt"%(sys.argv[0],sys.argv[0]))
	sys.exit()
else:
	configFile = sys.argv[1]

global errCount
global successCount
errCount = 0
successCount = 0

#Get variable values from parameter file
def getVarFromFile(filename):
    import imp
    f = open(filename)
    global data
    data = imp.load_source('data', '', f)
    f.close()
getVarFromFile(configFile)

ToolsWinTitle = data.ToolsWinTitle  # 'Siebel Tools - Siebel Repository'
ToolsexePath = data.ToolsexePath #r"C:\Siebel\15.0.0.0.0\Tools\BIN\siebdev.exe"
cfgPath = data.cfgPath #r'c:\Siebel\15.0.0.0.0\Tools\bin\enu\tools.cfg'
userName = data.userName #"SPANTH"
passWord = data.passWord #"SPANTH"
dataSource = data.dataSource #"Local"
srfFile = data.srfFile #r"C:\Siebel\15.0.0.0.0\Client\OBJECTS\enu\siebel_sia_auto.srf"
objListFile = data.objListFile #r"C:\Users\sathish.panthagani\Documents\Python Scripts\SiebelObjectList.txt"

if hasattr(data, 'ToolsLaunchTimeOut'): 
	ToolsLaunchTimeOut = data.ToolsLaunchTimeOut
else:
	ToolsLaunchTimeOut = 1000 #default if not exist in param file

if hasattr(data, 'PopupTimeOut'):
	PopupTimeOut =  data.PopupTimeOut
else:
	PopupTimeOut = 1  # default value if parameter does not exist

ToolsPath = ToolsexePath+" /c "+cfgPath+" /u "+userName+" /p "+passWord+" /d "+dataSource
#print(ToolsLaunchTimeOut)

def validateInputs():
	if os.path.exists(ToolsexePath) is False:
		print('ToolsexePath: %s does not exist'%ToolsexePath)
		sys.exit()
	if os.path.exists(cfgPath) is False:
		print('cfgPath: %s does not exists'%cfgPath)
		sys.exit()
	if os.path.exists(srfFile) is False:
		print('srfFile: %s does not exist'%srfFile)
		sys.exit()
	if os.path.exists(objListFile) is False:
		print('objListFile: %s does not exist'%objListFile)
		sys.exit()
	print("%s: Validation successful"%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))

#Validate inputs provided in file
validateInputs()

if hasattr(data,'LoadTime'):
	if data.LoadTime.upper() == 'SLOW':
		pywintime.Timings.Slow()
	elif data.LoadTime.upper() == 'FAST':
		pywintime.Timings.Fast()
	else:
		pywintime.Timings.Defaults()
else:
	pywintime.Timings.Defaults()

#Launch Tools
try:
	print("%s: Siebel Tools started.."%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
	app = Application().start(ToolsPath,timeout=ToolsLaunchTimeOut)
	#app = Application().connect(path=ToolsexePath)
	app[ToolsWinTitle].wait("exists enabled visible ready")
except pywintime.TimeoutError as e:
	print("%s: timed out while launching Siebel Tools"%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
	raise e
except:
	print("%s: error occured while launching Siebel Tools:"%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))

dlg = app.top_window() #dlg = app['Siebel Tools - Siebel Repository']
dlg.type_keys("^E") # to open Object Explorer
objexpl = app.SiebelToolsSiebelRepository.ObjectExplorer1.TreeView.WrapperObject() #Object explorer window
#dlg.minimize()

#####Open Object Compile Window and compile
def compileObj(ObjType, ObjName):
	global successCount
	global errCount
	errMsg = ""
	if ObjType == "Project":
		app[ToolsWinTitle].type_keys("{F7}") #Opens Compilation Window
		app['Object Compiler']['Siebel repository file:Edit'].set_edit_text(srfFile) #SRF File location
		app['Object Compiler']['ListBox'].Select(ObjName, select=True)
		app['Object Compiler']['Compile'].click()
	else:
		app[ToolsWinTitle].type_keys("^{F7}") #Opens Compilation Window
		if app['Object Compiler'].exists(1):
			app['Object Compiler']['Siebel repository file:Edit'].set_edit_text(srfFile) #SRF File location
			ObjCount = app['Object Compiler']['ListBox'].item_count()
			if ObjCount == 1:
				ObjList = app['Object Compiler']['ListBox'].item_texts()
				if ObjList[0] == ObjName: # verify the object name is matched

					app['Object Compiler']['Compile'].click()  #Compilation Starts
					tmpErrMsg = ""
					if app['Error'].exists(timeout=PopupTimeOut,retry_interval=1):
						tmpErrMsg = app['Error']['ErrorEdit'].TextBlock()
						app['Error']['OK'].click()
						if(tmpErrMsg):
							print("%s: Compilation failed: Exception occured: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),ObjType,ObjName))
							print(tmpErrMsg)
							errCount += 1
							errMsg = "ERRORPOP"
					else:
						pass
				else:
					app['Object Compiler']['Cancel'].click() # cancel compile
					errMsg = "OBJNAMEMISMATCH"
			else:
				errMsg = "MULTI"
			#app['Object Compiler']['Compile'].wait_not('visible') #not required
		else:
			errMsg = "NOTFOUND"
	return errMsg

######Query for the compile Objects
def QuerynCompileObjects(ObjType, ObjName):
	global successCount
	global errCount
	sEditCtrl = "~"+ObjType+"sEdit" #Object Plural Form is used for this window
	#sEditCtrl = ObjType+"sEdit" #Object Plural Form is used for this window
	#print(sEditCtrl)
	sTreeObjPath = '\\Siebel Objects\\'+ObjType
	targetobj = objexpl.get_item(sTreeObjPath).click() #click on object explorer items
	
	app[ToolsWinTitle][sEditCtrl].wait('visible') # It will wait till the window appears
	ObjNameTemp = "'"+ObjName+"'" # added quotes to avoid query errors
	dlg.type_keys("^Q") # Query for the object Name

	app[ToolsWinTitle][sEditCtrl].set_edit_text(ObjNameTemp)
	dlg.type_keys("^{ENTER}")

	#dlg.type_keys("+{VK_DOWN 2}")
	return compileObj(ObjType, ObjName) # Compiles Object
#########	

print("%s: Compilation started..."%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
#siebObjType = "Business Component"
#siebObjName = "ABO Bulk Request Actions*"

#added below to avoid typo errors
ObjectList = {	'Bitmap Category':['BITMAP CATEGORY','BITMAP'],
				'Business Component':['BUSINESS COMPONENT','BC', 'BUSCOMP'],
				'Business Object':['BUSINESS OBJECT','BO'], 
				'Business Service':['BUSINESS SERVICE','BS'],
				'Class':['CLASS'],
				'Command':['COMMAND'],
				'Find':['FIND'],
				'HTML Heirarchy Bitmap':['HTML HEIRARCHY BITMAP'],
				'Help Id':['HELP ID'],
				'Icon Map':['ICON MAP','ICON'],
				'Integration Object':['INTEGRATION OBJECT','IO','INT OBJ'],
				'Application':['APPLICATION','APP','APPL'],
				'Applet':['APPLET'],  #application and applet needs to be same sequence
				'Link':['LINK'],
				'Menu':['MENU'],
				'Message Category':['MESSAGE CATEGORY'],
				'Pick List':['PICK LIST'],
				'Project':['PROJECT'],
				'Screen':['SCREEN'],
				'Symbolic String':['SYMBOLIC STRING'],
				'Table':['TABLE'],
				'Task Group':['TASK GROUP'],
				'Toolbar':['TOOLBAR'],
				'Type':['TYPE'],
				'View':['VIEW'],
				'Web Page':['WEB PAGE'],
				'Web Template':['WEB TEMPLATE','WEB TEMPL','WEBTEMPL'],
				'Import Object':['IMPORT OBJECT']
			}
def searchObjType(searchFor):
	for k in ObjectList:
		if k == searchFor:
			return k
		else:
			for v in ObjectList[k]:
				if searchFor.upper() in v:
					return k
	return None

#dict holds the lines from objListFile
dict = {}
for line in open(objListFile):
	linelist = line.split(",")
	if len(linelist) < 3:
		siebObjType = linelist[0].strip()
		siebObjName = linelist[1].strip()
		dict[siebObjName] = siebObjType  #adding to dictionary to remove duplicate objects
#print(dict.items())
for key in dict:
	try:
		newObjType = searchObjType(dict[key])	
		ObjName = key
		if newObjType is not None:
			errorMsg = QuerynCompileObjects(newObjType,key)  #siebObjType,siebObjName
			prevObjType = newObjType
			prevObjName = key
			if errorMsg == "":
				print("%s: Compilation successful: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
				successCount += 1
			elif errorMsg == "MULTI":
				print("%s: Compilation failed: Multiple Objects found in Compile Window: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
				errCount += 1
			elif errorMsg == "NOTFOUND":
				print("%s: Compilation failed: Object not found: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
				errCount += 1
			elif errorMsg == "OBJNAMEMISMATCH":
				print("%s: Compilation failed: Object Name mismatch: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
				errCount += 1	
			
		else:
			print("%s: Compilation failed: ObjectType not supported: ObjectType: %s\tName: %s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),dict[key],ObjName))
			errCount += 1		
		
	except basewrapper.ElementNotEnabled:
		print("%s: Compilation failed: Exception Occured: ObjectType:%s\tName:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),prevObjType,prevObjName))
		errCount += 1
		tmpErrMsg = ""
		if app['Error'].exists(timeout=PopupTimeOut,retry_interval=1):
			tmpErrMsg = app['Error']['ErrorEdit'].TextBlock()
			app['Error']['OK'].click()
			if(tmpErrMsg):
				print(tmpErrMsg)
		else:
			pass
	except pywintime.TimeoutError:
		print("%s: Compilation failed: TimeoutError Occured: ObjectType:%s\tName:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
		break   # might be an issue and needs to stop execution
	except IndexError:
		print("%s: Compilation failed: ObjectType is not enabled in Object Explorer: ObjectType:%s\tName:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
		errCount += 1
	except AttributeError:
		print("%s: Compilation failed: first column (i.e., Name) and should be editable in Query Mode: ObjectType:%s\tName:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),newObjType,ObjName))
		errCount += 1		

print("%s: Compilation done..."%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
print("%s: Total Number of Objects compiled:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),successCount))
print("%s: Total Number of Objects failed:%s"%(time.strftime("%d %b %Y %H:%M:%S",time.localtime()),errCount))
# Close/exit Siebel Tools
try:
	dlg.close_alt_f4()
	print("%s: Siebel Tools closed.."%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
except:
	app.kill()
	print("%s: Siebel Tools closed due to exception."%time.strftime("%d %b %Y %H:%M:%S",time.localtime()))
	raise