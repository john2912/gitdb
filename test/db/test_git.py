from lib import *
from gitdb.exc import BadObject
from gitdb.db import GitDB
from gitdb.base import OStream, OInfo
from gitdb.util import hex_to_bin, bin_to_hex
		
class TestGitDB(TestDBBase):
	
	def test_reading(self):
		gdb = GitDB(fixture_path('../../.git/objects'))
		
		# we have packs and loose objects, alternates doesn't necessarily exist
		assert 1 < len(gdb.databases()) < 4
		
		# access should be possible
		gitdb_sha = hex_to_bin("5690fd0d3304f378754b23b098bd7cb5f4aa1976")
		assert isinstance(gdb.info(gitdb_sha), OInfo)
		assert isinstance(gdb.stream(gitdb_sha), OStream)
		assert gdb.size() > 200
		sha_list = list(gdb.sha_iter())
		assert len(sha_list) == gdb.size()
		
		# test partial shas
		for binsha in sha_list:
			assert gdb.partial_to_complete_sha_hex(bin_to_hex(binsha)[:8]) == binsha
		# END for each sha
		
		self.failUnlessRaises(BadObject, gdb.partial_to_complete_sha_hex, "0000")
		
	@with_rw_directory
	def test_writing(self, path):
		gdb = GitDB(path)
		
		# its possible to write objects
		self._assert_object_writing(gdb)
		self._assert_object_writing_async(gdb)
