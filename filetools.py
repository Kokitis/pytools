
import csv
import hashlib
import os
import pandas
from pprint import pprint

def checkDir(path, full = False):
	""" Creates a folder if it doesn't already exist.
		Parameters
		----------
			path: string
				Path to a folder.
			full: bool; default False
				If true, will create any parent folders
				if they do not already exists.
		Returns
		-------
			status: bool
				Whether the folder was successfully created.
	"""

	if not os.path.exists(path):
		if full:
			os.makedirs(path)
		else:
			os.mkdir(path)

	return os.path.exists(path)


def generateFileMd5(filename, blocksize=2**20):
	""" Generates the md5sum of a file. Does
		not require a lot of memory.
		Parameters
		----------
			filename: string
				The file to generate the md5sum for.
			blocksize: int; default 2**20
				The amount of memory to use when
				generating the md5sum string.
		Returns
		-------
			md5sum: string
				The md5sum string.
	"""
	m = hashlib.md5()
	with open( filename , "rb" ) as f:
		while True:
			buf = f.read(blocksize)
			if not buf: break
			m.update( buf )
	return m.hexdigest()

def listAllFiles(folder, exclude = []):
	""" Lists all files in a folder. Includes subfolders.
		Parameters
		----------
			folder: string
				The folder to search through.
			exclude: string, list<string>
				A path or list of paths to exclude from the recursive search.
		Returns
		-------
			list<string>
				A list of all files that were found.
	"""
	if isinstance(exclude, str): exclude = [exclude]
	
	file_list = list()

	for fn in os.listdir(folder):
		abs_path = os.path.join(folder, fn)
		if abs_path in exclude: continue
		if os.path.isdir(abs_path):
			file_list += listAllFiles(abs_path, exclude = exclude)
		elif os.path.isfile(abs_path): #Explicit check
			file_list.append(abs_path)
	return file_list


def searchForDuplicateFiles(folder, by = 'name', expand = False):
	""" Searches for duplicate files in a folder.
		Parameters
		----------
			folder: path
				The folder to search through. subfolders will be included.
			by: {'md5', 'name', 'size'}; default 'md5'
				The method to qualify two files as being the same.
			expand: bool; default False
				Whether to return the full paths to each file or
				only the parts that diverge.
		Return
		------
			duplicates: list<list<string>>
				A list of paired filenames representing identical files.
	"""
	all_files = listAllFiles(folder)

	checked_files = dict()
	_duplicate_keys = list()
	for filename in all_files:
		if by == 'md5':
			file_key = generateFileMd5(filename)
		elif by == 'name':
			file_key = os.path.basename(filename)
		elif by == 'size':
			file_key = os.path.getsize(filename)

		if file_key in checked_files:
			checked_files[file_key].append(filename)
			_duplicate_keys.append(file_key)
		else:
			checked_files[file_key] = [filename]
	_duplicates = list()
	for key in _duplicate_keys:
		_duplicates.append(checked_files[key])
	final_duplicates = list()
	for duplicate in _duplicates:
		duplicate = [i.replace(folder, "") for i in duplicate]
		final_duplicates.append(duplicate)
	return final_duplicates


def test():
	folder = "D:\\Proginoskes\\Documents\\Data\\Original Data\\"
	results = searchForDuplicateFiles(folder)
	pprint(results)
if __name__ == "__main__":
	test()