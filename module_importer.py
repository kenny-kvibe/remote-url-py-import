import ast
import importlib.abc
import importlib.machinery
import inspect
import os
import requests
import sys
import types
import typing

from logger import Logger


class MetaPathFinder(importlib.abc.MetaPathFinder):
	def _full_mod_name_from_path(self, path:str, is_package:bool | None = None) -> str:
		if is_package:
			return path.replace('/', '.').rsplit('.py', 1)[0].rsplit('/__init__', 1)[0]
		return path.replace('/', '.')

	def _path_from_full_mod_name(self, full_mod_name:str, is_package:bool | None = None) -> str:
		if is_package:
			return full_mod_name.replace('.', '/') + '/__init__.py'
		return full_mod_name.replace('.', '/') + '.py'


class LocalPathFinder(MetaPathFinder):
	def __init__(self):
		if self not in sys.meta_path:
			sys.meta_path.append(self)

	def _find_py_file(
		self,
		full_mod_name:str,
		path:str,
		is_package:bool | None = None
	) -> importlib.machinery.ModuleSpec | None:
		file_path = os.path.realpath(
			os.path.join(path, self._path_from_full_mod_name(full_mod_name, is_package)))
		if not os.path.exists(file_path):
			return None
		return importlib.machinery.ModuleSpec(
			name       = full_mod_name,
			loader     = importlib.machinery.SourceFileLoader(full_mod_name, file_path),
			is_package = is_package)

	def _find_py_file_spec(self, full_mod_name:str, path:str) -> importlib.machinery.ModuleSpec | None:
		Logger.debug(f'Searching PATH by file specification: {full_mod_name}')
		return self._find_py_file(full_mod_name, path)

	def _find_py_package_spec(self, full_mod_name:str, path:str) -> importlib.machinery.ModuleSpec | None:
		Logger.debug(f'Searching PATH by folder/__init__ specification: {full_mod_name}')
		return self._find_py_file(f'{full_mod_name}/__init__', path, True)

	def find_spec(
		self,
		full_mod_name:str,
		path:typing.Sequence[str] | None = None,
		target:types.ModuleType | None = None
	):
		paths = [os.path.dirname(__file__), *sys.path]
		if path is not None:
			paths = list(path) + paths

		Logger.info(f'Searching for LOCAL module: {full_mod_name}')

		for path_item in paths:
			spec = self._find_py_file_spec(full_mod_name, path_item)
			if spec is not None:
				Logger.info(f'SUCCESS, Found LOCAL module (file): {full_mod_name}')
				return spec

			spec = self._find_py_package_spec(full_mod_name, path_item)
			if spec is not None:
				Logger.info(f'SUCCESS, Found LOCAL module (package): {full_mod_name}')
				return spec

		Logger.warning(f'LOCAL module not found: {full_mod_name}')
		return None


class RemotePathFinder(MetaPathFinder):
	def __init__(self, base_url:str):
		Logger.info(f'Module URL: {base_url}')
		self.base_url = base_url
		self.local_finder = LocalPathFinder()
		if self not in sys.meta_path:
			sys.meta_path.append(self)

	def find_spec(
		self,
		full_mod_name:str,
		path:typing.Sequence[str] | None = None,
		target:types.ModuleType | None = None
	) -> importlib.machinery.ModuleSpec | None:
		if full_mod_name in sys.modules.keys():
			Logger.warning(f'Module is already loaded: {full_mod_name}')
			return None

		if self.local_finder not in sys.meta_path:
			spec = self.local_finder.find_spec(full_mod_name, path)
			if spec is not None:
				return spec

		Logger.info(f'Searching for REMOTE module: {full_mod_name}')

		spec = self._find_py_file_spec(full_mod_name)
		if spec is not None:
			Logger.info(f'SUCCESS, Found REMOTE module (file): {full_mod_name}')
			return spec

		spec = self._find_py_package_spec(full_mod_name)
		if spec is not None:
			Logger.info(f'SUCCESS, Found REMOTE module (package): {full_mod_name}')
			return spec

		Logger.warning(f'REMOTE module not found: {full_mod_name}')
		return None

	def _find_py_file(
		self,
		full_mod_name:str,
		is_package:bool | None = None
	) -> importlib.machinery.ModuleSpec | None:
		url = f'{self.base_url}/{self._path_from_full_mod_name(full_mod_name, is_package)}'
		source = self._download_remote_python_source(url, is_package)
		if source is None:
			return None
		return importlib.machinery.ModuleSpec(
			name       = full_mod_name,
			loader     = RemoteFileLoader(full_mod_name, source, url),
			origin     = url,
			is_package = is_package)

	def _find_py_file_spec(self, full_mod_name:str) -> importlib.machinery.ModuleSpec | None:
		Logger.debug(f'Searching URL by file specification: {full_mod_name}')
		return self._find_py_file(full_mod_name)

	def _find_py_package_spec(self, full_mod_name:str) -> importlib.machinery.ModuleSpec | None:
		Logger.debug(f'Searching URL by folder/__init__ specification: {full_mod_name}')
		return self._find_py_file(full_mod_name, True)

	def _download_remote_python_source(self, url:str, is_package:bool | None = None) -> str | None:
		try:
			response:requests.Response = requests.get(url)
			response.raise_for_status()
			Logger.info(f'GET request [{response.status_code}]: {url}')
		except requests.HTTPError as exc:
			Logger.warning(f'{exc.__class__.__name__}: GET request [{exc.response.status_code}]: {exc.response.reason}: {url}')
			return None
		source_code = str(response.text)
		if valid_python_module(source_code, os.path.basename(url)) is not None:
			return source_code
		Logger.warning(
			'Module found but it is not a valid python module: ' +
			self._full_mod_name_from_path(url.split(f"{self.base_url}/", 1)[-1], is_package))
		return None


class RemoteFileLoader(importlib.abc.Loader):
	def __init__(self, full_mod_name:str, source_code:str, url:str):
		self.full_mod_name = full_mod_name
		self.source_code = source_code
		self.url = url

	def create_module(self, spec:importlib.machinery.ModuleSpec) -> types.ModuleType:
		module = sys.modules.get(spec.name)
		if module is None:
			module = types.ModuleType(spec.name)
			sys.modules[spec.name] = module
		return module

	def exec_module(self, module:types.ModuleType) -> types.ModuleType:
		module.__file__ = self.url
		exec(self.source_code, module.__dict__)
		return module

	def get_source(self) -> str:
		return self.source_code


def init_logger(log_level:int = Logger.INFO):
	Logger.set_log_name('RemoteFinder')
	Logger.set_log_level(log_level)


def valid_python_module(code:str, file_name:str = '<unknown>') -> ast.Module | None:
	try:
		return ast.parse(code, file_name)
	except SyntaxError:
		return None


def inspect_python_source_code(src_object) -> str:
	return ''.join(inspect.getsourcelines(src_object)[0])


def imported_modules() -> tuple[str, ...]:
	return tuple(sys.modules.keys())


def importer_meta_classes() -> tuple[str, ...]:
	return tuple(
		(m.__name__ if isinstance(m, type) else m.__class__.__name__)
		for m in sys.meta_path)


def add_import_url(url:str) -> RemotePathFinder:
	return RemotePathFinder(url)


def add_import_github_repo(user_name:str, repo_name:str, repo_branch:str) -> RemotePathFinder:
	return RemotePathFinder(f'https://raw.githubusercontent.com/{user_name}/{repo_name}/{repo_branch}')
