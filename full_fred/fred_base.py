
from requests.exceptions import RequestException
import requests
import os

# expand on current docstrings to explain with greater clarity
# define tags, sources, series, categories, releases, etc.
# define realtime_start and realtime_end
# create a thing on how to set environment variables to enable broad use 
# integrate ALFRED, GeoFRED

class FredBase:

    def __init__(
            self, 
            api_key: str = None, 
            api_key_file: str = None,
            ):
        """
        FredBase defines methods common to Categories, Releases, 
        Series, Releases, Sources, Tags classes.
        """
        self.__realtime_start = "1776-07-04"
        self.__realtime_end = "9999-12-31"
        self.__url_base = "https://api.stlouisfed.org/fred/"
        self.__api_key = api_key
        self.__api_key_file = api_key_file
        self.__api_key_env_var = False
        if api_key is None and api_key_file is not None:
            self.set_api_key_file(api_key_file)
        elif self.env_api_key_found():
            self.__api_key_env_var = True

    def get_api_key_file(self) -> str:
        """
        Return currently assigned key file.
        """
        return self.__api_key_file

    def set_api_key_file(
            self,
            api_key_file: str,
            ) -> bool:
        """
        Return True if api key file attribute successfully assigned.
        If user-passed api_key_file is not found, let user know.
        """
        if api_key_file is None:
            e = 'set_api_key_file missing api_key_file argument'
            raise TypeError(e)
        if not os.path.isfile(api_key_file):
            e = "Can't find %s, on path" % api_key_file
            raise FileNotFoundError(e)
        self.__api_key_file = api_key_file
        return True

    def _read_api_key_file(
            self,
            ) -> str:
        """
        Read FRED api key from file. This method exists to minimize the
        time that the user's API key is human-readable
        """
        try:
            with open(self.__api_key_file, 'r') as key_file:
                return key_file.readline().strip()
        except FileNotFoundError as e:
            print(e)

    def env_api_key_found(self) -> bool:
        """
        Indicate whether a FRED_API_KEY environment variable is detected.
        """
        elif "FRED_API_KEY" in os.environ.keys():
            if os.environ["FRED_API_KEY"] is not None:
                return True
        return False

    def _add_optional_params(
            self,
            og_url_string: str,
            optional_params: dict,
            ) -> str:
        """
        Create a parameter string that adds any non-None parameters in optional_params to
        og_url_string and return og_url_string with these additions. If all optional_params
        are None, return og_url_string

        Parameters
        ----------
        og_url_string: str
            the string to append new, non-null parameter strings to

        optional_params: dict
            a dictionary mapping parameter strings to actual arguments passed by user
            for example:
                "&tag_group_id=": None 
                "&limit=": 23
            if the value is not None, "&limit=" + str(23) is added to og_url_string

        Returns
        -------
        str
            og_url_string with any existent k, v pairs concatenated to it.

        Notes
        -----
        Not all paramaters passed in optional_params need be optional. Most are.

        If tag_names is a substring of a parameter in optional_params, whitespace is
        replaced with "+" so the request URL encodes the whitespace in a standard way. 
        There's more on this at
        https://fred.stlouisfed.org/docs/api/fred/related_tags.html
        """
        new_url_string = og_url_string
        for k in optional_params.keys():
            if optional_params[k] is not None:
                if k == "&include_release_dates_with_no_data=":
                    try:
                        optional_params[k] = str(optional_params[k]).lower()
                    except TypeError:
                        e = "Cannot cast include_empty to str, " \
                                "cannot create request url to fetch" \
                                " data"
                        print(e)
                if "tag_names" in k:
                    tag_names = optional_params[k] 
                    try:
                        str_names = self._join_strings_by(tag_names, ";")
                        str_names = str_names.strip().replace(" ", "+")
                        optional_params[k] = str_names
                    except TypeError:
                        e = "Cannot add tag_names to FRED query url"
                        print(e)
                try:
                    a_parameter_string = k + str(optional_params[k])
                    new_url_string += a_parameter_string
                except TypeError:
                    print(k + " " + optional_params[k] + " cannot be cast to str")
        return new_url_string

    def _viable_api_key(self) -> str:
        """
        Verifies that there's an api key to make a request url with.
        Raise error if necessary allow methods to catch early in 
        query process whether a request for data can be sent to FRED.
        If there's a usable key, return which one to use
        
        Returns
        -------
        str
            A string indicating where to find user's api key
            attribute: user has set self.__api_key attribute
            env: it's an environment variable
            file: user has specified a file holding the key
        """
        if self.__api_key is None:
            if self.__api_key_file is None:
                if not self.env_api_key_found():
                    raise AttributeError("Cannot locate a FRED API key")
                return 'env'
            return 'file'
        return 'attribute'
    
    def _make_request_url(
            self, 
            var_url: str, 
            ):
        """
        Return the url that can be used to retrieve the desired data given var_url.
        """
        key_to_use = self._viable_api_key()
        url_base = [
                self.__url_base, 
                var_url, 
                "&file_type=json&api_key=",
                ]
        base = "".join(url_base)
        if key_to_use == 'attribute':
            return base + self.__api_key 
        if key_to_use == 'env':
            try:
                return base + os.environ["FRED_API_KEY"] 
            except KeyError as sans:
                print(sans, ' no longer found in environment')
        if key_to_use == 'file':
            return base + self._read_api_key_file()

    # modify: never print api key in message
    def _fetch_data(self, url_prefix: str) -> dict:
        """
        Make request URL, send it to FRED, return JSON upshot
        """
        url = self._make_request_url(url_prefix)
        json_data = self._get_response(url)
        if json_data is None:
            # never print api key in message for security
            message = "Data could not be retrieved, returning None"
            print(message)
            return
        return json_data

    def _get_realtime_date(self, 
            realtime_start: str = None,
            realtime_end: str = None,
            ) -> str:
        """
        Takes a string as input and returns the YYY-MM-DD 
        realtime date string to use for construction of a request url
        """
        rt_start = "&realtime_start="
        rt_end = "&realtime_end="
        if realtime_start is None:
            rt_start += self.__realtime_start
        else:
            try:
                realtime_start = str(realtime_start)
            except TypeError:
                pass # this needs to be more effective
        if realtime_end is None:
            rt_end += self.__realtime_end
        else:
            try:
                realtime_end = str(realtime_end)
            except TypeError:
                pass # this needs to be more effective
        return rt_start + rt_end
        
    def _get_response(self, a_url: str) -> dict:
        """
        Return a JSON dictionary response with data retrieved from a_url
        """
        try:
            response = requests.get(a_url)
        except RequestException:
            return
        return response.json()

    def _append_id_to_url(
            self, 
            a_url_prefix: str,
            an_int_id: int = None,
            a_str_id: str = None,
            ) -> str:
        """
        Return a_url_prefix with either an_int_id or a_str_id appended to it. 
        """
        if an_int_id is None and a_str_id is None:
            raise ValueError("No id argument given, cannot append to url")
        passed_id = an_int_id
        new_url_str = a_url_prefix
        if passed_id is None:
            passed_id = a_str_id
        try:
            new_url_str += str(passed_id)
        except TypeError:
            print("Unable to cast id to str, cannot append to url string")
        return new_url_str

    def _join_strings_by(
            self,
            strings: list,
            use_str: str,
            ) -> str:
        """
        Join an iterable of strings using use_str and return the fused string.
        """
        if strings is None or use_str is None:
            raise TypeError("strings and use_str are both required")
        try:
            fused_str = use_str.join(strings)
        except TypeError:
            print("Unable to join strings using %s" % use_str)
        return fused_str


