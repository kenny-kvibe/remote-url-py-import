import functools
import logging
import typing


class Logger:
	NONE     = logging.CRITICAL*2
	CRITICAL = logging.CRITICAL
	ERROR    = logging.ERROR
	WARNING  = logging.WARNING
	INFO     = logging.INFO
	DEBUG    = logging.DEBUG

	_level_to_name = {
		NONE:     'NONE',
		CRITICAL: 'CRITICAL',
		ERROR:    'ERROR',
		WARNING:  'WARNING',
		INFO:     'INFO',
		DEBUG:    'DEBUG'
	}

	_name_to_level = {
		'NONE':     NONE,
		'CRITICAL': CRITICAL,
		'ERROR':    ERROR,
		'WARNING':  WARNING,
		'INFO':     INFO,
		'DEBUG':    DEBUG
	}

	_name  = 'Logger'
	_level = WARNING

	logging.root.name  = _name
	logging.root.level = _level

	@classmethod
	def to_name(cls, level:int) -> str:
		return cls._level_to_name.get(level, cls._level_to_name[cls._level])

	@classmethod
	def to_level(cls, name:str) -> int:
		return cls._name_to_level.get(name.upper(), cls._level)

	@classmethod
	def get_log_level(cls) -> int:
		return cls._level

	@classmethod
	def get_log_levels(cls) -> tuple[str, ...]:
		return tuple(cls._name_to_level)

	@classmethod
	def get_log_level_name(cls) -> str:
		return cls.to_name(cls._level)

	@classmethod
	def set_log_name(cls, name:str):
		cls._name = str(name)
		logging.root.name = cls._name

	@functools.singledispatchmethod
	@classmethod
	def set_log_level(cls, arg:typing.Any):
		""" Argument is `name:str` or `level:int` """
		raise NotImplementedError(
			f'Unsupported type "{type(arg).__name__}" for "arg", supported are: int, str')

	@set_log_level.register
	@classmethod
	def _(cls, name:str):
		if name.upper() in cls._name_to_level.keys():
			cls._level = cls.to_level(name)
			logging.basicConfig(level = cls._level)

	@set_log_level.register
	@classmethod
	def _(cls, level:int):
		if level in cls._level_to_name.keys():
			cls._level = level
			logging.basicConfig(level = cls._level)

	@classmethod
	def log(cls, *msgs:str, sep:str = ' ', level:int|None = None, **log_kwargs):
		logging.log(cls._level if level is None else level, sep.join(msgs), **log_kwargs)

	@classmethod
	def critical(cls, *msgs:str, sep:str = ' ', **log_kwargs):
		cls.log(*msgs, sep=sep, level=cls.CRITICAL, **log_kwargs)

	@classmethod
	def error(cls, *msgs:str, sep:str = ' ', **log_kwargs):
		cls.log(*msgs, sep=sep, level=cls.ERROR, **log_kwargs)

	@classmethod
	def warning(cls, *msgs:str, sep:str = ' ', **log_kwargs):
		cls.log(*msgs, sep=sep, level=cls.WARNING, **log_kwargs)

	@classmethod
	def info(cls, *msgs:str, sep:str = ' ', **log_kwargs):
		cls.log(*msgs, sep=sep, level=cls.INFO, **log_kwargs)

	@classmethod
	def debug(cls, *msgs:str, sep:str = ' ', **log_kwargs):
		cls.log(*msgs, sep=sep, level=cls.DEBUG, **log_kwargs)


def _test() -> int:
	Logger.set_log_name('LOG')
	Logger.set_log_level(Logger.DEBUG)
	Logger.info(f'     Levels: {", ".join(Logger.get_log_levels())}')

	Logger.critical(' Hello from "critical()"')
	Logger.error('    Hello from "error()"')
	Logger.warning('  Hello from "warning()"')
	Logger.info('     Hello from "info()"')
	Logger.debug('    Hello from "debug()"')

	Logger.log('  Hello from "log()"', level=Logger.WARNING)
	return 0


if __name__ == '__main__':
	raise SystemExit(_test())

