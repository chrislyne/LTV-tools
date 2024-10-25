import maya.cmds as cmds
import LTV_utilities.fileWrangle as fileWrangle
import os
import tempfile
from shutil import copyfile
import LTV_utilities.unityConfig as unity

def exportAsAlembic(abcFilename):

	#get file/folder path
	parentFolder,remainingPath = fileWrangle.getParentFolder()

	#get workspace
	workspace = cmds.workspace( q=True, directory=True, rd=True)
	workspaceLen = len(workspace.split('/'))
	#get filename
	filename = cmds.file(q=True,sn=True)
	#get relative path (from scenes)
	relativePath = ''
	for dir in filename.split('/')[workspaceLen:-1]:
		relativePath += '%s/'%(dir)

	#string of objects to export
	exportString = ''
	returnString = ''
	sel = cmds.textScrollList('extrasList',q=True,allItems=True)
	if sel:
		for item in sel:
			exportString += ' -root %s'%(item)

		#get timeline
		startFrame = int(cmds.playbackOptions(q=True,minTime=True))
		endFrame = int(cmds.playbackOptions(q=True,maxTime=True))

		#set folder to export to  
		currentProjects,activeProject = unity.getUnityProject()
		folderPath = '%s/Assets/Resources/%s'%(currentProjects[activeProject],remainingPath)
		if not os.path.exists(folderPath):
			os.makedirs(folderPath)

		#check if plugin is already loaded
		if not cmds.pluginInfo('AbcImport',query=True,loaded=True):
			try:
				#load abcExport plugin
				cmds.loadPlugin( 'AbcImport' )
			except: 
				cmds.error('Could not load AbcImport plugin')

		#export .abc
		abcExportPath = '%s/%s_cache.abc'%(folderPath,abcFilename)
		abcTempPath = '%s/%s_cache.abc'%(tempfile.gettempdir().replace('\\','/'),abcFilename)
		command = '-frameRange %d %d -uvWrite -writeColorSets -writeFaceSets -writeVisibility -wholeFrameGeo -worldSpace -writeUVSets -dataFormat ogawa%s -file \"%s\"'%(startFrame,endFrame,exportString,abcTempPath)
		#load plugin
		if not cmds.pluginInfo('AbcExport',query=True,loaded=True):
			try:
				#load abcExport plugin
				cmds.loadPlugin( 'AbcExport' )
			except: cmds.error('Could not load AbcExport plugin')
		#write to disk
		cmds.AbcExport ( j=command )
		#copy file from temp folder to project
		copyfile(abcTempPath, abcExportPath)
		#export fbx for materials
		cmds.select(sel,r=True)
		print(abcExportPath)
		#cmds.file(abcExportPath.replace('.abc','_mat.fbx'),force=True,type='FBX export',es=True)
		cmds.FBXExport('-file', abcExportPath.replace('.abc','_mat.fbx'),'-s')

		returnString = "%s/%s_cache"%(remainingPath,abcFilename)
	
	return returnString

#export fbx
def exportAnimation(obj,animOnly):
	#rename file temporarily
	filename = cmds.file(q=True,sn=True)
	#objName = obj.split('|')[-1].split(':')[-1]
	objName = obj.split('|')[-1]
	objName = objName.replace(':','_')
	newName = '%s_%s'%(filename.rsplit('.',1)[0],objName)

	objParent = cmds.listRelatives(obj,p=True)
	if objParent:
		objParent = objParent[0]
	else:
		objParent = obj
	#select object to export
	try:
		if cmds.objExists('|%s|*CC_Base_BoneRoot'%objParent):
			exportObject = '%s|*CC_Base_BoneRoot'%(objParent)
			#exportObject = cmds.parent(exportObject, world=True)
		else:
			exportObject = '%s|*DeformationSystem'%(objParent)
		print("correct exportObject = %s"%exportObject)
		cmds.select(exportObject,r=True)
	except:
		exportObject = obj
		print("fallback exportObject = %s"%exportObject)
		cmds.select(exportObject,r=True)
	#define full file name
	if ':' in exportObject:
		ns = exportObject.split(':',1)[0]
		ns = ns.split('|')[-1]
		ns = ':%s'%ns
	else:
		ns = ':'
	refFileName  = ('%s.fbx'%(newName.rsplit('/',1)[-1].split('.')[0]))

	#output name
	parentFolder,remainingPath = fileWrangle.getParentFolder()
	currentProjects,activeProject = unity.getUnityProject()
	pathName = '%s/Assets/Resources/%s/%s'%(currentProjects[activeProject],remainingPath,refFileName)
	#make folder if it doesn't exist
	if not os.path.exists(pathName.rsplit('/',1)[0]):
		os.makedirs(pathName.rsplit('/',1)[0])

	#export fbx
	try:
		cmds.loadPlugin("fbxmaya")		#load plugin
	except:
		pass
	cmds.FBXExportFileVersion("-v","FBX201100") 	#set fbx version
	cmds.FBXExportBakeComplexAnimation("-v",True)	#set export animation
	cmds.FBXExportAnimationOnly("-v",animOnly)		#set export animation only
	cmds.FBXExportUseSceneName ("-v",True)			#set use scene name
	cmds.FBXExport('-file', pathName,'-s')			#do the export 
	#restore the filename
	cmds.file(rename=filename)

	return obj,newName,remainingPath


def copyUnityScene(unityVersion,unityEditorPath):
	#get file/folder path
	parentFolder,remainingPath = fileWrangle.getParentFolder()
	filename = cmds.file(q=True,sn=True,shn=True)
	#paths
	currentProjects,activeProject = unity.getUnityProject()
	unityTemplateFile = '%s/Assets/Scenes/Templates/shotTemplate.unity'%(currentProjects[activeProject])
	unitySceneFile = '%s/Assets/Scenes/%s/%s.unity'%(currentProjects[activeProject],remainingPath,filename.split('.')[0])
	print("unitySceneFile = %s"%unitySceneFile)
	#make folder
	folder = unitySceneFile.rsplit('/',1)[0]
	if not os.path.exists(folder):
		os.makedirs(folder)
	
	#make Unity Scene File
	try:
		projectPath = currentProjects[activeProject]
		scenePath = "Assets/Scenes/%s/%s.unity"%(remainingPath,filename.split('.')[0])
		shotName = "%s"%filename.split('.')[0]

		if platform.system() == "Windows":
			subprocess.Popen('\"%s/%s/Editor/Unity.exe\" -quit -projectPath \"%s\" -executeMethod BuildSceneBatch.PerformBuild -shotName \"%s\" -scenePath \"%s\" '%(unityEditorPath,unityVersion,projectPath,shotName,scenePath),shell=True)
		else:
			subprocess.Popen('%s/%s/Unity.app/Contents/MacOS/Unity -quit -batchmode -projectPath %s -executeMethod BuildSceneBatch.PerformBuild -shotName \"%s\" -scenePath \"%s\" '%(unityEditorPath,unityVersion,projectPath,shotName,scenePath),shell=True)
	except:
		print("Unable to populate Unity scene file")
		#copy blank Unity scene if auto population fails
		try:
			if not os.path.exists(unitySceneFile):
				copyfile(unityTemplateFile, unitySceneFile)
		except:
			print("no Unity scene file created")