# Engine : Bottom-up
#    Low-level procedures
#    Animation Procedures (duplicate joint hierarchy, plug original animation into duplicate, etc.)
#    AnimLayers
#    Model procedures
#    Export setup
#    Export
# UI : Top down
#    Main window
#    UI functionality
# TO DO:
# -make a variable for script name and insert that next to all "import" calls in UI command strings

#PURPOSE       
#PROCEDURE     
#PRESUMPTION   

script_import = "import FBXExporter as FBX\n"
garbageTag = ".deleteMe"

import maya.cmds as cmds
import maya.mel as mel
import string

# in: Documents\Settings\Maya\scripts\
mel.eval('source "FBXExporter_FBXOptions.mel"')


#PURPOSE        Tag the given node with the orgin attribute and set to true
#PROCEDURE      If the onbject exists and the attribute does not exist, add the attribute and set to TRUE
#PRESUMPTION    none
def TagForOrigin(node):
    if cmds.objExists(node) and not cmds.objExists(node + ".origin"):
        cmds.addAttr(node, shortName = "org", longName = "origin", at = "bool")
        cmds.setAttr(node + ".origin", True)


#PURPOSE        add attributes to the mesh so exporter can find them
#PROCEDURE      if object exists, and the attribute does not, add exportMeshes message attribute
#PRESUMPTIONS   none
def TagMeshForExport(mesh):
    if cmds.objExists(mesh) and not cmds.objExists(mesh + ".exportMeshes"):
        cmds.addAttr(mesh, shortName = "xms", longName = "exportMeshes", at = "message")
        cmds.setAttr(mesh + ".exportMeshes", channelBox=True)
        #cmds.setAttr(mesh + ".exportMesh",keyable=True)


#PURPOSE        Add attribute to the node so exporter can find export definitions
#PROCEDURE      If the onbject exists and the attribute does not exist, add the exportNode message attribute
#PRESUMPTION    none
def TagForExportNode(node):
    if cmds.objExists(node) and not cmds.objExists(node + ".exportNode"):
        cmds.addAttr(node, sn = "xnd", ln = "exportNode", at = "message")


#PURPOSE        Return the origin of the given namespace
#PROCEDURE      If ns is not empty string, list all joints with the matching namespace, else list all joints.
#               For list of joints, look for origin attribute and if it is set to true.  If found return name
#               of joint, else return "Error"
#PRESUMPTION    Origin attribute is on a joint, "Error" is not a valid joint name, ns does not include colon
def ReturnOrigin(ns):
    joints = []
    if ns:
        joints = cmds.ls((ns + ":*"), type = "joint")
    else:
        joints = cmds.ls(type = "joint")
        
    if len(joints):
        for curJoint in joints:
            if cmds.objExists(curJoint + ".origin") and cmds.getAttr(curJoint + ".origin"):
                return curJoint
                
    return "Error"
    

#PURPOSE        return the meshes connected to blendshape nodes; pruning the meshes filters the blendshapes, which is undesirable.
#PROCEDURE      Get a list of blendshape nodes
#               Follow those connections to the mesh shape node
#               Traverse up the hierarchy to find parent transform node
#PRESUMPTION    character has a valid namespace, ns does not contain colon, only supporting polygonal meshes
def FindMeshesWithBlendshapes(ns):
    returnList = []
    
    blendshapes = cmds.ls((ns + ":*" ), type = "blendShape")
    
    for curBlendShape in blendshapes:
        downstreamNodes = cmds.listHistory(curBlendShape, future = True)
        for curNode in downstreamNodes:
            if cmds.objectType(curNode, isType = "mesh"):
                parents = cmds.listRelatives(curNode, parent = True)
                returnList.append(parents[0])

    return returnList
    
    
#PURPOSE        Removes all nodes tagged as garbage
#PROCEDURE      List all transforms in the scene, iterate through list, anything with "deleteMe" attribute
#               will be deleted
#PRESUMPTION    The deleteMe attribute is the name of the attribute signifying garbage
def ClearGarbage():
    list = cmds.ls(tr=True)
    
    for cur in list:
        if cmds.objExists(cur + garbageTag):
            cmds.delete(cur)
            

#PURPOSE        Tag object as garbage
#PROCEDURE      If node is valid object and attribute does not exist, add deleteMe attribute
#PRESUMPTION    none
def TagForGarbage(node):
    if cmds.objExists(node) and not cmds.objExists(node + garbageTag):
        cmds.addAttr(node, shortName = "del", longName = "deleteMe", at = "bool")
        cmds.setAttr(node + garbageTag, True)


##############################################
#
#    Export settings node procs
#
##############################################


#PURPOSE        Return all export nodes connected to given origin
#PROCEDURE      If origin is valid and has the exportNode attribute,
#               return list of export nodes connected to it
#PRESUMPTION    Only export nodes are connected to exportNode attribute
def ReturnFBXExportNodes(origin):
    exportNodeList=[]
    
    if cmds.objExists(origin + ".exportNode"):
        exportNodeList = cmds.listConnections(origin + ".exportNode")
       
    return exportNodeList
    

#PURPOSE        Connect the fbx export node to the origin
#PROCEDURE      check if attribute exists and nodes are valid
#               if so, connect attributes
#PRESUMPTION    none
def ConnectFBXExportNodeToOrigin(exportNode, origin):
    if cmds.objExists(origin) and cmds.objExists(exportNode):
        if not cmds.objExists(origin + ".exportNode"):
            TagForExportNode(origin)
        if not cmds.objExists(exportNode + ".exportNode"):
            AddFBXNodeAttrs(exportNode)
        cmds.connectAttr(origin + ".exportNode", exportNode + ".exportNode")
   
            
#PURPOSE        delete given export node
#PROCEDURE      if object exists, delete
#PRESUMPTION    none
def DeleteFBXExportNode(exportNode):
    if cmds.objExists(exportNode):
        cmds.delete(exportNode)
        
        
#PURPOSE        to add the attribute to the export node to store our export settings
#PROCEDURE      for each attribute we want to add, check if it exists.  If not, add it.
#PRESUMPTION    assume fbxExportNode is a valid object (can add verification if necessary)
def AddFBXNodeAttrs(fbxExportNode):
    if not cmds.attributeQuery("export", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'export', at = "bool")
        
    if not cmds.attributeQuery("moveToOrigin", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'moveToOrigin', at = "bool")

    if not cmds.attributeQuery("zeroOrigin", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'zeroOrigin', at = "bool")
        
    if not cmds.attributeQuery("exportName", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'exportName', dt = "string")

    if not cmds.attributeQuery("useSubRange", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'useSubRange', at = "bool")

    if not cmds.attributeQuery("startFrame", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'startFrame', at = "float")

    if not cmds.attributeQuery("endFrame", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'endFrame', at = "float")

    if not cmds.attributeQuery("exportMeshes", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'exportMeshes', at = "message")

    if not cmds.attributeQuery("exportNode", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'exportNode', at = "message")

    if not cmds.attributeQuery("animLayers", node = fbxExportNode, exists = True):
        cmds.addAttr(fbxExportNode, ln = 'animLayers', dt = "string")

        
#PURPOSE        Create the export node to store our export settings
#PROCEDURE      Create an empty transform node
#               This will be sent to AddFBXNodeAttrs to add the needed attributes
#PRESUMPTION    none
def CreateFBXExportNode(characterName):
    fbxExportNode = cmds.group(em = True, name = characterName + "FBXExportNode#")
    AddFBXNodeAttrs(fbxExportNode)
    cmds.setAttr(fbxExportNode + ".export", 1)
    
    return fbxExportNode


##############################################
#
#    Model export procs
#
##############################################


#PURPOSE        To conenct the meshes to the export node so the exporter can find them
#PROCEDURE      Check to make sure meshes and export node are valid, check for attribute "exportMeshes"
#               if no attribute add it, then connect attributes
#PRESUMPTION    exportNode is an exportNode, and meshes is a list of transform nodes for polygon meshes
def ConnectFBXExportNodeToMeshes(exportNode, meshes):
    if cmds.objExists(exportNode):
        if not cmds.objExists(exportNode + ".exportMeshes"):
            AddFBXNodeAttrs(exportNode)
        
        for curMesh in meshes:
            if cmds.objExists(curMesh):
                if not cmds.objExists(curMesh + ".exportMeshes"):
                    TagMeshForExport(curMesh)
                cmds.connectAttr(exportNode + ".exportMeshes", curMesh + ".exportMeshes", force = True)


#PURPOSE        to disconnect the message attribute bewteen export node and mesh
#PROCEDURE      iterate through list of meshes and if mesh exists disconnect
#PRESUMPTION    that node and mesh are connected via exportMeshes message attribute
def DisconnectFBXExportNodeToMeshes(exportNode, meshes):
    if cmds.objExists(exportNode):
        for curMesh in meshes:
            if cmds.objExists(curMesh):
                cmds.disconnectAttr(exportNode + ".exportMeshes", curMesh + ".exportMeshes")
        

#PURPOSE        Return a list of meshes connected to the export node
#PROCEDURE      listConnection to exportMeshes attribute
#PRESUMPTION    exportMeshes is used to connect to the export meshes and that the meshes are valid
def ReturnConnectedMeshes(exportNode):
    meshes = cmds.listConnections((exportNode + ".exportMeshes"), source = False, destination = True)
    return meshes


##############################################
#
#    Animation export procs
#
##############################################


#PURPOSE        Unlock joint transforms for writing
#PROCEDURE      Use setAttr to unlock each joint
#PRESUMPTIONS   none
def UnlockJointTransforms(root):
    
    hierarchy = cmds.listRelatives(root, ad=True, f=True)
    hierarchy.append(root)
    
    for cur in hierarchy:
        cmds.setAttr( (cur + '.translateX'), lock = False)
        cmds.setAttr( (cur + '.translateY'), lock = False)
        cmds.setAttr( (cur + '.translateZ'), lock = False)
        cmds.setAttr( (cur + '.rotateX'), lock = False)
        cmds.setAttr( (cur + '.rotateY'), lock = False)
        cmds.setAttr( (cur + '.rotateZ'), lock = False)
        cmds.setAttr( (cur + '.scaleX'), lock = False)
        cmds.setAttr( (cur + '.scaleY'), lock = False)
        cmds.setAttr( (cur + '.scaleZ'), lock = False)


#PURPOSE        to connect given node to other given node via specified transform
#PROCEDURE      call connectAttr
#PRESUMPTIONS   assume two nodes exist and transform type is valid
def ConnectAttrs(sourceNode, destNode, transform):
        cmds.connectAttr(sourceNode + "." + transform + "X", destNode + "." + transform + "X")
        cmds.connectAttr(sourceNode + "." + transform + "Y", destNode + "." + transform + "Y")
        cmds.connectAttr(sourceNode + "." + transform + "Z", destNode + "." + transform + "Z")
  
        
#PURPOSE        Copy the bind skeleton and connect the copy to the original bind
#PROCEDURE      duplicate hierarchy
#               delete everything that is not a joint
#               unlock all the joints in the copy
#               connect the translate, rotate and scales
#               parent copy to the world
#               add delteMe attr
#PRESUMPTIONS   no joints are children of non-joint objects
def CopyAndConnectSkeleton(origin):
    newHierarchy=[]
    
    if origin != "Error" and cmds.objExists(origin):
        dupHierarchy = cmds.duplicate(origin)
        tempHierarchy = cmds.listRelatives(dupHierarchy[0], ad=True, f=True)
        
        for cur in tempHierarchy:
            if cmds.objExists(cur):
                if cmds.objectType(cur) != "joint":
                    cmds.delete(cur)
                    
        UnlockJointTransforms(dupHierarchy[0])
        
        origHierarchy = cmds.listRelatives(origin, ad=True, type="joint")
        newHierarchy = cmds.listRelatives(dupHierarchy[0], ad=True, type="joint")
        
        origHierarchy.append(origin)
        newHierarchy.append(dupHierarchy[0])

        for index in range(0, len(origHierarchy)):
            # print(f"index for attr connect: {index}")
            ConnectAttrs(origHierarchy[index], newHierarchy[index], "translate")
            ConnectAttrs(origHierarchy[index], newHierarchy[index], "rotate")
            ConnectAttrs(origHierarchy[index], newHierarchy[index], "scale")
        
        cmds.parent(dupHierarchy[0], world=True)
        TagForGarbage(dupHierarchy[0])

    return newHierarchy
    

#PURPOSE        Translate export skeleton to origin.  May or may not kill origin animation depending on input
#PROCEDURE      Bake the animation onto our origin
#               Create an anim Layer
#               Anim layer will either be additive or override, depending on parameters passed in (zeroOrigin boolean)
#               Add deleteMe attr to anim layer
#               Move to origin
#PRESUMPTIONS   origin is valid, end frame is greater than start frame, zeroOrigin is boolean
def TransformToOrigin(origin, startFrame, endFrame, zeroOrigin):
    cmds.bakeResults(origin, t = (startFrame, endFrame), at = ["rx","ry","rz","tx","ty","tz","sx","sy","sz"], hi="none")
    
    cmds.select(clear = True)
    cmds.select(origin)
    
    newAnimLayer= ""
    
    if zeroOrigin: # override
        newAnimLayer = cmds.animLayer(aso=True, mute = False, solo = False, override = True, passthrough = True, lock = False)
        cmds.setAttr(newAnimLayer + ".rotationAccumulationMode", 0)
        cmds.setAttr(newAnimLayer + ".scaleAccumulationMode", 1)
    else: # additive
        newAnimLayer = cmds.animLayer(aso=True, mute = False, solo = False, override = False, passthrough = False, lock = False)
        
    TagForGarbage(newAnimLayer)
    
    # turn animLayer on
    cmds.animLayer(newAnimLayer, edit = True, weight = 1)
    cmds.setKeyframe(newAnimLayer + ".weight")
    
    # move origin animation to world origin
    cmds.setAttr(origin + ".translate", 0,0,0)
    cmds.setAttr(origin + ".rotate", 0,0,0)
    cmds.setKeyframe(origin, al=newAnimLayer, t=startFrame)
    
    
##############################################
#
#    AnimLayers procs
#
##############################################


#PURPOSE        Record the anim layer settings used in animation and store in the export node as a string
#PROCEDURE      List all the anim layers, query their "mute" and "solo" attributes,
#               list them in one single string.  
#               Uses ; as sentinel value to split separate animLayers.
#               Uses , to split separate fields
#               Uses = to split attribute from value in field
#PRESUMPTIONS   none
def SetAnimLayerSettings(exportNode):    
    if not cmds.attributeQuery("animLayers", node = exportNode, exists = True):
        AddFBXNodeAttrs(exportNode)

    animLayers = cmds.ls(type="animLayer")
    
    animLayerCommandStr = ""
    
    for curLayer in animLayers:
        mute = cmds.animLayer(curLayer, query = True, mute = True)
        solo = cmds.animLayer(curLayer, query = True, solo = True)
        animLayerCommandStr += (curLayer + ", mute = " + str(mute) + ", solo = " + str(solo) + ";")
    
    cmds.setAttr(exportNode + ".animLayers", animLayerCommandStr, type = "string")
    

#PURPOSE        Set the animLayers based on the string value in the export node  
#PROCEDURE      Use the predefined sentinel values to split the string for separate animLayers
#               and parse out the attributes and their values, then set
#PRESUMPTION    Uses ; as sentinel value to split separate animLayers.
#               Uses , to split separate fields
#               Uses = to split attribute from value in field
#               Order is: Layer, Mute, Solo 
def SetAnimLayersFromSettings(exportNode):
    
    if cmds.objExists(exportNode) and cmds.objExists(exportNode + ".animLayers"):
        animLayersRootString = cmds.getAttr(exportNode + ".animLayers", asString=True)
        
        if animLayersRootString:
            animLayerEntries = animLayersRootString.split(";")
            
            for curEntry in animLayerEntries:
                if curEntry:
                    fields = curEntry.split(",")
                    
                    animLayerField = fields[0]
                    curMuteField = fields[1]
                    curSoloField = fields[2]

                    muteFieldStr = curMuteField.split(" = ")
                    soloFieldStr = curSoloField.split(" = ")
                    
                    # convert strings to bool values
                    muteFieldBool = True
                    soloFieldBool = True
                    
                    if muteFieldStr[1] != "True":
                        muteFieldBool = False
                    if soloFieldStr[1] != "True":
                        soloFieldBool = False
                    
                    cmds.animLayer(animLayerField, edit = True, mute = muteFieldBool, solo = soloFieldBool)
     
                    
#PURPOSE       
#PROCEDURE     
#
#PRESUMPTIONS   
def ClearAnimLayerSettings(exportNode):
    cmds.setAttr(exportNode + ".animLayers", "", type = "string")


##############################################
#
#     Export procs
#     Two different pipelines: exporting rigged characters, animations
#
##############################################


# PURPOSE       Write export FBX file
# PROCEDURE     Error check, write Path Relative export file by calling file()
# PRESUMPTIONS  *THAT YOU WANT TO EXPORT PATH RELATIVE*
def ExportFBX(exportNode):
    curWorkspace = cmds.workspace(q=True, rd=True)
    fileName = cmds.getAttr(exportNode + ".exportName")
    
    if fileName:
        newFBX = curWorkspace + fileName
        cmds.file(newFBX, force=True, type='FBX export', pr=True, es=True)
    else:
        cmds.warning("No Valid Export Filename for Export Node " + exportNode + "\n")
    

# PURPOSE       Assemble and verify settings and conditions for FBXExport
# PROCEDURE     Error check, assemble and verify settings, call ExportFBX()
# PRESUMPTIONS  *THAT YOU WANT TO EXPORT PATH RELATIVE*
def ExportFBXAnimation(characterName, exportNode):
    
    ClearGarbage()
    characters = []
    
    if characterName:
        characters.append(characterName)
    else:
        references = cmds.file(reference=1, query=True)
        for curRef in references:
            characters.append(cmds.file(curRef, namespace = 1, query = True))
            
    for curCharacter in characters:
        
        # get meshes with blendshapes
        meshes = FindMeshesWithBlendshapes(curCharacter)
        
        # get origin
        origin = ReturnOrigin(curCharacter)
        
        exportNodes = []
        
        if exportNode:
            exportNodes.append(exportNode)
        else:
            exportNodes = ReturnFBXExportNodes(origin)
                       
        for curExportNode in exportNodes:
            test=ReturnConnectedMeshes(curExportNode)  
            
            if cmds.getAttr(curExportNode + ".export") and origin != "Error" and not test:
                exportRig = CopyAndConnectSkeleton(origin)
                
                startFrame = cmds.playbackOptions(query = True, minTime=1)
                endFrame = cmds.playbackOptions(query = True, maxTime=1)
                
                subAnimCheck = cmds.getAttr(curExportNode + ".useSubRange")

                if subAnimCheck:
                    startFrame = cmds.getAttr(curExportNode + ".startFrame")
                    endFrame = cmds.getAttr(curExportNode + ".endFrame")
                    
                if cmds.getAttr(curExportNode + ".moveToOrigin"):
                    newOrigin = cmds.listConnections(origin + ".translateX", source = False, d = True)
                    zeroOriginFlag = cmds.getAttr(curExportNode + ".zeroOrigin")
                    TransformToOrigin(newOrigin[0], startFrame, endFrame, zeroOriginFlag)
                    
                cmds.select(clear = True)
                cmds.select(exportRig, add=True)
                cmds.select(meshes, add=True)
                
                SetAnimLayersFromSettings(curExportNode)
                
                mel.eval("SetFBXExportOptionsAnimation(" + str(startFrame) + "," + str(endFrame) + ")") 
                
                ExportFBX(curExportNode)
                
            ClearGarbage()
                                    
    
def ExportFBXCharacter(exportNode):
    origin = ReturnOrigin("")
    
        
    if exportNode:
        exportNodes.append(exportNode)
    else:
        exportNodes = ReturnFBXExportNodes(origin)

    parentNode = cmds.listRelatives(origin, parent=True, fullPath = True)
    
    if parentNode:
        cmds.parent(origin, world = True)
        
    for curExportNode in exportNodes:
        if cmds.getAttr(curExportNode + ".export"):
            mel.eval("SetFBXExportOptionsModel()")
            
            cmds.select(clear=True)
            
            meshes = ReturnConnectedMeshes(curExportNode)
            cmds.select(origin, add=True)
            cmds.select(meshes, add=True)
            
            ExportFBX(curExportNode)
            
        if parentNode:
            cmds.parent(origin, parentNode[0])


##############################################
#
#     UI Code
#
##############################################


#################################
#
#     Animation UI Procs
#
#################################


#PURPOSE    To populate the actor panel in the animation tab
#PROCEDURE    Get list of all references in the scene
#                for each reference, get the namespace
#                call ReturnOrigin for each namespace
#                if not "Error", add namespace to textScrollList
#PRESUMPTIONS    single-layered referencing, rigs are not referenced in, references have namespace
def FBXExporterUI_PopulateAnimationActorsPanel():
    cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", edit=True, removeAll=True)

    references=cmds.file(query=True, reference=True)
    
    for curRef in references:
        if not cmds.file(curRef, query=True, deferReference=True):
            print("in")
            ns=cmds.file(curRef, query=True, namespace=True)
            origin=ReturnOrigin(ns)
            
            if origin != "Error":
                cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", edit=True, append=ns)
            else:
                print(f"Mesh connected to {ns}, will not descend")
      
#PURPOSE    To populate the animation export nodes textScrollList with export nodes connected to the origin of the character
#            selected in the actorsTextScrollList
#PROCEDURE  Get the selected actor's namespace from actorsTextScrollList
#            If valid, get origin with ReturnFBXExportNodes()
#            If origin is valid, get export nodes with ReturnFBXExportNodes
#            Iterate through list in export nodes. If not connected to meshes (i.e. not intended for model export),
#            add to exportNodeTextScrollList
#PRESUMPTIONS    export node connected to meshes is a model export node
def FBXExporterUI_PopulateAnimationExportNodesPanel():
    # clear export nodes text scroll list
    cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", edit=True, removeAll=True)
    ns = cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", query=True, selectItem=True)
    
    if ns:
        origin = ReturnOrigin(ns[0])
    
        if origin != "Error":
            exportNodes = ReturnFBXExportNodes(origin)
            
            if exportNodes:
                for cur in exportNodes:
                    testForMeshes = ReturnConnectedMeshes(cur)
                    # if no meshes are returned, this means the export node is intended for animation export and therefore should be included in the textScrollList
                    if not testForMeshes:
                        cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", edit=True, append=cur)


#PURPOSE    Create a new export node to connect to the origin of the character selected in the actors textScrollList
#            
#PROCEDURE  Get the name of the actor's namespace by querying the actorsTextScrollList,
#            get the origin using ReturnOrigin,
#            create the export node with CreateExportNode,
#            connect to the origin with ConnectExportNodeToOrigin
#            update UI
#PRESUMPTIONS    none
def FBXExporterUI_AnimationCreateNewExportNode():
    ns = cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", query=True, selectItem=True)

    if ns:
        origin = ReturnOrigin(ns[0])
        if origin != "Error":
            exportNode = CreateFBXExportNode(ns[0])        
            
            if exportNode:
                ConnectFBXExportNodeToOrigin(exportNode, origin)
                FBXExporterUI_PopulateAnimationExportNodesPanel()


#PURPOSE    
#PROCEDURE  
#           
#PRESUMPTIONS    
def FBXExporterUI_ExportSelectedAnimation():
    exportNodes = cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
    ns = cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", query=True, selectItem=True)
    
    if exportNodes and ns:
        ExportFBXAnimation(ns[0], exportNodes[0])
        

#PURPOSE    
#PROCEDURE  
#           
#PRESUMPTIONS    
def FBXExporterUI_ExportAllAnimationForSelectedCharacter():
    ns = cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", query=True, selectItem=True)
    
    ExportFBXAnimation(ns[0], "")


#PURPOSE    Export all animation.  *WARNING THIS IS BROKEN*
#PROCEDURE  
#           
#PRESUMPTIONS    
def FBXExporterUI_ExportAllAnimation():
    ns = cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", query=True, allItems=True)
    
    for curChar in ns:
        origin = ReturnOrigin(curChar)
        if origin != "Error":
            exportNodes = ReturnFBXExportNodes(origin)
            
            for curAnimation in exportNodes:
                ExportFBXAnimation(curChar, "")
  

#PURPOSE    Unlock the UI elements on the animation tab and set them according to the attributes on selected export node
#            
#PROCEDURE  Get the selected export node from the exportNodesTextScrollList
#            query its attributes and set ui elements based on values
#            
#            
#           
#PRESUMPTIONS    exportNode is a valid object
def FBXExporterUI_UpdateAnimationExportSettings():
    exportNodes = cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
    
    if exportNodes:
        AddFBXNodeAttrs(exportNodes[0]) # make sure export node is up to date in terms of attrs expected
        cmds.checkBoxGrp("FBXExporter_window_animationExportCheckBoxGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".export"))
        cmds.checkBoxGrp("FBXExporter_window_animationZeroOriginCheckBoxGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".moveToOrigin"))
        cmds.checkBoxGrp("FBXExporter_window_animationSubRangeCheckBoxGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".useSubRange"))
        
        if (cmds.getAttr(exportNodes[0] + ".useSubRange")):
            # activate frame start and frame end float fields
            cmds.floatFieldGrp("FBXExporter_window_animationStartFrameFloatFieldGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".startFrame"))
            cmds.floatFieldGrp("FBXExporter_window_animationEndFrameFloatFieldGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".endFrame"))
        else:
            cmds.floatFieldGrp("FBXExporter_window_animationStartFrameFloatFieldGrp", edit=True, enable=False)
            cmds.floatFieldGrp("FBXExporter_window_animationEndFrameFloatFieldGrp", edit=True, enable=False)

        if (cmds.getAttr(exportNodes[0] + ".moveToOrigin")):
            cmds.checkBoxGrp("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".zeroOrigin"))
        else:
            cmds.checkBoxGrp("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", edit=True, enable=False)
        
        test=cmds.getAttr(exportNodes[0] + ".animLayers")
        if test:
            cmds.button("FBXExporter_window_animationRecordAnimLayersButton", edit=True, enable=True, label="Re-Record Anim Layers", backgroundColor = [0.25, 0.25, 1.0])
        else:
            cmds.button("FBXExporter_window_animationRecordAnimLayersButton", edit=True, enable=True, label="Record Anim Layers", backgroundColor = [1.0, 0.25, 0.25])
        
        cmds.button("FBXExporter_window_animationPreviewAnimLayersButton", edit=True, enable=True)
        cmds.button("FBXExporter_window_animationClearAnimLayersButton", edit=True, enable=True)
         
        cmds.textFieldButtonGrp("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", edit=True, enable=True, text = cmds.getAttr(exportNodes[0] + ".exportName"))
        
            
#PURPOSE      to update the selected export node with settings in the UI
#PROCEDURE    get export nodes from textScrollList
#             update export node attributes
#             setAttr based on value queried from UI
#PRESUMPTIONS none
def FBXExporterUI_UpdateExportNodeFromAnimationSettings():
    exportNodes = cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
      
    if exportNodes and cmds.objExists(exportNodes[0]):
        AddFBXNodeAttrs(exportNodes[0])
        
        cmds.setAttr(exportNodes[0] + ".export", cmds.checkBoxGrp("FBXExporter_window_animationExportCheckBoxGrp", query=True, value1=True))
        cmds.setAttr(exportNodes[0] + ".moveToOrigin", cmds.checkBoxGrp("FBXExporter_window_animationZeroOriginCheckBoxGrp", query=True, value1=True))
        cmds.setAttr(exportNodes[0] + ".zeroOrigin", cmds.checkBoxGrp("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", query=True, value1=True))
        cmds.setAttr(exportNodes[0] + ".useSubRange", cmds.checkBoxGrp("FBXExporter_window_animationSubRangeCheckBoxGrp", query=True, value1=True))

        if (cmds.getAttr(exportNodes[0] + ".useSubRange")):
            cmds.setAttr(exportNodes[0] + ".startFrame", cmds.floatFieldGrp("FBXExporter_window_animationStartFrameFloatFieldGrp", query=True, value1=True))
            cmds.setAttr(exportNodes[0] + ".endFrame", cmds.floatFieldGrp("FBXExporter_window_animationEndFrameFloatFieldGrp", query=True, value1=True))

        cmds.setAttr(exportNodes[0] + ".exportName", cmds.textFieldButtonGrp("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", query=True, text=True), type="string")
        
        
#################################
#
#     Model UI Procs
#
#################################


#PURPOSE    Populate the root joints panel in the model tab
#PROCEDURE    Search for the origin.  If none found, list all joints in the scene
#PRESUMPTIONS    Origin is going to be a joint
def FBXExporterUI_PopulateModelRootJointsPanel():
    
    cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", edit=True, removeAll=True)
    
    origin = ReturnOrigin("")
    
    if origin != "Error":
        cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", edit=True, ebg=False, append=origin)
    else:
        joints=cmds.ls(type="joint")
        for curJoint in joints:
            cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", edit=True, bgc=[1, 0.1, 0.1], append=curJoint)


#PURPOSE Tag a joint to be an origin
#PROCEDURE get joint from the textScrollList, then call tagForOrigin, repopulate model root joint panel
#PRESUMPTION origin is valid
def FBXExporterUI_ModelTagForOrigin():
    joints= cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", query=True, selectedItem=True)
    TagForOrigin(joints[0])
    FBXExporterUI_PopulateModelRootJointsPanel()
      
    
#PURPOSE Populate the Export Nodes panel with FBX export nodes connected to the origin
#PROCEDURE Get origin from OriginTextScrollList, call ReturnFBXExportNodes, populate ModelExportNodesTextScrollList with list from that proc
#PRESUMPTION none
def FBXExporterUI_PopulateModelExportNodesPanel():
    origin=cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", query=True, selectItem=True)
    cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", edit=True, removeAll=True)
    
    if origin:
        exportNodes=ReturnFBXExportNodes(origin[0])
        
        if exportNodes:
            for cur in exportNodes:
                cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", edit=True, append=cur)
  
    
#PURPOSE Popultate the geom panel
#PROCEDURE clear the geom text scroll list, get selected export node, get meshes with ReturnConnectedMeshes, iterate through list, add each item to panel
#PRESUMPTION selected export node is a valid object
def FBXExporterUI_PopulateGeomPanel():
    cmds.textScrollList("FBXExporter_window_modelGeomTextScrollList", edit=True, removeAll=True)
    exportNodes = cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", query=True, selectItem=True)
        
    meshes=ReturnConnectedMeshes(exportNodes[0])
    
    if meshes:
        for curMesh in meshes:
            cmds.textScrollList("FBXExporter_window_modelGeomTextScrollList", edit=True, append=curMesh)

    
#PURPOSE to create new export node and add to mModel Export Nodes panel
#PROCEDURE get origin from modelOriginTextScrollList, call CreateFBXExportNode, connect to origin, repopulate ModelsExportNodesPanel
#PRESUMPTION none
def FBXExporterUI_ModelCreateNewExportNode():
    origin=cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", query=True, selectItem=True)

    if origin[0] != "Error":
        exportNode = CreateFBXExportNode(origin[0])
        
        if exportNode:
            ConnectFBXExportNodeToOrigin(exportNode, origin[0])
            FBXExporterUI_PopulateModelExportNodesPanel()    
    
      
#PURPOSE     Connect and disconnect meshes from the export node and update geom panel
#PROCEDURE get export node from textScrollList
#            get selected meshes from geom panel
#            if list of selected meshes is not empty, call DisconnectFBXExportNodeToMeshes with the list
#            if list is empty, call ConnectFBXExportNodeToMeshes
#            repopulate Geom model panel
#PRESUMPTION none
def FBXExporterUI_ModelAddRemoveMeshes():
    exportNodes=cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", query=True, selectItem=True) 
    meshes     =cmds.textScrollList("FBXExporter_window_modelGeomTextScrollList", query=True, selectItem=True) 

    if exportNodes:
        if meshes:
            DisconnectFBXExportNodeToMeshes(exportNodes[0], meshes)
        else:
            sel=cmds.ls(selection=True)
            if sel:
                ConnectFBXExportNodeToMeshes(exportNodes[0], sel)
        
        FBXExporterUI_PopulateGeomPanel()
        

#PURPOSE     Populate the UI with the export settings stored in the selected export node
#PROCEDURE   Get the selected export node from the export node scrollist
#            unlock the UI settings and set them according to the values in the selected export node
#            
#            
#            
#PRESUMPTION selected exportNode is a valid object
def FBXExporterUI_UpdateModelExportSettings():
    exportNodes = cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", query=True,selectItem=True)
    
    cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", edit=True, enable=True, text="")
    
    # in case new attrs were added to boilerplate since node was first created, normalize:
    AddFBXNodeAttrs(exportNodes[0]) 
    
    if exportNodes:
        cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", edit=True, text=cmds.getAttr(exportNodes[0] + ".exportName"))
        cmds.checkBoxGrp("FBXExporter_window_modelExportCheckBoxGrp", edit=True, enable=True, value1=cmds.getAttr(exportNodes[0] + ".export"))


#PURPOSE     Update the selected export node with the options set in the UI
#PROCEDURE   Read in the values of the UI and call setAttr on the selected export node
#            unlock the UI settings and set them according to the values in the selected export node
#            
#            
#            
#PRESUMPTION selected exportNode is valid and has the needed attributes
def FBXExporterUI_UpdateExportNodeFromModelSettings():
    exportNodes=cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", query=True, selectItem=True)
    
    if exportNodes:
        cmds.setAttr((exportNodes[0] + ".exportName"), cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", query=True, text=True), type="string")
        cmds.setAttr((exportNodes[0] + ".export"), cmds.checkBoxGrp("FBXExporter_window_modelExportCheckBoxGrp", query=True, value1=cmds.getAttr(exportNodes[0] + ".export")))


#PURPOSE     Export all characters from the scene
#PROCEDURE   
#            
#            
#            
#            
#PRESUMPTION 
def FBXExporterUI_ModelExportAllCharacters():
    origin=ReturnOrigin("")
    
    exportNodes=ReturnFBXExportNodes(origin)
    
    for cur in exportNodes:
        if cmds.objectExists(cur):
            ExportFBXCharacter(cur)


#PURPOSE     Export selected exportNode
#PROCEDURE   
#            
#            
#            
#            
#PRESUMPTION 
def FBXExporterUI_ModelExportSelectedCharacter():
    exportNodes=cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", query=True, selectItem=True)
    
    ExportFBXCharacter(exportNodes[0])


#################################
#
#    AnimLayers UI Procs
#
#################################


#PURPOSE     set the animLayer attribute on the selected export node
#PROCEDURE   get the selected export node from the UI
#            call SetAnimLayerSettings()
#            reset the button
#PRESUMPTION multiselection for textScrollList is off
def FBXExporterUI_RecordAnimLayers():
    exportNodes=cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
    
    if exportNodes and cmds.objExists(exportNodes[0]):
        SetAnimLayerSettings(exportNodes[0])
        cmds.button("FBXExporter_window_animationRecordAnimLayersButton", edit=True, label = "Re-Record Anim Layers", backgroundColor = [0.25, 0.25, 1.0])


#PURPOSE     set the animLayers according to the selected exportNode
#PROCEDURE   get selected export node from the UI
#            SetAnimLayersFromSettings()
#PRESUMPTION multiselection for textScrollList is off
def FBXExporterUI_PreviewAnimLayers():
    exportNodes=cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
    
    if exportNodes and cmds.objExists(exportNodes[0]):
        SetAnimLayersFromSettings(exportNodes[0])


#PURPOSE     blank out the animLayers string attribute in the selected export node
#PROCEDURE   get selected export nide from UI
#            call ClearAnimLayerSettings()
#            reset the Record Anim Layers button
#PRESUMPTION multiselection for textScrollList is off
def FBXExporterUI_ClearAnimLayers():
    exportNodes=cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", query=True, selectItem=True)
    
    if exportNodes and cmds.objExists(exportNodes[0]):
        ClearAnimLayerSettings(exportNodes[0])
        cmds.button("FBXExporter_window_animationRecordAnimLayersButton", edit=True, label = "Record Anim Layers", backgroundColor = [1.0, 0.25, 0.25])


#################################
#
#    Generic UI Procs
#
#################################


#PURPOSE     Allow user to choose file export filename and location
#PROCEDURE   pass in a flag to determine if request is from model or animation tab
#            get the project path
#            filename from fileDialog2
#            prune off project path
#            set the UI
#            update the export node
#            TODO: add support for non path-relative exports.  Currently pr=True is set in ExportFBX(), appending filename to end of project path string.
#PRESUMPTION proect is set properly
#            flag 1: animation tab, flag 2: model tab
def FBXExporterUI_BrowseExportFilename(flag):
    temp=""
    
    if flag == 1:
        temp=cmds.textFieldButtonGrp("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", query=True, text=True)
    elif flag == 2:
        temp=cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", query=True, text=True)
    
    project=cmds.workspace(q=True, rd=True)
    dirmask=project + "/" + temp
    newFileList = cmds.fileDialog2(fm=0, startingDirectory=dirmask, fileFilter="FBX export (*.fbx)")
        
    newFile=""
    
    if newFileList:
        newFile=newFileList[0]
        newFile=newFile.replace(project, "")
    else:
        newFile = temp
        
    if flag == 1:
        cmds.textFieldButtonGrp("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", edit=True, text=newFile)
        FBXExporterUI_UpdateExportNodeFromAnimationSettings()
        
    elif flag == 2:
        cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", edit=True, text=newFile)
        FBXExporterUI_UpdateExportNodeFromModelSettings()


#PURPOSE     Select the export node in the scene that is selected in the UI
#PROCEDURE   get export node name from selected element in ui element
#            clear slection
#            select export node
#PRESUMPTION uiElement is a textScrollList
#            elements in uiElement are valid
def FBXExporterUI_SelectExportNode(uiElement):
    exportNodes=cmds.textScrollList(uiElement, query=True, selectItem=True)
    
    if exportNodes and cmds.objExists(exportNodes[0]):
        cmds.select(clear=True)
        cmds.select(exportNodes[0])


#PURPOSE     Delete the export node in the scene that is selected in the UI
#PROCEDURE   get export node name from selected element in ui element
#            call DeleteFBXExportNode
#            update UI
#PRESUMPTION uiElement is a textScrollList
#            elements in uiElement are valid
def FBXExporterUI_DeleteExportNode(uiElement):
    exportNodes=cmds.textScrollList(uiElement, query=True, selectItem=True)
    
    if exportNodes and cmds.objExists(exportNodes[0]):
        DeleteFBXExportNode(exportNodes[0])    
        FBXExporterUI_PopulateAnimationExportNodesPanel()
        FBXExporterUI_PopulateModelExportNodesPanel()


#PURPOSE     Generate window where user can enter text to rename selected export node
#PROCEDURE   Create a new window
#            Get export node name from textScrollList
#            
#PRESUMPTION uiElement is a textScrollList
#            multiselection is off
def FBXExporterUI_RenameExportNode_UI(uiElement):
    exportNodes=cmds.textScrollList(uiElement, query=True, selectItem=True)

    if cmds.window("FBXExporter_renameExportNode_window", exists=True):
        cmds.deleteUI("FBXExporter_renameExportNode_window")
        
    cmds.window("FBXExporter_renameExportNode_window", s = False, width=225, height = 100, menuBar=True, title= "Rename ExportNode")

    cmds.frameLayout("FBXExporter_rename_frameLayout", collapsable=False, label="", borderVisible=False)
    cmds.formLayout("FBXExporter_rename_formLayout", numberOfDivisions=100, parent="FBXExporter_rename_frameLayout")
    
    cmds.textFieldGrp("FBXExporter_rename_textFieldGrp", label="New Name", columnWidth2=[75,175], parent="FBXExporter_rename_formLayout")
    cmds.button("FBXExporter_rename_renameButton", width=75, label="Rename", parent="FBXExporter_rename_formLayout", command="import FBXExporter as FBX\nFBXExporterUI_RenameExportNode(\"" + exportNodes[0] + "\")")
    cmds.button("FBXExporter_rename_cancelButton", width=75, label="Cancel", parent="FBXExporter_rename_formLayout", command="cmds.deleteUI(\"FBXExporter_renameExportNode_window\")")
    
    cmds.formLayout("FBXExporter_rename_formLayout", edit=True, attachForm=[("FBXExporter_rename_textFieldGrp", 'top', 5), ("FBXExporter_rename_textFieldGrp", 'left', 5), ("FBXExporter_rename_renameButton", 'left',50)])
    cmds.formLayout("FBXExporter_rename_formLayout", edit = True, attachControl = [("FBXExporter_rename_renameButton", 'top', 10, "FBXExporter_rename_textFieldGrp"), ("FBXExporter_rename_cancelButton", 'top', 10, "FBXExporter_rename_textFieldGrp"), ("FBXExporter_rename_cancelButton", 'left', 50, "FBXExporter_rename_renameButton")])

    cmds.showWindow("FBXExporter_renameExportNode_window")
    
     
def FBXExporterUI_RenameExportNode(exportNode):
    newName = cmds.textFieldGrp("FBXExporter_rename_textFieldGrp", query=True, text=True)
    cmds.rename(exportNode, newName)
    
    FBXExporterUI_PopulateAnimationExportNodesPanel()
    FBXExporterUI_PopulateModelExportNodesPanel()
    
    cmds.deleteUI("FBXExporter_renameExportNode_window")
    
    
#################################
#
#    Help windows
#
#################################


def FBXExporter_AnimationHelpWindow():
    if cmds.window("FBXExporter_animationHelpWindow", exists=True):
        cmds.deleteUI("FBXExporter_animationHelpWindow")
        
    cmds.window("FBXExporter_animationHelpWindow", s=True, width=500, height=500, menuBar=True, title="Help on Animation Export")
    cmds.paneLayout(configuration='horizontal4')
    cmds.scrollField(editable=False, wordWrap=True, \
        text="\
Animation Export:\n\
Animation export assumes single-level referencing with proper namespace.\n\n\
Actors: \n\
All referenced characters with an origin joint tagged with the origin attribute will be listed in the Actors field by their namespace.  Please see the Model Help window for instructions on tagging a charcter's origin with the origin attribute.\n\n\
Export Nodes:\n\
The Export Nodes panel will autofill with export nodes connected to the origin of the selected actor from the Actors field.  Clicking on the New Export Node will create a new node.  Each export node represents a separate animation.\n\n\
Export:\n\
The Export checkbox flag means the current export node will be available for export.  Nodes without this checkbox ticked will not be exported.\n\n\
Move to Origin:\n\
Not yet supported\n\n\
Sub Range:\n\
Check this box to enable the subrange option for the selected node.  This will enable the Start Frame and End Frame fields where you can set the range for the specified animation.  Otherwise, the animation will use the frame range of the project.\n\n\
Export File Name:\n\
Click on the Browse button to browse to where you want the exported file to go.  The path will be project-relative.\n\n\
Export Selected Animation:\n\
Click this button to export the animation selected in Export Nodes\n\n\
Export All Animations for Selected Character:\n\
Click this button to export all animations for the selcted actor in the Actors field.  This flag will ignore what is selected in Export Nodes and export from all founds nodes for the character.\n\n\
Export All Animations:\n\
Click this button to export all animations for all characters.  All selections will be ignored.\
        ")
    
    cmds.showWindow("FBXExporter_animationHelpWindow")



def FBXExporter_ModelHelpWindow():
    if cmds.window("FBXExporter_modelHelpWindow", exists=True):
        cmds.deleteUI("FBXExporter_modelHelpWindow")
        
    cmds.window("FBXExporter_modelHelpWindow", s=True, width=500, height=500, menuBar=True, title="Help on Model Export")
    cmds.paneLayout(configuration='horizontal4')
    cmds.scrollField(editable=False, wordWrap=True, \
        text="\
Model Export:\n\
Model export assumes one skeleton per export.  Referencing for model export is not supported.\n\n\
Root Joints: \n\
Panel will list all the joints tagged with the \"origin\" attribute.  If no joint is tagged with the attribute, it will list all joints in the scene and turn red.  Select the root joint and click the Tag as Origin button.\n\n\
Export Nodes:\n\
The Export Nodes panel will autofill with export nodes connected to the origin of the selected actor from the Actors field.  Clicking on the New Export Node will create a new node.  Each export node represents a separate character export (for example, separate LODs).\n\n\
Meshes:\n\
The Meshes panel shows all the geometry associated with the selected export node.  This can be used if you have mesh variations skinned to the same rig or LODs.\n\n\
Export File Name:\n\
Click on the Browse button to browse to where you want the exported file to go.  The path will be project-relative.\n\n\
Export Selected Character:\n\
Click this button to export the character selected in Export Nodes\n\n\
Export All Characters:\n\
Click this button to export all character definitions for the skeleton.  All selections will be ignored.\
        ")
    
    cmds.showWindow("FBXExporter_modelHelpWindow")


#################################
#
#    Main UI
#
#################################


def FBXExporter_UI():
    if cmds.window("FBXExporter_window", exists=True):
        cmds.deleteUI("FBXExporter_window")
    cmds.window("FBXExporter_window", s=True, width=400,height=600,menuBar=True, title="FBX Exporter")
    
    # generate menuBar commands
    cmds.menu("FBXExporter_window_editMenu", label = "Edit")
    cmds.menuItem(label="Save Settings", parent="FBXExporter_window_editMenu")
    cmds.menuItem(label="Reset Settings", parent="FBXExporter_window_editMenu")

    cmds.menu("FBXExporter_window_helpMenu", label = "Help")
    cmds.menuItem(label="Anim Export", command="import FBXExporter as FBX\nFBXExporter_AnimationHelpWindow()", parent="FBXExporter_window_helpMenu")
    cmds.menuItem(label="Model Export", command="import FBXExporter as FBX\nFBXExporter_ModelHelpWindow()", parent="FBXExporter_window_helpMenu")
  
    # create main tab layout
    cmds.formLayout("FBXExporter_window_mainForm")
    cmds.tabLayout("FBXExporter_window_tabLayout", innerMarginWidth=5, innerMarginHeight=5)
    cmds.formLayout("FBXExporter_window_mainForm", edit=True, attachForm=[("FBXExporter_window_tabLayout", 'top', 0), ("FBXExporter_window_tabLayout", 'left', 0), ("FBXExporter_window_tabLayout", 'bottom', 0), ("FBXExporter_window_tabLayout", 'right', 0)])
    
    # create animation UI elements
    cmds.frameLayout("FBXExporter_window_animationFrameLayout", collapsable=False, label="", borderVisible=False, parent="FBXExporter_window_tabLayout")
    cmds.formLayout("FBXExporter_window_animationFormLayout", numberOfDivisions=100, parent="FBXExporter_window_animationFrameLayout")
    cmds.textScrollList("FBXExporter_window_animationActorsTextScrollList", width=250, height=325, numberOfRows=18,allowMultiSelection=False, selectCommand="import FBXExporter as FBX\nFBXExporterUI_PopulateAnimationExportNodesPanel()", parent = "FBXExporter_window_animationFormLayout")
    cmds.textScrollList("FBXExporter_window_animationExportNodesTextScrollList", width=250, height=325, numberOfRows=18,allowMultiSelection=False, selectCommand="import FBXExporter as FBX\nFBXExporterUI_UpdateAnimationExportSettings()", parent = "FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationNewExportNodeButton", width=250, height=50, label="New Export Node", command="import FBXExporter as FBX\nFBXExporterUI_AnimationCreateNewExportNode()", parent = "FBXExporter_window_animationFormLayout")
    cmds.checkBoxGrp("FBXExporter_window_animationExportCheckBoxGrp", numberOfCheckBoxes=1, label="Export", columnWidth2 = [85,70], enable=False, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", parent = "FBXExporter_window_animationFormLayout")
    cmds.checkBoxGrp("FBXExporter_window_animationZeroOriginCheckBoxGrp", numberOfCheckBoxes=1, label="Move to Origin", columnWidth2 = [85,70], enable=False, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()\nFBXExporterUI_UpdateAnimationExportSettings()", parent = "FBXExporter_window_animationFormLayout")
    cmds.checkBoxGrp("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", numberOfCheckBoxes=1, label="Zero Motion on Origin", columnWidth2 = [120,70], enable=False, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", parent = "FBXExporter_window_animationFormLayout")
    cmds.checkBoxGrp("FBXExporter_window_animationSubRangeCheckBoxGrp", numberOfCheckBoxes=1, label="Use Sub Range", columnWidth2 = [85,70], enable=False, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()\nFBXExporterUI_UpdateAnimationExportSettings()", parent = "FBXExporter_window_animationFormLayout")
    cmds.floatFieldGrp("FBXExporter_window_animationStartFrameFloatFieldGrp", numberOfFields=1, label="Start Frame", columnWidth2=[75,70], enable=False, value1=0.0, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", parent="FBXExporter_window_animationFormLayout")
    cmds.floatFieldGrp("FBXExporter_window_animationEndFrameFloatFieldGrp", numberOfFields=1, label="End Frame", columnWidth2=[75,70], enable=False, value1=1.0, changeCommand = "import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", parent="FBXExporter_window_animationFormLayout")
    cmds.textFieldButtonGrp("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", label="Export File Name", columnWidth3=[100,300,30], enable=False, text="", buttonLabel="Browse", bc="import FBXExporter as FBX\nFBXExporterUI_BrowseExportFilename(1)", cc="import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", parent="FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationRecordAnimLayersButton", enable=False, width=150, height=50, label="Record Anim Layers", backgroundColor=[1, .25, .25], command="import FBXExporter as FBX\nFBXExporterUI_RecordAnimLayers()", parent="FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationPreviewAnimLayersButton", enable=False, width=150, height=50, label="Preview Anim Layers", command="import FBXExporter as FBX\nFBXExporterUI_PreviewAnimLayers()", parent="FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationClearAnimLayersButton", enable=False, width=150, height=50, label="Clear Anim Layers", command="import FBXExporter as FBX\nFBXExporterUI_ClearAnimLayers()", parent="FBXExporter_window_animationFormLayout")
    cmds.text("FBXExporter_window_animationActorText", label="Actors", parent="FBXExporter_window_animationFormLayout")
    cmds.text("FBXExporter_window_animationExportNodesText", label="Export Nodes", parent="FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationExportSelectedAnimationButton", width=300, height=50, label="Export Selected Animation", command="import FBXExporter as FBX\nFBXExporterUI_ExportSelectedAnimation()", parent = "FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationAllAnimationForSelectedCharacterButton", width=300, height=50, label="Export All Animation for Selected Character", command="import FBXExporter as FBX\nFBXExporterUI_ExportAllAnimationForSelectedCharacter()", parent = "FBXExporter_window_animationFormLayout")
    cmds.button("FBXExporter_window_animationExportAllAnimationsButton", width=300, height=50, label="Export All Animations", command="import FBXExporter as FBX\nFBXExporterUI_ExportAllAnimation()", parent = "FBXExporter_window_animationFormLayout")
    
    cmds.popupMenu("FBXExporter_window_animationExportNodesPopupMenu", button = 3, parent="FBXExporter_window_animationExportNodesTextScrollList")
    cmds.menuItem("FBXExporter_window_animationSelectNodeMenuItem", label="Select", command="import FBXExporter as FBX\nFBXExporterUI_SelectExportNode(\"FBXExporter_window_animationExportNodesTextScrollList\")", parent="FBXExporter_window_animationExportNodesPopupMenu")
    cmds.menuItem("FBXExporter_window_animationRenameNodeMenuItem", label="Rename", command="import FBXExporter as FBX\nFBXExporterUI_RenameExportNode_UI(\"FBXExporter_window_animationExportNodesTextScrollList\")", parent="FBXExporter_window_animationExportNodesPopupMenu")
    cmds.menuItem("FBXExporter_window_animationDeleteNodeMenuItem", label="Delete", command="import FBXExporter as FBX\nFBXExporterUI_DeleteExportNode(\"FBXExporter_window_animationExportNodesTextScrollList\")", parent="FBXExporter_window_animationExportNodesPopupMenu")
    
    # create model UI elements
    cmds.frameLayout("FBXExporter_window_modelFrameLayout", collapsable=False, label="", borderVisible=False, parent="FBXExporter_window_tabLayout")
    cmds.formLayout("FBXExporter_window_modelFormLayout", numberOfDivisions=100, parent="FBXExporter_window_modelFrameLayout")
    cmds.textScrollList("FBXExporter_window_modelOriginTextScrollList", width=175, height=220, numberOfRows=18, allowMultiSelection=False, sc="import FBXExporter as FBX\nFBXExporterUI_PopulateModelExportNodesPanel()", parent="FBXExporter_window_modelFormLayout")
    cmds.textScrollList("FBXExporter_window_modelExportNodesTextScrollList", width=175, height=220, numberOfRows=18, allowMultiSelection=False, selectCommand="import FBXExporter as FBX\nFBXExporterUI_PopulateGeomPanel()\nFBXExporterUI_UpdateModelExportSettings()", parent="FBXExporter_window_modelFormLayout")
    cmds.textScrollList("FBXExporter_window_modelGeomTextScrollList", width=175, height=220, numberOfRows=18, allowMultiSelection=True, parent="FBXExporter_window_modelFormLayout")
    cmds.button("FBXExporter_window_modelTagAsOriginButton", width=175, height=50, label = "Tag as Origin", command="import FBXExporter as FBX\nFBXExporterUI_ModelTagForOrigin()\n", parent="FBXExporter_window_modelFormLayout")
    cmds.button("FBXExporter_window_modelNewExportNodeButton", width=175, height=50, label = "New Export Node", command="import FBXExporter as FBX\nFBXExporterUI_ModelCreateNewExportNode()", parent="FBXExporter_window_modelFormLayout")
    cmds.button("FBXExporter_window_modelAddRemoveMeshesButton", width=175, height=50, label = "Add / Remove Meshes", command="import FBXExporter as FBX\nFBXExporterUI_ModelAddRemoveMeshes()", parent="FBXExporter_window_modelFormLayout")
    cmds.checkBoxGrp("FBXExporter_window_modelExportCheckBoxGrp", numberOfCheckBoxes=1, label="Export", cc="import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromModelSettings()", columnWidth2 = [85,70], enable=False, parent = "FBXExporter_window_modelFormLayout")
    cmds.text("FBXExporter_window_modelOriginText", label="Root Joints", parent="FBXExporter_window_modelFormLayout")
    cmds.text("FBXExporter_window_modelExportNodesText", label="Export Nodes", parent="FBXExporter_window_modelFormLayout")
    cmds.text("FBXExporter_window_modelMeshesText", label="Meshes", parent="FBXExporter_window_modelFormLayout")
    cmds.textFieldButtonGrp("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", label="Export File Name", bc="import FBXExporter as FBX\nFBXExporterUI_BrowseExportFilename(2)", cc="import FBXExporter as FBX\nFBXExporterUI_UpdateExportNodeFromAnimationSettings()", columnWidth3=[100,300,30], enable=False, text="", buttonLabel="Browse", parent="FBXExporter_window_modelFormLayout")
    cmds.button("FBXExporter_window_modelExportMeshButton", width=175, height=50, label = "Export Selected Character", command="import FBXExporter as FBX\nFBXExporterUI_ModelExportSelectedCharacter()", parent="FBXExporter_window_modelFormLayout")
    cmds.button("FBXExporter_window_modelExportAllMeshesButton", width=175, height=50, label = "Export All Characters", command="import FBXExporter as FBX\nFBXExporterUI_ModelExportAllCharacters()", parent="FBXExporter_window_modelFormLayout")
   
    cmds.popupMenu("FBXExporter_window_modelExportNodesPopupMenu", button = 3, parent="FBXExporter_window_modelExportNodesTextScrollList")
    cmds.menuItem("FBXExporter_window_modelSelectNodeMenuItem", label="Select", command="import FBXExporter as FBX\nFBXExporterUI_SelectExportNode(\"FBXExporter_window_modelExportNodesTextScrollList\")", parent="FBXExporter_window_modelExportNodesPopupMenu")
    cmds.menuItem("FBXExporter_window_modelRenameNodeMenuItem", label="Rename", command="import FBXExporter as FBX\nFBXExporterUI_RenameExportNode_UI(\"FBXExporter_window_modelExportNodesTextScrollList\")", parent="FBXExporter_window_modelExportNodesPopupMenu")
    cmds.menuItem("FBXExporter_window_modelDeleteNodeMenuItem", label="Delete", command="import FBXExporter as FBX\nFBXExporterUI_DeleteExportNode(\"FBXExporter_window_modelExportNodesTextScrollList\")", parent="FBXExporter_window_modelExportNodesPopupMenu")
    
    # set up tabs
    cmds.tabLayout("FBXExporter_window_tabLayout", edit=True, tabLabel=(("FBXExporter_window_animationFrameLayout","Animation"),("FBXExporter_window_modelFrameLayout","Model")))
    
    # set up animation form layout
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachForm=   [("FBXExporter_window_animationActorText", 'top', 5), ("FBXExporter_window_animationActorText", 'left', 5),("FBXExporter_window_animationActorsTextScrollList", 'left', 5),("FBXExporter_window_animationExportNodesText", 'top', 5), ("FBXExporter_window_animationExportCheckBoxGrp", 'top', 25),("FBXExporter_window_animationZeroOriginCheckBoxGrp", 'top', 25), ("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", 'top', 25),("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", 'right', 5)])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationExportNodesTextScrollList", 'left', 5, "FBXExporter_window_animationActorsTextScrollList"),             ("FBXExporter_window_animationExportCheckBoxGrp", 'left', 20, "FBXExporter_window_animationExportNodesTextScrollList"),                         ("FBXExporter_window_animationZeroOriginCheckBoxGrp", 'left', 5, "FBXExporter_window_animationExportCheckBoxGrp"),             ("FBXExporter_window_animationZeroMotionOriginCheckBoxGrp", 'left',  5, "FBXExporter_window_animationZeroOriginCheckBoxGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationSubRangeCheckBoxGrp", 'left', 20, "FBXExporter_window_animationExportNodesTextScrollList"),             ("FBXExporter_window_animationSubRangeCheckBoxGrp", 'top', 5, "FBXExporter_window_animationZeroOriginCheckBoxGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationStartFrameFloatFieldGrp", 'left', 30, "FBXExporter_window_animationExportNodesTextScrollList"),         ("FBXExporter_window_animationStartFrameFloatFieldGrp", 'top', 5, "FBXExporter_window_animationSubRangeCheckBoxGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationEndFrameFloatFieldGrp", 'left', 1, "FBXExporter_window_animationStartFrameFloatFieldGrp"),              ("FBXExporter_window_animationEndFrameFloatFieldGrp", 'top', 5, "FBXExporter_window_animationSubRangeCheckBoxGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", 'left', 5, "FBXExporter_window_animationExportNodesTextScrollList"), ("FBXExporter_window_animationExportFileNameTextFieldButtonGrp", 'top', 5, "FBXExporter_window_animationStartFrameFloatFieldGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationNewExportNodeButton", 'left', 5, "FBXExporter_window_animationActorsTextScrollList"),                   ("FBXExporter_window_animationNewExportNodeButton", 'top', 5, "FBXExporter_window_animationExportNodesTextScrollList")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationActorsTextScrollList", 'top', 5, "FBXExporter_window_animationActorText"),                              ("FBXExporter_window_animationExportNodesTextScrollList", 'top', 5, "FBXExporter_window_animationExportNodesText"),                             ("FBXExporter_window_animationExportNodesText", 'left', 225, "FBXExporter_window_animationActorText")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationRecordAnimLayersButton", 'top', 10, "FBXExporter_window_animationExportFileNameTextFieldButtonGrp"),    ("FBXExporter_window_animationPreviewAnimLayersButton", 'top', 10, "FBXExporter_window_animationExportFileNameTextFieldButtonGrp"),             ("FBXExporter_window_animationClearAnimLayersButton", 'top', 10, "FBXExporter_window_animationExportFileNameTextFieldButtonGrp")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationRecordAnimLayersButton", 'left', 10, "FBXExporter_window_animationExportNodesTextScrollList"),          ("FBXExporter_window_animationPreviewAnimLayersButton", 'left', 10, "FBXExporter_window_animationRecordAnimLayersButton"),                      ("FBXExporter_window_animationClearAnimLayersButton", 'left', 10, "FBXExporter_window_animationPreviewAnimLayersButton")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationExportSelectedAnimationButton", 'top', 10, "FBXExporter_window_animationRecordAnimLayersButton"),       ("FBXExporter_window_animationAllAnimationForSelectedCharacterButton", 'top', 10, "FBXExporter_window_animationExportSelectedAnimationButton"), ("FBXExporter_window_animationExportAllAnimationsButton", 'top', 10, "FBXExporter_window_animationAllAnimationForSelectedCharacterButton")])
    cmds.formLayout("FBXExporter_window_animationFormLayout", edit=True, attachControl=[("FBXExporter_window_animationExportSelectedAnimationButton", 'left', 100, "FBXExporter_window_animationExportNodesTextScrollList"),  ("FBXExporter_window_animationAllAnimationForSelectedCharacterButton", 'left', 100, "FBXExporter_window_animationExportNodesTextScrollList"),   ("FBXExporter_window_animationExportAllAnimationsButton", 'left', 100, "FBXExporter_window_animationExportNodesTextScrollList")])
    
    # set up model form layout
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit=True, attachForm=[("FBXExporter_window_modelOriginText", 'top', 5), ("FBXExporter_window_modelOriginText", 'left', 5), ("FBXExporter_window_modelExportNodesText", 'top', 5), ("FBXExporter_window_modelMeshesText", 'top', 5), ("FBXExporter_window_modelExportCheckBoxGrp", 'top', 25), ("FBXExporter_window_modelTagAsOriginButton", 'left', 0)])   
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportNodesText", 'left', 125, "FBXExporter_window_modelOriginText"), ("FBXExporter_window_modelMeshesText", 'left', 120, "FBXExporter_window_modelExportNodesText")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelOriginTextScrollList", 'top', 5, "FBXExporter_window_modelOriginText"),("FBXExporter_window_modelExportNodesTextScrollList", 'top', 5, "FBXExporter_window_modelExportNodesText"), ("FBXExporter_window_modelGeomTextScrollList", 'top', 5, "FBXExporter_window_modelMeshesText")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportNodesTextScrollList", 'left', 5, "FBXExporter_window_modelOriginTextScrollList"), ("FBXExporter_window_modelGeomTextScrollList", 'left', 5, "FBXExporter_window_modelExportNodesTextScrollList")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelNewExportNodeButton", 'left', 5, "FBXExporter_window_modelOriginTextScrollList"), ("FBXExporter_window_modelNewExportNodeButton", 'top', 5, "FBXExporter_window_modelExportNodesTextScrollList")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", 'left', 5, "FBXExporter_window_modelGeomTextScrollList"),("FBXExporter_window_modelTagAsOriginButton", 'top', 5, "FBXExporter_window_modelOriginTextScrollList")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportMeshButton", 'top', 15, "FBXExporter_window_modelExportFileNameTextFieldButtonGrp"),("FBXExporter_window_modelExportMeshButton", 'left', 125, "FBXExporter_window_modelGeomTextScrollList")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelAddRemoveMeshesButton", 'top', 5, "FBXExporter_window_modelGeomTextScrollList"),("FBXExporter_window_modelAddRemoveMeshesButton", 'left', 5, "FBXExporter_window_modelNewExportNodeButton")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportAllMeshesButton", 'top', 5, "FBXExporter_window_modelExportMeshButton"),("FBXExporter_window_modelExportAllMeshesButton", 'left', 125, "FBXExporter_window_modelGeomTextScrollList")])
    cmds.formLayout("FBXExporter_window_modelFormLayout", edit= True, attachControl=[("FBXExporter_window_modelExportFileNameTextFieldButtonGrp", 'top', 5, "FBXExporter_window_modelExportCheckBoxGrp"),("FBXExporter_window_modelExportCheckBoxGrp", 'left', 125, "FBXExporter_window_modelGeomTextScrollList")])
    
    # populate UI
    FBXExporterUI_PopulateModelRootJointsPanel()
    FBXExporterUI_PopulateAnimationActorsPanel()
    
    # scriptJob to refresh UI
    cmds.scriptJob(parent="FBXExporter_window", e=["PostSceneRead", "import FBXExporter as FBX\nFBXExportUI_PopulateModelRootJointsPanel()"])
    cmds.scriptJob(parent="FBXExporter_window", e=["PostSceneRead", "import FBXExporter as FBX\nFBXExportUI_PopulateAnimationActorsPanel()"])
    
    cmds.showWindow("FBXExporter_window")
