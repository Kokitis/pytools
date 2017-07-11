
import datetime
import re
from numbers import Number
from ._timestamp import Timestamp

class Duration(datetime.timedelta):
	""" Inherits from datetime.timedelta. Designed to parse
		many forms of timedelta representations.
		Notes
		-----
			Each 1 month duration is converted to a 30 day duration,
			and each 1 year duration is converted to a 365 day duration.
		Supported Formats
		-----------------
			ISO Duration: string
				Format: P[nnY][nnM][nnW][nnD]T[nnH][nnM][nn.nnnS] (may be lowercase)
			ISO Interval: string
				Format: [Timestamp]/[Timestamp], [ISO Duration]/[Timestamp],
					[Timestamp]/[ISO Duration]
				Notes: if a combined timestamp/ duration is given,
					only the duration part is used.
			Datetime Tuple: Tuple<number x {6,7}>
				A tuple containing the number values for each datetime field.
				Format: (years, months, days, hours, minutes, seconds)
			Number: Called with Duration([number], [unit]),
				where 'unit' is any of the datetime.timedelta supported types.
			Generic Objects: Any object with days/seconds/microseconds attributes, 
				a .total_seconds() method, or a .to_timedelta() method.
	"""
	duration_regex = re.compile(
		r"""
		[pP]?
		((?P<years>[\d]+)[yY])?[-]?
		((?P<months>[\d]+)[mM])?[-]?
		((?P<weeks>[\d]+)[wW])?[-]?
		((?P<days>[\d]+)[dD])?
		[tT]?
		((?P<hours>[\d]+)[hH])?[-]?
		((?P<minutes>[\d]+)[mM])?[-]?
		((?P<seconds>[\d]+(.[\d]+)?)[sS])?""",
		re.VERBOSE
	)
	timestamp_regex = re.compile(
		r"""
		(?P<date>[\d]{4}-[\d]{2}-[\d]{2})?[\sT]?
		(?P<time>[\d]{2}:[\d]{2}:[\d]{2}(\.[\d]+)?)?""",
		re.VERBOSE
	)

	def __new__(cls, value = None, unit = None, **kwargs):
		"""
			Keyword Arguments
			-----------------
			All arguments are optional and default to 0. 
			Arguments may be integers or floats, and may be positive or negative.
				days:         number; defualt 0
				seconds:      number; default 0
				microseconds: number; default 0
				milliseconds: number; default 0
				minutes:      number; default 0
				hours:        number; default 0
				weeks:        number; default 0
		"""
		if value is None: datetime_keys = kwargs
		else: 
			if unit is not None: kwargs['unit'] = unit
			datetime_keys = cls._parseInput(value, **kwargs)
		return super().__new__(cls, **datetime_keys)

	def __str__(self):
		return self.toiso()

	@classmethod
	def _parseGenericObject(cls, generic, force = False, **kwargs):
		""" Attempts to parse a generic timedelta object. If all attempts
			to extract information from the object fail and 'force' = True (default),
			then a 0-length Duration object is created instead.
		"""
		generic_values = dict()
		# Try extracting the day, seconds, and microseconds from the object.
		try:
			generic_values['days'] = generic.days
			generic_values['seconds'] = generic.seconds
			generic_values['microseconds'] = generic.microseconds
			return generic_values
		except Exception: pass
		# Try extracting the total number of seconds contained in the object
		try:
			generic_values['seconds'] = generic.total_seconds()
			return generic_values
		except AttributeError: pass

		# Try to extract a more usable object type
		try:
			generic_values = generic.to_timedelta()
			return cls._parseGenericObject(generic_values)
		except Exception: pass
		if force:
			return {'seconds': 0}
		else:
			message = "Unsupported generic type: {} ({})".format(generic, type(generic))
			raise ValueError(message)

	@classmethod
	def _parseHumanReadable(cls, string):
		""" Parses durations written in common non-numerical formats."""
		message = "_parseHumanReadable is not implemented."
		raise NotImplementedError(message)

	@classmethod
	def _parseInterval(cls, value):
		""" Parses an ISO interval.
			Supported Formats:
				<start>/<end>      Ex. "2007-03-01T13:00:00Z/2008-05-11T15:30:00Z"
				<start>/<duration> Ex. "2007-03-01T13:00:00Z/P1Y2M10DT2H30M"
				<duration>/<end>   Ex. "P1Y2M10DT2H30M/2008-05-11T15:30:00Z"
			Returns
			-------
				Duration
		"""
		leftright = value.split('/')
		left = leftright[0]
		right = leftright[1] if len(leftright) != 1 else ""
		if '-' in left and '-' in right: result = cls(Timestamp(right) - Timestamp(left))
		elif '-' not in left:  result = cls._parseiso(left)
		elif '-' not in right: result = cls._parseiso(right)
		else:
			message = "Invalid format passed to timetools.{}: {}".format(str(cls), value)
			raise TypeError(message)

		return result

	@classmethod
	def _parseiso(cls, string):
		""" Parses a string with formatted as an ISO duration: PnnYnnMnnWnnDTnnHnnMnnST """
		matches = cls.duration_regex.search(string).groupdict()
		for k, v in matches.items():
			if v is None: v = 0
			else: v = float(v)
			matches[k] = v
		if 'years' in matches:  matches['days'] += 365 * matches.pop('years')
		if 'months' in matches: matches['days'] += 30  * matches.pop('months')

		return matches

	@classmethod
	def _parseInput(cls, element, **kwargs):
		""" Chooses which parse to apply to the input, if supported."""
		if isinstance(element, str):
			result = cls._parseString(element)
		elif isinstance(element, tuple):
			result = cls._parseTuple(element)
		elif isinstance(element, (int, float, Number)):
			result = cls._parseNumber(element, **kwargs)
		else: result = cls._parseGenericObject(element, **kwargs)
		return result

	@classmethod
	def _parseNumericString(cls, string):
		print(string)
		message = "_parseNumericString is not implemented."
		raise NotImplementedError(message)

	@classmethod
	def _parseNumber(cls, number, **kwargs):
		""" parses a (number, unit) tuple. """
		days = 0
		seconds = 0
		microseconds = 0
		if 'unit' in kwargs:
			# Remove any other time values (seconds/days/etc.)
			kwargs = {kwargs['unit'].lower(): number}

		for key, item in kwargs.items():
			key = key.lower()
			if key == 'seconds':   seconds += item
			elif key == 'minutes': seconds += 60*item
			elif key == 'hours':   seconds += 3600*item
			elif key == 'days':    days += item
			elif key == 'weeks':   days = 7 * item
			elif key == 'months':  days = 30*item
			elif key == 'years':   days = 365*item
			elif key == 'microseconds': microseconds += item
			elif key == 'milliseconds': microseconds += item / 1000
		result = {
			'microseconds': microseconds,
			'seconds': seconds,
			'days': days
		}
		return result

	@classmethod
	def _parseString(cls, string):
		if '/' not in string: result = cls._parseiso(string)
		elif len([i for i in string if not i.isdigit()]) < 3:
			result = cls._parseNumericString(string)
		else: result = cls._parseInterval(string)
		return result

	@staticmethod
	def _parseTimestamp(cls, string):
		""" Parses durations formatted as Y:M:D:H:M:S. """
		pass

	@staticmethod
	def _parseTuple(value):
		""" Returns a Duration object generated from a tuple of time values.
			Format: (years, months, days, hours, minutes, seconds[,microseconds])
		"""
		years, months, days, hours, minutes, seconds, *microseconds = value

		if len(microseconds) == 1: microseconds = microseconds[0]
		if microseconds < 1: microseconds *= 1000000
		days += 365 * years + 30 * seconds

		result = {
			'days': days,
			'hours': hours,
			'minutes': minutes,
			'seconds': seconds,
			'microseconds': microseconds
		}

		return result
	######################### Public methods that return a Duration object #########################

	@classmethod
	def fromDict(cls, keys):
		""" Parses a dict of time values. """
		return cls(**keys)

	@classmethod
	def fromString(cls, string):
		result = cls._parseString(string)
		return cls.fromDict(result)

	@classmethod
	def fromTuple(cls, value):
		result = cls._parseTuple(value)
		return cls.fromDict(result)
	##################### Public Methods to convert the timedelta to another format ################

	def todict(self):
		""" Returns a dictionary that can be used to instantiate another timedelta or Duration object. """
		result = {
			'days': self.days,
			'seconds': self.seconds,
			'microseconds': self.microseconds
		}
		return result

	def tolongdict(self):
		""" Returns a dictionary with more human readable date and time keys. """
		original = self.todict()
		longdict = dict()
		# Get date values
		days = original['days']
		longdict['years'], days = divmod(days, 365)
		longdict['weeks'], longdict['days'] = divmod(days, 7)

		# Get time values
		seconds = original['seconds']
		longdict['hours'], seconds = divmod(seconds, 3600)
		longdict['minutes'], longdict['seconds'] = divmod(seconds, 60)
		longdict['seconds'] += original['microseconds'] / 1000000

		return longdict

	def isoformat(self):
		""" To make calls compatible with Timestamp.isoformat() """
		return self.toiso()
	def isoFormat(self):
		""" To be consistent with other function names """
		return self.toiso()
	def toiso(self, compact = True):
		""" Converts the timedelta to an ISO Duration string. By default, 
			weeks are used instead of months, so the original duration string
			used to create to Duration object may differ (but will be equivilant to)
			the output of this method.
			Parameters
			----------
				compact: bool; default False
					Whether to omit emty fields.
		"""

		values = self.tolongdict()
		datetime_map = [
			'P', ('years', 'Y'), ('months', 'M'), ('weeks', 'W'), ('days', 'D'), 
			'T', ('hours', 'H'), ('minutes', 'M'), ('seconds', 'S')]
		isostring = ""
		for key in datetime_map:
			if isinstance(key, tuple):
				value = values.get(key[0], 0)
				if value == 0 and compact: continue
				else: isostring += str(value) + key[1]
			else:
				isostring += key
		isostring = ''.join(isostring)

		if isostring == 'PT' and not compact:  # Duration of 0 seconds
			isostring = 'PT0S'
		if isostring[1] == 'P': isostring = isostring[1:]
		if isostring[-1] == 'T': isostring = isostring[:1]

		return isostring

	def totalSeconds(self):
		return self.total_seconds()

	def totalDays(self):
		values = self.todict()
		days = values['days'] + (24*3600*values['seconds'])
		return days

	def totalYears(self):
		return self.totalDays() / 365

	def to_numeric(self, units):
		"""Backwords-compatible method"""
		units = units.lower()
		if units == 'days':
			value = self.totalDays()
		elif units == 'years':
			value = self.totalYears()
		elif units == 'months':
			value = self.totalYears()*12
		else:
			message = "The units provided '{}' are not supported.".format(units)
			raise ValueError(message)

		return value