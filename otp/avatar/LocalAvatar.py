# File: L (Python 2.2)

from ShowBaseGlobal import *
from DirectGui import *
from PythonUtil import *
from IntervalGlobal import *
import Avatar
import DistributedAvatar
import Task
import PositionExaminer
import ToontownGlobals
import ChatManager
import math
import string
import whrandom
import DirectNotifyGlobal
import DistributedSmoothNode
import DirectGuiGlobals
import Toon
import Localizer

class LocalAvatar(DistributedAvatar.DistributedAvatar, DistributedSmoothNode.DistributedSmoothNode):
    notify = DirectNotifyGlobal.directNotify.newCategory('LocalAvatar')
    wantMouse = base.config.GetBool('want-mouse', 0)
    sleepTimeout = base.config.GetInt('sleep-timeout', 120)
    _LocalAvatar__enableMarkerPlacement = base.config.GetBool('place-markers', 0)
    acceptingNewFriends = base.config.GetBool('accepting-new-friends', 1)
    
    def __init__(self, cr):
        
        try:
            pass
        except:
            self.LocalAvatar_initialized = 1
            DistributedAvatar.DistributedAvatar.__init__(self, cr)
            DistributedSmoothNode.DistributedSmoothNode.__init__(self, cr)
            self.initializeCollisions()
            self.initializeSmartCamera()
            self.animMultiplier = 1.0
            self.customMessages = []
            self.soundRun = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_runloop.wav')
            self.soundWalk = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_walkloop.wav')
            self.soundWhisper = base.loadSfx('phase_3.5/audio/sfx/GUI_whisper_3.mp3')
            self.positionExaminer = PositionExaminer.PositionExaminer()
            friendsGui = loader.loadModelOnce('phase_3.5/models/gui/friendslist_gui')
            friendsButtonNormal = friendsGui.find('**/FriendsBox_Closed')
            friendsButtonPressed = friendsGui.find('**/FriendsBox_Rollover')
            friendsButtonRollover = friendsGui.find('**/FriendsBox_Rollover')
            self.bFriendsList = DirectButton(image = (friendsButtonNormal, friendsButtonPressed, friendsButtonRollover), relief = None, pos = (1.1919999999999999, 0, 0.875), scale = 0.80000000000000004, text = ('', Localizer.FriendsListLabel, Localizer.FriendsListLabel), text_scale = 0.089999999999999997, text_fg = Vec4(1, 1, 1, 1), text_shadow = Vec4(0, 0, 0, 1), text_pos = (0, -0.17999999999999999), text_font = ToontownGlobals.getInterfaceFont(), command = self.sendFriendsListEvent)
            self.bFriendsList.hide()
            self.friendsListButtonActive = 0
            self.friendsListButtonObscured = 0
            friendsGui.removeNode()
            self.chatMgr = ChatManager.ChatManager()
            self.commonChatFlags = 0
            self.garbleChat = 1
            self.isPageUp = 0
            self.isPageDown = 0
            self.sleepFlag = 0
            self.movingFlag = 0
            self.lastNeedH = None
            self.accept('friendOnline', self._LocalAvatar__friendOnline)
            self.accept('friendOffline', self._LocalAvatar__friendOffline)
            self.accept('clickedWhisper', self._LocalAvatar__clickedWhisper)
            self.sleepCallback = None
            self.accept('wakeup', self.wakeUp)

        return None

    
    def sendFriendsListEvent(self):
        messenger.send('wakeup')
        messenger.send('openFriendsList')

    
    def delete(self):
        
        try:
            pass
        except:
            self.LocalAvatar_deleted = 1
            self.deleteCollisions()
            self.positionExaminer.delete()
            del self.positionExaminer
            self.bFriendsList.destroy()
            del self.bFriendsList
            self.chatMgr.delete()
            del self.chatMgr
            del self.soundRun
            del self.soundWalk
            del self.soundWhisper
            self.ignoreAll()
            DistributedAvatar.DistributedAvatar.delete(self)

        return None

    
    def initializeCollisions(self):
        self.cSphere = CollisionSphere(0.0, 0.0, 0.0, 1.5)
        self.cSphereNode = CollisionNode('cSphereNode')
        self.cSphereNode.addSolid(self.cSphere)
        self.cSphereNodePath = self.attachNewNode(self.cSphereNode)
        self.cSphereNodePath.hide()
        self.cSphereBitMask = ToontownGlobals.WallBitmask
        self.cSphereNode.setFromCollideMask(self.cSphereBitMask)
        self.cSphereNode.setIntoCollideMask(BitMask32.allOff())
        base.mouse2cam.node().setVelocityNode(self.cSphereNode)
        self.cRay = CollisionRay(0.0, 0.0, 4.0, 0.0, 0.0, -1.0)
        self.cRayNode = CollisionNode('cRayNode')
        self.cRayNode.addSolid(self.cRay)
        self.cRayNodePath = self.attachNewNode(self.cRayNode)
        self.cRayNodePath.hide()
        self.cRayBitMask = ToontownGlobals.FloorBitmask
        self.cRayNode.setFromCollideMask(self.cRayBitMask)
        self.cRayNode.setIntoCollideMask(BitMask32.allOff())
        self.pusher = CollisionHandlerPusher()
        self.pusher.setInPattern('enter%in')
        self.pusher.setOutPattern('exit%in')
        self.lifter = CollisionHandlerFloor()
        self.lifter.setInPattern('on-floor')
        self.lifter.setOutPattern('off-floor')
        self.lifter.setOffset(ToontownGlobals.FloorOffset)
        self.lifter.setMaxVelocity(16.0)
        self.cTrav = CollisionTraverser()
        base.cTrav = self.cTrav
        self.collisionsOn()
        self.pusher.addColliderDrive(self.cSphereNode, base.drive.node())
        self.lifter.addColliderDrive(self.cRayNode, base.drive.node())
        self.ccTrav = CollisionTraverser()
        self.ccLine = CollisionSegment(0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.ccLineNode = CollisionNode('ccLineNode')
        self.ccLineNode.addSolid(self.ccLine)
        self.ccLineNodePath = self.attachNewNode(self.ccLineNode)
        self.ccLineNodePath.hide()
        self.ccLineBitMask = ToontownGlobals.CameraBitmask
        self.ccLineNode.setFromCollideMask(self.ccLineBitMask)
        self.ccLineNode.setIntoCollideMask(BitMask32.allOff())
        self.camCollisionQueue = CollisionHandlerQueue()
        self.ccTrav.addCollider(self.ccLineNode, self.camCollisionQueue)
        self.camFloorRayNode = self.attachNewNode('camFloorRayNode')
        self.ccRay = CollisionRay(0.0, 0.0, 0.0, 0.0, 0.0, -1.0)
        self.ccRayNode = CollisionNode('ccRayNode')
        self.ccRayNode.addSolid(self.ccRay)
        self.ccRayNodePath = self.camFloorRayNode.attachNewNode(self.ccRayNode)
        self.ccRayNodePath.hide()
        self.ccRayBitMask = ToontownGlobals.FloorBitmask
        self.ccRayNode.setFromCollideMask(self.ccRayBitMask)
        self.ccRayNode.setIntoCollideMask(BitMask32.allOff())
        self.ccTravFloor = CollisionTraverser()
        self.camFloorCollisionQueue = CollisionHandlerQueue()
        self.ccTravFloor.addCollider(self.ccRayNode, self.camFloorCollisionQueue)
        nearPlaneDist = base.camLens.getNear()
        hFov = base.camLens.getHfov()
        vFov = base.camLens.getVfov()
        hOff = nearPlaneDist * math.tan(deg2Rad(hFov / 2))
        vOff = nearPlaneDist * math.tan(deg2Rad(vFov / 2))
        camPnts = [
            Point3(hOff, nearPlaneDist, vOff),
            Point3(-hOff, nearPlaneDist, vOff),
            Point3(hOff, nearPlaneDist, -vOff),
            Point3(-hOff, nearPlaneDist, -vOff),
            Point3(0.0, 0.0, 0.0)]
        avgPnt = Point3(0.0, 0.0, 0.0)
        for camPnt in camPnts:
            avgPnt = avgPnt + camPnt
        
        avgPnt = avgPnt / len(camPnts)
        sphereRadius = 0.0
        for camPnt in camPnts:
            dist = Vec3(camPnt - avgPnt).length()
            if dist > sphereRadius:
                sphereRadius = dist
            
        
        sphereRadius *= 1.1499999999999999
        self.ccSphere = CollisionSphere(avgPnt[0], avgPnt[1], avgPnt[2], sphereRadius)
        self.ccSphereNode = CollisionNode('ccSphereNode')
        self.ccSphereNode.addSolid(self.ccSphere)
        self.ccSphereNodePath = base.camera.attachNewNode(self.ccSphereNode)
        self.ccSphereNodePath.hide()
        self.ccSphereBitMask = ToontownGlobals.CameraBitmask
        self.ccSphereNode.setFromCollideMask(self.ccSphereBitMask)
        self.ccSphereNode.setIntoCollideMask(BitMask32.allOff())
        self.camPusher = CollisionHandlerPusher()
        self.camPusher.addColliderNode(self.ccSphereNode, base.camera.node())
        self.ccPusherTrav = CollisionTraverser()
        self.ccSphere2 = self.ccSphere
        self.ccSphereNode2 = CollisionNode('ccSphereNode2')
        self.ccSphereNode2.addSolid(self.ccSphere2)
        self.ccSphereNodePath2 = base.camera.attachNewNode(self.ccSphereNode2)
        self.ccSphereNodePath2.hide()
        self.ccSphereBitMask2 = ToontownGlobals.CameraBitmask
        self.ccSphereNode2.setFromCollideMask(self.ccSphereBitMask2)
        self.ccSphereNode2.setIntoCollideMask(BitMask32(0))
        self.camPusher2 = CollisionHandlerPusher()
        self.ccPusherTrav.addCollider(self.ccSphereNode2, self.camPusher2)
        self.camPusher2.addColliderNode(self.ccSphereNode2, base.camera.node())
        return None

    
    def deleteCollisions(self):
        del self.cSphere
        del self.cSphereNode
        self.cSphereNodePath.removeNode()
        del self.cSphereNodePath
        del self.cRay
        del self.cRayNode
        self.cRayNodePath.removeNode()
        del self.cRayNodePath
        del self.pusher
        self.ignore('entero157')
        del self.lifter
        del self.cTrav
        del self.ccTrav
        del self.ccLine
        del self.ccLineNode
        self.ccLineNodePath.removeNode()
        del self.ccLineNodePath
        del self.camCollisionQueue
        del self.ccRay
        del self.ccRayNode
        self.ccRayNodePath.removeNode()
        del self.ccRayNodePath
        del self.ccTravFloor
        del self.camFloorCollisionQueue
        del self.ccSphere
        del self.ccSphereNode
        self.ccSphereNodePath.removeNode()
        del self.ccSphereNodePath
        del self.camPusher
        del self.ccPusherTrav
        del self.ccSphere2
        del self.ccSphereNode2
        self.ccSphereNodePath2.removeNode()
        del self.ccSphereNodePath2
        del self.camPusher2

    
    def collisionsOff(self):
        self.cTrav.removeCollider(self.cSphereNode)
        self.cTrav.removeCollider(self.cRayNode)
        self.oneTimeCollide()
        return None

    
    def collisionsOn(self):
        self.cTrav.addCollider(self.cSphereNode, self.pusher)
        self.cTrav.addCollider(self.cRayNode, self.lifter)
        return None

    
    def oneTimeCollide(self):
        driveNode = base.drive.node()
        driveNode.setPos(self.getPos())
        tempCTrav = CollisionTraverser()
        tempCTrav.addCollider(self.cSphereNode, self.pusher)
        tempCTrav.addCollider(self.cRayNode, self.lifter)
        tempCTrav.traverse(render)
        self.setPos(driveNode.getPos())

    
    def attachCamera(self):
        pos = self.getPos()
        hpr = self.getHpr()
        base.enableMouse()
        camera.reparentTo(self)
        base.setMouseOnNode(self.node())
        if self.wantMouse:
            base.mouseInterfaceNode.setIgnoreMouse(0)
        else:
            base.mouseInterfaceNode.setIgnoreMouse(1)
        base.mouseInterfaceNode.setPos(pos)
        base.mouseInterfaceNode.setHpr(hpr)
        self.setWalkSpeedNormal()

    
    def setWalkSpeedNormal(self):
        base.mouseInterfaceNode.setForwardSpeed(ToontownGlobals.ToonForwardSpeed)
        base.mouseInterfaceNode.setReverseSpeed(ToontownGlobals.ToonReverseSpeed)
        base.mouseInterfaceNode.setRotateSpeed(ToontownGlobals.ToonRotateSpeed)
        return None

    
    def setWalkSpeedSlow(self):
        base.mouseInterfaceNode.setForwardSpeed(ToontownGlobals.ToonForwardSlowSpeed)
        base.mouseInterfaceNode.setReverseSpeed(ToontownGlobals.ToonReverseSlowSpeed)
        base.mouseInterfaceNode.setRotateSpeed(ToontownGlobals.ToonRotateSlowSpeed)
        return None

    
    def setWalkSpeed(self, fwd, rev, rotate):
        base.mouseInterfaceNode.setForwardSpeed(fwd)
        base.mouseInterfaceNode.setReverseSpeed(rev)
        base.mouseInterfaceNode.setRotateSpeed(rotate)
        return None

    
    def detachCamera(self):
        base.disableMouse()

    
    def addTabHook(self):
        self.accept('tab', self.nextCameraPos, [
            1])
        self.accept('shift-tab', self.nextCameraPos, [
            0])
        self.accept('page_up', self.pageUp)
        self.accept('page_down', self.pageDown)
        self.accept('arrow_up', self.clearPageUpDown)
        self.accept('arrow_up-up', self.clearPageUpDown)
        self.accept('arrow_down', self.clearPageUpDown)
        self.accept('arrow_down-up', self.clearPageUpDown)

    
    def removeTabHook(self):
        self.ignore('tab')
        self.ignore('shift-tab')
        self.ignore('page_up')
        self.ignore('page_down')
        self.ignore('arrow_up')
        self.ignore('arrow_up-up')
        self.ignore('arrow_down')
        self.ignore('arrow_down-up')
        self.clearPageUpDown()

    
    def pageUp(self):
        if not (self.isPageUp):
            self.isPageDown = 0
            self.isPageUp = 1
            self.lerpCameraFov(70, 0.59999999999999998)
            self.setCameraPositionByIndex(self.cameraIndex)
        

    
    def pageDown(self):
        if not (self.isPageDown):
            self.isPageUp = 0
            self.isPageDown = 1
            self.lerpCameraFov(70, 0.59999999999999998)
            self.setCameraPositionByIndex(self.cameraIndex)
        

    
    def clearPageUpDown(self):
        if self.isPageDown or self.isPageUp:
            self.lerpCameraFov(ToontownGlobals.DefaultCameraFov, 0.59999999999999998)
            self.isPageDown = 0
            self.isPageUp = 0
            self.setCameraPositionByIndex(self.cameraIndex)
        

    
    def nextCameraPos(self, forward):
        self._LocalAvatar__cameraHasBeenMoved = 1
        if forward:
            self.cameraIndex += 1
            if self.cameraIndex > len(self.cameraPositions) - 1:
                self.cameraIndex = 0
            
        else:
            self.cameraIndex -= 1
            if self.cameraIndex < 0:
                self.cameraIndex = len(self.cameraPositions) - 1
            
        self.setCameraPositionByIndex(self.cameraIndex)

    
    def initCameraPositions(self):
        camHeight = self.getClampedAvatarHeight()
        heightScaleFactor = camHeight * 0.33333333329999998
        defLookAt = Point3(0.0, 1.5, camHeight)
        qtXoffset = 3.0
        qtPosition = (Point3(qtXoffset - 1, -10.0, camHeight + 5.0), Point3(qtXoffset, 2.0, camHeight))
        self.cameraPositions = [
            (Point3(0.0, -9.0 * heightScaleFactor, camHeight), defLookAt, Point3(0.0, camHeight, camHeight * 4.0), Point3(0.0, camHeight, camHeight * -1.0), 0),
            (Point3(0.0, 0.5, camHeight), defLookAt, Point3(0.0, camHeight, camHeight * 1.3300000000000001), Point3(0.0, camHeight, camHeight * 0.66000000000000003), 1),
            (Point3(5.7000000000000002 * heightScaleFactor, 7.6500000000000004 * heightScaleFactor, camHeight + 2.0), Point3(0.0, 1.0, camHeight), Point3(0.0, 1.0, camHeight * 4.0), Point3(0.0, 1.0, camHeight * -1.0), 0),
            (Point3(0.0, -24.0 * heightScaleFactor, camHeight + 4.0), defLookAt, Point3(0.0, 1.5, camHeight * 4.0), Point3(0.0, 1.5, camHeight * -1.0), 0),
            (Point3(0.0, -12.0 * heightScaleFactor, camHeight + 4.0), defLookAt, Point3(0.0, 1.5, camHeight * 4.0), Point3(0.0, 1.5, camHeight * -1.0), 0)] + self.auxCameraPositions
        return None

    
    def addCameraPosition(self, camPos = None):
        if camPos == None:
            lookAtNP = self.attachNewNode('lookAt')
            lookAtNP.setPos(base.cam, 0, 1, 0)
            lookAtPos = lookAtNP.getPos()
            camHeight = self.getClampedAvatarHeight()
            camPos = (base.cam.getPos(self), lookAtPos, Point3(0.0, 1.5, camHeight * 4.0), Point3(0.0, 1.5, camHeight * -1.0), 1)
            lookAtNP.removeNode()
        
        self.auxCameraPositions.append(camPos)
        self.cameraPositions.append(camPos)

    
    def removeCameraPosition(self):
        if len(self.cameraPositions) > 1:
            camPos = self.cameraPositions[self.cameraIndex]
            if camPos in self.auxCameraPositions:
                self.auxCameraPositions.remove(camPos)
            
            if camPos in self.cameraPositions:
                self.cameraPositions.remove(camPos)
            
            self.nextCameraPos(1)
        

    
    def printCameraPositions(self):
        print '['
        for i in range(len(self.cameraPositions)):
            self.printCameraPosition(i)
            print ','
        
        print ']'

    
    def printCameraPosition(self, index):
        cp = self.cameraPositions[index]
        print '(Point3(%0.2f, %0.2f, %0.2f),' % (cp[0][0], cp[0][1], cp[0][2])
        print 'Point3(%0.2f, %0.2f, %0.2f),' % (cp[1][0], cp[1][1], cp[1][2])
        print 'Point3(%0.2f, %0.2f, %0.2f),' % (cp[2][0], cp[2][1], cp[2][2])
        print 'Point3(%0.2f, %0.2f, %0.2f),' % (cp[3][0], cp[3][1], cp[3][2])
        print '%d,' % cp[4]
        print ')'
def posCamera(self, lerp, time):
        if not lerp:
            self.positionCameraWithPusher(self.getCompromiseCameraPos(), self.getLookAtPoint())
        else:
            camPos = self.getCompromiseCameraPos()
            savePos = camera.getPos()
            saveHpr = camera.getHpr()
            self.positionCameraWithPusher(camPos, self.getLookAtPoint())
            x = camPos[0]
            y = camPos[1]
            z = camPos[2]
            destHpr = camera.getHpr()
            h = destHpr[0]
            p = destHpr[1]
            r = destHpr[2]
            camera.setPos(savePos)
            camera.setHpr(saveHpr)
            taskMgr.remove('posCamera')
            camera.lerpPosHpr(x, y, z, h, p, r, time, task = 'posCamera')

    
    def getClampedAvatarHeight(self):
        return max(self.getHeight(), 3.0)

    
    def getVisibilityPoint(self):
        return Point3(0.0, 0.0, self.getHeight())

    
    def setLookAtPoint(self, la):
        self._LocalAvatar__curLookAt = Point3(la)

    
    def getLookAtPoint(self):
        return Point3(self._LocalAvatar__curLookAt)

    
    def setIdealCameraPos(self, pos):
        self._LocalAvatar__idealCameraPos = Point3(pos)
        self.updateSmartCameraCollisionLineSegment()

    
    def getIdealCameraPos(self):
        return Point3(self._LocalAvatar__idealCameraPos)

    
    def setCameraPositionByIndex(self, index):
        camSettings = self.cameraPositions[index]
        self.setIdealCameraPos(camSettings[0])
        if self.isPageUp and self.isPageDown and not (self.isPageUp) and not (self.isPageDown):
            self._LocalAvatar__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[1])
        elif self.isPageUp:
            self._LocalAvatar__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[2])
        elif self.isPageDown:
            self._LocalAvatar__cameraHasBeenMoved = 1
            self.setLookAtPoint(camSettings[3])
        else:
            self.notify.error('This case should be impossible.')
        self._LocalAvatar__disableSmartCam = camSettings[4]
        if self._LocalAvatar__disableSmartCam:
            self.cameraZOffset = 0.0
        

    
    def getCompromiseCameraPos(self):
        if self._LocalAvatar__idealCameraObstructed == 0:
            compromisePos = self.getIdealCameraPos()
        else:
            visPnt = self.getVisibilityPoint()
            idealPos = self.getIdealCameraPos()
            distance = Vec3(idealPos - visPnt).length()
            ratio = self.closestObstructionDistance / distance
            compromisePos = idealPos * ratio + visPnt * (1 - ratio)
            liftMult = 1.0 - ratio * ratio
            compromisePos = Point3(compromisePos[0], compromisePos[1], compromisePos[2] + self.getHeight() * 0.40000000000000002 * liftMult)
        compromisePos.setZ(compromisePos[2] + self.cameraZOffset)
        return compromisePos

    
    def updateSmartCameraCollisionLineSegment(self):
        pointB = self.getIdealCameraPos()
        pointA = self.getVisibilityPoint()
        pullbackDist = 1.5
        vectorAB = Vec3(pointB - pointA)
        lengthAB = vectorAB.length()
        if lengthAB > pullbackDist:
            pullbackVector = vectorAB * (pullbackDist / lengthAB)
            pointA = Point3(pointA + Point3(pullbackVector))
            lengthAB -= pullbackDist
        
        if lengthAB > 0.001:
            self.ccLine.setPointA(pointA)
            self.ccLine.setPointB(pointB)
        

    
    def initializeSmartCamera(self):
        self._LocalAvatar__idealCameraObstructed = 0
        self.closestObstructionDistance = 0.0
        self.cameraIndex = 0
        self.auxCameraPositions = []
        self.cameraZOffset = 0.0
        self._LocalAvatar__onLevelGround = 0
        self._LocalAvatar__geom = render
        self._LocalAvatar__disableSmartCam = 0

    
    def setOnLevelGround(self, flag):
        self._LocalAvatar__onLevelGround = flag

    
    def setGeom(self, geom):
        self._LocalAvatar__geom = geom

    
    def startUpdateSmartCamera(self):
        self._LocalAvatar__floorDetected = 0
        self._LocalAvatar__cameraHasBeenMoved = 0
        self.initCameraPositions()
        self.setCameraPositionByIndex(self.cameraIndex)
        self.posCamera(0, 0.0)
        self._LocalAvatar__instantaneousCamPos = camera.getPos()
        self.cTrav.addCollider(self.ccSphereNode, self.camPusher)
        self._LocalAvatar__lastPosWrtRender = camera.getPos(render)
        self._LocalAvatar__lastHprWrtRender = camera.getHpr(render)
        taskName = self.taskName('updateSmartCamera')
        taskMgr.remove(taskName)
        taskMgr.add(self.updateSmartCamera, taskName)

    
    def stopUpdateSmartCamera(self):
        self.cTrav.removeCollider(self.ccSphereNode)
        taskName = self.taskName('updateSmartCamera')
        taskMgr.remove(taskName)

    
    def updateSmartCamera(self, task):
        if not (self._LocalAvatar__cameraHasBeenMoved):
            if self._LocalAvatar__lastPosWrtRender == camera.getPos(render):
                if self._LocalAvatar__lastHprWrtRender == camera.getHpr(render):
                    return Task.cont
                
            
        
        self._LocalAvatar__cameraHasBeenMoved = 0
        self._LocalAvatar__lastPosWrtRender = camera.getPos(render)
        self._LocalAvatar__lastHprWrtRender = camera.getHpr(render)
        camWasObstructed = self._LocalAvatar__idealCameraObstructed
        self._LocalAvatar__idealCameraObstructed = 0
        if not (self._LocalAvatar__disableSmartCam):
            self.ccTrav.traverse(self._LocalAvatar__geom)
            if self.camCollisionQueue.getNumEntries() > 0:
                self.camCollisionQueue.sortEntries()
                self.handleCameraObstruction(self.camCollisionQueue.getEntry(0), camWasObstructed)
            
            if not (self._LocalAvatar__onLevelGround):
                self.handleCameraFloorInteraction()
            
        
        self.nudgeCamera()
        return Task.cont

    
    def positionCameraWithPusher(self, pos, lookAt):
        camera.setPos(pos)
        self.ccPusherTrav.traverse(self._LocalAvatar__geom)
        camera.lookAt(lookAt)

    
    def nudgeCamera(self):
        CLOSE_ENOUGH = 0.10000000000000001
        curCamPos = self._LocalAvatar__instantaneousCamPos
        curCamHpr = camera.getHpr()
        targetCamPos = self.getCompromiseCameraPos()
        targetCamLookAt = self.getLookAtPoint()
        posDone = 0
        if Vec3(curCamPos - targetCamPos).length() <= CLOSE_ENOUGH:
            camera.setPos(targetCamPos)
            posDone = 1
        
        camera.setPos(targetCamPos)
        camera.lookAt(targetCamLookAt)
        targetCamHpr = camera.getHpr()
        hprDone = 0
        if Vec3(curCamHpr - targetCamHpr).length() <= CLOSE_ENOUGH:
            hprDone = 1
        
        if posDone and hprDone:
            return None
        
        lerpRatio = 0.14999999999999999
        lerpRatio = 1 - pow(1 - lerpRatio, globalClock.getDt() * 30.0)
        self._LocalAvatar__instantaneousCamPos = targetCamPos * lerpRatio + curCamPos * (1 - lerpRatio)
        newHpr = targetCamHpr * lerpRatio + curCamHpr * (1 - lerpRatio)
        camera.setPos(self._LocalAvatar__instantaneousCamPos)
        camera.setHpr(newHpr)

    
    def popCameraToDest(self):
        newCamPos = self.getCompromiseCameraPos()
        newCamLookAt = self.getLookAtPoint()
        self.positionCameraWithPusher(newCamPos, newCamLookAt)
        self._LocalAvatar__instantaneousCamPos = camera.getPos()

    
    def handleCameraObstruction(self, camObstrCollisionEntry, camWasObstructed):
        collisionPoint = camObstrCollisionEntry.getFromIntersectionPoint()
        collisionVec = Vec3(collisionPoint - self.ccLine.getPointA())
        distance = collisionVec.length()
        if not camWasObstructed and camWasObstructed and self.closestObstructionDistance > distance:
            popCameraUp = 1
        else:
            popCameraUp = 0
        self._LocalAvatar__idealCameraObstructed = 1
        self.closestObstructionDistance = distance
        if popCameraUp:
            self.popCameraToDest()
        

    
    def handleCameraFloorInteraction(self):
        self.camFloorRayNode.setPos(camera.getPos())
        self.ccTravFloor.traverse(self._LocalAvatar__geom)
        if self.camFloorCollisionQueue.getNumEntries() == 0:
            return None
        
        self.camFloorCollisionQueue.sortEntries()
        camObstrCollisionEntry = self.camFloorCollisionQueue.getEntry(0)
        camHeightFromFloor = camObstrCollisionEntry.getFromIntersectionPoint()[2]
        heightOfFloorUnderCamera = (camera.getPos()[2] - ToontownGlobals.FloorOffset) + camHeightFromFloor
        camIdealHeightFromFloor = self.getIdealCameraPos()[2]
        camTargetHeight = heightOfFloorUnderCamera + camIdealHeightFromFloor
        self.cameraZOffset = camTargetHeight - camIdealHeightFromFloor
        if self.cameraZOffset < 0.0:
            self.cameraZOffset = self.cameraZOffset * 0.33333333329999998
            if self.cameraZOffset < -(self.getClampedAvatarHeight() * 0.5):
                if self.cameraZOffset < -self.getClampedAvatarHeight():
                    self.cameraZOffset = 0.0
                else:
                    self.cameraZOffset = -(self.getClampedAvatarHeight() * 0.5)
            
        
        if self._LocalAvatar__floorDetected == 0:
            self._LocalAvatar__floorDetected = 1
            self.popCameraToDest()
        

    
    def lerpCameraFov(self, fov, time):
        taskMgr.remove('cam-fov-lerp-play')
        oldFov = base.camLens.getHfov()
        if abs(fov - oldFov) > 0.10000000000000001:
            
            def setCamFov(fov):
                base.camLens.setFov(fov)

            self.camLerpInterval = LerpFunctionInterval(setCamFov, fromData = oldFov, toData = fov, duration = time, name = 'cam-fov-lerp')
            self.camLerpInterval.play()
        

    
    def gotoNode(self, node):
        possiblePoints = (Point3(3, 6, 0), Point3(-3, 6, 0), Point3(6, 6, 0), Point3(-6, 6, 0), Point3(3, 9, 0), Point3(-3, 9, 0), Point3(6, 9, 0), Point3(-6, 9, 0), Point3(9, 9, 0), Point3(-9, 9, 0), Point3(6, 0, 0), Point3(-6, 0, 0), Point3(6, 3, 0), Point3(-6, 3, 0), Point3(9, 9, 0), Point3(-9, 9, 0), Point3(0, 12, 0), Point3(3, 12, 0), Point3(-3, 12, 0), Point3(6, 12, 0), Point3(-6, 12, 0), Point3(9, 12, 0), Point3(-9, 12, 0), Point3(0, -6, 0), Point3(-3, -6, 0), Point3(0, -9, 0), Point3(-6, -9, 0))
        for point in possiblePoints:
            pos = self.positionExaminer.consider(node, point)
            if pos:
                self.setPos(node, pos)
                self.lookAt(node)
                self.setHpr(self.getH() + whrandom.choice((-10, 10)), 0, 0)
                base.drive.node().setPos(self.getPos())
                base.drive.node().setHpr(self.getHpr())
                return None
            
        
        self.setPos(node, 0, 0, 0)
        base.drive.node().setPos(self.getPos())
        base.drive.node().setHpr(self.getHpr())

    
    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages
        messenger.send('customMessagesChanged')

    
    def displayWhisper(self, fromId, chatString, whisperType):
        sender = None
        if fromId != 0:
            sender = toonbase.tcr.identifyAvatar(fromId)
        
        if whisperType == WhisperPopup.WTNormal or whisperType == WhisperPopup.WTQuickTalker:
            if sender == None:
                return None
            
            chatString = sender.getName() + ': ' + chatString
        
        whisper = WhisperPopup(chatString, ToontownGlobals.getInterfaceFont(), whisperType)
        if sender != None:
            whisper.setClickable(sender.getName(), fromId)
        
        whisper.manage(toonbase.marginManager)
        base.playSfx(self.soundWhisper)

    
    def setAnimMultiplier(self, value):
        self.animMultiplier = value

    
    def getAnimMultiplier(self):
        return self.animMultiplier

    
    def runSound(self):
        self.soundWalk.stop()
        base.playSfx(self.soundRun, looping = 1)

    
    def walkSound(self):
        self.soundRun.stop()
        base.playSfx(self.soundWalk, looping = 1)

    
    def stopSound(self):
        self.soundRun.stop()
        self.soundWalk.stop()

    
    def wakeUp(self):
        if self.sleepCallback != None:
            taskMgr.remove(self.uniqueName('sleepwatch'))
            self.startSleepWatch(self.sleepCallback)
        
        self.lastMoved = globalClock.getFrameTime()
        if self.sleepFlag:
            self.sleepFlag = 0
        

    
    def gotoSleep(self):
        if not (self.sleepFlag):
            self.b_setAnimState('Sleep', self.animMultiplier)
            self.sleepFlag = 1
        

    
    def forceGotoSleep(self):
        self.sleepFlag = 0
        self.gotoSleep()

    
    def startSleepWatch(self, callback):
        self.sleepCallback = callback
        taskMgr.doMethodLater(self.sleepTimeout, callback, self.uniqueName('sleepwatch'))

    
    def stopSleepWatch(self):
        taskMgr.remove(self.uniqueName('sleepwatch'))
        self.sleepCallback = None

    
    def trackAnimToSpeed(self, task):
        speed = base.mouseInterfaceNode.getSpeed()
        rotSpeed = base.mouseInterfaceNode.getRotSpeed()
        if speed != 0.0 or rotSpeed != 0.0:
            if not (self.movingFlag):
                self.movingFlag = 1
                self.stopLookAround()
            
        elif self.movingFlag:
            self.movingFlag = 0
            self.startLookAround()
        
        if self.movingFlag or self.hp <= 0:
            self.wakeUp()
        elif not (self.sleepFlag):
            now = globalClock.getFrameTime()
            if now - self.lastMoved > self.sleepTimeout:
                self.gotoSleep()
            
        
        state = None
        if self.sleepFlag:
            state = 'Sleep'
        elif self.hp > 0:
            state = 'Happy'
        else:
            state = 'Sad'
        if state != self.lastState:
            self.lastState = state
            self.b_setAnimState(state, self.animMultiplier)
            if state == 'Sad':
                self.setWalkSpeedSlow()
            else:
                self.setWalkSpeedNormal()
        
        if self.cheesyEffect == ToontownGlobals.CEFlatProfile or self.cheesyEffect == ToontownGlobals.CEFlatPortrait:
            needH = None
            if rotSpeed > 0.0:
                needH = -10
            elif rotSpeed < 0.0:
                needH = 10
            elif speed != 0.0:
                needH = 0
            
            if needH != None and self.lastNeedH != needH:
                node = self.getGeomNode().getChild(0)
                lerp = Sequence(LerpHprInterval(node, 0.5, Vec3(needH, 0, 0), blendType = 'easeInOut'), name = 'cheesy-lerp-hpr', autoPause = 1)
                lerp.start()
                self.lastNeedH = needH
            
        else:
            self.lastNeedH = None
        action = self.setSpeed(speed, rotSpeed)
        if action != self.lastAction:
            self.lastAction = action
            if action == Toon.WALK_INDEX or action == Toon.REVERSE_INDEX:
                self.walkSound()
            elif action == Toon.RUN_INDEX:
                self.runSound()
            else:
                self.stopSound()
        
        return Task.cont

    
    def startTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        task = Task.Task(self.trackAnimToSpeed)
        self.lastMoved = globalClock.getFrameTime()
        self.lastState = None
        self.lastAction = None
        self.trackAnimToSpeed(task)
        taskMgr.add(self.trackAnimToSpeed, taskName)

    
    def stopTrackAnimToSpeed(self):
        taskName = self.taskName('trackAnimToSpeed')
        taskMgr.remove(taskName)
        self.stopSound()

    
    def startChat(self):
        self.chatMgr.start()
        self.accept('chatUpdate', self.b_setChat)
        self.accept('chatUpdateQT', self.b_setQT)
        self.accept('chatUpdateQTQuest', self.b_setQTQuest)
        self.accept('chatUpdateQTCustom', self.b_setQTCustom)
        self.accept('whisperUpdate', self.whisperTo)
        self.accept('whisperUpdateQT', self.whisperQTTo)
        self.accept('whisperUpdateQTQuest', self.whisperQTQuestTo)
        self.accept('whisperUpdateQTCustom', self.whisperQTCustomTo)
        self.accept(ToontownGlobals.ThinkPosHotkey, self.thinkPos)
        self.accept(ToontownGlobals.PrintCamPosHotkey, self.printCamPos)
        if self._LocalAvatar__enableMarkerPlacement:
            self.accept(ToontownGlobals.PlaceMarkerHotkey, self._LocalAvatar__placeMarker)
        
        return None

    
    def stopChat(self):
        self.chatMgr.stop()
        self.ignore('chatUpdate')
        self.ignore('chatUpdateQT')
        self.ignore('chatUpdateQTQuest')
        self.ignore('chatUpdateQTCustom')
        self.ignore('whisperUpdate')
        self.ignore('whisperUpdateQT')
        self.ignore('whisperUpdateQTQuest')
        self.ignore('whisperUpdateQTCustom')
        self.ignore(ToontownGlobals.ThinkPosHotkey)
        if self._LocalAvatar__enableMarkerPlacement:
            self.ignore(ToontownGlobals.PlaceMarkerHotkey)
        
        return None

    
    def printCamPos(self):
        node = base.camera.getParent()
        pos = base.cam.getPos(node)
        hpr = base.cam.getHpr(node)
        print 'cam pos = ', `pos`, ', cam hpr = ', `hpr`

    
    def getAvPosStr(self):
        pos = self.getPos()
        hpr = self.getHpr()
        serverVersion = toonbase.tcr.getServerVersion()
        districtName = toonbase.tcr.getShardName(toonbase.localToon.defaultShard)
        if hasattr(toonbase.tcr.playGame.hood, 'loader') and hasattr(toonbase.tcr.playGame.hood.loader, 'place') and toonbase.tcr.playGame.getPlace() != None:
            zoneId = toonbase.tcr.playGame.getPlace().getZoneId()
        else:
            zoneId = '?'
        strPosCoordText = 'X: %.3f' % pos[0] + ', Y: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + ', H: %.3f' % hpr[0] + '\nZone: %s' % str(zoneId) + ', Ver: %s, ' % serverVersion + 'District: %s' % districtName
        return strPosCoordText

    
    def thinkPos(self):
        pos = self.getPos()
        hpr = self.getHpr()
        serverVersion = toonbase.tcr.getServerVersion()
        districtName = toonbase.tcr.getShardName(toonbase.localToon.defaultShard)
        if hasattr(toonbase.tcr.playGame.hood, 'loader') and hasattr(toonbase.tcr.playGame.hood.loader, 'place') and toonbase.tcr.playGame.getPlace() != None:
            zoneId = toonbase.tcr.playGame.getPlace().getZoneId()
        else:
            zoneId = '?'
        strPos = 'X: %.3f' % pos[0] + '\nY: %.3f' % pos[1] + '\nZ: %.3f' % pos[2] + '\nH: %.3f' % hpr[0] + '\nZone: %s' % str(zoneId) + ',\nVer: %s, ' % serverVersion + '\nDistrict: %s' % districtName
        print 'Current position=', strPos.replace('\n', ', ')
        self.setChat(strPos, CFThought)

    
    def _LocalAvatar__placeMarker(self):
        pos = self.getPos()
        hpr = self.getHpr()
        chest = loader.loadModelOnce('phase_4/models/props/coffin')
        chest.reparentTo(render)
        chest.setColor(1, 0, 0, 1)
        chest.setPosHpr(pos, hpr)
        chest.setScale(0.5)

    
    def stopPosHprBroadcast(self):
        taskName = self.taskName('sendPosHpr')
        taskMgr.remove(taskName)

    
    def startPosHprBroadcast(self):
        taskName = self.taskName('sendPosHpr')
        xyz = self.getPos()
        hpr = self.getHpr(0)
        self._LocalAvatar__storeX = xyz[0]
        self._LocalAvatar__storeY = xyz[1]
        self._LocalAvatar__storeZ = xyz[2]
        self._LocalAvatar__storeH = hpr[0]
        self._LocalAvatar__storeP = hpr[1]
        self._LocalAvatar__storeR = hpr[2]
        self._LocalAvatar__storeStop = 0
        self._LocalAvatar__epsilon = 0.01
        self._LocalAvatar__broadcastFrequency = 0.20000000000000001
        self.b_clearSmoothing()
        self.d_setSmPosHpr(self._LocalAvatar__storeX, self._LocalAvatar__storeY, self._LocalAvatar__storeZ, self._LocalAvatar__storeH, self._LocalAvatar__storeP, self._LocalAvatar__storeR)
        taskMgr.remove(taskName)
        taskMgr.doMethodLater(self._LocalAvatar__broadcastFrequency, self.posHprBroadcast, taskName)

    
    def posHprBroadcast(self, task):
        self.d_broadcastPosHpr()
        taskName = self.taskName('sendPosHpr')
        taskMgr.doMethodLater(self._LocalAvatar__broadcastFrequency, self.posHprBroadcast, taskName)
        return Task.done

    
    def d_broadcastPosHpr(self):
        xyz = self.getPos()
        hpr = self.getHpr(0)
        if abs(self._LocalAvatar__storeX - xyz[0]) > self._LocalAvatar__epsilon:
            newX = xyz[0]
        else:
            newX = None
        if abs(self._LocalAvatar__storeY - xyz[1]) > self._LocalAvatar__epsilon:
            newY = xyz[1]
        else:
            newY = None
        if abs(self._LocalAvatar__storeZ - xyz[2]) > self._LocalAvatar__epsilon:
            newZ = xyz[2]
        else:
            newZ = None
        if abs(self._LocalAvatar__storeH - hpr[0]) > self._LocalAvatar__epsilon:
            newH = hpr[0]
        else:
            newH = None
        if abs(self._LocalAvatar__storeP - hpr[1]) > self._LocalAvatar__epsilon:
            newP = hpr[1]
        else:
            newP = None
        if abs(self._LocalAvatar__storeR - hpr[2]) > self._LocalAvatar__epsilon:
            newR = hpr[2]
        else:
            newR = None
        if not newX and newY and newZ and newH and newP:
            pass
        if not newR:
            if not (self._LocalAvatar__storeStop):
                self._LocalAvatar__storeStop = 1
                self.d_setSmStop()
            
        elif newH:
            if not newX and newY and newZ and newP:
                pass
            if not newR:
                self._LocalAvatar__storeStop = 0
                if newH:
                    self._LocalAvatar__storeH = newH
                
                self.d_setSmH(self._LocalAvatar__storeH)
            elif newX or newY:
                if not newZ and newH and newP:
                    pass
                if not newR:
                    self._LocalAvatar__storeStop = 0
                    if newX:
                        self._LocalAvatar__storeX = newX
                    
                    if newY:
                        self._LocalAvatar__storeY = newY
                    
                    self.d_setSmXY(self._LocalAvatar__storeX, self._LocalAvatar__storeY)
                elif newX and newY or newZ:
                    if not newH and newP:
                        pass
                    if not newR:
                        self._LocalAvatar__storeStop = 0
                        if newX:
                            self._LocalAvatar__storeX = newX
                        
                        if newY:
                            self._LocalAvatar__storeY = newY
                        
                        if newZ:
                            self._LocalAvatar__storeZ = newZ
                        
                        self.d_setSmPos(self._LocalAvatar__storeX, self._LocalAvatar__storeY, self._LocalAvatar__storeZ)
                    elif newX and newY or newH:
                        if not newZ and newP:
                            pass
                        if not newR:
                            self._LocalAvatar__storeStop = 0
                            if newX:
                                self._LocalAvatar__storeX = newX
                            
                            if newY:
                                self._LocalAvatar__storeY = newY
                            
                            if newH:
                                self._LocalAvatar__storeH = newH
                            
                            self.d_setSmXYH(self._LocalAvatar__storeX, self._LocalAvatar__storeY, self._LocalAvatar__storeH)
                        elif newX and newY and newZ or newH:
                            if not newP:
                                pass
                            if not newR:
                                self._LocalAvatar__storeStop = 0
                                if newX:
                                    self._LocalAvatar__storeX = newX
                                
                                if newY:
                                    self._LocalAvatar__storeY = newY
                                
                                if newZ:
                                    self._LocalAvatar__storeZ = newZ
                                
                                if newH:
                                    self._LocalAvatar__storeH = newH
                                
                                self.d_setSmXYZH(self._LocalAvatar__storeX, self._LocalAvatar__storeY, self._LocalAvatar__storeZ, self._LocalAvatar__storeH)
                            else:
                                self._LocalAvatar__storeStop = 0
                                if newX:
                                    self._LocalAvatar__storeX = newX
                                
                                if newY:
                                    self._LocalAvatar__storeY = newY
                                
                                if newZ:
                                    self._LocalAvatar__storeZ = newZ
                                
                                if newH:
                                    self._LocalAvatar__storeH = newH
                                
                                if newP:
                                    self._LocalAvatar__storeP = newP
                                
                                if newR:
                                    self._LocalAvatar__storeR = newR
                                
                                self.d_setSmPosHpr(self._LocalAvatar__storeX, self._LocalAvatar__storeY, self._LocalAvatar__storeZ, self._LocalAvatar__storeH, self._LocalAvatar__storeP, self._LocalAvatar__storeR)

    
    def d_broadcastPositionNow(self):
        self.d_clearSmoothing()
        self.d_broadcastPosHpr()

    
    def setFriendsListButtonActive(self, active):
        self.friendsListButtonActive = active
        if active:
            self.accept(ToontownGlobals.FriendsListHotkey, self.sendFriendsListEvent)
        else:
            self.ignore(ToontownGlobals.FriendsListHotkey)
        self._LocalAvatar__doFriendsListButton()

    
    def obscureFriendsListButton(self, increment):
        self.friendsListButtonObscured += increment
        self._LocalAvatar__doFriendsListButton()

    
    def _LocalAvatar__doFriendsListButton(self):
        if self.friendsListButtonActive and self.friendsListButtonObscured <= 0:
            self.bFriendsList.show()
        else:
            self.bFriendsList.hide()

    
    def travCollisionsLOS(self, n = None):
        if n == None:
            n = self._LocalAvatar__geom
        
        self.ccTrav.traverse(n)

    
    def travCollisionsFloor(self, n = None):
        if n == None:
            n = self._LocalAvatar__geom
        
        self.ccTravFloor.traverse(n)

    
    def travCollisionsPusher(self, n = None):
        if n == None:
            n = self._LocalAvatar__geom
        
        self.ccPusherTrav.traverse(n)

    
    def _LocalAvatar__friendOnline(self, doId):
        if self.oldFriendsList != None:
            now = globalClock.getFrameTime()
            elapsed = now - self.timeFriendsListChanged
            if elapsed < 10.0 and self.oldFriendsList.count(doId) == 0:
                self.oldFriendsList.append(doId)
                return None
            
        
        friend = toonbase.tcr.identifyFriend(doId)
        if friend != None:
            self.setSystemMessage(doId, Localizer.WhisperFriendComingOnline % friend.getName())
        

    
    def _LocalAvatar__friendOffline(self, doId):
        friend = toonbase.tcr.identifyFriend(doId)
        if friend != None:
            self.setSystemMessage(0, Localizer.WhisperFriendLoggedOut % friend.getName())
        

    
    def _LocalAvatar__clickedWhisper(self, doId):
        friend = toonbase.tcr.identifyFriend(doId)
        if friend != None:
            messenger.send('clickedNametag', [
                friend])
            self.chatMgr.whisperTo(friend.getName(), doId)
        


