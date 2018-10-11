__all__ = ['Response', 'datadict']
from typing import *
from dataclasses import dataclass, asdict
from pytools.datatools.dataclass_validation import validate_item
import yaml
import json
from functools import partial, wraps
from pathlib import Path


def coerce_to_safe_value(item: Any) -> Any:
	if isinstance(item, (bool, int, float, str, dict)):
		result = item
	elif isinstance(item, (list, set, tuple)):
		result = [coerce_to_safe_value(i) for i in item]
	elif hasattr(item, 'to_json'):

		result = item.to_json()
	elif hasattr(item, 'tojson'):
		result = item.tojson()
	elif hasattr(item, 'asdict'):
		result = item.asdict()
	elif hasattr(item, 'to_dict'):
		result = item.to_dict()
	elif hasattr(item, 'todict'):
		result = item.todict()
	elif hasattr(item, 'as_dict'):
		result = item.as_dict()
	else:
		result = str(item)

	if isinstance(result, dict):
		result = {k: coerce_to_safe_value(v) for k, v in result.items()}

	return result


# noinspection PyAttributeOutsideInit
@dataclass
class Response:
	"""
		Converts any dataclass into a dict-like object with type-checking.
		Adds a .is_valid attribute which is True if all values are of the required type.
		Supports unpacking with '**'
	"""
	instance_key = 'instanceOf'

	def __getitem__(self, item: str) -> Any:
		try:
			return getattr(self, item)
		except AttributeError:
			message = "'{}' has no key '{}'".format(self.__class__.__name__, item)
			raise KeyError(message)
		except TypeError:
			message = "'{}' must be a string".format(item)
			raise TypeError(message)

	def __post_init__(self):
		pass

	def get(self, key: Any, default: Any = None) -> Any:
		try:
			value = self[key]
		except (KeyError, TypeError, AttributeError):
			value = default
		return value

	def keys(self) -> KeysView:
		return self.fields().keys()

	def values(self) -> List[Any]:
		return [self.get(i) for i in self.keys()]

	def fields(self) -> Dict[str, Any]:
		return self.__annotations__

	def items(self) -> List[Tuple[str, Any]]:
		return list(zip(self.keys(), self.values()))

	def to_dict(self) -> Dict[str, Any]:
		# incase asdict fails for some reason
		# return {k: self.get(k) for k in self.keys()}
		# use safe = True for compatibility with json and yaml.

		result = dict()
		for key in self.fields().keys():  # Only the defined values will be returned.

			value = self.get(key)
			result[key] = value
		return result

	def to_yaml(self, style = None) -> str:
		data = self.to_json()
		yaml_string = yaml.safe_dump(data, default_flow_style = style)

		return yaml_string

	def to_json(self) -> str:
		data = coerce_to_safe_value(self.to_dict())

		return data

	def is_valid(self) -> bool:
		result = True
		for key, value_type in self.fields().items():
			value = self.get(key)
			vstatus = validate_item(value, value_type)
			result = result and vstatus
			if not result:
				is_valid = False
				break
		else:
			is_valid = True

		return is_valid

	@classmethod
	def from_dict(cls, data = None, **kwargs) -> 'Response':
		if data is None:
			data = kwargs
		if Response.instance_key in data:
			data.pop(Response.instance_key)
		# noinspection PyArgumentList
		return cls(**data)

	@classmethod
	def from_yaml(cls, filename: Union[str, Path]) -> 'Response':
		filename = Path(filename)
		d = yaml.load(filename.read_text())
		return cls.from_dict(d)


T = TypeVar('T')
S = TypeVar('S', bound = Response)


def _wrap_dataclass(cls: T) -> S:
	intermediate: S = cls
	allowed = ['__getitem__']
	for key in dir(Response):
		if (key.startswith('_') or key in dir(cls)) and key not in allowed: continue
		# noinspection PyCallByClass
		setattr(intermediate, key, object.__getattribute__(Response, key))
	return intermediate


def datadict(dcls: T) -> Callable[..., S]:
	dcls = dataclass(dcls)
	dcls = _wrap_dataclass(dcls)

	@wraps(dcls)
	def wrapper(*args, **kwargs) -> S:
		obj: S = dcls(*args, **kwargs)
		return obj

	return wrapper


if __name__ == "__main__":
	@datadict
	# @dataclass
	class TestA:
		a: str
		b: int
		c: float


	t = TestA('abc', 12, 3.14)
	# print(t)
	from pprint import pprint
# pprint(t.to_dict())