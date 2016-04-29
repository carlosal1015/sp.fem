"""
@author: Tom Gustafsson


This file is part of sp.fem.

sp.fem is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

sp.fem is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with sp.fem.  If not, see <http://www.gnu.org/licenses/>. 
"""
import numpy as np
from numpy.polynomial.polynomial import polyder,polyval2d

class Element:
    """Finite element."""

    maxdeg=0 # maximum polynomial degree; for determining quadrature
    dim=0 # spatial dimension
    tdim=0 # target dimension
    torder=0 # target tensorial order

    """
    The discretized field is a mapping
       U : C^dim -> C^(tdim x ... x tdim)
    where the product is taken 'torder' times.
    """

    # number of ...
    n_dofs=0 # nodal dofs
    i_dofs=0 # interior dofs
    f_dofs=0 # facet dofs (2d and 3d only)
    e_dofs=0 # edge dofs (3d only)

    def lbasis(self,X,i):
        """Returns local basis functions evaluated at some local points."""
        raise NotImplementedError("Element.lbasis: local basis (lbasis) not implemented!")

    def gbasis(self,X,i,tind):
        """Returns global basis functions evaluated at some local points."""
        raise NotImplementedError("Element.gbasis: local basis (lbasis) not implemented!")

class ElementHdiv(Element):
    """Hdiv conforming finite element."""

    def gbasis(self,mapping,X,i,tind):
        if isinstance(X,dict):
            raise NotImplementedError("Calling ElementHdiv gbasis with dict not implemented!")
        else:
            x={}
            x[0]=X[0,:]
            x[1]=X[1,:]
            [phi,dphi]=self.lbasis(x,i)

        DF=mapping.DF(X,tind)
        detDF=mapping.detDF(X,tind)

        u={}
        u[0]=(DF[0][0]*phi[0]+DF[0][1]*phi[1])/detDF
        u[1]=(DF[1][0]*phi[0]+DF[1][1]*phi[1])/detDF

        du=dphi/detDF

        ddu=None

        return u,du,ddu

class ElementTriRT0(ElementHdiv):
    """Lowest order Raviart-Thomas element for triangle."""

    maxdeg=1
    f_dofs=1

    def lbasis(self,X,i):
        phi={}
        phi[0]={
                0:lambda x,y: x,
                1:lambda x,y: x,
                2:lambda x,y: -x+1.,
                }[i](X[0],X[1])
        phi[1]={
                0:lambda x,y: y-1.,
                1:lambda x,y: y,
                2:lambda x,y: -y,
                }[i](X[0],X[1])
        dphi={
            0:lambda x,y: 2+0.*x,
            1:lambda x,y: 2+0.*x,
            2:lambda x,y: -2+0.*x,
            }[i](X[0],X[1])

        return phi,dphi

class ElementH1(Element):
    """H1 conforming finite element."""

    def gbasis(self,mapping,X,i,tind):
        if isinstance(X,dict):
            [phi,dphi]=self.lbasis(X,i)
            u=phi
            du={}
        else:
            x={}
            x[0]=X[0,:]
            if mapping.dim>=2:
                x[1]=X[1,:]
            if mapping.dim>=3:
                x[2]=X[2,:]
            [phi,dphi]=self.lbasis(x,i)
            u=np.tile(phi,(len(tind),1))
            du={}
            
        invDF=mapping.invDF(X,tind) # investigate if 'x' should used after else

        self.dim=mapping.dim

        if mapping.dim==1:
            du=np.outer(invDF,dphi)
        elif mapping.dim==2:
            du[0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]
            du[1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]
        elif mapping.dim==3:
            du[0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]+invDF[2][0]*dphi[2]
            du[1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]+invDF[2][1]*dphi[2]
            du[2]=invDF[0][2]*dphi[0]+invDF[1][2]*dphi[1]+invDF[2][2]*dphi[2]
        else:
            raise NotImplementedError("ElementH1.gbasis: not implemented for the given dim.")
        ddu=None # TODO fix ddu (for H1 element, Laplacian?)

        return u,du,ddu

class ElementH1Vec(ElementH1):
    """H1 element -> vectorial H1 element."""
    def __init__(self,elem):
        if elem.dim==0:
            print "ElementH1Vec.__init__(): Warning! Parent element has no dim-variable!"
        self.dim=elem.dim
        self.elem=elem
        # multiplicate the amount of DOF's with dim
        self.n_dofs=self.elem.n_dofs*self.dim
        self.f_dofs=self.elem.f_dofs*self.dim
        self.i_dofs=self.elem.i_dofs*self.dim
        self.e_dofs=self.elem.e_dofs*self.dim
        self.maxdeg=elem.maxdeg

    def gbasis(self,mapping,X,i,tind):
        ind=np.floor(float(i)/float(self.dim))
        n=i-self.dim*ind

        u={}
        du={}

        if isinstance(X,dict):
            [phi,dphi]=self.elem.lbasis(X,ind)
        else:
            x={}
            x[0]=X[0,:]
            x[1]=X[1,:]
            if mapping.dim>=3:
                x[2]=X[2,:]
            [phi,dphi]=self.elem.lbasis(x,ind)
            phi=np.tile(phi,(len(tind),1))
            for itr in range(self.dim):
                dphi[itr]=np.tile(dphi[itr],(len(tind),1))

        # fill appropriate slots of u and du (u[0] -> x-component of u etc.)
        for itr in range(self.dim):
            if itr==n:
                u[itr]=phi
                invDF=mapping.invDF(X,tind) # investigate if 'x' should used after else
                du[itr]={}
                if mapping.dim==2:
                    du[itr][0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]
                    du[itr][1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]
                elif mapping.dim==3:
                    du[itr][0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]+invDF[2][0]*dphi[2]
                    du[itr][1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]+invDF[2][1]*dphi[2]
                    du[itr][2]=invDF[0][2]*dphi[0]+invDF[1][2]*dphi[1]+invDF[2][2]*dphi[2]
                else:
                    raise NotImplementedError("ElementH1Vec.gbasis: not implemented for the given dim.")
            else:
                u[itr]=0*phi
                du[itr]={}
                for jtr in range(self.dim):
                    du[itr][jtr]=0*phi
            
        ddu=None
        return u,du,ddu
        
class ElementQ1(ElementH1):
    """Simplest quadrilateral element."""
    
    def __init__(self):
        self.maxdeg=2
        self.n_dofs=1
        
    def lbasis(self,X,i):
        phi={
            0:lambda x,y: 0.25*(1-x)*(1-y),
            1:lambda x,y: 0.25*(1+x)*(1-y),
            2:lambda x,y: 0.25*(1+x)*(1+y),
            3:lambda x,y: 0.25*(1-x)*(1+y)
            }[i](X[0],X[1])
        dphi={}
        dphi[0]={
            0:lambda x,y: 0.25*(-1+y),
            1:lambda x,y: 0.25*(1-y),
            2:lambda x,y: 0.25*(1+y),
            3:lambda x,y: 0.25*(-1-y)
            }[i](X[0],X[1])
        dphi[1]={
            0:lambda x,y: 0.25*(-1+x),
            1:lambda x,y: 0.25*(-1-x),
            2:lambda x,y: 0.25*(1+x),
            3:lambda x,y: 0.25*(1-x)
            }[i](X[0],X[1])
        return phi,dphi
        
class ElementQ2(ElementH1):
    """Second order quadrilateral element."""
    
    def __init__(self):
        self.maxdeg=3
        self.n_dofs=1
        self.f_dofs=1
        self.i_dofs=1
        
    def lbasis(self,X,i):
        phi={
            0:lambda x,y: 0.25*(x**2-x)*(y**2-y),
            1:lambda x,y: 0.25*(x**2+x)*(y**2-y),
            2:lambda x,y: 0.25*(x**2+x)*(y**2+y),
            3:lambda x,y: 0.25*(x**2-x)*(y**2+y),
            4:lambda x,y: 0.5*(y**2-y)*(1-x**2),
            5:lambda x,y: 0.5*(x**2+x)*(1-y**2),
            6:lambda x,y: 0.5*(y**2+y)*(1-x**2),
            7:lambda x,y: 0.5*(x**2-x)*(1-y**2),
            8:lambda x,y: (1-x**2)*(1-y**2)
            }[i](X[0],X[1])
        dphi={}
        dphi[0]={
            0:lambda x,y:((-1 + 2*x)*(-1 + y)*y)/4.,
            1:lambda x,y:((1 + 2*x)*(-1 + y)*y)/4.,
            2:lambda x,y:((1 + 2*x)*y*(1 + y))/4.,
            3:lambda x,y:((-1 + 2*x)*y*(1 + y))/4.,
            4:lambda x,y:-(x*(-1 + y)*y),
            5:lambda x,y:-((1 + 2*x)*(-1 + y**2))/2.,
            6:lambda x,y:-(x*y*(1 + y)),
            7:lambda x,y:-((-1 + 2*x)*(-1 + y**2))/2.,
            8:lambda x,y:2*x*(-1 + y**2)
            }[i](X[0],X[1])
        dphi[1]={
            0:lambda x,y:((-1 + x)*x*(-1 + 2*y))/4.,
            1:lambda x,y:(x*(1 + x)*(-1 + 2*y))/4.,
            2:lambda x,y:(x*(1 + x)*(1 + 2*y))/4.,
            3:lambda x,y:((-1 + x)*x*(1 + 2*y))/4.,
            4:lambda x,y:-((-1 + x**2)*(-1 + 2*y))/2.,
            5:lambda x,y:-(x*(1 + x)*y),
            6:lambda x,y:-((-1 + x**2)*(1 + 2*y))/2.,
            7:lambda x,y:-((-1 + x)*x*y),
            8:lambda x,y:2*(-1 + x**2)*y
            }[i](X[0],X[1])
        return phi,dphi

class ElementTriPp(ElementH1):
    """A somewhat slow implementation of hierarchical p-basis for triangular mesh."""
    def __init__(self,p):
        self.p=p
        self.maxdeg=p
        self.n_dofs=1
        self.f_dofs=np.max([p-1,0])
        self.i_dofs=np.max([(p-1)*(p-2)/2,0])
        self.dim=2

        self.nbdofs=3*self.n_dofs+3*self.f_dofs+self.i_dofs

    def intlegpoly(self,x,n):
        """Generate integrated Legendre polynomials."""
        n=n+1
        
        P={}
        P[0]=np.ones(x.shape)
        if n>1:
            P[1]=x
        
        for i in np.arange(1,n):
            P[i+1]=((2.*i+1.)/(i+1.))*x*P[i]-(i/(i+1.))*P[i-1]
            
        iP={}
        iP[0]=np.ones(x.shape)
        if n>1:
            iP[1]=x
            
        for i in np.arange(1,n-1):
            iP[i+1]=(P[i+1]-P[i-1])/(2.*i+1.)
            
        dP={}
        dP[0]=np.zeros(x.shape)
        for i in np.arange(1,n):
            dP[i]=P[i-1]
        
        return iP,dP
        
    def lbasis(self,X,n):
        """Evaluate n'th Lagrange basis of order self.p."""        
        p=self.p

        if len(X)!=2:
            raise NotImplementedError("ElementTriPp: not implemented for the given dimension of X.")

        phi={}
        phi[0]=1.-X[0]-X[1]
        phi[1]=X[0]
        phi[2]=X[1]
        
        # local basis function gradients TODO fix these somehow
        gradphi_x={}
        gradphi_x[0]=-1.*np.ones(X[0].shape)
        gradphi_x[1]=1.*np.ones(X[0].shape)
        gradphi_x[2]=np.zeros(X[0].shape)
        
        gradphi_y={}
        gradphi_y[0]=-1.*np.ones(X[0].shape)
        gradphi_y[1]=np.zeros(X[0].shape)
        gradphi_y[2]=1.*np.ones(X[0].shape)

        if n<=2:
            # return first three
            dphi={}
            dphi[0]=gradphi_x[n]
            dphi[1]=gradphi_y[n]
            return phi[n],dphi

        # use same ordering as in mesh
        e=np.array([[0,1],[1,2],[0,2]]).T
        offset=3
        
        # define edge basis functions
        if(p>1):
            for i in range(3):
                eta=phi[e[1,i]]-phi[e[0,i]]
                deta_x=gradphi_x[e[1,i]]-gradphi_x[e[0,i]]
                deta_y=gradphi_y[e[1,i]]-gradphi_y[e[0,i]]
                
                # generate integrated Legendre polynomials
                [P,dP]=self.intlegpoly(eta,p-2)
                   #print len(P)
                   #print len(dP)
                
                for j in range(len(P)):
                    phi[offset]=phi[e[0,i]]*phi[e[1,i]]*P[j]
                    gradphi_x[offset]=gradphi_x[e[0,i]]*phi[e[1,i]]*P[j]+\
                                      gradphi_x[e[1,i]]*phi[e[0,i]]*P[j]+\
                                      deta_x*phi[e[0,i]]*phi[e[1,i]]*dP[j]
                    gradphi_y[offset]=gradphi_y[e[0,i]]*phi[e[1,i]]*P[j]+\
                                      gradphi_y[e[1,i]]*phi[e[0,i]]*P[j]+\
                                      deta_y*phi[e[0,i]]*phi[e[1,i]]*dP[j]
                    if offset==n:
                        # return if computed
                        dphi={}
                        dphi[0]=gradphi_x[n]
                        dphi[1]=gradphi_y[n]
                        return phi[n],dphi
                    offset=offset+1  
        
        # define interior basis functions
        if(p>2):
            B={}
            dB_x={}
            dB_y={}
            if(p>3):
                pm3=ElementTriPp(p-3)
                for itr in range(pm3.nbdofs):
                    pphi,pdphi=self.lbasis(X,itr)
                    B[itr]=pphi
                    dB_x[itr]=pdphi[0]
                    dB_y[itr]=pdphi[1]
                N=pm3.nbdofs
            else:
                B[0]=np.ones(X[0].shape)
                dB_x[0]=np.zeros(X[0].shape)
                dB_y[0]=np.zeros(X[0].shape)
                N=1
                
            bubble=phi[0]*phi[1]*phi[2]
            dbubble_x=gradphi_x[0]*phi[1]*phi[2]+\
                      gradphi_x[1]*phi[2]*phi[0]+\
                      gradphi_x[2]*phi[0]*phi[1]
            dbubble_y=gradphi_y[0]*phi[1]*phi[2]+\
                      gradphi_y[1]*phi[2]*phi[0]+\
                      gradphi_y[2]*phi[0]*phi[1]
            
            for i in range(N):
                phi[offset]=bubble*B[i]
                gradphi_x[offset]=dbubble_x*B[i]+dB_x[i]*bubble
                gradphi_y[offset]=dbubble_y*B[i]+dB_y[i]*bubble
                if offset==n:
                    # return if computed
                    dphi={}
                    dphi[0]=gradphi_x[n]
                    dphi[1]=gradphi_y[n]
                    return phi[n],dphi
                offset=offset+1

        raise IndexError("ElementTriPp.lbasis: reached end of lbasis without returning anything.")

class ElementTriDG(ElementH1):
    def __init__(self,elem):
        # change all dofs to interior dofs
        self.elem=elem
        self.i_dofs=3*elem.n_dofs+3*elem.f_dofs+elem.i_dofs
        self.dim=2
    def lbasis(self,X,i):
        return self.elem.lbasis(X,i)
    
class ElementTetP0(ElementH1):
    i_dofs=1
    max_deg=1

    def lbasis(self,X,i):
        phi={
            0:lambda x,y,z: 1+0*x
            }[i](X[0],X[1],X[2])
        dphi={}
        dphi[0]={
                0:lambda x,y,z: 0*x
                }[i](X[0],X[1],X[2])
        dphi[1]={
                0:lambda x,y,z: 0*x
                }[i](X[0],X[1],X[2])
        dphi[2]={
                0:lambda x,y,z: 0*x
                }[i](X[0],X[1],X[2])
        return phi,dphi

class ElementTriP0(ElementH1):
    i_dofs=1
    max_deg=1

    def lbasis(self,X,i):
        phi={
            0:lambda x,y: 1+0*x
            }[i](X[0],X[1])
        dphi={}
        dphi[0]={
                0:lambda x,y: 0*x
                }[i](X[0],X[1])
        dphi[1]={
                0:lambda x,y: 0*x
                }[i](X[0],X[1])
        return phi,dphi

class ElementP0(ElementTriP0):
    pass

class ElementTriMini(ElementH1):
    dim=2
    n_dofs=1
    i_dofs=1
    max_deg=3

    def lbasis(self,X,i):
        phi={
            0:lambda x,y: 1-x-y,
            1:lambda x,y: x,
            2:lambda x,y: y,
            3:lambda x,y: (1-x-y)*x*y
            }[i](X[0],X[1])

        dphi={}
        dphi[0]={
                0:lambda x,y: -1+0*x,
                1:lambda x,y: 1+0*x,
                2:lambda x,y: 0*x,
                3:lambda x,y: (1-x-y)*y-x*y
                }[i](X[0],X[1])
        dphi[1]={
                0:lambda x,y: -1+0*x,
                1:lambda x,y: 0*x,
                2:lambda x,y: 1+0*x,
                3:lambda x,y: (1-x-y)*x-x*y
                }[i](X[0],X[1])
        return phi,dphi
        
class ElementTetP2(ElementH1):
    
    dim=3
    n_dofs=1
    e_dofs=1
    maxdeg=2
    
    def lbasis(self,X,i):
        
        phi={ # order (0,0,0) (1,0,0) (0,1,0) (0,0,1) and then according to mesh local t2e
            0:lambda x,y,z: 1. - 3.*x + 2.*x**2 - 3.*y + 4.*x*y + 2.*y**2 - 3.*z + 4.*x*z + 4.*y*z + 2.*z**2,
            1:lambda x,y,z: 0. - 1.*x + 2.*x**2,
            2:lambda x,y,z: 0. - 1.*y + 2.*y**2,
            3:lambda x,y,z: 0. - 1.*z + 2.*z**2,
            4:lambda x,y,z: 0. + 4.*x - 4.*x**2 - 4.*x*y - 4.*x*z,
            5:lambda x,y,z: 0. + 4.*x*y,
            6:lambda x,y,z: 0. + 4.*y - 4.*x*y - 4.*y**2 - 4.*y*z,
            7:lambda x,y,z: 0. + 4.*z - 4.*x*z - 4.*y*z - 4.*z**2,
            8:lambda x,y,z: 0. + 4.*x*z,
            9:lambda x,y,z: 0. + 4.*y*z,
            }[i](X[0],X[1],X[2])
    
        dphi={}
        dphi[0]={
                0:lambda x,y,z: -3. + 4.*x + 4.*y + 4.*z,
                1:lambda x,y,z: -1. + 4.*x,
                2:lambda x,y,z: 0.*x,
                3:lambda x,y,z: 0.*x,
                4:lambda x,y,z: 4. - 8.*x - 4.*y - 4.*z,
                5:lambda x,y,z: 4.*y,
                6:lambda x,y,z: -4.*y,
                7:lambda x,y,z: -4.*z,
                8:lambda x,y,z: 4.*z,
                9:lambda x,y,z: 0.*x,
                }[i](X[0],X[1],X[2])
        dphi[1]={
                0:lambda x,y,z: -3. + 4.*x + 4.*y + 4.*z,
                1:lambda x,y,z: 0.*x,
                2:lambda x,y,z: -1. + 4.*y,
                3:lambda x,y,z: 0.*x,
                4:lambda x,y,z: -4.*x,
                5:lambda x,y,z: 4.*x,
                6:lambda x,y,z: 4. - 4.*x - 8.*y - 4.*z,
                7:lambda x,y,z: -4.*z,
                8:lambda x,y,z: 0.*x,
                9:lambda x,y,z: 4.*z,
                }[i](X[0],X[1],X[2])
        dphi[2]={
                0:lambda x,y,z: -3. + 4.*x + 4.*y + 4.*z,
                1:lambda x,y,z: 0.*x,
                2:lambda x,y,z: 0.*x,
                3:lambda x,y,z: -1. + 4.*z,
                4:lambda x,y,z: -4.*x,
                5:lambda x,y,z: 0.*x,
                6:lambda x,y,z: -4.*y,
                7:lambda x,y,z: 4. - 4.*x - 4.*y - 8.*z,
                8:lambda x,y,z: 4.*x,
                9:lambda x,y,z: 4.*y,       
                }[i](X[0],X[1],X[2])
                
        return phi,dphi
        
class ElementLineP1(ElementH1):
    n_dofs=1
    dim=1
    maxdeg=1
    
    def lbasis(self,X,i):
        phi={
            0:lambda x: 1-x,
            1:lambda x: x,
            }[i](X[0])

        dphi={}
        dphi={
                0:lambda x: -1+0*x,
                1:lambda x: 1+0*x,
                }[i](X[0])
                
        return phi,dphi        
        
class ElementTriP1(ElementH1):
    n_dofs=1
    dim=2
    maxdeg=1
    
    def lbasis(self,X,i):
        phi={
            0:lambda x,y: 1-x-y,
            1:lambda x,y: x,
            2:lambda x,y: y
            }[i](X[0],X[1])

        dphi={}
        dphi[0]={
                0:lambda x,y: -1+0*x,
                1:lambda x,y: 1+0*x,
                2:lambda x,y: 0*x
                }[i](X[0],X[1])
        dphi[1]={
                0:lambda x,y: -1+0*x,
                1:lambda x,y: 0*x,
                2:lambda x,y: 1+0*x
                }[i](X[0],X[1])
                
        return phi,dphi
        
class ElementTetP1(ElementH1):
    
    n_dofs=1
    maxdeg=1
    dim=3

    def lbasis(self,X,i):

        phi={
            0:lambda x,y,z: 1-x-y-z,
            1:lambda x,y,z: x,
            2:lambda x,y,z: y,
            3:lambda x,y,z: z,
            }[i](X[0],X[1],X[2])

        dphi={}
        dphi[0]={
                0:lambda x,y,z: -1+0*x,
                1:lambda x,y,z: 1+0*x,
                2:lambda x,y,z: 0*x,
                3:lambda x,y,z: 0*x
                }[i](X[0],X[1],X[2])
        dphi[1]={
                0:lambda x,y,z: -1+0*x,
                1:lambda x,y,z: 0*x,
                2:lambda x,y,z: 1+0*x,
                3:lambda x,y,z: 0*x
                }[i](X[0],X[1],X[2])
        dphi[2]={
                0:lambda x,y,z: -1+0*x,
                1:lambda x,y,z: 0*x,
                2:lambda x,y,z: 0*x,
                3:lambda x,y,z: 1+0*x
                }[i](X[0],X[1],X[2])

        return phi,dphi

