import numpy as np

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

class ElementH1(Element):
    """H1 conforming finite element."""

    def gbasis(self,mapping,X,i,tind):
        if isinstance(X,dict):
            [phi,dphi]=self.lbasis(X,i)
            u=phi
            du={}
            invDF=mapping.invDF(X,tind)
            
            if mapping.dim==2:
                du[0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]
                du[1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]
            elif mapping.dim==3:
                du[0]=invDF[0][0]*dphi[0]+invDF[1][0]*dphi[1]+invDF[2][0]*dphi[2]
                du[1]=invDF[0][1]*dphi[0]+invDF[1][1]*dphi[1]+invDF[2][1]*dphi[2]
                du[2]=invDF[0][2]*dphi[0]+invDF[1][2]*dphi[1]+invDF[2][2]*dphi[2]
            else:
                raise NotImplementedError("ElementH1.gbasis: not implemented for the given dim.")
            ddu=None # TODO fix ddu (for H1 element, Laplacian?)
            
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
            invDF=mapping.invDF(X,tind)
            
            if mapping.dim==2:
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

class ElementTriPpFast(ElementH1):
    def __init__(self,p):
        self.p=p
        self.maxdeg=p
        self.n_dofs=1
        self.f_dofs=np.max([p-1,0])
        self.i_dofs=np.max([(p-1)*(p-2)/2,0])

        self.nbdofs=3*self.n_dofs+3*self.f_dofs+self.i_dofs
        # TODO build bfuns using e.g. sympy and make handles of those.


class ElementTriPp(ElementH1):
    """A somewhat slow implementation of p-refinements for triangular mesh."""
    def __init__(self,p):
        self.p=p
        self.maxdeg=p
        self.n_dofs=1
        self.f_dofs=np.max([p-1,0])
        self.i_dofs=np.max([(p-1)*(p-2)/2,0])

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

class ElementP1(ElementH1):
    
    n_dofs=1
    maxdeg=1
    
    def __init__(self,dim=1):
        self.dim=dim

    def lbasis(self,X,i):
        # TODO implement for 1D

        if self.dim==2:
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
        elif self.dim==3:
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
        else:
            raise NotImplementedError("ElementP1.lbasis: not implemented for the given X.shape[0].")

        return phi,dphi


