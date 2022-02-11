import numpy as np
import itk
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid
import sys
import os

#M118_T2W: T2W image
#128x128
#16 slices
#16-bit

#M118_AllSlicesBvalues.bin: All DW images for all (16) slices and all (5) b-values.
#96x96
#96 total slices (16 slices x 5 b-values)
#64-bit

#M118_ADCfit.bin : ADC maps from 3-parameter fitting of previous b-value images
#96x96
#16 slices
#64-bit

#M118_DCE_all_images : All 157 time points of DCE images for all 16 slices
#128x128
#2512 slices (157 time points, 16 slices)
#64-bit

def convertImage(inName, outName, pixelType, shape, spacing, permute=None):

    # may need .byteswap(). depending on endianess

    a = np.fromfile(inName, pixelType, -1).reshape( shape, order="F" )
    img = itk.image_from_array(a)
    if not permute is None:
        img = itk.permute_axes_image_filter(img, order=permute)
    img.SetSpacing(spacing)

    itk.imwrite(img, outName)


idir=sys.argv[1]
odir=sys.argv[2]
id=sys.argv[3]

os.makedirs( os.path.join(odir, id, "T2", "images"), exist_ok=True)
os.makedirs( os.path.join(odir, id, "DWI", "images"), exist_ok=True)
os.makedirs( os.path.join(odir, id, "DWI", "analysis"), exist_ok=True)
os.makedirs( os.path.join(odir, id, "DCE", "images"), exist_ok=True)
os.makedirs( os.path.join(odir, id, "DCE", "analysis"), exist_ok=True)

t2ImageIn = os.path.join(idir,id, "T2","images",id+"_T2W.raw")
t2ImageOut = os.path.join(odir,id,"T2","images",id+"_T2W.nii.gz")
convertImage(t2ImageIn, t2ImageOut, np.short, (128,128,16), [0.25,0.25,1.5] )


# order is [x,y,b-value,z]
dwiImageIn = os.path.join(idir,id, "DWI","images",id+"_DWI.bin")
dwiImageOut = os.path.join(odir,id,"DWI","images",id+"_DWI.nii.gz")
bvecOut = os.path.join(odir,id,"DWI","images",id+"_DWI.bvec")
bvalOut = os.path.join(odir,id,"DWI","images",id+"_DWI.bval")
convertImage(dwiImageIn, dwiImageOut, np.double, (96,96,5,16), [0.333, 0.333, 1.5,1], [0,1,3,2] )
with open(bvalOut, 'w') as bvalFile:
    bvalFile.write( "10 535 1070 1479 2141\n")
    bvalFile.close()
with open(bvecOut, 'w') as bvecFile:
    bvecFile.write( "1 1 1 1 1\n")
    bvecFile.write( "1 1 1 1 1\n")
    bvecFile.write( "1 1 1 1 1\n")
    bvecFile.close()

dwiShape = (96,96,16)
dwiSpacing = [0.333, 0.333, 1.5]

adcIn=os.path.join(idir,id, "DWI","analysis",id+"_DWI_ADCMaps.raw")
adcOut=os.path.join(odir,id, "DWI","analysis",id+"_DWI_ADCMaps.nii.gz")
convertImage(adcIn, adcOut, np.double, dwiShape, dwiSpacing)

kurtosisImageIn = os.path.join(idir,id, "DWI","analysis",id+"_DWI_KurtosisMaps.raw")
kurtosisImageOut = os.path.join(odir,id,"DWI","analysis",id+"_DWI_KurtosisMaps.nii.gz")
convertImage(kurtosisImageIn, kurtosisImageOut, np.double, dwiShape, dwiSpacing)

dwiMaskIn = os.path.join(idir,id, "DWI","analysis",id+"_DWI_Mask.raw")
dwiMaskOut = os.path.join(odir,id,"DWI","analysis",id+"_DWI_Mask.nii.gz")
convertImage(dwiMaskIn, dwiMaskOut, np.ubyte, dwiShape, dwiSpacing)

dwiLabels = os.path.join(odir,id,"DWI","analysis",id+"_DWI_Labels.csv")
with open(dwiLabels, 'w') as dwiKey:
    dwiKey.write( 'label,structure,note\n')
    dwiKey.write( '1,muscle,"NA"\n')
    dwiKey.write( '2,kidney,"NA"\n')
    dwiKey.write( '3,tumor,"NA"\n')
    dwiKey.write( '4,phantom_1,"10% aq. PVP phantom"\n')
    dwiKey.write( '5,phantom_2,"10% aq. PVP phantom"\n')
    dwiKey.close()



dceShape = (128,128,16)
dceSpacing = [0.25,0.25,1.5]

# Contrast injected at 120s (index=27.27)
dceImageIn = os.path.join(idir,id, "DCE","images",id+"_DCE.bin")
dceImageOut = os.path.join(odir,id,"DCE","images",id+"_DCE.nii.gz")
convertImage( dceImageIn, dceImageOut, np.double, (128,128,16,157), [0.25, 0.25, 1.5, 4.4])

tr1ImageIn=os.path.join(idir,id, "DCE","images",id+"_AFI_TR1.raw")
tr1ImageOut=os.path.join(odir,id, "DCE","images",id+"_AFI_TR1.nii.gz")
convertImage( tr1ImageIn, tr1ImageOut, np.float32, dceShape, dceSpacing)

tr2ImageIn=os.path.join(idir,id, "DCE","images",id+"_AFI_TR2.raw")
tr2ImageOut=os.path.join(odir,id, "DCE","images",id+"_AFI_TR2.nii.gz")
convertImage( tr2ImageIn, tr2ImageOut, np.float32, dceShape, dceSpacing)


b1ImageIn=os.path.join(idir,id, "DCE","analysis",id+"_B1FitMaps.raw")
b1ImageOut=os.path.join(odir,id, "DCE","analysis",id+"_B1FitMaps.nii.gz")
b1ImageIn=os.path.join(idir,id, "DCE","analysis",id+"_B1Maps.raw")
b1ImageOut=os.path.join(odir,id, "DCE","analysis",id+"_B1Maps.nii.gz")
convertImage(b1ImageIn, b1ImageOut, np.float32, dceShape, dceSpacing)

for deg in ['2deg', '5deg', '8deg', '12deg', '16deg', '20deg']:
    degIn=os.path.join(idir,id, "DCE","images",id+"_VFA_"+deg+".raw")
    degOut=os.path.join(odir,id, "DCE","images",id+"_VFA_"+deg+".nii.gz")
    convertImage(degIn, degOut, np.float32, dceShape, dceSpacing)

t1ImageIn=os.path.join(idir,id, "DCE","analysis",id+"_T1Maps.raw")
t1ImageOut=os.path.join(odir,id, "DCE","analysis",id+"_T1Maps.nii.gz")
convertImage(t1ImageIn, t1ImageOut, np.float32, dceShape, dceSpacing)

kImageIn=os.path.join(idir,id, "DCE","analysis",id+"_KtransMaps.bin")
kImageOut=os.path.join(odir,id, "DCE","analysis",id+"_KtransMaps.nii.gz")
convertImage(kImageIn, kImageOut, np.float64, dceShape, dceSpacing)

vImageIn=os.path.join(idir,id, "DCE","analysis",id+"_VeMaps.bin")
vImageOut=os.path.join(odir,id, "DCE","analysis",id+"_VeMaps.nii.gz")
convertImage(vImageIn, vImageOut, np.float64, dceShape, dceSpacing)

#1 = muscle
#2 = kidney (note the kidney ROI for DCE is thinner and only placed on the renal cortex)
#3 = tumor
#4 = phantom 1 (10% aq. PVP phantom)
#5 = phantom 2 (40% aq. PVP phantom).

dceMaskIn=os.path.join(idir,id, "DCE","analysis",id+"_DCE_Mask.raw")
dceMaskOut=os.path.join(odir,id, "DCE","analysis",id+"_DCE_Mask.nii.gz")
convertImage(dceMaskIn, dceMaskOut, np.ubyte, dceShape, dceSpacing)
dceLabels=os.path.join(odir,id, "DCE","analysis",id+"_DCE_Labels.csv")
with open(dceLabels, 'w') as dceKey:
    dceKey.write( 'label,structure,note\n')
    dceKey.write( '1,muscle,"NA"\n')
    dceKey.write( '2,kidney,"renal cortex"\n')
    dceKey.write( '3,tumor,"NA"\n')
    dceKey.write( '4,phantom_1,"10% aq. PVP phantom"\n')
    dceKey.write( '5,phantom_2,"10% aq. PVP phantom"\n')
    dceKey.close()

