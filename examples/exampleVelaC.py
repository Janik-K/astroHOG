# This file is part of AstroHOG
#
# Copyright (C) 2013-2017 Juan Diego Soler

import sys
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt

sys.path.append('/Users/jsoler/Documents/astrohog/')
from astrohog import *
from rgbtools import *

from astropy.wcs import WCS
from reproject import reproject_interp

def astroHOGexampleVelaC(vmin, vmax, ksz=1, suffix=''):

   dir='/Users/soler/Downloads/'
   hdu1=fits.open(dir+'HNC_3mm_Vela_C_T_MB.fits')
   hdu2=fits.open(dir+'12CO_MEDIAN_hann2.fits')

   v1=vmin*1000.;	v2=vmax*1000.
   v1str=str(vmin) #"%4.1f" % vmin     
   v2str=str(vmax) #"%4.1f" % vmax
   limsv=np.array([v1, v2, v1, v2])
   strksz="%i" % ksz
   
   cube1=hdu1[0].data
   sz1=np.shape(hdu1[0].data)
   CTYPE3=hdu1[0].header['CTYPE3']
   CDELT3=hdu1[0].header['CDELT3']
   CRVAL3=hdu1[0].header['CRVAL3']
   CRPIX3=hdu1[0].header['CRPIX3']
   zmin1=int(CRPIX3+(v1-CRVAL3)/CDELT3)
   zmax1=int(CRPIX3+(v2-CRVAL3)/CDELT3)
   velvec1=hdu1[0].header['CRVAL3']+(np.arange(sz1[0])-hdu1[0].header['CRPIX3'])*hdu1[0].header['CDELT3']

   refhdr1=hdu1[0].header.copy()
   NAXIS31=refhdr1['NAXIS3']
   del refhdr1['NAXIS3']
   del refhdr1['CTYPE3']
   del refhdr1['CRVAL3']
   del refhdr1['CRPIX3']
   del refhdr1['CDELT3']
   refhdr1['NAXIS']=2
   refhdr1['WCSAXES']=2

   cube2=hdu2[0].data
   sz2=np.shape(hdu2[0].data)
   CTYPE3=hdu2[0].header['CTYPE3']
   CDELT3=hdu2[0].header['CDELT3']
   CRVAL3=hdu2[0].header['CRVAL3']
   CRPIX3=hdu2[0].header['CRPIX3']
   zmin2=int(CRPIX3+(v1-CRVAL3)/CDELT3)
   zmax2=int(CRPIX3+(v2-CRVAL3)/CDELT3)
   velvec2=hdu2[0].header['CRVAL3']+(np.arange(sz2[0])-hdu2[0].header['CRPIX3'])*hdu2[0].header['CDELT3'] 

   refhdr2=hdu2[0].header.copy()
   NAXIS32=refhdr2['NAXIS3']
   del refhdr2['NAXIS3']
   del refhdr2['CTYPE3']
   del refhdr2['CRVAL3']
   del refhdr2['CRPIX3']
   del refhdr2['CDELT3']
   refhdr2['NAXIS']=2
   refhdr2['WCSAXES']=2

   newcube1=np.zeros([NAXIS31, sz2[1], sz2[2]])		
   cube1[np.isnan(cube1).nonzero()]=0. 

   print('Reprojecting to common grid')
   for i in range(0, NAXIS31):
      hduX=fits.PrimaryHDU(cube1[i,:,:])
      hduX.header=refhdr1
      mapX, footprintX=reproject_interp(hduX, refhdr2)
      newcube1[i,:,:]=mapX

      #import pdb; pdb.set_trace()

   # ==========================================================================================================
   res=40. #arcsec
   pxsz=np.abs(refhdr2['CDELT1'])*60.*60. #arcsec
   pxksz=np.int(np.round(ksz/pxsz))

   # ==========================================================================================================
   sz1=np.shape(newcube1)  
   newcube1[np.isnan(newcube1).nonzero()]=0.
   meanI=(newcube1.sum(axis=2)).sum(axis=1)  
   #x=np.sort(meanI)
   minrm=np.std(meanI[(meanI==np.min(meanI)).nonzero()]) 
   mask1=np.zeros(sz1)
   mask1[(newcube1==0.).nonzero()]=0.
   mask1[(newcube1 > minrm).nonzero()]=1
   mask1[:,0:ksz,:]=0.; mask1[:,sz1[1]-ksz:sz1[1],:]=0.
   mask1[:,:,0:ksz]=0.; mask1[:,:,sz1[2]-ksz:sz1[2]]=0.
   mask1[:,sz1[1]-80:sz1[1],:]=0.;

   sz2=np.shape(cube2)
   cube2[np.isnan(cube2).nonzero()]=0.
   minrm=np.std(cube2[0,:,:])
   mask2=np.zeros(sz2)
   mask2[(cube2 > minrm).nonzero()]=1.

   # ============================================================================================================
   print('Calculating HOG correlation')
   corrplane, corrcube, scube1, scube2 =HOGcorr_cube(newcube1, cube2, zmin1, zmax1, zmin2, zmax2, pxsz=pxsz, ksz=ksz, res=res, mask1=mask1, mask2=mask2)

   im=plt.imshow(corrplane, origin='lower', extent=limsv/1e3, interpolation='none')
   plt.contour(corrplane, [np.std(corrplane), 2.*np.std(corrplane)], origin='lower', colors=('w','w'), extent=limsv/1e3)
   plt.xlabel(r'$v_{12CO}$ [km/s]')
   plt.ylabel(r'$v_{HNC}$ [km/s]')
   plt.yticks(rotation='vertical')
   plt.colorbar(im)
   #plt.show()
   plt.savefig('VelaCHOG_HCNand12CO'+'_k'+strksz+'_v'+v1str+'to'+v2str+suffix+'_CorrPlane.png', bbox_inches='tight')
   plt.close()

   ix=(corrplane == np.max(corrplane)).nonzero()[0][0]
   jx=(corrplane == np.max(corrplane)).nonzero()[1][0]
   v1maxCorr=velvec1[zmin1+ix]/1e3; strv1maxCorr="%4.1f" % v1maxCorr
   v2maxCorr=velvec2[zmin2+jx]/1e3; strv2maxCorr="%4.1f" % v2maxCorr

   refhdr2postHOG=refhdr2.copy()
   szPost=np.shape(corrcube.sum(axis=0))

   ax1=plt.subplot(1,1,1, projection=WCS(refhdr2postHOG))
   im=ax1.imshow(corrcube[ix,jx,:,:], origin='lower', cmap='seismic', interpolation='none')
   ax1.coords.grid(color='gray')
   ax1.coords['glon'].set_axislabel('Galactic Longitude')
   ax1.coords['glat'].set_axislabel('Galactic Latitude')
   ax1.set_title(r'HOG corr. $v_{HCN}=$'+strv1maxCorr+' $v_{12CO}=$'+strv2maxCorr+'km/s')
   plt.colorbar(im, orientation='horizontal',fraction=0.06, pad=0.025)
   #plt.colorbar(im, fraction=0.046, pad=0.04)
   #plt.show()
   plt.savefig('VelaCHOG_HCNand12CO'+'_k'+strksz+'_v'+v1str+'to'+v2str+suffix+'_CorrMapMax.png', bbox_inches='tight')
   plt.close()
 
   inmap=scube1[zmin1+ix,:,:]
   inmap[inmap < 0.]=0.
   red  =(inmap-np.min(inmap))/(np.max(inmap)-np.min(inmap))
   inmap=scube2[zmin2+jx,:,:]
   inmap[inmap < 0.]=0.
   green=(inmap-np.min(inmap))/(np.max(inmap)-np.min(inmap))
   blue =np.zeros(np.shape(green))

   sz=np.shape(red)
   rgb=np.zeros([sz[0], sz[1], 3])
   rgb[:,:,0]=red
   rgb[:,:,1]=green
   rgb[:,:,2]=blue

   ax1=plt.subplot(1,1,1, projection=WCS(refhdr2))
   ax1.imshow(rgb, origin='lower')
   ax1.coords.grid(color='white')
   ax1.coords['glon'].set_axislabel('Galactic Longitude')
   ax1.coords['glat'].set_axislabel('Galactic Latitude')
   ax1.set_title(r'$v_{HCN}=$'+strv1maxCorr+' $v_{12CO}=$'+strv2maxCorr+'km/s')
   #plt.show()
   plt.savefig('VelaCHOG_HCNand12CO'+'_k'+strksz+'_v'+v1str+'to'+v2str+suffix+'_maxCorrChannelsRGB.png', bbox_inches='tight')
   plt.close()

   #import pdb; pdb.set_trace()


ksz=72. #36. # in arcseconds
astroHOGexampleVelaC(0., 5., ksz=ksz)




