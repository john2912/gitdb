# Copyright (C) 2010, 2011 Sebastian Thiel (byronimo@gmail.com) and contributors
#
# This module is part of GitDB and is released under
# the New BSD License: http://www.opensource.org/licenses/bsd-license.php
from base import (
						CompoundDB, 
						ObjectDBW, 
						FileDBBase
					)

from loose import LooseObjectDB
from pack import PackedDB
from ref import ReferenceDB

from gitdb.util import (
						LazyMixin, 
						normpath,
						join,
						dirname
					)
from gitdb.exc import (
						InvalidDBRoot, 
						BadObject, 
						AmbiguousObjectName
						)
import os

__all__ = ('GitDB', 'RefGitDB')


class GitDB(FileDBBase, ObjectDBW, CompoundDB):
	"""A git-style object database, which contains all objects in the 'objects'
	subdirectory.
	:note: The type needs to be initialized on the ./objects directory to function, 
		as it deals solely with object lookup. Use a RefGitDB type if you need
		reference and push support."""
	# Configuration
	PackDBCls = PackedDB
	LooseDBCls = LooseObjectDB
	ReferenceDBCls = ReferenceDB
	
	# Directories
	packs_dir = 'pack'
	loose_dir = ''
	alternates_dir = os.path.join('info', 'alternates')
	
	def __init__(self, root_path):
		"""Initialize ourselves on a git ./objects directory"""
		super(GitDB, self).__init__(root_path)
		
	def _set_cache_(self, attr):
		if attr == '_dbs' or attr == '_loose_db':
			self._dbs = list()
			loose_db = None
			for subpath, dbcls in ((self.packs_dir, self.PackDBCls), 
									(self.loose_dir, self.LooseDBCls),
									(self.alternates_dir, self.ReferenceDBCls)):
				path = self.db_path(subpath)
				if os.path.exists(path):
					self._dbs.append(dbcls(path))
					if dbcls is self.LooseDBCls:
						loose_db = self._dbs[-1]
					# END remember loose db
				# END check path exists
			# END for each db type
			
			# should have at least one subdb
			if not self._dbs:
				raise InvalidDBRoot(self.root_path())
			# END handle error
			
			# we the first one should have the store method
			assert loose_db is not None and hasattr(loose_db, 'store'), "First database needs store functionality"
			
			# finally set the value
			self._loose_db = loose_db
		else:
			super(GitDB, self)._set_cache_(attr)
		# END handle attrs
		
	#{ ObjectDBW interface
		
	def store(self, istream):
		return self._loose_db.store(istream)
		
	def ostream(self):
		return self._loose_db.ostream()
	
	def set_ostream(self, ostream):
		return self._loose_db.set_ostream(ostream)
		
	#} END objectdbw interface
	
	
class RefGitDB(GitDB):
	"""Git like database with support for object lookup as well as reference resolution.
	Our rootpath is set to the actual .git directory (bare on unbare).
	
	The root_path will be the git objects directory. Use git_dir() to obtain the actual top-level 
	git directory."""
	#directories
	objs_dir = 'objects'
	__slots__  = "_git_dir"	# slots has no effect here, its just to keep track of used attrs
	
	def __init__(self, root_path):
		"""Initialize ourselves on the .git directory, or the .git/objects directory."""
		root_path = normpath(root_path)	# truncate trailing /
		self._git_dir = root_path
		if root_path.endswith(self.objs_dir):
			self._git_dir = dirname(root_path)
		else:
			root_path = join(root_path, self.objs_dir)
		#END handle directory
		assert self._git_dir.endswith('.git'), "require initialization on a git directory, got %s" % self._git_dir
		super(RefGitDB, self).__init__(root_path)
	
	
	#{ Interface
	def git_dir(self):
		""":return: main git directory containing objects and references"""
		return self._git_dir
	
	#} END interface
