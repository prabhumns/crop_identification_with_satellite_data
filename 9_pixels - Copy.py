<<<<<<< HEAD
import h5py
import tables
import time
import gc
from osgeo import gdal, osr, ogr, gdal_array
import os
import numpy as np
from numpy.linalg import inv
import _pickle as pickle
from random import shuffle
from shutil import copyfile

sat_file = 'E:/Time Series/satdata/12/1557907_2016-12-29_RE1_3A_Analytic.tif'

main_folder = 'E:/Time Series'

crops = {1:'CORN',4:'SORGHUM', 5:'SOYABEENS', 13:'POP_OR_ORN', 36:'ALFALFA', 28:'OATS', 27:'RYE', 53:'PEAS', 111:'WATER_BODY', 121:'DEVELOPED', 122:'DEVELOPED', 123:'DEVELOPED', 124:'DEVELOPED',141:'FOREST', 142:'FOREST',243:'CABBAGE' }

def Convert(k, old_gt, old_cs, new_cs):
	a = k[0]; s= k[1]
	transform = osr.CoordinateTransformation(old_cs,new_cs)
	o1 = old_gt[0] + a*old_gt[1] + s*old_gt[2]
	o2 = old_gt[3] + a*old_gt[4] + s*old_gt[5]
	d = transform.TransformPoint(o1,o2)
	return (d[0],d[1])

def calculate(a, g):
	B= np.mat([[a[0]-g[0]],[a[1]-g[3]]])
	A = np.mat([[g[1],g[2]],[g[4],g[5]]])
	X = inv(A) * B
	return (int(X[0]), int(X[1]))


def Crop(i,j, sdb_gt, sdb_cs):
	lis = os.listdir(main_folder + '/crop_data')
	for crop_file in lis:
		if crop_file[-4:] == '.tif':
			cd = gdal.Open(main_folder + '/crop_data/' + crop_file)
			cd_gt = cd.GetGeoTransform()
			cd_cs = osr.SpatialReference()
			cd_cs.ImportFromWkt(cd.GetProjectionRef())
			q = Convert((i,j), old_gt = sdb_gt, old_cs = sdb_cs, new_cs = cd_cs)
			ww = calculate(q, cd_gt)
			#print(ww)
			x = ww[0]; y = ww[1]
			if x >= 0 and x < cd.RasterXSize and y >=0 and y < cd.RasterYSize:
				return int(gdal_array.DatasetReadAsArray(cd, x,y,1, 1))
	return 0
			
def check_crop_data(i,j,sdb_gt,sdb_cs, crops):
	sdb_gt = sdb.GetGeoTransform()
	sdb_cs = osr.SpatialReference()
	sdb_cs.ImportFromWkt(sdb.GetProjectionRef())
	p = Crop(i, j, sdb_gt, sdb_cs)
	if p in crops:
		if Crop(i+1, j, sdb_gt, sdb_cs) == p:
			if Crop(i, j+1, sdb_gt, sdb_cs) == p:
				if Crop(i+1, j+1, sdb_gt, sdb_cs) == p:
					return crops[p]
				else:
					return 'USELESS'
			else:
				return 'USELESS'
		else:
			return 'USELESS'
	else:
		return 'USELESS'


def check_centre(i,j):
	try:
		a = sdb_data[:,j-1,i-1]
		b = sdb_data[:,j-1,i] 
		c = sdb_data[:,j-1,i+1]
		d = sdb_data[:,j,i-1]
		e = sdb_data[:,j,i]
		f = sdb_data[:,j,i+1]
		g = sdb_data[:,j+1,i-1]
		h = sdb_data[:,j+1,i]
		i = sdb_data[:,j+1,i+1]
	except IndexError:
		return []
	if (a != np.array([0,0,0,0,0])).any() and (b != np.array([0,0,0,0,0])).any() and (c != np.array([0,0,0,0,0])).any() and (d != np.array([0,0,0,0,0])).any() and (e != np.array([0,0,0,0,0])).any() and (f != np.array([0,0,0,0,0])).any() and (g != np.array([0,0,0,0,0])).any() and (h != np.array([0,0,0,0,0])).any() and (i != np.array([0,0,0,0,0])).any():
		return [t for n in [a,b,c,d,e,f,g,h,i] for t in list(n)] 
	else:
		return []

data = {}
print('loading data')
for key in os.listdir('E:/Time Series/hdf_files'):
	filename = 'E:/Time Series/hdf_files/'+ key
	f = h5py.File(filename, 'r')
	data[key] = list(list(f.values())[0])
	f.close()

file_object = open('E:/Time Series/9_pixels.pkl', 'rb')
t = pickle.load(file_object)
file_object.close()
print('done loading')
print(t)
sdb = gdal.Open(sat_file)
sdb_ncols = sdb.RasterXSize
sdb_nrows = sdb.RasterYSize
sdb_gt = sdb.GetGeoTransform()
sdb_cs = osr.SpatialReference()
sdb_cs.ImportFromWkt(sdb.GetProjectionRef())
sdb_data = gdal_array.DatasetReadAsArray(sdb,0,0,sdb_ncols, sdb_nrows)
for i in range(t, sdb_ncols):
	for j in range(sdb_nrows):
		example = check_centre(i, j)
		if len(example) == 45:
			crop_name = check_crop_data(i,j,sdb_gt,sdb_cs, crops)
			if crop_name != 'USELESS':
				try:
					data[crop_name].append(example)
				except KeyError:
					data[crop_name] = [example]
	print(i)
	if i%10 == 0:
		if input('save? Y or N: ') == 'Y':
			print('saving', i)
			t = time.time()
			for key, value in data.items():
				if key in ['ALFALFA', 'CORN', 'DEVELOPED', 'FOREST', 'OATS', 'SOYABEENS']: continue
				key1 = 'E:/Time Series/hdf_files/'+key
				key2 = 'E:/Time Series/hdf_files_backup/'+key+'.bkp'
				h5file = tables.open_file(key1, mode='w', title="Test Array")
				root  = h5file.root
				h5file.create_array(root, "test", value)
				h5file.close()
				copyfile(key1, key2)
				print(key, '----', len(value))
			file_object = open('E:/Time Series/9_pixels.pkl', 'wb')
			pickle.dump(i+1, file_object)
			file_object.close()
			copyfile('E:/Time Series/9_pixels.pkl','E:/Time Series/9_pixels.bkp' )
			print('done saving time: ', time.time()-t);
=======
import h5py
import tables
import time
import gc
from osgeo import gdal, osr, ogr, gdal_array
import os
import numpy as np
from numpy.linalg import inv
import _pickle as pickle
from random import shuffle
from shutil import copyfile

sat_file = 'E:/Time Series/satdata/12/1557907_2016-12-29_RE1_3A_Analytic.tif'

main_folder = 'E:/Time Series'

crops = {1:'CORN',4:'SORGHUM', 5:'SOYABEENS', 13:'POP_OR_ORN', 36:'ALFALFA', 28:'OATS', 27:'RYE', 53:'PEAS', 111:'WATER_BODY', 121:'DEVELOPED', 122:'DEVELOPED', 123:'DEVELOPED', 124:'DEVELOPED',141:'FOREST', 142:'FOREST',243:'CABBAGE' }

def Convert(k, old_gt, old_cs, new_cs):
	a = k[0]; s= k[1]
	transform = osr.CoordinateTransformation(old_cs,new_cs)
	o1 = old_gt[0] + a*old_gt[1] + s*old_gt[2]
	o2 = old_gt[3] + a*old_gt[4] + s*old_gt[5]
	d = transform.TransformPoint(o1,o2)
	return (d[0],d[1])

def calculate(a, g):
	B= np.mat([[a[0]-g[0]],[a[1]-g[3]]])
	A = np.mat([[g[1],g[2]],[g[4],g[5]]])
	X = inv(A) * B
	return (int(X[0]), int(X[1]))


def Crop(i,j, sdb_gt, sdb_cs):
	lis = os.listdir(main_folder + '/crop_data')
	for crop_file in lis:
		if crop_file[-4:] == '.tif':
			cd = gdal.Open(main_folder + '/crop_data/' + crop_file)
			cd_gt = cd.GetGeoTransform()
			cd_cs = osr.SpatialReference()
			cd_cs.ImportFromWkt(cd.GetProjectionRef())
			q = Convert((i,j), old_gt = sdb_gt, old_cs = sdb_cs, new_cs = cd_cs)
			ww = calculate(q, cd_gt)
			#print(ww)
			x = ww[0]; y = ww[1]
			if x >= 0 and x < cd.RasterXSize and y >=0 and y < cd.RasterYSize:
				return int(gdal_array.DatasetReadAsArray(cd, x,y,1, 1))
	return 0
			
def check_crop_data(i,j,sdb_gt,sdb_cs, crops):
	sdb_gt = sdb.GetGeoTransform()
	sdb_cs = osr.SpatialReference()
	sdb_cs.ImportFromWkt(sdb.GetProjectionRef())
	p = Crop(i, j, sdb_gt, sdb_cs)
	if p in crops:
		if Crop(i+1, j, sdb_gt, sdb_cs) == p:
			if Crop(i, j+1, sdb_gt, sdb_cs) == p:
				if Crop(i+1, j+1, sdb_gt, sdb_cs) == p:
					return crops[p]
				else:
					return 'USELESS'
			else:
				return 'USELESS'
		else:
			return 'USELESS'
	else:
		return 'USELESS'


def check_centre(i,j):
	try:
		a = sdb_data[:,j-1,i-1]
		b = sdb_data[:,j-1,i] 
		c = sdb_data[:,j-1,i+1]
		d = sdb_data[:,j,i-1]
		e = sdb_data[:,j,i]
		f = sdb_data[:,j,i+1]
		g = sdb_data[:,j+1,i-1]
		h = sdb_data[:,j+1,i]
		i = sdb_data[:,j+1,i+1]
	except IndexError:
		return []
	if (a != np.array([0,0,0,0,0])).any() and (b != np.array([0,0,0,0,0])).any() and (c != np.array([0,0,0,0,0])).any() and (d != np.array([0,0,0,0,0])).any() and (e != np.array([0,0,0,0,0])).any() and (f != np.array([0,0,0,0,0])).any() and (g != np.array([0,0,0,0,0])).any() and (h != np.array([0,0,0,0,0])).any() and (i != np.array([0,0,0,0,0])).any():
		return [t for n in [a,b,c,d,e,f,g,h,i] for t in list(n)] 
	else:
		return []

data = {}
print('loading data')
for key in os.listdir('E:/Time Series/hdf_files'):
	filename = 'E:/Time Series/hdf_files/'+ key
	f = h5py.File(filename, 'r')
	data[key] = list(list(f.values())[0])
	f.close()

file_object = open('E:/Time Series/9_pixels.pkl', 'rb')
t = pickle.load(file_object)
file_object.close()
print('done loading')
print(t)
sdb = gdal.Open(sat_file)
sdb_ncols = sdb.RasterXSize
sdb_nrows = sdb.RasterYSize
sdb_gt = sdb.GetGeoTransform()
sdb_cs = osr.SpatialReference()
sdb_cs.ImportFromWkt(sdb.GetProjectionRef())
sdb_data = gdal_array.DatasetReadAsArray(sdb,0,0,sdb_ncols, sdb_nrows)
for i in range(t, sdb_ncols):
	for j in range(sdb_nrows):
		example = check_centre(i, j)
		if len(example) == 45:
			crop_name = check_crop_data(i,j,sdb_gt,sdb_cs, crops)
			if crop_name != 'USELESS':
				try:
					data[crop_name].append(example)
				except KeyError:
					data[crop_name] = [example]
	print(i)
	if i%10 == 0:
		if input('save? Y or N: ') == 'Y':
			print('saving', i)
			t = time.time()
			for key, value in data.items():
				if key in ['ALFALFA', 'CORN', 'DEVELOPED', 'FOREST', 'OATS', 'SOYABEENS']: continue
				key1 = 'E:/Time Series/hdf_files/'+key
				key2 = 'E:/Time Series/hdf_files_backup/'+key+'.bkp'
				h5file = tables.open_file(key1, mode='w', title="Test Array")
				root  = h5file.root
				h5file.create_array(root, "test", value)
				h5file.close()
				copyfile(key1, key2)
				print(key, '----', len(value))
			file_object = open('E:/Time Series/9_pixels.pkl', 'wb')
			pickle.dump(i+1, file_object)
			file_object.close()
			copyfile('E:/Time Series/9_pixels.pkl','E:/Time Series/9_pixels.bkp' )
			print('done saving time: ', time.time()-t); exit()
>>>>>>> b1d77540898af5ff5f5be875cbd0eee6732525ba
