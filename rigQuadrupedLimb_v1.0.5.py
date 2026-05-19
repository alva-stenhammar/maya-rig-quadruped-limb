"""
AUTO LIMB RIGGING SCRIPT V.1.0.5
Created by Alva Stenhammar

TO ADD:
- make hock control better
- make button to match ik to fk and vice versa
- create controls if there are none?

"""


import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel
import functools
import math

scriptVersion = "V.1.0.5"



def _______________UI_______________(): pass


def createUI(autoRigLimb):
    """ Create and open the UI. """
    

    # WINDOW CREATION
    windowID = "rigQuadrupedLimbWindowID"
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    cmds.window(windowID, title=f"Rig Quadruped Limb {scriptVersion}", sizeable=False)

    mainLayout = cmds.columnLayout(width=330, margins=5)

    cmds.columnLayout(margins=10,
                      parent=mainLayout)
    cmds.text(label="Rig Quadruped Limb Tool", width=300,
              font="boldLabelFont")
    cmds.separator(height=10, style="none")

    
    # LAYOUT-1: GLOBAL SETTINGS
    layout = cmds.frameLayout(label="Options",
                     width=320,
                     marginWidth=20,
                     marginHeight=10,
                     backgroundShade=True,
                     font="boldLabelFont",
                     parent=mainLayout)
    
    cmds.text(label="""Select hip/shoulder joint to rig.""", width=280,
              font="smallPlainLabelFont")
    
    cmds.separator(height=2,
                  style="none",
                  backgroundColor=(0.2, 0.2, 0.2))

    cmds.rowColumnLayout(numberOfColumns=2,
                         columnWidth=[(1, 140), (2, 140)],
                         columnOffset=[(1, "right", 10), (2, "left", 10)],
                         rowSpacing=(1, 5))

    cmds.text("Limb Side:")
    limbSideMenu = cmds.optionMenu()
    cmds.menuItem(label="Left")
    cmds.menuItem(label="Right")

    cmds.text("Limb Type:")
    limbTypeMenu = cmds.optionMenu()
    cmds.menuItem(label="Front")
    cmds.menuItem(label="Rear")

    cmds.text(label="Limb Name:")
    limbNameField = cmds.textField(text="leg")

    cmds.text(label="Control Suffix:")
    controlSuffixField = cmds.textField(text="CTRL")

    cmds.text(label="Stretch:")
    stretchBox = cmds.checkBox(label="", value=True)
    
    cmds.text(label="Roll Joints:")
    rollJointsBox = cmds.checkBox(label="", value=True)

    cmds.text(label="Pole Vector Arrow:")
    poleVectorArrowBox = cmds.checkBox(label="", value=True)

    cmds.separator(height=10, style="none", parent=mainLayout)


    # APPLY/CANCEL BUTTONS
    cmds.separator(height=5, style="none", enableBackground=False)

    cmds.rowLayout(numberOfColumns=1,
                   columnWidth=(1, 300), parent=layout)
    
    cmds.button(label="Apply", width=280,
                command=functools.partial(autoRigLimb,
                                          limbSideMenu,
                                          limbTypeMenu,
                                          limbNameField,
                                          controlSuffixField,
                                          stretchBox,
                                          rollJointsBox,
                                          poleVectorArrowBox))
    
    cmds.columnLayout(margins=10,
                      parent=mainLayout)
    cmds.text(label="Created by Alva Stenhammar", width=300,
              font="obliqueLabelFont")
    cmds.text(label=scriptVersion, width=300,
              font="smallObliqueLabelFont")
        
    cmds.showWindow()



def _______________GENERIC_______________(): pass


def lerp(a: float, b: float, t: float) -> float:
        """ Linear interpolate on the scale given by a to b, using t as the point on that scale. """
        return (1 - t) * a + t * b



def dist(a: list[float], b: list[float]) -> float:
        """ Calculate distance between two points in 3D space. """
        return math.sqrt(((b[0] - a[0]) ** 2) + ((b[1] - a[1]) ** 2) + ((b[2] - a[2]) ** 2))



def _______________CREATE_______________(): pass
    
    

def createFKIK(jointHierarchy: list,
              limbNames: tuple,
              controlNames: tuple):
    """ Adds FK and IK setup with switch between. """

    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    limbType = limb.split("_")[1]

    newJointTypes = ["_IK", "_FK"]
    if limbType == "rear":
        newJointTypes.append("_DRIVER")


    # create new joint chains
    for newJointType in newJointTypes:
        for i in range(4):
            newJointName = jointHierarchy[i] + newJointType

            cmds.joint(name=newJointName, radius=1)
            cmds.matchTransform(newJointName, jointHierarchy[i])
            cmds.makeIdentity(newJointName,
                              apply=True, rotate=True, scale=False)

        cmds.select(clear=True)
    
    # set preferred for IK joints
    IKjoints = []
    for i, joint in enumerate(jointHierarchy):
        if i < 4:
            IKjoints.append(f"{joint}_IK")

    for i, obj in enumerate(IKjoints):
        currentRotation = cmds.xform(obj,query=True,rotation=True,worldSpace=False)
        cmds.setAttr(f'{obj}.preferredAngleX', currentRotation[0])
        cmds.setAttr(f'{obj}.preferredAngleY', currentRotation[1])
        cmds.setAttr(f'{obj}.preferredAngleZ', currentRotation[2])
   

    # FK

    # connect fk controls to fk joints
    for i in range(4):
        cmds.parentConstraint(f"{jointHierarchy[i]}_FK_CTRL",
                              f"{jointHierarchy[i]}_FK",
                              maintainOffset=False)

    
    # IK

    # IK HANDLES
    # create driver ik handle for rear legs
    if limbType == "rear":
        mel.eval("ikSpringSolver")
        cmds.ikHandle(name=f"{limb}_DRIVER_ikHandle",
                      solver="ikSpringSolver",
                      startJoint=f"{root}_DRIVER",
                      endEffector=f"{foot}_DRIVER")
        
        # update pole vector to fix flipping
        cmds.setAttr(f"{limb}_DRIVER_ikHandle.poleVectorX", 0)
        cmds.setAttr(f"{limb}_DRIVER_ikHandle.poleVectorY", 0)
        cmds.setAttr(f"{limb}_DRIVER_ikHandle.poleVectorZ", 1)

    # create main ik handle
    cmds.ikHandle(name=f"{knee}_ikHandle",
                  solver="ikRPsolver",
                  startJoint=f"{root}_IK",
                  endEffector=f"{hock}_IK")
    
    # create hock ik handle
    cmds.ikHandle(name=f"{hock}_ikHandle",
                  solver="ikRPsolver",
                  startJoint=f"{hock}_IK",
                  endEffector=f"{foot}_IK")


    # HOCK CONTROL OFFSET
    # create hock ctrl offset group
    cmds.group(f"{knee}_ikHandle", name=f"{hock}_CTRL")
    cmds.group(f"{hock}_CTRL", name=f"{hock}_CTRL_OFFSET")
    
    # find foot pivot and match ctrl offset group pivot to it
    footPivot = cmds.xform(foot,
                           query=True, worldSpace=True, pivots=True)
    
    cmds.xform(f"{hock}_CTRL",
               f"{hock}_CTRL_OFFSET",
               worldSpace=True,
               pivots=(footPivot[0], footPivot[1], footPivot[2]))


    # PARENTING
    # if rear leg, make driver leg control ik handles
    if limbType == "rear":
        cmds.parent(f"{hock}_CTRL_OFFSET", f"{hock}_DRIVER")
        cmds.parent(f"{hock}_ikHandle", f"{foot}_DRIVER")
        
        cmds.parentConstraint(footControl, f"{limb}_DRIVER_ikHandle")
        cmds.parent(f"{limb}_DRIVER_ikHandle", f"{limb}_GRP")
        
    else:
        cmds.parent(f"{hock}_CTRL_OFFSET", f"{limb}_GRP")
        cmds.pointConstraint(footControl, f"{hock}_CTRL_OFFSET")
        cmds.parent(f"{hock}_ikHandle", f"{limb}_GRP")
        cmds.parentConstraint(footControl, f"{hock}_ikHandle")

    # make foot control drive ankle joint orientation
    cmds.orientConstraint(footControl, f"{foot}_IK")


    # POLE VECTOR
    if limbType == "rear":
        cmds.poleVectorConstraint(kneeControl, f"{limb}_DRIVER_ikHandle")
    else:
        cmds.poleVectorConstraint(kneeControl, f"{knee}_ikHandle")


    
def createFKIKblend(jointHierarchy: list[str],
                    limbNames: tuple,
                    controlNames: tuple):
    """ Make FK and IK joints control main joints and add ability to blend between them. """

    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    limbType = limb.split("_")[1]

    # add attribute divider
    cmds.select(mainControl)
    cmds.addAttr(attributeType="enum",
                 longName="optionsDivider",
                 niceName="——————————",
                 enumName="OPTIONS")
    cmds.setAttr(f"{mainControl}.optionsDivider", channelBox=True)
    cmds.select(clear=True)

    # add fk/ik switch attribute to main controller
    cmds.select(mainControl)
    cmds.addAttr(attributeType="float",
                 hasMaxValue=True, hasMinValue=True,
                 maxValue=1, minValue=0,
                 longName="FKIKswitch",
                 niceName="FK/IK Switch")
    cmds.setAttr(f"{mainControl}.FKIKswitch", keyable=True)
    cmds.setAttr(f"{mainControl}.FKIKswitch", 1)
    cmds.select(clear=True)

    # constrain main joints to ik and fk joints
    for i in range(4):
        cmds.parentConstraint(f"{jointHierarchy[i]}_IK",
                              f"{jointHierarchy[i]}_FK",
                              jointHierarchy[i],
                              maintainOffset=False)

    cmds.shadingNode("reverse", asUtility=True, name=f"{limb}_FKIK_reverse")
    cmds.connectAttr(f"{mainControl}.FKIKswitch",
                     f"{limb}_FKIK_reverse.inputX",
                     force=True)

    for i in range(4):
        getConstraint = cmds.listConnections(jointHierarchy[i], type="parentConstraint")[0]
        getWeights = cmds.parentConstraint(getConstraint, query=True, weightAliasList=True)

        cmds.connectAttr(f"{mainControl}.FKIKswitch",
                         f"{getConstraint}.{getWeights[0]}",
                         force=True)
        cmds.connectAttr(f"{limb}_FKIK_reverse.outputX",
                         f"{getConstraint}.{getWeights[1]}",
                         force=True)
        
    # UPDATE HIERARCHY
    cmds.parent(f"{jointHierarchy[0]}_FK",
                f"{jointHierarchy[0]}_IK",
                (limb + "_GRP"))
    
    if limbType == "rear":
        cmds.parent(f"{jointHierarchy[0]}_DRIVER", f"{limb}_GRP")
        cmds.pointConstraint(rootControl,
                             f"{jointHierarchy[0]}_DRIVER")
    
    cmds.pointConstraint(rootControl, f"{jointHierarchy[0]}_IK")
    
    cmds.parentConstraint(rootControl, f"{limb}_GRP",
                          maintainOffset=True)
    
    cmds.select(clear=True)



def createStretch(jointHierarchy: list,
                  limbNames: tuple,
                  controlNames: tuple):
    """ Add stretch to IK limb with options for stretchiness and stretch type. """

    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    limbType = limb.split("_")[1]

    # create stretch joints
    for i in range(4):
        newJointName = f"{jointHierarchy[i]}_STRETCH"

        cmds.joint(name=newJointName, radius=0.5)
        cmds.matchTransform(newJointName, jointHierarchy[i])
        cmds.makeIdentity(newJointName,
                          apply=True, rotate=True, scale=False)

    cmds.select(clear=True)

    # create end position locator, move to foot joint, and parent to foot control
    cmds.spaceLocator(name=f"{limb}_STRETCH_endPos_LOC")
    cmds.matchTransform(f"{limb}_STRETCH_endPos_LOC", jointHierarchy[3])
    cmds.parent(f"{limb}_STRETCH_endPos_LOC", footControl)

    # build distance nodes for each section (but skip toe joints)
    cmds.shadingNode("plusMinusAverage", asUtility=True, name=(limb + "_length"))

    for i in range(4 - 1):
            cmds.shadingNode("distanceBetween", asUtility=True, name=f"{jointHierarchy[i]}_distnode")

            cmds.connectAttr(f"{jointHierarchy[i]}_STRETCH.worldMatrix",
                             f"{jointHierarchy[i]}_distnode.inMatrix1",
                             force=True)
            cmds.connectAttr(f"{jointHierarchy[i+1]}_STRETCH.worldMatrix",
                             f"{jointHierarchy[i]}_distnode.inMatrix2",
                             force=True)
            
            cmds.connectAttr(f"{jointHierarchy[i]}_STRETCH.rotatePivotTranslate",
                             f"{jointHierarchy[i]}_distnode.point1",
                             force=True)
            cmds.connectAttr(f"{jointHierarchy[i+1]}_STRETCH.rotatePivotTranslate",
                             f"{jointHierarchy[i]}_distnode.point2",
                             force=True)
            
            cmds.connectAttr(f"{jointHierarchy[i]}_distnode.distance",
                             f"{limb}_length.input1D[{str(i)}]",
                             force=True)

    # get distance from root to stretch end locator
    cmds.shadingNode("distanceBetween", asUtility=True, name=f"{limb}_STRETCH_distnode")

    cmds.connectAttr(f"{root}_STRETCH.worldMatrix",
                     f"{limb}_STRETCH_distnode.inMatrix1",
                     force=True)
    cmds.connectAttr(f"{limb}_STRETCH_endPos_LOC.worldMatrix",
                     f"{limb}_STRETCH_distnode.inMatrix2",
                     force=True)
    
    cmds.connectAttr(f"{root}_STRETCH.rotatePivotTranslate",
                     f"{limb}_STRETCH_distnode.point1",
                     force=True)
    cmds.connectAttr(f"{limb}_STRETCH_endPos_LOC.rotatePivotTranslate",
                     f"{limb}_STRETCH_distnode.point2",
                     force=True)
    
    # create nodes to check for and control stretching
    cmds.shadingNode("multiplyDivide", asUtility=True, name=f"{limb}_scaleFactor")
    cmds.shadingNode("condition", asUtility=True, name=f"{limb}_condition")

    # adjust node settings
    cmds.setAttr(f"{limb}_scaleFactor.operation", 2)
    cmds.setAttr(f"{limb}_condition.operation", 2)
    cmds.setAttr(f"{limb}_condition.secondTerm", 1)

    # connect stretch distance to scale factor
    cmds.connectAttr(f"{limb}_STRETCH_distnode.distance",
                     f"{limb}_scaleFactor.input1X",
                     force=True)
    
    # connect leg distance to scale factor
    cmds.connectAttr(f"{limb}_length.output1D",
                     f"{limb}_scaleFactor.input2X",
                     force=True)
    
    # connect stretch factor to the condition's first term
    cmds.connectAttr(f"{limb}_scaleFactor.outputX",
                     f"{limb}_condition.firstTerm",
                     force=True)
    
    # connect stretch factor to color if true (stretch value)
    cmds.connectAttr(f"{limb}_scaleFactor.outputX",
                     f"{limb}_condition.colorIfTrueR",
                     force=True)
    
    # connect stretch value to ik and driver joints (using translate instead of scale)
    for i in range(4 - 1):
        # create node to calculate translateX value
        cmds.shadingNode("multiplyDivide", asUtility=True, name=f"{jointHierarchy[i + 1]}_translation")
        cmds.setAttr(f"{jointHierarchy[i + 1]}_translation.operation", 1)     # 1 = multiply

        # calculate translateX value with default translateX multiplied by scale factor
        cmds.connectAttr(f"{jointHierarchy[i + 1]}_STRETCH.translateX",
                         f"{jointHierarchy[i + 1]}_translation.input1X")
        cmds.connectAttr(f"{limb}_condition.outColorR",
                         f"{jointHierarchy[i + 1]}_translation.input2X")
        
        # connect translate output to ik and driver joints translateX
        cmds.connectAttr(f"{jointHierarchy[i + 1]}_translation.outputX",
                         f"{jointHierarchy[i + 1]}_IK.translateX")
        
        if limbType == "rear":
            cmds.connectAttr(f"{jointHierarchy[i + 1]}_translation.outputX",
                             f"{jointHierarchy[i + 1]}_DRIVER.translateX")
            
    
    # STRETCH CONTROL ATTRIBUTES

    # create stretchiness and stretch type attributes for main control
    cmds.select(mainControl)
    cmds.addAttr(attributeType="enum",
                 enumName="Both:Stretch:Squash",
                 longName="stretchType",
                 niceName="Stretch Type")
    cmds.setAttr(f"{mainControl}.stretchType", keyable=True)
    cmds.select(clear=True)

    cmds.select(mainControl)
    cmds.addAttr(attributeType="float",
                 hasMaxValue=True, hasMinValue=True,
                 maxValue=1, minValue=0,
                 longName="stretchiness",
                 niceName="Stretchiness")
    cmds.setAttr(f"{mainControl}.stretchiness", keyable=True)
    cmds.select(clear=True)


    # create blend colors node
    cmds.shadingNode("blendColors", asUtility=True, name=f"{limb}_blendColors")
    cmds.setAttr(f"{limb}_blendColors.color2",
                 1, 0, 0, type="double3")

    cmds.connectAttr(f"{limb}_scaleFactor.outputX",
                     f"{limb}_blendColors.color1R",
                     force=True)
    cmds.connectAttr(f"{limb}_blendColors.outputR",
                     f"{limb}_condition.colorIfTrueR",
                     force=True)

    # connect to foot control attribute
    cmds.connectAttr(f"{mainControl}.stretchiness",
                     f"{limb}_blendColors.blender",
                     force=True)
    
    # connect attributes for stretch control
    # stretch type = both
    cmds.setAttr(f"{mainControl}.stretchType", 0)
    cmds.setAttr(f"{limb}_condition.operation", 1) # 1 = not equal

    cmds.setDrivenKeyframe(f"{limb}_condition.operation",
                           currentDriver=f"{mainControl}.stretchType")
    
    # stretch type = stretch
    cmds.setAttr(f"{mainControl}.stretchType", 1)
    cmds.setAttr(f"{limb}_condition.operation", 3) # 3 = greater than

    cmds.setDrivenKeyframe(f"{limb}_condition.operation",
                           currentDriver=f"{mainControl}.stretchType")
    
    # stretch type = squash
    cmds.setAttr(f"{mainControl}.stretchType", 2)
    cmds.setAttr(f"{limb}_condition.operation", 5) # 5 = less than or equal

    cmds.setDrivenKeyframe(f"{limb}_condition.operation",
                           currentDriver=f"{mainControl}.stretchType")
    
    # set default values
    cmds.setAttr(f"{mainControl}.stretchiness", 1)
    cmds.setAttr(f"{mainControl}.stretchType", 1)

    # update hierarchy
    cmds.parent(f"{jointHierarchy[0]}_STRETCH", f"{limb}_GRP")

    cmds.select(clear=True)



def createVolumePreservation(jointHierarchy: list,
                             limbNames: tuple,
                             controlNames: tuple):
    """ Add volume preservation for IK limb with volume offset attribute. """
    
    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    # create volume offset attribute on main controller
    cmds.select(mainControl)
    cmds.addAttr(attributeType="float",
                 longName="volumeOffset",
                 niceName="Volume Offset")
    cmds.setAttr(f"{mainControl}.volumeOffset", keyable=True)
    cmds.select(clear=True)

    # create multiply divide node with operation power
    cmds.shadingNode("multiplyDivide", asUtility=True, name=f"{limb}_volume")
    cmds.setAttr(f"{limb}_volume.operation", 3)

    # connect main stretch value to volume node
    cmds.connectAttr(f"{limb}_blendColors.outputR",
                     f"{limb}_volume.input1X",
                     force=True)

    # connect volume node to condition node to control scaling
    cmds.connectAttr(f"{limb}_volume.outputX",
                     f"{limb}_condition.colorIfTrueG",
                     force=True)
    
    # connect to knee
    cmds.connectAttr(f"{limb}_condition.outColorG",
                     f"{knee}.scaleY",
                     force=True)
    cmds.connectAttr(f"{limb}_condition.outColorG",
                     f"{knee}.scaleZ",
                     force=True)
    
    # connect to hock
    cmds.connectAttr(f"{limb}_condition.outColorG",
                     f"{hock}.scaleY",
                     force=True)
    cmds.connectAttr(f"{limb}_condition.outColorG",
                     f"{hock}.scaleZ",
                     force=True)
    
    # connect to main volume attribute
    cmds.connectAttr(f"{mainControl}.volumeOffset",
                     f"{limb}_volume.input2X",
                     force=True)
    
    cmds.select(clear=True)



def createRollJoints(jointHierarchy: list,
                     limbNames: tuple,
                     controlNames: tuple):
    """ Adds roll joints for the root joint (femur/humerus) and foot joint. """

    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    rollJointList = [f"{root}_ROLL", f"{foot}_ROLL", f"{root}_FOLLOW", f"{root}_FOLLOW_TIP"]

    for i, rollJointName in enumerate(rollJointList):
        rollJoint = "_".join(rollJointList[i].split("_")[:-1])

    # create roll joints and move to the normal joints
        cmds.joint(name=rollJointName, radius=1)
        cmds.matchTransform(rollJointName, rollJoint)
        cmds.makeIdentity(rollJointName,
                          apply=True, translate=False, rotate=True, scale=False)

        cmds.select(clear=True)

        if i < 2:       # apply to 1st and 2nd items
            cmds.parent(rollJointName, rollJoint)
        elif i > 2:     # apply to 4th item
            cmds.parent(rollJointName, f"{root}_FOLLOW")

        cmds.select(clear=True)

    
    # UPPER LEG
    
    # temp point constraint to move joint to the middle
    cmds.pointConstraint(root,
                         knee,
                         f"{root}_FOLLOW_TIP",
                         maintainOffset=False, name="tempPC")
    cmds.delete("tempPC")

    # move joint out
    cmds.move(0, 0, -5, f"{root}_FOLLOW",
              relative=True, objectSpace=True, worldSpaceDistance=True)

    # create aim locator for root roll joint to follow
    cmds.spaceLocator(name=f"{root}_ROLL_AIM")

    # move it to the root joint and parent it to the follow joint
    cmds.matchTransform(f"{root}_ROLL_AIM", f"{root}_FOLLOW")
    cmds.parent(f"{root}_ROLL_AIM", f"{root}_FOLLOW")
    
    # move locator out
    cmds.move(0, 0, -5, f"{root}_ROLL_AIM",
              relative=True, objectSpace=True, worldSpaceDistance=True)
    
    # make root joint aim at next joint with aim locator as world up object
    cmds.aimConstraint(knee, f"{root}_ROLL",
                       aim=(1, 0, 0), upVector=(0, 0, -1),
                       maintainOffset=True,
                       worldUpType="object",
                       worldUpObject=f"{root}_ROLL_AIM")
    
    # create ik handle so follow joints will follow the leg
    cmds.ikHandle(name=f"{limb}_FOLLOW_ikHandle",
                  solver="ikRPsolver",
                  startJoint=f"{root}_FOLLOW",
                  endEffector=f"{root}_FOLLOW_TIP")

    # parent it  and move it to the follow joint
    cmds.parentConstraint(knee, f"{limb}_FOLLOW_ikHandle")
    cmds.matchTransform(f"{limb}_FOLLOW_ikHandle", knee)
    
    # reset pole vector to stop limb twisting
    for axis in ["X", "Y", "Z"]:
        cmds.setAttr(f"{limb}_FOLLOW_ikHandle.poleVector{axis}", 0)

    
    # LOWER LEG

    # create aim locator for foot roll joint to follow
    cmds.spaceLocator(name=f"{foot}_ROLL_AIM")

    # move it to the root joint and parent it to the follow joint
    cmds.matchTransform(f"{foot}_ROLL_AIM", f"{foot}_ROLL")
    cmds.parent(f"{foot}_ROLL_AIM", foot)
    
    # move locator out
    cmds.move(5, 0, 0, f"{foot}_ROLL_AIM",
              relative=True, objectSpace=True, worldSpaceDistance=True)
    
    # make roll joint aim at joint above (hock) with aim locator as world up object
    cmds.aimConstraint(hock, f"{foot}_ROLL",
                       aim=(0, 1, 0), upVector=(1, 0, 1), maintainOffset=True,
                       worldUpType="object", worldUpObject=f"{foot}_ROLL_AIM")

    # update hierarchy
    cmds.parent(f"{root}_FOLLOW", f"{limb}_GRP")
    cmds.parent(f"{limb}_FOLLOW_ikHandle", f"{limb}_GRP")
    

    cmds.select(clear=True)



def createPoleVectorArrow(jointHierarchy: list[str],
                          limb: str,
                          knee: str,
                          ctrlSuffix: str):
    """ Add annotation arrow between the joint and the pole vector control. """

    arrowName = f"{knee}_ARROW"
    annotationShape = cmds.createNode("annotationShape", name=f"{arrowName}Shape")

    cmds.connectAttr(f"{knee}_IK_{ctrlSuffix}Shape.worldMatrix[0]",
                        f"{annotationShape}.dagObjectMatrix[0]")
    
    cmds.parentConstraint(f"{jointHierarchy[1]}_IK", arrowName, maintainOffset=False)

    # if there is a controls group, parent arrow to it
    if cmds.objExists(f"{limb}_IK_controls"):
        cmds.parent(arrowName, f"{limb}_IK_controls")



def createFKIKvisiblity(limb: str, mainControl: str):
    """ If there is a group of the IK and FK controls, connect the visibility attribute to the FK/IK switch. """

    if cmds.objExists(f"{limb}_FK_controls"):
        cmds.shadingNode("reverse", asUtility=True, name=f"{limb}_FKIK_visibility_reverse")

        cmds.connectAttr(f"{mainControl}.FKIKswitch", f"{limb}_FKIK_visibility_reverse.inputX")
        cmds.connectAttr(f"{limb}_FKIK_visibility_reverse.outputX", f"{limb}_FK_controls.visibility")
    
    if cmds.objExists(f"{limb}_IK_controls"):
        cmds.connectAttr(f"{mainControl}.FKIKswitch", f"{limb}_IK_controls.visibility")



def createProxyAttributes(controlNames: tuple):
    """ Add proxy attributes to all relevant controls. """

    # unpack
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    cmds.select(clear=True)

    # IK controls
    for IKcontrol in [rootControl, kneeControl, hockControl, footControl]:
        for attribute in ["optionsDivider", "FKIKswitch", "stretchType", "stretchiness", "volumeOffset"]:
            if IKcontrol == kneeControl:
                continue
            cmds.select(IKcontrol)
            cmds.addAttr(longName=attribute, proxy=f"{mainControl}.{attribute}")
            cmds.setAttr(f"{IKcontrol}.{attribute}", keyable=True)
            cmds.select(clear=True)

    # FK controls
    for IKcontrol in [rootControl, kneeControl, hockControl, footControl]:
        FKcontrol = IKcontrol.replace("IK", "FK")

        for attribute in ["optionsDivider", "FKIKswitch"]:
            cmds.select(FKcontrol)
            cmds.addAttr(longName=attribute, proxy=f"{mainControl}.{attribute}")
            cmds.setAttr(f"{FKcontrol}.{attribute}", keyable=True)
            cmds.select(clear=True)



def connectControls(jointHierarchy: list[str],
                    limbNames: tuple,
                    controlNames: tuple):
    """ Connect the controls to each other and setup parenting. """

    # unpack
    limb, root, knee, hock, foot = limbNames
    mainControl, rootControl, kneeControl, hockControl, footControl = controlNames

    limbType = limb.split("_")[1]


    # FK CONTROLS
    
    FKcontrolList = []
    for control in [rootControl, kneeControl, hockControl, footControl]:
        FKcontrol = control.replace("IK", "FK")
        FKcontrolList.append(FKcontrol)

    for i, FKcontrol in enumerate(FKcontrolList):
        if i != 0:
            cmds.parentConstraint(FKcontrolList[i - 1], f"{FKcontrol}_GRP",
                                  maintainOffset=True)

    
    # IK CONTROLS

    # HOCK
    # connect hock joint y translate -> control y translate
    cmds.shadingNode("decomposeMatrix", name=f"{hock}_decomposeMatrix", asUtility=True)
    cmds.connectAttr(f"{hock}.worldMatrix[0]", f"{hock}_decomposeMatrix.inputMatrix",
                    force=True)
    cmds.connectAttr(f"{hock}_decomposeMatrix.outputTranslateY", f"{hockControl}_GRP.translateY",
                    force=True)
        
    if limbType == "rear":
        # constraint hock control between foot and root
        hockConstraint = cmds.pointConstraint(footControl, rootControl, f"{hockControl}_GRP",
                                            maintainOffset=True, skip="y")[0]
        
        cmds.setAttr(f"{hockConstraint}.{rootControl}W1", 0.35)

    else:
        cmds.pointConstraint(footControl, f"{hockControl}_GRP",
                             maintainOffset=True, skip="y")


    # POLE VECTOR
    # add attribute divider
    cmds.select(kneeControl)
    cmds.addAttr(attributeType="enum",
                 longName="optionsDivider",
                 niceName="——————————",
                 enumName="OPTIONS")
    cmds.setAttr(f"{kneeControl}.optionsDivider", channelBox=True)
    cmds.select(clear=True)

    # create follow attribute
    cmds.select(kneeControl)
    cmds.addAttr(attributeType="float",
                 hasMaxValue=True, hasMinValue=True,
                 maxValue=1, minValue=0,
                 longName="follow",
                 niceName="Follow")
    cmds.setAttr(f"{kneeControl}.follow", keyable=True)
    cmds.setAttr(f"{kneeControl}.follow", 1)
    cmds.select(clear=True)

    # create world space locator
    if not cmds.objExists("worldSpace_LOCATOR"):
        cmds.spaceLocator(name="worldSpace_LOCATOR")
        cmds.parent("worldSpace_LOCATOR", "rig_systems")
    
        if cmds.objExists("main_CTRL"):
            cmds.parent("worldSpace_LOCATOR", "main_CTRL")
    
    # pole vector offset setup
    offsetParent = cmds.spaceLocator(name=f"{limb}_poleVector_offsetParent")[0]
    upObject = cmds.spaceLocator(name=f"{limb}_poleVector_aim_upObject")[0]

    cmds.matchTransform(upObject, f"{root}_IK", position=True, rotation=False)

    cmds.move(0, 0, 10, upObject,
              relative=True, objectSpace=True, worldSpaceDistance=True)

    cmds.pointConstraint(f"{root}_IK", offsetParent)
    cmds.aimConstraint(footControl, offsetParent,
                       aim=(1, 0, 0), upVector=(0, 1, 0),
                       maintainOffset=True,
                       worldUpType="object",
                       worldUpObject=upObject)
    
    kneeConstraint = cmds.parentConstraint("worldSpace_LOCATOR", offsetParent, f"{kneeControl}_GRP", maintainOffset=True)[0]

    reverseNode = cmds.shadingNode("reverse", asUtility=True, name=f"{limb}_poleVectorFollow_reverse")

    cmds.connectAttr(f"{kneeControl}.follow", f"{reverseNode}.inputX")
    cmds.connectAttr(f"{reverseNode}.outputX", f"{kneeConstraint}.worldSpace_LOCATORW0")
    cmds.connectAttr(f"{kneeControl}.follow", f"{kneeConstraint}.{offsetParent}W1")


    # HOCK CONTROL
    if limbType == "rear":
        multiValue = 5
    else:
        multiValue = 10

    cmds.shadingNode("multiplyDivide", asUtility=True, name=f"{hock}_multi")

    cmds.connectAttr(f"{hockControl}.translate",
                     f"{hock}_multi.input1",
                     force=True)

    cmds.connectAttr(f"{hock}_multi.outputZ",
                     f"{hock}_CTRL.rotateZ",
                     force=True)
    cmds.connectAttr(f"{hock}_multi.outputY",
                     f"{hock}_CTRL.rotateX",
                     force=True)
    
    cmds.setAttr(f"{hock}_multi.input2Y", multiValue)
    cmds.setAttr(f"{hock}_multi.input2Z", multiValue)

    
    # hierarchy
    cmds.parent(offsetParent, f"{limb}_GRP")
    cmds.parent(upObject, f"{limb}_GRP")



def _______________BUILD_______________(): pass


def autoRigLimb(limbSideMenu,
                limbTypeMenu,
                limbNameField,
                controlSuffixField,
                stretchBox,
                rollJointsBox,
                poleVectorArrowBox,
                *args):
    """ Automatically rigs quadruped limbs. """


    # set up variable values from UI

    if cmds.optionMenu(limbSideMenu, query=True, value=True) == "Left":
        limbSide = "L"
    else:
        limbSide = "R"
    
    if cmds.optionMenu(limbTypeMenu, query=True, value=True) == "Front":
        limbType = "front"
    else:
        limbType = "rear"
    
    limbName = cmds.textField(limbNameField, query=True, text=True)
    ctrlSuffix = cmds.textField(controlSuffixField, query=True, text=True)
    stretch = cmds.checkBox(stretchBox, query=True, value=True)
    rollJoints = cmds.checkBox(rollJointsBox, query=True, value=True)
    poleVectorArrow = cmds.checkBox(poleVectorArrowBox, query=True, value=True)
    
    # check selection
    selection = cmds.ls(selection=True, type="joint")

    if not selection:
        cmds.error("No joint selected.",
                   noContext=True)
    else:
        jointRoot = selection[0]

    # get joint hierarchy
    jointHierarchy = cmds.listRelatives(jointRoot, 
                                        allDescendents=True, type="joint")
    jointHierarchy.append(jointRoot)
    jointHierarchy.reverse()
    cmds.select(clear=True)

    if len(jointHierarchy) < 5:
        cmds.error("Joint chain is too short.",
                   noContext=True)
    
    # build names
    limb = f"{limbSide}_{limbType}_{limbName}"
    root = jointHierarchy[0]
    knee = jointHierarchy[1]
    hock = jointHierarchy[2]
    foot = jointHierarchy[3]

    mainControl = f"{limb}_{ctrlSuffix}"
    rootControl = f"{root}_IK_{ctrlSuffix}"
    kneeControl = f"{knee}_IK_{ctrlSuffix}"
    hockControl = f"{hock}_IK_{ctrlSuffix}"
    footControl = f"{foot}_IK_{ctrlSuffix}"

    # pack names
    limbNames = (limb, root, knee, hock, foot)
    controlNames = (mainControl, rootControl, kneeControl, hockControl, footControl)

    # check controls
    for control in controlNames:
        if not cmds.objExists(control):
            cmds.error("Control not found. Controls need to be named after the joint " \
                       "and include a control suffix. Example: L_hip_[controlSuffix]")
        if not cmds.objExists(f"{control}_GRP"):
            cmds.group(control, name=f"{control}_GRP",
                       relative=True)

    # create hierarchy
    if not cmds.objExists(f"{limb}_GRP"):
        cmds.group(empty=True, name=f"{limb}_GRP")

    cmds.matchTransform(f"{limb}_GRP", jointRoot)
    cmds.makeIdentity(f"{limb}_GRP",
                      apply=True, translate=True, rotate=True, scale=False)

    if not cmds.objExists("rig_systems"):
        cmds.group(name="rig_systems", empty=True)

    cmds.parent(f"{limb}_GRP", "rig_systems")

    cmds.select(clear=True)

    createFKIK(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)
    createFKIKblend(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)

    if stretch:
        createStretch(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)
        createVolumePreservation(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)
    
    if rollJoints:
        createRollJoints(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)
    
    if poleVectorArrow:
        createPoleVectorArrow(jointHierarchy=jointHierarchy, limb=limb, knee=knee, ctrlSuffix=ctrlSuffix)
    
    createFKIKvisiblity(limb=limb, mainControl=mainControl)
    createProxyAttributes(controlNames=controlNames)

    connectControls(jointHierarchy=jointHierarchy, limbNames=limbNames, controlNames=controlNames)

    cmds.select(clear=True)




createUI(autoRigLimb)