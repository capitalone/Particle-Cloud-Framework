# Copyright 2018 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib
import inspect
import pkgutil
from copy import deepcopy
from pcf.core.pcf_exceptions import InvalidConfigException


def generate_pcf_id(flavor, pcf_name):
    return "{}:{}".format(flavor, pcf_name)


def extract_components_from_pcf_id(pcf_id):
    pcf_components = pcf_id.split(":")
    flavor = pcf_components[0]
    name = ":".join(pcf_components[1:])

    return flavor, name


def update_dict(curr_dict, updated_dict):
    new_dict = deepcopy(curr_dict)
    return new_dict, _update_dict(new_dict, updated_dict, diff_dict={})


def diff_dict(curr_dict, updated_dict):
    return _update_dict(curr_dict, updated_dict, diff_dict={}, eval=True)


def _update_dict(curr_dict, updated_dict, eval=False, diff_dict={}, root=True):
    if root:
        diff_dict = {}
        root = False

    if isinstance(updated_dict, dict):
        gen = updated_dict.items()
    elif isinstance(updated_dict, list):
        gen = enumerate(sorted(updated_dict))

    for k, v in gen:
        try:
            cv = curr_dict[k]

            if v is not None and not v:
                if cv != v:
                    diff_dict[k] = {"original": cv, "updated": v}
                    if not eval:
                        curr_dict[k] = v

            elif isinstance(v, dict):
                diff_dict[k] = {}
                _update_dict(cv, v, eval=eval, diff_dict=diff_dict[k], root=root)

                if not diff_dict[k]:
                    diff_dict.pop(k)

            elif isinstance(v, list):
                if not is_list_equal(v, cv):
                    diff_dict[k] = {"original": list(cv), "updated": v}

                    # v_str = json.dumps(v, sort_keys=True)
                    # cv_str = json.dumps(cv, sort_keys=True)
                    # if v_str != cv_str:
                    #     diff_dict[k] = {"original": list(cv),
                    #                     "updated": v}

                    if not eval:
                        curr_dict[k] = v

                        # diff_dict[k] = {}
                        # if len(v) != len(cv):
                        #     diff_dict[k] = {"original": list(cv),
                        #                     "updated": v}
                        # else:
                        #     diff_dict = _update_dict(cv, v, eval=eval, root=root, diff_dict=diff_dict)
                        #
                        # if not diff_dict[k]:
                        #     diff_dict.pop(k)
            elif v != cv:
                diff_dict[k] = {"original": cv, "updated": v}
                if not eval:
                    curr_dict[k] = v
        except Exception as e:
            diff_dict[k] = {"new": v}
            if not eval:
                curr_dict[k] = v

    return diff_dict


def is_dict_update_needed(curr_dict, updated_dict):
    return {} != diff_dict(curr_dict, updated_dict)


def keep_and_replace_keys(curr_dict, keep_replace_dict):
    new_dict = deepcopy(curr_dict)
    keys = list(new_dict.keys())
    for k in keys:
        if k not in keep_replace_dict.keys():
            new_dict.pop(k)
        elif keep_replace_dict[k] and keep_replace_dict[k] != "":
            new_dict[keep_replace_dict[k]] = new_dict.pop(k)

    return new_dict


def keep_and_remove_keys(curr_dict, remove_dict):
    new_dict = deepcopy(curr_dict)
    keys = list(new_dict.keys())
    for k in keys:
        if k in remove_dict.keys():
            new_dict.pop(k)
    return new_dict


def is_list_equal(list_a, list_b):
    if (
        not isinstance(list_a, list)
        or not isinstance(list_b, list)
        or len(list_a) != len(list_b)
    ):
        return False

    try:
        diff = set(list_a) - set(list_b)
        if len(diff) > 0:
            return False

    except TypeError:
        for x in list_a:
            x_exists = False
            for y in list_b:
                if isinstance(x, dict) and isinstance(y, dict):
                    if is_dict_equal(x, y):
                        x_exists = True
                        break

            if not x_exists:
                return False

    return True


def is_dict_equal(dict_a, dict_b):
    if not isinstance(dict_a, dict) or not isinstance(dict_b, dict):
        return False

    dict_equal = True

    for k, v_a in dict_a.items():
        if k not in dict_b:
            dict_equal = False
        else:
            v_b = dict_b[k]
            if isinstance(v_a, list):
                dict_equal = is_list_equal(v_a, v_b)
            elif isinstance(v_a, dict):
                dict_equal = is_dict_equal(v_a, v_b)
            else:
                dict_equal = v_a == v_b

        if not dict_equal:
            break

    return dict_equal


def get_item_from_dicts(key, *dicts):
    if not dicts or len(dicts) == 0:
        return None

    for d in dicts:
        if key in d:
            return d[key]


def replace_value_nested_dict(curr_dict, list_nested_keys, new_value):
    if len(list_nested_keys) == 0:
        return curr_dict
    if isinstance(curr_dict, list):
        for item in curr_dict:
            replace_value_nested_dict(item, list_nested_keys, new_value)
        return curr_dict
    for k,v in curr_dict.items():
        if k == list_nested_keys[0].rstrip('0123456789'):
            if len(list_nested_keys) == 1:
                list_index = list_nested_keys[0][len(list_nested_keys[0].rstrip('0123456789')):]
                if list_index:
                    curr_dict[k][int(list_index)]= new_value
                else:
                    curr_dict[k] = new_value
            else:
                list_nested_keys.pop(0)
                curr_dict[k] = replace_value_nested_dict(
                    curr_dict.get(k, {}), list_nested_keys, new_value
                )

    return curr_dict


def find_nested_dict_value(curr_dict, list_nested_keys):
    if len(list_nested_keys) == 0:
        return ""
    nested_value = None
    for k, v in curr_dict.items():
        if k == list_nested_keys[0]:
            if len(list_nested_keys) == 1:
                nested_value = curr_dict[k]
            else:
                list_nested_keys.pop(0)
                nested_value = find_nested_dict_value(
                    curr_dict.get(k, {}), list_nested_keys
                )

    return nested_value


def find_nested_vars(curr_dict, nested_key=None, var_list=[]):
    """
    Returns a list of tuples with the nested key and var that needs to be replaced by parent

    Args:
        curr_dict (dict): dictionary (can be nested)
        nested_key (str): used for keeping track of nested keys for easy replaces later on
        var_list (list of tuples): used to keep track of all key, var keep pair during recursion

    Returns:
         [(nested_key, var_to_be_replaced), ... ]
    """
    for key, value in curr_dict.items():
        if nested_key:
            new_nested_key = nested_key + "." + key
        else:
            new_nested_key = key

        if isinstance(value, dict):
            find_nested_vars(value, nested_key=new_nested_key, var_list=var_list)
        elif isinstance(value, list):
            for index,item in enumerate(value):
                if isinstance(item, dict) or isinstance(item, list):
                    find_nested_vars(item, nested_key=new_nested_key, var_list=var_list)

                if isinstance(item, str):
                    try:
                        if item[0] == "$":
                            split_value = item[1:].split('$')
                            var_list.append((new_nested_key + str(index), split_value))
                    except Exception as e:
                        print(item)
        else:
            if isinstance(value, str):
                try:
                    if value[0] == "$":
                        split_value = value[1:].split("$")
                        var_list.append((new_nested_key, split_value))
                except Exception as e:
                    print(value)

    return var_list


def param_filter(curr_dict, key_set, remove=False):
    """
    Filters param dictionary to only have keys in the key set

    Args:
        curr_dict (dict): param dictionary
        key_set (set): set of keys you want
        remove (bool): filters by what to remove instead of what to keep
    Returns:
        filtered param dictionary
    """
    if remove:
        return {key: curr_dict[key] for key in curr_dict.keys() if key not in key_set}
    else:
        return {key: curr_dict[key] for key in key_set if key in curr_dict.keys()}


def get_particle_unique_identifiers(flavor_name):
    """
    Gets the unique identifiers for the particle flavor. Uses the particle flavor scanner to search for the given particle.

    Args:
        flavor_name (str): particle flavor name

    Returns:
        unique identifiers (list)
    """
    from pcf.core import particle_flavor_scanner

    particle_flavor = particle_flavor_scanner.get_particle_flavor(flavor_name)

    return particle_flavor.UNIQUE_KEYS


def transform_list_of_dicts_to_desired_list(curr_list, nested_key_name, new_list=[]):
    """
    Returns a list of key values specified by the nested key

    Args:
        curr_list (list): list of dicts to be dissected
        nested_key_name (str): key name within nested dicts desired
        new_list (list): used to append desired key values to new list

    Returns:
        [nested_key_value, ...]
    """
    for x in curr_list:
        for k, v in x.items():
            if k == nested_key_name:
                if v not in new_list:
                    new_list.append(v)
    return new_list


def list_to_dict(key_name, dict_list):
    """
    Converts a list of dicts to a dictionary object

    Args:
        key_name (str): field in dict whose unique value is used as the key
        dict_list (list): list of dicts who has key_name

    Returns:
         dict_from_list (dict): dict whose keys are the values of the key_name field
    """
    dict_from_list = {d[key_name]: d for d in dict_list}
    return dict_from_list


def get_value_from_particles(particles, particle_class, attr_name):
    """
    Searches a list for particles of a specified class and returns one of its attributes

    Args:
        particles (list): list of particles
        particle_class (class): class that is being searched for
        attr_name (string): name of the attribute being returned

    Returns:
        value (string): value of the attr

    """
    if len(particles) > 0:
        particle_list = list(
            filter(lambda x: x.flavor == particle_class.flavor, particles)
        )
        if len(particle_list) == 1:
            particle_list[0].sync_state()
            value = getattr(particle_list[0], attr_name, None)
            if value:
                return value
    raise InvalidConfigException(
        "No parents to get value to from. Please provide the value for {}".format(
            attr_name
        )
    )


def pkg_submodules(package, recursive=True):
    """ Return a list of all submodules in a given package, recursively by default """

    if isinstance(package, str):
        try:
            package = importlib.import_module(package)
        except ImportError:
            return []

    submodules = []
    for _loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name

        try:
            submodules.append(importlib.import_module(full_name))
        except ImportError:
            continue

        if recursive and is_pkg:
            submodules += pkg_submodules(full_name)

    return submodules


def particle_class_from_flavor(flavor):
    """ Return the class object of the given flavor (or None) by searching
        through all particle and quasiparticle submodules in the pcf module
    """

    particle_submodules = pkg_submodules("pcf.particle")
    quasiparticle_submodules = pkg_submodules("pcf.quasiparticle")
    modules = particle_submodules + quasiparticle_submodules

    for module in modules:
        classes = inspect.getmembers(module, inspect.isclass)

        if classes:
            for _name, class_obj in classes:
                if getattr(class_obj, "flavor", None) == flavor:
                    return class_obj

    return None
