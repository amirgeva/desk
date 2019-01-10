from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
from panda3d.core import Texture, GeomNode

def tex_coord(c,C):
    return c/C

class WindowBox:
    def __init__(self,front_texture,back_texture):
        self.format = GeomVertexFormat.getV3t2()
        self.vdata = GeomVertexData('vcube', self.format, Geom.UHDynamic)
        self.update_vertices((0,0,500,300),(1000,1000))
        self.node = self.makeBox(front_texture, back_texture)

    def update_vertices(self,rect,desktop):
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.texcoord = GeomVertexWriter(self.vdata, 'texcoord')
        w2=0.5*rect[2]
        h=rect[3]
        d=5
        # front vertices
        self.vertex.addData3(-w2, 0, -h)
        self.vertex.addData3( w2, 0, -h)
        self.vertex.addData3( w2, 0,  0)
        self.vertex.addData3(-w2, 0,  0)
        tl=tex_coord(rect[0],desktop[0])
        tt=tex_coord(rect[1],desktop[1])
        tr=tex_coord(rect[0]+rect[2],desktop[0])
        tb=tex_coord(rect[1]+rect[3],desktop[1])
        self.texcoord.addData2f(tl, tb)
        self.texcoord.addData2f(tr, tb)
        self.texcoord.addData2f(tr, tt)
        self.texcoord.addData2f(tl, tt)
        # frame vertices
        ch=20
        self.vertex.addData3(-w2,0,0)    #4
        self.vertex.addData3(-w2,0,ch)   #5
        self.vertex.addData3(-w2,10,ch)  #6
        self.vertex.addData3(-w2,10,-h)  #7
        self.vertex.addData3(-w2,0,-h)   #8
        self.vertex.addData3(-w2,0,-h)   #9
        self.vertex.addData3(-w2,0,ch)   #10

        self.texcoord.addData2(0.1,0.0)
        self.texcoord.addData2(0.1,0.1)
        self.texcoord.addData2(0.1,0.2)
        self.texcoord.addData2(0.1,0.9)
        self.texcoord.addData2(0.1,1.0)
        self.texcoord.addData2(0.0,0.9)
        self.texcoord.addData2(0.0,0.2)

        self.vertex.addData3(w2,0,0)    #4
        self.vertex.addData3(w2,0,ch)   #5
        self.vertex.addData3(w2,10,ch)  #6
        self.vertex.addData3(w2,10,-h)  #7
        self.vertex.addData3(w2,0,-h)   #8
        self.vertex.addData3(w2,0,-h)   #9
        self.vertex.addData3(w2,0,ch)   #10

        self.texcoord.addData2(0.9,0.0)
        self.texcoord.addData2(0.9,0.1)
        self.texcoord.addData2(0.9,0.2)
        self.texcoord.addData2(0.9,0.9)
        self.texcoord.addData2(0.9,1.0)
        self.texcoord.addData2(1.0,0.9)
        self.texcoord.addData2(1.0,0.2)


    def makeFront(self):
        tris = GeomTriangles(Geom.UHDynamic)
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        g= Geom(self.vdata)
        g.addPrimitive(tris)
        return g

    def makeFrame(self):
        tris = GeomTriangles(Geom.UHDynamic)
        tris.addVertices(4,11,5)
        tris.addVertices(5,11,12)
        tris.addVertices(6,5,12)
        tris.addVertices(6,12,13)
        tris.addVertices(6,14,7)
        tris.addVertices(6,13,14)
        tris.addVertices(7,15,8)
        tris.addVertices(7,14,15)
        tris.addVertices(6,9,10)
        tris.addVertices(6,7,9)
        tris.addVertices(13,17,16)
        tris.addVertices(13,16,14)
        g= Geom(self.vdata)
        g.addPrimitive(tris)
        return g

    def makeBox(self,front_texture,back_texture):
        fnode = GeomNode('front')
        fnode.addGeom(self.makeFront())
        bnode = GeomNode('back')
        bnode.addGeom(self.makeFrame())
        cube_node = GeomNode('cube')
        cube_node.add_child(fnode)
        cube_node.add_child(bnode)
        cube = render.attachNewNode(cube_node)
        if front_texture:
            cube.find('front').setTexture(front_texture)
        if back_texture:
            cube.find('back').setTexture(back_texture)
        return cube


